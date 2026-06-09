"""
路径规划子图（真 LangGraph StateGraph）—— Plan-and-Execute + Re-Plan

两种模式共用一张图：
  plan 模式：  retrieve(CRAG 了解知识结构) → planner(按画像生成步骤) → executor(映射资源/补全字段) → END
  replan 模式：replanner(按反馈用 LLM 重规划下游步骤) → executor → END

对标 LangGraph 官方 Plan-and-Execute：真正基于反馈重规划（取代旧版机械的列表跳过/插入）。
"""
from typing import List, Dict, Any, Optional
import logging

from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, START, END

from app.agents.graph.state import PathState
from app.services.llm import structured
from app.services.rag import rag_service

logger = logging.getLogger(__name__)


class _Step(BaseModel):
    name: str
    objective: str
    difficulty: str = Field(description="基础/核心/进阶")
    duration_minutes: int = 30
    resource_types: List[str] = Field(default_factory=lambda: ["document", "mindmap"])
    prerequisites: List[str] = Field(default_factory=list)
    rag_query: str = ""


class _Plan(BaseModel):
    steps: List[_Step]


def _profile_brief(profile: Dict[str, Any]) -> str:
    if not profile:
        return "暂无画像（按通用初学者处理）"
    return "、".join(
        f"{k}={v.get('value')}" for k, v in profile.items()
        if isinstance(v, dict) and v.get("value")
    ) or "暂无画像"


def _normalize_steps(steps: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """补全 step_id / status，保证与前端 PathSteps 契约一致。"""
    out = []
    for i, s in enumerate(steps):
        out.append({
            "step_id": f"step_{i + 1}",
            "name": s.get("name", f"步骤{i+1}"),
            "objective": s.get("objective", ""),
            "difficulty": s.get("difficulty", "核心"),
            "duration_minutes": int(s.get("duration_minutes", 30) or 30),
            "resource_types": s.get("resource_types", ["document"]),
            "resource_ids": s.get("resource_ids", []),
            "status": s.get("status", "pending"),
            "prerequisites": s.get("prerequisites", []),
            "rag_query": s.get("rag_query", s.get("name", "")),
        })
    return out


# ============ 节点 ============

async def _retrieve(state: PathState) -> PathState:
    """了解主题知识结构（CRAG），供 planner 参考"""
    crag = await rag_service.crag_retrieve(state["topic"], top_k=8)
    return {"crag": crag.model_dump()}


async def _planner(state: PathState) -> PathState:
    crag = state.get("crag", {})
    context = "\n".join(
        f"- [{c.get('source')}] {c.get('content','')[:160]}"
        for c in crag.get("chunks", [])
    ) or "暂无知识库参考"
    try:
        plan = await structured(
            [
                {"role": "system", "content":
                    "你是个性化学习路径规划专家。结合学生画像与知识库结构，"
                    "生成 5-8 个循序渐进的学习步骤。根据画像调整难度、时长与资源类型。"},
                {"role": "user", "content":
                    f"主题：{state['topic']}\n学生画像：{_profile_brief(state.get('profile',{}))}\n"
                    f"知识库参考：\n{context}"},
            ],
            _Plan, temperature=0.4,
        )
        return {"steps": [s.model_dump() for s in plan.steps]}
    except Exception as e:  # noqa: BLE001
        logger.warning(f"planner 失败，使用默认路径: {e}")
        return {"steps": _default_steps(state["topic"])}


async def _replanner(state: PathState) -> PathState:
    """按反馈用 LLM 重规划：too_hard 补前置/拆细，too_easy 提速/进阶，confused 换讲法。"""
    fb = state.get("feedback_type", "")
    target = state.get("feedback_step_id", "")
    existing = state.get("existing_steps", [])
    intent = {
        "too_hard": "学生觉得太难：在该步骤前补充前置知识并把难点拆细、降低难度。",
        "too_easy": "学生觉得太简单：精简或跳过该步骤，提高后续难度、增加进阶/挑战内容。",
        "confused": "学生感到困惑：保留目标但更换讲解方式（更多图示/示例/类比）。",
        "need_help": "学生需要帮助：在该步骤增加示例与练习巩固。",
    }.get(fb, "根据反馈优化后续学习步骤。")
    try:
        plan = await structured(
            [
                {"role": "system", "content":
                    "你是自适应学习路径规划专家。根据学生对某步骤的反馈，重规划学习路径。"
                    "保持已完成步骤不变，主要调整目标步骤及其后续。"},
                {"role": "user", "content":
                    f"主题：{state['topic']}\n学生画像：{_profile_brief(state.get('profile',{}))}\n"
                    f"反馈针对步骤：{target}\n调整意图：{intent}\n"
                    f"当前路径：{[{'step_id':s.get('step_id'),'name':s.get('name'),'difficulty':s.get('difficulty')} for s in existing]}"},
            ],
            _Plan, temperature=0.4,
        )
        return {"steps": [s.model_dump() for s in plan.steps],
                "notes": f"已根据「{fb}」反馈重规划。"}
    except Exception as e:  # noqa: BLE001
        logger.warning(f"replanner 失败，返回原路径: {e}")
        return {"steps": existing, "notes": "重规划失败，保留原路径。"}


def _executor(state: PathState) -> PathState:
    """补全 step_id / status，使输出契约稳定。"""
    return {"steps": _normalize_steps(state.get("steps", []))}


def _default_steps(topic: str) -> List[Dict[str, Any]]:
    return [
        {"name": f"{topic}基础概念", "objective": f"了解{topic}的基本概念与术语",
         "difficulty": "基础", "duration_minutes": 30,
         "resource_types": ["document", "mindmap"], "prerequisites": [], "rag_query": f"{topic} 基础 概念"},
        {"name": f"{topic}核心原理", "objective": f"掌握{topic}的核心原理",
         "difficulty": "核心", "duration_minutes": 45,
         "resource_types": ["document", "code"], "prerequisites": ["step_1"], "rag_query": f"{topic} 原理"},
        {"name": f"{topic}实践应用", "objective": f"通过实例理解{topic}的应用",
         "difficulty": "核心", "duration_minutes": 40,
         "resource_types": ["code", "exercise"], "prerequisites": ["step_2"], "rag_query": f"{topic} 实例"},
        {"name": f"{topic}综合练习", "objective": "通过练习巩固所学",
         "difficulty": "进阶", "duration_minutes": 35,
         "resource_types": ["exercise"], "prerequisites": ["step_3"], "rag_query": f"{topic} 练习"},
    ]


# ============ 图构建 ============

def _route_start(state: PathState) -> str:
    return "replanner" if state.get("mode") == "replan" else "retrieve"


def build_path_graph():
    g = StateGraph(PathState)
    g.add_node("retrieve", _retrieve)
    g.add_node("planner", _planner)
    g.add_node("replanner", _replanner)
    g.add_node("executor", _executor)

    g.add_conditional_edges(START, _route_start, {"retrieve": "retrieve", "replanner": "replanner"})
    g.add_edge("retrieve", "planner")
    g.add_edge("planner", "executor")
    g.add_edge("replanner", "executor")
    g.add_edge("executor", END)
    return g.compile()


path_graph = build_path_graph()
