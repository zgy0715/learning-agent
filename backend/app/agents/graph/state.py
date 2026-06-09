"""
LangGraph 各智能体状态定义（TypedDict）

每个状态对应一张真实的 StateGraph：节点读取/更新状态字段，条件边据此路由。
total=False 允许节点只返回部分字段做增量更新。
"""
from typing import TypedDict, List, Dict, Any, Optional


# ============ 画像分析图（ReAct 风格：意图→抽取→合并→决策）============
class ProfileState(TypedDict, total=False):
    user_id: str
    messages: List[Dict[str, Any]]      # 对话历史
    latest_message: str                 # 最新一条用户消息
    current_profile: Dict[str, Any]     # 历史画像 {dim: {value, confidence}}

    intent: str                         # 识别出的用户意图
    extracted: Dict[str, Any]           # 本轮抽取 {dim: {value, confidence, evidence}}
    merged_profile: Dict[str, Any]      # 合并后画像 {dim: {value, confidence}}
    evidence: Dict[str, str]            # 各维度证据
    confidence_scores: Dict[str, float]
    profile_updated: bool

    decision: str                       # "respond" | "followup"
    reply_messages: List[Dict[str, str]]  # 供路由层流式生成回复的 messages


# ============ 资源生成图（Supervisor + Critic + Self-Refine 循环）============
class ResourceState(TypedDict, total=False):
    user_id: str
    task_id: str
    topic: str
    resource_types: List[str]
    profile: Dict[str, Any]

    plan: Dict[str, Any]                # supervisor 拆解：难度/风格/各资源要点
    crag: Dict[str, Any]                # CRAG 结果 {chunks, citations, knowledge_sufficient, notes}
    context: str                        # 拼接好的取证上下文
    material: str                       # 核心讲解文档

    artifacts: List[Dict[str, Any]]     # 各 worker 产物 {type, content, agent, format}
    critique: Dict[str, Any]            # critic 评审 {score, issues, suggestions, per_artifact}
    revision_count: int
    final_resources: List[Dict[str, Any]]


# ============ 路径规划图（Plan-and-Execute + Re-Plan）============
class PathState(TypedDict, total=False):
    user_id: str
    topic: str
    profile: Dict[str, Any]
    crag: Dict[str, Any]

    mode: str                           # "plan" | "replan"
    feedback_type: str                  # replan 时的反馈类型
    feedback_step_id: str
    existing_steps: List[Dict[str, Any]]

    steps: List[Dict[str, Any]]         # 规划/重规划后的步骤
    notes: str
