"""
RAG 检索服务 —— 真实向量检索 + CRAG（Corrective RAG）

相比旧版改进：
- 删除 `np.random.randn` 假向量，改用 embedding_service 的真实向量。
- 新增 crag_retrieve()：真召回 → LLM 逐块相关性评分 → 过滤 → 不足则改写 query 重试一次，
  返回 knowledge_sufficient 标志，作为「防幻觉」的依据（参考 CRAG / Self-RAG）。
- cosine 增加维度对齐保护，避免不同 embedding 模型混用时崩溃。
"""
from typing import List, Dict, Optional
from pydantic import BaseModel
import numpy as np
import logging

from app.database import get_collection
from app.services.embedding import embedding_service
from app.services.llm import structured
from app.config import settings

logger = logging.getLogger(__name__)


class Document(BaseModel):
    """检索到的文档片段"""
    content: str
    source: str
    score: float
    metadata: Dict = {}


class CRAGResult(BaseModel):
    """CRAG 检索结果"""
    chunks: List[Document] = []
    citations: List[str] = []           # 去重后的来源列表
    knowledge_sufficient: bool = True   # 知识库是否足以支撑作答（防幻觉关键标志）
    notes: str = ""                     # 说明（如改写、知识不足等）


# ---- CRAG 内部使用的结构化 schema ----
class _ChunkGrade(BaseModel):
    index: int
    relevant: bool
    score: float  # 0~1


class _GradeResult(BaseModel):
    grades: List[_ChunkGrade]


class _RewrittenQuery(BaseModel):
    query: str


class RAGService:
    """RAG 检索服务"""

    def __init__(self):
        self._embeddings_cache = {}

    # ====================== 基础向量检索 ======================

    async def retrieve(
        self,
        query: str,
        top_k: int = 5,
        course_id: Optional[str] = None,
    ) -> List[Document]:
        """真实向量语义检索（余弦相似度）"""
        try:
            query_embedding = await embedding_service.embed_one(query)

            query_filter: Dict = {}
            if course_id:
                query_filter["course_id"] = course_id

            cursor = get_collection("knowledge_docs").find(query_filter)
            docs = await cursor.to_list(2000)
            if not docs:
                return []

            scored: List[Document] = []
            for doc in docs:
                doc_embedding = doc.get("embedding", [])
                if not doc_embedding:
                    continue
                score = self._cosine_similarity(query_embedding, doc_embedding)
                scored.append(Document(
                    content=doc.get("content", ""),
                    source=doc.get("metadata", {}).get("source_file", "unknown"),
                    score=score,
                    metadata=doc.get("metadata", {}),
                ))

            scored.sort(key=lambda x: x.score, reverse=True)
            return scored[:top_k]
        except Exception as e:  # noqa: BLE001
            logger.error(f"RAG retrieve error: {e}")
            return []

    async def hybrid_retrieve(
        self,
        query: str,
        top_k: int = 5,
        course_id: Optional[str] = None,
    ) -> List[Document]:
        """混合检索（向量 + 关键词），保留供 knowledge_search 工具使用"""
        try:
            vector_results = await self.retrieve(query, top_k * 2, course_id)
            keyword_results = await self._keyword_search(query, top_k * 2, course_id)

            seen, merged = set(), []
            for doc in vector_results + keyword_results:
                if doc.content not in seen:
                    seen.add(doc.content)
                    merged.append(doc)
            merged.sort(key=lambda x: x.score, reverse=True)
            return merged[:top_k]
        except Exception as e:  # noqa: BLE001
            logger.error(f"Hybrid retrieve error: {e}")
            return []

    # ====================== CRAG（防幻觉核心） ======================

    async def crag_retrieve(
        self,
        query: str,
        top_k: int = 5,
        course_id: Optional[str] = None,
        allow_rewrite: bool = True,
    ) -> CRAGResult:
        """
        纠错式检索：召回 → LLM 评分过滤 → 不足则改写 query 重试一次。

        返回 knowledge_sufficient，让上层智能体据此「有据则答、无据则声明不足」，从源头防幻觉。
        """
        candidates = await self.retrieve(query, max(top_k * 2, 8), course_id)
        if not candidates:
            return CRAGResult(
                chunks=[], citations=[], knowledge_sufficient=False,
                notes="知识库中未检索到任何内容（可能未建索引或 embedding 后端不可用）",
            )

        graded = await self._grade_relevance(query, candidates)
        threshold = settings.CRAG_RELEVANCE_THRESHOLD
        relevant = [c for c, g in graded if g.relevant and g.score >= threshold]

        notes = ""
        if len(relevant) < settings.CRAG_MIN_RELEVANT and allow_rewrite:
            # 相关结果不足 → 改写 query 再试一次
            new_query = await self._rewrite_query(query)
            if new_query and new_query != query:
                notes = f"原查询相关资料不足，已改写为「{new_query}」重试。"
                retry = await self.crag_retrieve(
                    new_query, top_k, course_id, allow_rewrite=False
                )
                # 合并去重
                merged = {c.content: c for c in relevant}
                for c in retry.chunks:
                    merged.setdefault(c.content, c)
                relevant = list(merged.values())

        relevant.sort(key=lambda x: x.score, reverse=True)
        relevant = relevant[:top_k]
        citations = list(dict.fromkeys(c.source for c in relevant))
        sufficient = len(relevant) >= settings.CRAG_MIN_RELEVANT

        if not sufficient and not notes:
            notes = "知识库中缺乏与该主题强相关的资料。"

        return CRAGResult(
            chunks=relevant, citations=citations,
            knowledge_sufficient=sufficient, notes=notes,
        )

    async def _grade_relevance(self, query, candidates: List[Document]):
        """LLM 一次性对所有候选块评分（失败则退化为向量分数）"""
        try:
            listing = "\n\n".join(
                f"[{i}] {c.content[:400]}" for i, c in enumerate(candidates)
            )
            messages = [
                {"role": "system", "content":
                    "你是检索相关性评审。判断每个文档片段是否能帮助回答用户问题，"
                    "给出 relevant(true/false) 与 score(0~1)。只评估相关性，不要编造内容。"},
                {"role": "user", "content":
                    f"用户问题：{query}\n\n候选片段：\n{listing}"},
            ]
            result = await structured(messages, _GradeResult, temperature=0.0)
            by_index = {g.index: g for g in result.grades}
            graded = []
            for i, c in enumerate(candidates):
                g = by_index.get(i, _ChunkGrade(index=i, relevant=c.score > 0.3, score=c.score))
                graded.append((c, g))
            return graded
        except Exception as e:  # noqa: BLE001
            logger.warning(f"CRAG 评分失败，退化为向量分数: {e}")
            return [
                (c, _ChunkGrade(index=i, relevant=c.score > 0.3, score=float(c.score)))
                for i, c in enumerate(candidates)
            ]

    async def _rewrite_query(self, query: str) -> str:
        """改写检索 query（扩展同义/上位概念以提高召回）"""
        try:
            messages = [
                {"role": "system", "content":
                    "你是检索查询优化器。将用户问题改写为更利于知识库检索的查询，"
                    "可补充同义词/学科术语。只输出改写后的查询字符串。"},
                {"role": "user", "content": f"原查询：{query}"},
            ]
            result = await structured(messages, _RewrittenQuery, temperature=0.3)
            return result.query.strip()
        except Exception as e:  # noqa: BLE001
            logger.warning(f"query 改写失败: {e}")
            return query

    # ====================== 关键词检索 / 索引 ======================

    async def _keyword_search(
        self, query: str, top_k: int, course_id: Optional[str] = None
    ) -> List[Document]:
        """MongoDB 关键词检索（需文本索引；无索引则静默返回空）"""
        try:
            query_filter: Dict = {"$text": {"$search": query}}
            if course_id:
                query_filter["course_id"] = course_id
            cursor = get_collection("knowledge_docs").find(query_filter).limit(top_k)
            docs = await cursor.to_list(top_k)
            return [
                Document(
                    content=doc.get("content", ""),
                    source=doc.get("metadata", {}).get("source_file", "unknown"),
                    score=0.5,
                    metadata=doc.get("metadata", {}),
                )
                for doc in docs
            ]
        except Exception as e:  # noqa: BLE001
            logger.debug(f"关键词检索不可用（可忽略）: {e}")
            return []

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """余弦相似度（维度不一致时返回 0，避免不同模型混用崩溃）"""
        if not vec1 or not vec2 or len(vec1) != len(vec2):
            return 0.0
        a, b = np.array(vec1), np.array(vec2)
        n1, n2 = np.linalg.norm(a), np.linalg.norm(b)
        if n1 == 0 or n2 == 0:
            return 0.0
        return float(np.dot(a, b) / (n1 * n2))

    async def index_document(self, course_id: str, chunks: List[Dict]):
        """索引文档切片（批量真实 embedding）"""
        try:
            texts = [c.get("content", "") for c in chunks]
            embeddings = await embedding_service.embed_batch(texts)
            dim = len(embeddings[0]) if embeddings and embeddings[0] else 0

            docs = []
            for i, (chunk, emb) in enumerate(zip(chunks, embeddings)):
                docs.append({
                    "course_id": course_id,
                    "chapter": chunk.get("chapter", ""),
                    "content": chunk.get("content", ""),
                    "chunk_index": i,
                    "embedding": emb,
                    "embedding_model": settings.EMBEDDING_MODEL,
                    "embedding_dim": dim,
                    "metadata": chunk.get("metadata", {}),
                })
            if docs:
                await get_collection("knowledge_docs").insert_many(docs)
            logger.info(f"Indexed {len(docs)} chunks for course {course_id} (dim={dim})")
        except Exception as e:  # noqa: BLE001
            logger.error(f"Index document error: {e}")
            raise


# 全局 RAG 服务实例
rag_service = RAGService()
