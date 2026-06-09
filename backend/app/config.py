"""
配置管理模块
从环境变量读取配置，提供全局配置对象
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """应用配置"""
    # LLM 配置
    LLM_PROVIDER: str = "openai"
    LLM_API_KEY: str = ""
    LLM_MODEL: str = "gpt-4o"
    LLM_BASE_URL: Optional[str] = None

    # MongoDB 配置
    MONGODB_URL: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "a3_learning_agent"

    # Embedding 配置
    # provider: ollama | sentence_transformers | openai_compatible
    # DeepSeek 无 embedding 接口，故向量检索默认走本地 ollama，失败自动回退 sentence_transformers
    EMBEDDING_PROVIDER: str = "ollama"
    EMBEDDING_BASE_URL: str = "http://localhost:11434/v1"   # ollama / openai_compatible
    EMBEDDING_API_KEY: str = "ollama"                        # ollama 占位即可
    EMBEDDING_MODEL: str = "bge-m3"                          # ollama / openai_compatible 模型名
    EMBEDDING_ST_MODEL: str = "BAAI/bge-small-zh-v1.5"       # sentence_transformers 回退模型
    EMBEDDING_DIMENSION: int = 1024                          # 仅供参考，实际维度按真实向量动态确定

    # Agent 调参
    RESOURCE_QUALITY_THRESHOLD: float = 80.0   # Self-Refine 质量阈值
    RESOURCE_MAX_REVISIONS: int = 2            # 资源最大修订轮数
    CRAG_RELEVANCE_THRESHOLD: float = 0.5      # CRAG 单块相关性保留阈值
    CRAG_MIN_RELEVANT: int = 1                 # 低于此数量触发 query 改写重试

    # 安全配置
    GUARDRAILS_ENABLED: bool = True

    # 可观测性配置
    LANGFUSE_ENABLED: bool = False
    LANGFUSE_PUBLIC_KEY: str = ""
    LANGFUSE_SECRET_KEY: str = ""
    LANGFUSE_HOST: str = "http://localhost:3000"

    # 服务配置
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# 全局配置实例
settings = Settings()
