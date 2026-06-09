"""
画像分析 Agent（真 LangGraph 实现）

对外保持 analyze() 契约不变，内部驱动 profile_graph：
  意图识别 → LLM 结构化抽取 6 维画像 → 置信度加权合并 → 决策。

相比旧版：
- 删除关键词 if/else，画像由 LLM 真实推断（含证据）。
- 画像按 version 持久化到 profiles 集合（修复旧版写 core_memory、而路由读 profiles 的脱节）。
- 额外返回 reply_messages，供路由层做「真 token 流式」回复。
"""
from typing import List, Dict, Any
from datetime import datetime
import logging

from app.agents.graph.profile_graph import profile_graph
from app.database import get_collection

logger = logging.getLogger(__name__)


class ProfileAgent:
    """画像分析 Agent —— 真 LangGraph 状态图驱动"""

    async def analyze(
        self,
        messages: List[Dict],
        current_profile: Dict,
        user_id: str,
    ) -> Dict:
        """
        分析用户对话，更新学习画像。

        Returns:
            {response 或 reply_messages, profile_updated, profile_dimensions, confidence_scores, tokens_used}
        """
        try:
            user_messages = [m for m in messages if m.get("role") == "user"]
            if not user_messages:
                return {
                    "response": "你好！我是你的个性化学习助手。告诉我你想学什么、目前的基础如何，"
                                "我会为你分析画像、生成多模态学习资源并规划学习路径。",
                    "profile_updated": False,
                    "profile_dimensions": current_profile,
                    "reply_messages": None,
                    "tokens_used": 0,
                }

            latest = user_messages[-1].get("content", "")

            # 驱动真 LangGraph 状态图
            state = await profile_graph.ainvoke({
                "user_id": user_id,
                "messages": messages,
                "latest_message": latest,
                "current_profile": current_profile or {},
            })

            merged = state.get("merged_profile", current_profile or {})
            updated = state.get("profile_updated", False)

            # 画像变更 → 落库为新版本（前端 /api/profile 即可读到真实演化）
            if updated:
                await self._persist_profile(
                    user_id, merged, state.get("evidence", {}),
                )

            return {
                # response 留空：由路由层用 reply_messages 流式生成，避免重复调用 LLM
                "response": "",
                "reply_messages": state.get("reply_messages"),
                "intent": state.get("intent", ""),
                "profile_updated": updated,
                "profile_dimensions": merged,
                "confidence_scores": state.get("confidence_scores", {}),
                "tokens_used": 0,
            }
        except Exception as e:  # noqa: BLE001
            logger.error(f"Profile analysis error: {e}")
            return {
                "response": "抱歉，处理时出现了一点问题，请再说一次你的需求。",
                "profile_updated": False,
                "profile_dimensions": current_profile,
                "reply_messages": None,
                "tokens_used": 0,
            }

    async def _persist_profile(self, user_id: str, dimensions: Dict, evidence: Dict):
        """画像以版本递增方式写入 profiles 集合"""
        try:
            latest = await get_collection("profiles").find_one(
                {"user_id": user_id}, sort=[("version", -1)],
            )
            new_version = (latest.get("version", 0) + 1) if latest else 1
            await get_collection("profiles").insert_one({
                "user_id": user_id,
                "version": new_version,
                "dimensions": dimensions,
                "evidence": evidence,
                "updated_at": datetime.now(),
                "update_source": "conversation",
            })
        except Exception as e:  # noqa: BLE001
            logger.error(f"持久化画像失败: {e}")
