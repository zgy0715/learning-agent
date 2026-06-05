"""
路径规划Agent
使用Plan-and-Execute模式规划个性化学习路径
"""
from typing import List, Dict, Optional
from pydantic import BaseModel
import logging
import json

from app.services.llm import chat, format_messages
from app.services.memory import memory_service
from app.services.rag import rag_service

logger = logging.getLogger(__name__)


class PathAgent:
    """
    路径规划Agent（Plan-and-Execute模式）

    工作流程：
    1. Planner: 结合用户画像生成学习计划
    2. Executor: 逐步执行计划，匹配资源
    3. Feedback: 根据用户反馈动态调整
    4. Re-Planner: 必要时重新规划
    """

    def __init__(self):
        self.max_iterations = 3

    async def plan(
        self,
        user_id: str,
        topic: str
    ) -> Dict:
        """
        规划学习路径

        Args:
            user_id: 用户ID
            topic: 学习主题

        Returns:
            Dict: 学习路径
        """
        try:
            # 获取用户画像
            core_memory = await memory_service.get_core_memory(user_id)
            user_profile = core_memory.get("current_profile", {})

            # 检索知识库，了解主题结构
            rag_results = await rag_service.hybrid_retrieve(
                query=topic,
                top_k=10
            )

            # 生成学习计划
            steps = await self._generate_plan(topic, user_profile, rag_results)

            return {
                "steps": steps,
                "topic": topic,
                "user_profile": user_profile
            }

        except Exception as e:
            logger.error(f"Path planning error: {e}")
            raise

    async def handle_feedback(
        self,
        path_id: str,
        step_id: str,
        feedback_type: str
    ) -> Dict:
        """
        处理用户反馈

        Args:
            path_id: 学习路径ID
            step_id: 步骤ID
            feedback_type: 反馈类型

        Returns:
            Dict: 调整后的路径
        """
        try:
            # 获取当前路径
            from app.database import get_collection
            path = await get_collection("learning_paths").find_one(
                {"_id": path_id}
            )

            if not path:
                return {"error": "路径不存在"}

            steps = path.get("steps", [])

            # 根据反馈类型调整
            if feedback_type == "too_hard":
                # 太难：插入前置知识步骤
                new_steps = await self._insert_prerequisites(steps, step_id)
            elif feedback_type == "too_easy":
                # 太简单：跳过当前步骤
                new_steps = self._skip_step(steps, step_id)
            else:
                new_steps = steps

            return {
                "steps": new_steps,
                "adjusted": True
            }

        except Exception as e:
            logger.error(f"Handle feedback error: {e}")
            return {"error": str(e)}

    async def _generate_plan(
        self,
        topic: str,
        user_profile: Dict,
        rag_results: List
    ) -> List[Dict]:
        """生成学习计划"""
        # 构建知识库上下文
        context = "\n".join([
            f"- {r.source}: {r.content[:200]}"
            for r in rag_results[:5]
        ]) if rag_results else "暂无知识库内容"

        # 构建画像上下文
        profile_context = json.dumps(user_profile, ensure_ascii=False) if user_profile else "暂无用户画像"

        prompt = f"""请为以下主题生成一个个性化学习路径：

主题：{topic}

用户画像：
{profile_context}

知识库参考：
{context}

请生成5-8个学习步骤，每个步骤包含：
1. step_id: 步骤ID（如step_1, step_2）
2. name: 步骤名称
3. objective: 学习目标
4. difficulty: 难度（基础/核心/进阶）
5. duration_minutes: 预估时长（分钟）
6. resource_types: 需要的资源类型列表
7. prerequisites: 前置知识依赖
8. rag_query: 用于检索知识库的查询语句

要求：
1. 循序渐进，由浅入深
2. 根据用户画像调整难度和时长
3. 每个步骤目标明确
4. 考虑知识点的逻辑关系

返回JSON格式：
```json
{{
  "steps": [
    {{
      "step_id": "step_1",
      "name": "...",
      "objective": "...",
      "difficulty": "基础",
      "duration_minutes": 30,
      "resource_types": ["document", "mindmap"],
      "prerequisites": [],
      "rag_query": "..."
    }}
  ]
}}```"""

        messages = format_messages(
            "你是一个专业的学习路径规划专家。只返回JSON格式。",
            prompt
        )

        response = await chat(messages, max_tokens=2000)
        try:
            # 解析JSON
            clean_response = response.strip()
            if clean_response.startswith("```"):
                clean_response = clean_response.split("\n", 1)[1]
            if clean_response.endswith("```"):
                clean_response = clean_response.rsplit("```", 1)[0]
            result = json.loads(clean_response)
            return result.get("steps", [])
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse plan response: {response}")
            # 返回默认计划
            return self._default_plan(topic)

    async def _insert_prerequisites(self, steps: List[Dict], step_id: str) -> List[Dict]:
        """插入前置知识步骤"""
        # 找到目标步骤
        target_index = None
        for i, step in enumerate(steps):
            if step.get("step_id") == step_id:
                target_index = i
                break

        if target_index is None:
            return steps

        # 生成前置知识步骤
        target_step = steps[target_index]
        prerequisite_step = {
            "step_id": f"step_{len(steps) + 1}",
            "name": f"{target_step['name']} - 前置知识",
            "objective": f"学习{target_step['name']}所需的前置知识",
            "difficulty": "基础",
            "duration_minutes": 15,
            "resource_types": ["document", "mindmap"],
            "prerequisites": [],
            "rag_query": target_step.get("rag_query", "")
        }

        # 插入到目标步骤之前
        new_steps = steps[:target_index] + [prerequisite_step] + steps[target_index:]
        return new_steps

    def _skip_step(self, steps: List[Dict], step_id: str) -> List[Dict]:
        """跳过步骤"""
        return [s for s in steps if s.get("step_id") != step_id]

    def _default_plan(self, topic: str) -> List[Dict]:
        """默认学习计划"""
        return [
            {
                "step_id": "step_1",
                "name": f"{topic}基础概念",
                "objective": f"了解{topic}的基本概念和术语",
                "difficulty": "基础",
                "duration_minutes": 30,
                "resource_types": ["document", "mindmap"],
                "prerequisites": [],
                "rag_query": f"{topic} 基础 概念"
            },
            {
                "step_id": "step_2",
                "name": f"{topic}核心原理",
                "objective": f"掌握{topic}的核心原理和工作机制",
                "difficulty": "核心",
                "duration_minutes": 45,
                "resource_types": ["document", "code"],
                "prerequisites": ["step_1"],
                "rag_query": f"{topic} 原理 机制"
            },
            {
                "step_id": "step_3",
                "name": f"{topic}实践应用",
                "objective": f"通过实例理解{topic}的实际应用",
                "difficulty": "核心",
                "duration_minutes": 40,
                "resource_types": ["code", "exercise"],
                "prerequisites": ["step_2"],
                "rag_query": f"{topic} 实例 应用"
            },
            {
                "step_id": "step_4",
                "name": f"{topic}进阶内容",
                "objective": f"深入了解{topic}的进阶知识",
                "difficulty": "进阶",
                "duration_minutes": 50,
                "resource_types": ["document", "exercise"],
                "prerequisites": ["step_3"],
                "rag_query": f"{topic} 进阶 高级"
            },
            {
                "step_id": "step_5",
                "name": f"{topic}综合练习",
                "objective": f"通过综合练习巩固所学知识",
                "difficulty": "进阶",
                "duration_minutes": 35,
                "resource_types": ["exercise", "code"],
                "prerequisites": ["step_4"],
                "rag_query": f"{topic} 练习 总结"
            }
        ]
