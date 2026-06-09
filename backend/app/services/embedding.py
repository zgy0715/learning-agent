"""
Embedding 向量服务 —— 真实文本向量化

替代原 rag.py 中 `np.random.randn` 的假向量。支持多后端并自动回退：
  1. ollama / openai_compatible：走 OpenAI 兼容的 /embeddings 接口（默认 ollama bge-m3）
  2. sentence_transformers：纯 Python 本地模型，离线可用，作为兜底

设计要点：
- 任一后端可用即返回真实向量；全部失败则抛出明确错误（绝不返回随机/假向量）
- 维度由真实向量动态决定（bge-m3=1024, bge-small-zh=512），cosine 比较时按维度对齐
- 带缓存，批量优先
"""
from typing import List, Optional, Callable, Awaitable
import asyncio
import logging
import hashlib

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    """多后端文本向量化服务（带自动回退与缓存）"""

    def __init__(self):
        self._cache: dict[str, List[float]] = {}
        self._st_model = None          # sentence_transformers 模型懒加载
        self._st_failed = False        # 标记 ST 不可用，避免反复重试
        self._dim: Optional[int] = None  # 运行期实际向量维度

    # ---------- 对外接口 ----------

    async def embed_one(self, text: str) -> List[float]:
        """向量化单条文本"""
        result = await self.embed_batch([text])
        return result[0]

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """向量化一批文本（带缓存）"""
        if not texts:
            return []

        # 命中缓存的直接取，未命中的批量请求
        pending_idx = [i for i, t in enumerate(texts) if self._key(t) not in self._cache]
        if pending_idx:
            pending_texts = [texts[i] for i in pending_idx]
            vectors = await self._embed_with_fallback(pending_texts)
            for i, vec in zip(pending_idx, vectors):
                self._cache[self._key(texts[i])] = vec
                if self._dim is None and vec:
                    self._dim = len(vec)

        return [self._cache[self._key(t)] for t in texts]

    @property
    def dimension(self) -> Optional[int]:
        return self._dim

    # ---------- 后端回退编排 ----------

    async def _embed_with_fallback(self, texts: List[str]) -> List[List[float]]:
        """按优先级依次尝试各后端，返回首个成功结果"""
        backends = self._backend_chain()
        last_err: Optional[Exception] = None

        for name, fn in backends:
            try:
                vectors = await fn(texts)
                if vectors and all(v for v in vectors):
                    logger.debug(f"Embedding via [{name}] ok, dim={len(vectors[0])}")
                    return vectors
            except Exception as e:  # noqa: BLE001
                last_err = e
                logger.warning(f"Embedding backend [{name}] failed: {e}")

        # 所有后端均失败：明确报错，绝不返回假向量
        raise RuntimeError(
            "所有 embedding 后端均不可用，无法进行真实向量检索。"
            "请确保已运行 ollama（ollama pull bge-m3）或安装 sentence-transformers。"
            f" 最后错误: {last_err}"
        )

    def _backend_chain(self) -> List[tuple[str, Callable[[List[str]], Awaitable[List[List[float]]]]]]:
        """根据配置决定后端尝试顺序"""
        provider = (settings.EMBEDDING_PROVIDER or "ollama").lower()
        oai = ("openai_compatible", self._embed_openai_compatible)
        st = ("sentence_transformers", self._embed_sentence_transformers)
        if provider == "sentence_transformers":
            return [st, oai]
        # ollama 与 openai_compatible 走同一条 OpenAI 兼容路径
        return [oai, st]

    # ---------- 后端实现 ----------

    async def _embed_openai_compatible(self, texts: List[str]) -> List[List[float]]:
        """OpenAI 兼容 /embeddings 接口（ollama 默认 http://localhost:11434/v1）"""
        base = settings.EMBEDDING_BASE_URL.rstrip("/")
        url = f"{base}/embeddings"
        headers = {"Authorization": f"Bearer {settings.EMBEDDING_API_KEY or 'sk'}"}
        payload = {"model": settings.EMBEDDING_MODEL, "input": texts}

        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
        # 按 index 排序，保证与输入顺序一致
        items = sorted(data["data"], key=lambda x: x.get("index", 0))
        return [item["embedding"] for item in items]

    async def _embed_sentence_transformers(self, texts: List[str]) -> List[List[float]]:
        """本地 sentence_transformers 模型（CPU 友好，放线程池避免阻塞事件循环）"""
        if self._st_failed:
            raise RuntimeError("sentence_transformers 不可用（已标记）")

        if self._st_model is None:
            self._st_model = await asyncio.to_thread(self._load_st_model)

        def _encode() -> List[List[float]]:
            embs = self._st_model.encode(
                texts, normalize_embeddings=True, convert_to_numpy=True
            )
            return embs.tolist()

        return await asyncio.to_thread(_encode)

    def _load_st_model(self):
        """懒加载 ST 模型（首次会下载）"""
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as e:
            self._st_failed = True
            raise RuntimeError("未安装 sentence-transformers") from e
        logger.info(f"加载本地 embedding 模型: {settings.EMBEDDING_ST_MODEL}（首次会下载）")
        return SentenceTransformer(settings.EMBEDDING_ST_MODEL)

    @staticmethod
    def _key(text: str) -> str:
        h = hashlib.md5(text.encode("utf-8")).hexdigest()
        return f"{settings.EMBEDDING_MODEL}:{h}"


# 全局单例
embedding_service = EmbeddingService()
