"""
Agent记忆服务
实现三层记忆架构：核心记忆、回忆记忆、归档记忆
模拟Letta（原MemGPT）的记忆管理
"""
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import logging

from app.database import get_collection

logger = logging.getLogger(__name__)


class MemoryService:
    """Agent记忆服务"""

    async def get_core_memory(self, user_id: str) -> Dict:
        """
        获取核心记忆
        核心记忆包含当前活跃画像、会话上下文、当前学习目标

        Args:
            user_id: 用户ID

        Returns:
            Dict: 核心记忆内容
        """
        try:
            # 从MongoDB获取核心记忆
            memory = await get_collection("core_memory").find_one({"user_id": user_id})
            if memory:
                return memory.get("content", {})

            # 返回默认核心记忆
            return {
                "user_id": user_id,
                "current_profile": {},
                "current_goal": "",
                "session_context": "",
                "updated_at": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Get core memory error: {e}")
            return {}

    async def update_core_memory(
        self,
        user_id: str,
        key: str,
        value: any
    ):
        """
        更新核心记忆

        Args:
            user_id: 用户ID
            key: 记忆键
            value: 记忆值
        """
        try:
            memory = await self.get_core_memory(user_id)
            memory[key] = value
            memory["updated_at"] = datetime.now().isoformat()

            await get_collection("core_memory").update_one(
                {"user_id": user_id},
                {"$set": {"content": memory}},
                upsert=True
            )

        except Exception as e:
            logger.error(f"Update core memory error: {e}")

    async def search_recall_memory(
        self,
        user_id: str,
        query: str = "",
        limit: int = 10,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[Dict]:
        """
        搜索回忆记忆
        回忆记忆包含对话历史、学习行为时间线

        Args:
            user_id: 用户ID
            query: 搜索查询（可选）
            limit: 返回数量限制
            start_time: 开始时间
            end_time: 结束时间

        Returns:
            List[Dict]: 回忆记忆列表
        """
        try:
            # 构建查询条件
            query_filter = {"user_id": user_id}

            if start_time:
                query_filter["timestamp"] = {"$gte": start_time}
            if end_time:
                if "timestamp" in query_filter:
                    query_filter["timestamp"]["$lte"] = end_time
                else:
                    query_filter["timestamp"] = {"$lte": end_time}

            # 如果有查询文本，添加文本搜索
            if query:
                query_filter["$text"] = {"$search": query}

            # 查询对话历史
            cursor = get_collection("chat_messages").find(
                query_filter
            ).sort("timestamp", -1).limit(limit)

            messages = await cursor.to_list(limit)

            # 查询学习行为
            behavior_cursor = get_collection("learning_behaviors").find(
                query_filter
            ).sort("timestamp", -1).limit(limit)

            behaviors = await behavior_cursor.to_list(limit)

            # 合并并排序
            results = []
            for msg in messages:
                results.append({
                    "type": "message",
                    "content": msg.get("content", ""),
                    "timestamp": msg.get("timestamp"),
                    "role": msg.get("role")
                })

            for behavior in behaviors:
                results.append({
                    "type": "behavior",
                    "content": behavior.get("type", ""),
                    "timestamp": behavior.get("timestamp"),
                    "details": behavior.get("details", {})
                })

            # 按时间排序
            results.sort(key=lambda x: x.get("timestamp", datetime.min), reverse=True)
            return results[:limit]

        except Exception as e:
            logger.error(f"Search recall memory error: {e}")
            return []

    async def archive_memory(
        self,
        user_id: str,
        content: str,
        metadata: Optional[Dict] = None
    ):
        """
        写入归档记忆
        归档记忆包含历史画像版本、已完成的资源、学习成果

        Args:
            user_id: 用户ID
            content: 记忆内容
            metadata: 元数据
        """
        try:
            archive = {
                "user_id": user_id,
                "content": content,
                "metadata": metadata or {},
                "timestamp": datetime.now()
            }

            await get_collection("archival_memory").insert_one(archive)

        except Exception as e:
            logger.error(f"Archive memory error: {e}")

    async def search_archival_memory(
        self,
        user_id: str,
        query: str,
        limit: int = 5
    ) -> List[Dict]:
        """
        语义搜索归档记忆

        Args:
            user_id: 用户ID
            query: 搜索查询
            limit: 返回数量限制

        Returns:
            List[Dict]: 归档记忆列表
        """
        try:
            # 使用MongoDB文本搜索
            cursor = get_collection("archival_memory").find(
                {
                    "user_id": user_id,
                    "$text": {"$search": query}
                }
            ).limit(limit)

            memories = await cursor.to_list(limit)
            return [
                {
                    "content": m.get("content", ""),
                    "metadata": m.get("metadata", {}),
                    "timestamp": m.get("timestamp")
                }
                for m in memories
            ]

        except Exception as e:
            logger.error(f"Search archival memory error: {e}")
            return []

    async def core_memory_append(
        self,
        user_id: str,
        label: str,
        content: str
    ):
        """
        追加核心记忆（模拟Letta的core_memory_append）

        Args:
            user_id: 用户ID
            label: 记忆标签
            content: 要追加的内容
        """
        try:
            memory = await self.get_core_memory(user_id)

            if label in memory:
                # 如果已存在，追加内容
                if isinstance(memory[label], str):
                    memory[label] += f"\n{content}"
                elif isinstance(memory[label], list):
                    memory[label].append(content)
            else:
                memory[label] = content

            memory["updated_at"] = datetime.now().isoformat()

            await get_collection("core_memory").update_one(
                {"user_id": user_id},
                {"$set": {"content": memory}},
                upsert=True
            )

        except Exception as e:
            logger.error(f"Core memory append error: {e}")

    async def archival_memory_insert(
        self,
        user_id: str,
        content: str,
        metadata: Optional[Dict] = None
    ):
        """
        插入归档记忆（模拟Letta的archival_memory_insert）

        Args:
            user_id: 用户ID
            content: 记忆内容
            metadata: 元数据
        """
        await self.archive_memory(user_id, content, metadata)


# 全局记忆服务实例
memory_service = MemoryService()
