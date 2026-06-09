"""
路径规划 Agent（真 LangGraph 实现）

对外保持 plan() / handle_feedback() 契约，内部驱动 path_graph：
  plan：  CRAG 了解知识结构 → LLM 按画像规划 → 补全字段
  replan：按反馈用 LLM 真重规划下游步骤（取代旧版机械的列表跳过/插入）

修复旧版 bug：handle_feedback 现在把重规划结果写回 learning_paths 并重建进度，
前端重新拉取即可看到变化（旧版结果从不落库）。
"""
from typing import List, Dict, Optional
from datetime import datetime
import logging

from bson import ObjectId
from bson.errors import InvalidId

from app.agents.graph.path_graph import path_graph
from app.services.memory import memory_service
from app.database import get_collection

logger = logging.getLogger(__name__)


class PathAgent:
    """路径规划 Agent —— 真 LangGraph Plan-and-Execute 图驱动"""

    async def plan(self, user_id: str, topic: str) -> Dict:
        """规划学习路径"""
        try:
            profile = await self._get_profile(user_id)
            state = await path_graph.ainvoke({
                "user_id": user_id, "topic": topic,
                "profile": profile, "mode": "plan",
            })
            return {"steps": state.get("steps", []), "topic": topic, "user_profile": profile}
        except Exception as e:  # noqa: BLE001
            logger.error(f"Path planning error: {e}")
            raise

    async def handle_feedback(self, path_id: str, step_id: str, feedback_type: str) -> Dict:
        """按反馈重规划路径，并持久化（修复旧版结果不落库的 bug）。"""
        try:
            path = await self._find_path(path_id)
            if not path:
                return {"error": "路径不存在"}

            profile = await self._get_profile(path.get("user_id", ""))
            state = await path_graph.ainvoke({
                "user_id": path.get("user_id", ""), "topic": path.get("topic", ""),
                "profile": profile, "mode": "replan",
                "feedback_type": feedback_type, "feedback_step_id": step_id,
                "existing_steps": path.get("steps", []),
            })
            new_steps = state.get("steps", path.get("steps", []))

            # 写回新版本步骤 + 重建进度记录
            await self._persist_replan(path, new_steps)
            return {"steps": new_steps, "adjusted": True, "notes": state.get("notes", "")}
        except Exception as e:  # noqa: BLE001
            logger.error(f"Handle feedback error: {e}")
            return {"error": str(e)}

    # ---------- 辅助 ----------

    async def _get_profile(self, user_id: str) -> Dict:
        doc = await get_collection("profiles").find_one(
            {"user_id": user_id}, sort=[("version", -1)],
        )
        if doc:
            return doc.get("dimensions", {})
        # 回退到核心记忆（兼容旧数据）
        core = await memory_service.get_core_memory(user_id)
        return core.get("current_profile", {})

    async def _find_path(self, path_id: str) -> Optional[Dict]:
        """按 ObjectId 查路径（旧版用字符串查 _id 是 bug）。"""
        try:
            return await get_collection("learning_paths").find_one({"_id": ObjectId(path_id)})
        except (InvalidId, TypeError):
            return await get_collection("learning_paths").find_one({"_id": path_id})

    async def _persist_replan(self, path: Dict, new_steps: List[Dict]):
        pid = path["_id"]
        await get_collection("learning_paths").update_one(
            {"_id": pid},
            {"$set": {"steps": new_steps, "version": path.get("version", 1) + 1,
                      "updated_at": datetime.now()}},
        )
        # 重建进度（首步 current，其余 pending）
        await get_collection("learning_progress").delete_many({"path_id": str(pid)})
        for i, _ in enumerate(new_steps):
            await get_collection("learning_progress").insert_one({
                "path_id": str(pid), "user_id": path.get("user_id", ""),
                "step_index": i, "status": "current" if i == 0 else "pending",
                "start_time": datetime.now() if i == 0 else None,
                "complete_time": None, "score": None,
            })
