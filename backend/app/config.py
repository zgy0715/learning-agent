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
    EMBEDDING_MODEL: str = "BAAI/bge-m3"
    EMBEDDING_DIMENSION: int = 1024

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
