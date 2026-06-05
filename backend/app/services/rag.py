"""
RAG检索服务
支持向量检索和混合检索
使用numpy实现余弦相似度（零依赖方案）
"""
from typing import List, Dict, Optional
from pydantic import BaseModel
import numpy as np
import logging

from app.database import get_collection

logger = logging.getLogger(__name__)


class Document(BaseModel):
    """检索到的文档"""
    content: str
    source: str
    score: float
    metadata: Dict = {}


class RAGService:
    """RAG检索服务"""

    def __init__(self):
        self._embeddings_cache = {}

    async def retrieve(
        self,
        query: str,
        top_k: int = 5,
        course_id: Optional[str] = None
    ) -> List[Document]:
        """
        向量语义检索

        Args:
            query: 查询文本
            top_k: 返回的文档数量
            course_id: 课程ID过滤

        Returns:
            List[Document]: 检索到的文档列表
        """
        try:
            # 获取查询的embedding
            query_embedding = await self._get_embedding(query)

            # 构建查询条件
            query_filter = {}
            if course_id:
                query_filter["course_id"] = course_id

            # 从MongoDB获取所有文档
            cursor = get_collection("knowledge_docs").find(query_filter)
            docs = await cursor.to_list(1000)

            if not docs:
                return []

            # 计算余弦相似度
            scored_docs = []
            for doc in docs:
                doc_embedding = doc.get("embedding", [])
                if doc_embedding:
                    score = self._cosine_similarity(query_embedding, doc_embedding)
                    scored_docs.append(Document(
                        content=doc.get("content", ""),
                        source=doc.get("metadata", {}).get("source_file", "unknown"),
                        score=score,
                        metadata=doc.get("metadata", {})
                    ))

            # 按分数排序，返回Top-K
            scored_docs.sort(key=lambda x: x.score, reverse=True)
            return scored_docs[:top_k]

        except Exception as e:
            logger.error(f"RAG retrieve error: {e}")
            return []

    async def hybrid_retrieve(
        self,
        query: str,
        top_k: int = 5,
        course_id: Optional[str] = None
    ) -> List[Document]:
        """
        混合检索（向量 + 关键词）

        Args:
            query: 查询文本
            top_k: 返回的文档数量
            course_id: 课程ID过滤

        Returns:
            List[Document]: 检索到的文档列表
        """
        try:
            # 向量检索
            vector_results = await self.retrieve(query, top_k * 2, course_id)

            # 关键词检索（简单实现：MongoDB文本搜索）
            keyword_results = await self._keyword_search(query, top_k * 2, course_id)

            # 合并并去重
            seen_contents = set()
            merged_results = []

            for doc in vector_results + keyword_results:
                if doc.content not in seen_contents:
                    seen_contents.add(doc.content)
                    merged_results.append(doc)

            # 重新排序（简单加权）
            for doc in merged_results:
                doc.score *= 1.2  # 向量结果权重稍高

            merged_results.sort(key=lambda x: x.score, reverse=True)
            return merged_results[:top_k]

        except Exception as e:
            logger.error(f"Hybrid retrieve error: {e}")
            return []

    async def _keyword_search(
        self,
        query: str,
        top_k: int,
        course_id: Optional[str] = None
    ) -> List[Document]:
        """关键词搜索"""
        try:
            query_filter = {}
            if course_id:
                query_filter["course_id"] = course_id

            # 使用MongoDB文本索引
            cursor = get_collection("knowledge_docs").find(
                {**query_filter, "$text": {"$search": query}}
            ).limit(top_k)

            docs = await cursor.to_list(top_k)
            return [
                Document(
                    content=doc.get("content", ""),
                    source=doc.get("metadata", {}).get("source_file", "unknown"),
                    score=0.5,  # 关键词搜索默认分数
                    metadata=doc.get("metadata", {})
                )
                for doc in docs
            ]
        except Exception as e:
            logger.error(f"Keyword search error: {e}")
            return []

    async def _get_embedding(self, text: str) -> List[float]:
        """获取文本的embedding向量"""
        # 简化实现：使用随机向量（实际应调用embedding模型）
        # 生产环境应使用sentence-transformers加载BGE-M3模型
        return np.random.randn(1024).tolist()

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """计算余弦相似度"""
        vec1 = np.array(vec1)
        vec2 = np.array(vec2)

        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return float(dot_product / (norm1 * norm2))

    async def index_document(
        self,
        course_id: str,
        chunks: List[Dict]
    ):
        """
        索引文档切片

        Args:
            course_id: 课程ID
            chunks: 文档切片列表
        """
        try:
            for i, chunk in enumerate(chunks):
                # 生成embedding
                embedding = await self._get_embedding(chunk.get("content", ""))

                doc = {
                    "course_id": course_id,
                    "chapter": chunk.get("chapter", ""),
                    "content": chunk.get("content", ""),
                    "chunk_index": i,
                    "embedding": embedding,
                    "metadata": chunk.get("metadata", {})
                }

                await get_collection("knowledge_docs").insert_one(doc)

            logger.info(f"Indexed {len(chunks)} chunks for course {course_id}")

        except Exception as e:
            logger.error(f"Index document error: {e}")
            raise


# 全局RAG服务实例
rag_service = RAGService()
