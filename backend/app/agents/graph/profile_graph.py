"""
画像分析子图（真 LangGraph StateGraph）

ReAct 风格流程：
  analyze_intent → extract_profile → merge_profile → decide → END

- extract_profile：用 LLM 结构化抽取 6 维画像（含证据），替代旧版关键词 if/else。
- merge_profile：与历史画像做「置信度加权」的信念更新（belief update），而非直接覆盖。
- decide：判断信息是否足够，决定直接作答还是追问；产出供路由层「真流式」生成回复的 messages。
"""
from typing import List, Dict, Any, Optional
import logging

from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, START, END

from app.agents.graph.state import ProfileState
from app.services.llm import structured

logger = logging.getLogger(__name__)

# 6 个画像维度（与前端雷达图 / models/user.py 对齐）
PROFILE_DIMENSIONS = [
    "knowledge_base", "cognitive_style", "error_patterns",
    "learning_preference", "learning_pace", "goal_orientation",
]
DIMENSION_CN = {
    "knowledge_base": "知识基础(初学/入门/进阶/精通)",
    "cognitive_style": "认知风格(视觉型/听觉型/动觉型/阅读型)",
    "error_patterns": "易错点偏好(概念混淆/计算粗心/逻辑不清/记忆困难)",
    "learning_preference": "学习偏好(视频为主/文字为主/练习为主/混合型)",
    "learning_pace": "学习节奏(快节奏/适中/慢节奏/碎片化)",
    "goal_orientation": "目标导向(应试取证/技能实践/兴趣探索/学术研究)",
}


class _DimExtract(BaseModel):
    value: str = Field(description="该维度的取值")
    confidence: float = Field(ge=0, le=1, description="本次推断置信度")
    evidence: str = Field(default="", description="支撑该判断的对话证据")


class _IntentResult(BaseModel):
    intent: str = Field(description="学习请求/练习请求/规划请求/资源请求/求助请求/一般对话 之一")
    needs_followup: bool = Field(description="信息是否不足以直接给出有用回复")


class _ProfileExtract(BaseModel):
    knowledge_base: Optional[_DimExtract] = None
    cognitive_style: Optional[_DimExtract] = None
    error_patterns: Optional[_DimExtract] = None
    learning_preference: Optional[_DimExtract] = None
    learning_pace: Optional[_DimExtract] = None
    goal_orientation: Optional[_DimExtract] = None


# ============ 节点 ============

async def _analyze_intent(state: ProfileState) -> ProfileState:
    msg = state["latest_message"]
    history = "\n".join(
        f"{m.get('role')}: {m.get('content','')}" for m in state.get("messages", [])[-6:]
    )
    try:
        result = await structured(
            [
                {"role": "system", "content": "你是学习助手的意图识别模块，分析用户最新消息的意图。"},
                {"role": "user", "content": f"对话历史:\n{history}\n\n最新消息:{msg}"},
            ],
            _IntentResult, temperature=0.0,
        )
        return {"intent": result.intent, "decision": "followup" if result.needs_followup else "respond"}
    except Exception as e:  # noqa: BLE001
        logger.warning(f"intent 分析失败: {e}")
        return {"intent": "一般对话", "decision": "respond"}


async def _extract_profile(state: ProfileState) -> ProfileState:
    msg = state["latest_message"]
    history = "\n".join(
        f"{m.get('role')}: {m.get('content','')}" for m in state.get("messages", [])[-8:]
    )
    dims_desc = "\n".join(f"- {k}: {DIMENSION_CN[k]}" for k in PROFILE_DIMENSIONS)
    try:
        result = await structured(
            [
                {"role": "system", "content":
                    "你是学习画像分析专家。基于对话，推断学生的学习特征。"
                    "只对对话中有明确线索的维度给出判断，没有线索的维度留空（null）。"
                    "为每个判断给出 0~1 置信度与对话证据，不要臆测。\n维度定义:\n" + dims_desc},
                {"role": "user", "content": f"对话历史:\n{history}\n\n最新消息:{msg}"},
            ],
            _ProfileExtract, temperature=0.1,
        )
        extracted: Dict[str, Any] = {}
        for dim in PROFILE_DIMENSIONS:
            val = getattr(result, dim, None)
            if val and val.value:
                extracted[dim] = {
                    "value": val.value, "confidence": float(val.confidence),
                    "evidence": val.evidence,
                }
        return {"extracted": extracted}
    except Exception as e:  # noqa: BLE001
        logger.warning(f"画像抽取失败: {e}")
        return {"extracted": {}}


def _merge_profile(state: ProfileState) -> ProfileState:
    """置信度加权的信念更新：新证据置信度更高才采纳；同值则累积置信度。"""
    current = dict(state.get("current_profile") or {})
    extracted = state.get("extracted") or {}
    evidence: Dict[str, str] = {}
    conf_scores: Dict[str, float] = {}
    changed = False

    for dim, new in extracted.items():
        old = current.get(dim) or {}
        old_conf = float(old.get("confidence", 0) or 0)
        new_conf = float(new.get("confidence", 0) or 0)
        old_val = old.get("value")
        new_val = new.get("value")

        if old_val == new_val and old_val is not None:
            # 同一判断被再次佐证 → 置信度向上累积（封顶 0.98）
            merged_conf = min(0.98, old_conf + (1 - old_conf) * new_conf * 0.5)
            current[dim] = {"value": new_val, "confidence": round(merged_conf, 3)}
            changed = changed or merged_conf > old_conf
        elif new_conf >= old_conf:
            # 新证据更强 → 采纳新值
            current[dim] = {"value": new_val, "confidence": round(new_conf, 3)}
            changed = True
        else:
            continue
        evidence[dim] = new.get("evidence", "")
        conf_scores[dim] = current[dim]["confidence"]

    return {
        "merged_profile": current, "evidence": evidence,
        "confidence_scores": conf_scores, "profile_updated": changed,
    }


def _decide(state: ProfileState) -> ProfileState:
    """组装供路由层流式生成回复的 messages（真实回复在路由层逐 token 产出）。"""
    profile = state.get("merged_profile", {})
    profile_brief = "、".join(
        f"{k}={v.get('value')}" for k, v in profile.items()
        if v.get("confidence", 0) > 0.3
    ) or "暂不明确"

    followup = state.get("decision") == "followup"
    style = (
        "信息还不够，请在帮助用户的同时，自然地追问 1 个最关键的问题以完善画像（不要列表式逼问）。"
        if followup else
        "信息已足够，直接给出具体、可执行的帮助，不要反复追问。"
    )
    system = (
        "你是高效、专业的个性化学习助手。根据学生画像调整讲解的深度与风格。\n"
        f"当前画像：{profile_brief}\n"
        f"意图：{state.get('intent','一般对话')}\n回复原则：{style}\n"
        "使用 Markdown，条理清晰。"
    )
    reply_messages = [{"role": "system", "content": system}]
    for m in state.get("messages", [])[-6:]:
        role = m.get("role")
        if role in ("user", "assistant"):
            reply_messages.append({"role": role, "content": m.get("content", "")})
    return {"reply_messages": reply_messages}


# ============ 图构建 ============

def build_profile_graph():
    g = StateGraph(ProfileState)
    g.add_node("analyze_intent", _analyze_intent)
    g.add_node("extract_profile", _extract_profile)
    g.add_node("merge_profile", _merge_profile)
    g.add_node("decide", _decide)

    g.add_edge(START, "analyze_intent")
    g.add_edge("analyze_intent", "extract_profile")
    g.add_edge("extract_profile", "merge_profile")
    g.add_edge("merge_profile", "decide")
    g.add_edge("decide", END)
    return g.compile()


profile_graph = build_profile_graph()
