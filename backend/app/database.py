"""
MongoDB 数据库连接管理
提供异步MongoDB连接和常用集合访问
"""
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import IndexModel, ASCENDING
from typing import Optional
import logging

from app.config import settings

logger = logging.getLogger(__name__)

# 全局数据库客户端
_client: Optional[AsyncIOMotorClient] = None
_db = None


async def connect_db():
    """连接MongoDB数据库"""
    global _client, _db
    try:
        _client = AsyncIOMotorClient(settings.MONGODB_URL)
        _db = _client[settings.MONGODB_DB_NAME]
        logger.info(f"Connected to MongoDB: {settings.MONGODB_URL}")
        await init_indexes()
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        raise


async def close_db():
    """关闭数据库连接"""
    global _client
    if _client:
        _client.close()
        logger.info("MongoDB connection closed")


def get_db():
    """获取数据库实例"""
    return _db


def get_collection(name: str):
    """获取指定集合"""
    return _db[name]


async def init_indexes():
    """初始化数据库索引"""
    db = _db

    # users 集合索引
    await db.users.create_indexes([
        IndexModel([("username", ASCENDING)], unique=True)
    ])

    # profiles 集合索引
    await db.profiles.create_indexes([
        IndexModel([("user_id", ASCENDING)]),
        IndexModel([("user_id", ASCENDING), ("version", ASCENDING)])
    ])

    # chat_messages 集合索引
    await db.chat_messages.create_indexes([
        IndexModel([("session_id", ASCENDING)]),
        IndexModel([("timestamp", ASCENDING)])
    ])

    # resources 集合索引
    await db.resources.create_indexes([
        IndexModel([("user_id", ASCENDING)]),
        IndexModel([("topic", ASCENDING)]),
        IndexModel([("resource_type", ASCENDING)])
    ])

    # learning_paths 集合索引
    await db.learning_paths.create_indexes([
        IndexModel([("user_id", ASCENDING)]),
        IndexModel([("user_id", ASCENDING), ("topic", ASCENDING)])
    ])

    # tasks 集合索引
    await db.tasks.create_indexes([
        IndexModel([("task_id", ASCENDING)], unique=True)
    ])

    # knowledge_docs 集合索引
    await db.knowledge_docs.create_indexes([
        IndexModel([("course_id", ASCENDING)]),
        IndexModel([("chunk_index", ASCENDING)])
    ])

    logger.info("Database indexes initialized")
