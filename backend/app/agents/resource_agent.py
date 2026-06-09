"""
资源生成 Agent（真 LangGraph 实现）

对外保持 generate() 契约不变，内部驱动 resource_graph：
  Supervisor 拆解 → CRAG 取证 → 写文档 → 多 Worker 并行 → Critic 自检 →（低分则 Revise 循环）→ 安全 → 聚合。

相比旧版：
- 真多智能体编排（取代 asyncio.gather 硬跑 prompt）。
- 真 Self-Refine 质量分（取代写死 85）。
- 每个节点写真实进度到 task（取代 pending 直接跳 completed）。
- 内容 grounded 于 CRAG 取证并带引用（防幻觉）。
"""
from typing import List, Dict, Optional, Callable, Awaitable
from datetime import datetime
import logging

from app.agents.graph.resource_graph import build_resource_graph
from app.models.resource import ResourceType
from app.database import get_collection

logger = logging.getLogger(__name__)


class ResourceAgent:
    """资源生成 Agent —— 真 LangGraph Supervisor+Critic 图驱动"""

    async def generate(
        self,
        user_id: str,
        topic: str,
        resource_types: List[ResourceType],
        task_id: str,
    ) -> Dict:
        """生成学习资源（带真实进度写入）"""
        try:
            # 读取最新画像，供 supervisor 个性化
            profile_doc = await get_collection("profiles").find_one(
                {"user_id": user_id}, sort=[("version", -1)],
            )
            profile = profile_doc.get("dimensions", {}) if profile_doc else {}

            # 进度回调：每个节点把真实步骤写进 task，前端 SSE/轮询即可看到
            async def progress_cb(node: str, step: str, progress: float):
                await get_collection("tasks").update_one(
                    {"task_id": task_id},
                    {"$set": {
                        "status": "running", "current_step": step,
                        "current_node": node, "progress": round(progress, 2),
                        "updated_at": datetime.now(),
                    }},
                )

            graph = build_resource_graph(progress_cb=progress_cb)
            type_values = [t.value if isinstance(t, ResourceType) else t for t in resource_types]

            state = await graph.ainvoke({
                "user_id": user_id, "task_id": task_id, "topic": topic,
                "resource_types": type_values, "profile": profile,
                "revision_count": 0,
            })

            crag = state.get("crag", {})
            critique = state.get("critique", {})
            return {
                "resources": state.get("final_resources", []),
                "rag_sources": crag.get("citations", []),
                "knowledge_sufficient": crag.get("knowledge_sufficient", True),
                "quality_report": {
                    "score": critique.get("score", 0),
                    "grounded": critique.get("grounded", True),
                    "issues": critique.get("issues", []),
                    "suggestions": critique.get("suggestions", []),
                    "passed": critique.get("score", 0) >= 60,
                    "revisions": state.get("revision_count", 0),
                },
            }
        except Exception as e:  # noqa: BLE001
            logger.error(f"Resource generation error: {e}")
            raise
