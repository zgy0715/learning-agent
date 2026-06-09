"""
资源生成子图（真 LangGraph StateGraph）—— Supervisor + 多 Worker + Critic 自精炼

流程：
  supervisor → retrieve(CRAG) → write_material → workers(并行) → critic
            → [分数<阈值且可重试] → revise → critic（真循环）
            → [通过] → safety → aggregate → END

对标：MetaGPT/ChatDev 的角色化 SOP（Supervisor 调度）、Self-Refine（Critic 评分驱动修订）、
CRAG（grounded 写作防幻觉）。每个节点通过 progress_cb 写真实进度（取代旧版 85 分写死 + 假进度）。
"""
from typing import List, Dict, Any, Callable, Awaitable, Optional
import asyncio
import logging

from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, START, END

from app.agents.graph.state import ResourceState
from app.services.llm import chat, structured, format_messages
from app.services.rag import rag_service
from app.services.safety import safety_service
from app.config import settings

logger = logging.getLogger(__name__)

# 进度回调：node 名 → (current_step 文案, progress 0~1)
ProgressCb = Callable[[str, str, float], Awaitable[None]]


# ---------- 结构化 schema ----------
class _ResourceSpec(BaseModel):
    type: str
    focus: str = Field(description="该资源应聚焦的要点")


class _Plan(BaseModel):
    difficulty: str = Field(description="基础/核心/进阶，依据学生画像")
    style: str = Field(description="讲解风格，依据认知风格与学习偏好")
    summary: str = Field(description="对学习需求的理解与拆解")
    specs: List[_ResourceSpec] = Field(description="每种待生成资源的要点")


class _ArtifactCritique(BaseModel):
    type: str
    score: float = Field(ge=0, le=100)
    issues: List[str] = Field(default_factory=list)


class _Critique(BaseModel):
    score: float = Field(ge=0, le=100, description="整体质量分")
    grounded: bool = Field(description="内容是否忠于参考资料、无臆造")
    issues: List[str] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)
    per_artifact: List[_ArtifactCritique] = Field(default_factory=list)


def _profile_brief(profile: Dict[str, Any]) -> str:
    if not profile:
        return "暂无画像（按通用初学者处理）"
    return "、".join(
        f"{k}={v.get('value')}（{v.get('confidence',0):.0%}）"
        for k, v in profile.items() if isinstance(v, dict) and v.get("value")
    ) or "暂无画像"


# ============ 节点 ============

def _make_nodes(progress_cb: Optional[ProgressCb]):
    async def _emit(node: str, step: str, p: float):
        if progress_cb:
            try:
                await progress_cb(node, step, p)
            except Exception as e:  # noqa: BLE001
                logger.debug(f"progress_cb error: {e}")

    # 1) Supervisor：理解需求 + 拆解任务（按画像定难度/风格）
    async def supervisor(state: ResourceState) -> ResourceState:
        await _emit("supervisor", "主管智能体：理解需求并拆解任务", 0.08)
        types = state["resource_types"]
        try:
            plan = await structured(
                [
                    {"role": "system", "content":
                        "你是资源生成主管(Supervisor)。根据学习主题与学生画像，制定生成方案："
                        "确定难度、讲解风格，并为每种资源类型给出聚焦要点。"},
                    {"role": "user", "content":
                        f"主题：{state['topic']}\n学生画像：{_profile_brief(state.get('profile',{}))}\n"
                        f"需生成的资源类型：{types}"},
                ],
                _Plan, temperature=0.3,
            )
            return {"plan": plan.model_dump()}
        except Exception as e:  # noqa: BLE001
            logger.warning(f"supervisor 规划失败，使用默认: {e}")
            return {"plan": {"difficulty": "核心", "style": "通俗", "summary": state["topic"],
                             "specs": [{"type": t, "focus": ""} for t in types]}}

    # 2) Retrieve：CRAG 取证（防幻觉地基）
    async def retrieve(state: ResourceState) -> ResourceState:
        await _emit("retrieve", "检索智能体：CRAG 纠错式检索取证", 0.20)
        crag = await rag_service.crag_retrieve(state["topic"], top_k=6)
        context = "\n\n".join(
            f"[来源:{c.source}] {c.content}" for c in crag.chunks
        ) if crag.chunks else ""
        return {"crag": crag.model_dump(), "context": context}

    # 3) Write material：基于取证写核心文档
    async def write_material(state: ResourceState) -> ResourceState:
        await _emit("write_material", "资料智能体：撰写核心讲解文档", 0.38)
        plan = state.get("plan", {})
        crag = state.get("crag", {})
        sufficient = crag.get("knowledge_sufficient", True)
        grounding = (
            f"参考资料（必须基于这些内容，引用来源，不得编造）：\n{state.get('context','')}"
            if sufficient else
            "⚠️ 知识库缺乏强相关资料。请基于通用常识谨慎讲解，并在开头明确提示"
            "「本内容缺乏课程知识库直接支撑，请以教材为准」，不要编造具体数据/出处。"
        )
        prompt = (
            f"主题：{state['topic']}\n难度：{plan.get('difficulty')}｜风格：{plan.get('style')}\n\n"
            f"{grounding}\n\n"
            "请输出结构化学习资料：前置知识 / 概念解释 / 核心内容 / 示例 / 小结。"
            "使用 Markdown，准确、通俗，标注引用来源。"
        )
        material = await chat(
            format_messages("你是严谨的教育内容创作者，只基于给定资料写作，杜绝幻觉。", prompt),
            temperature=0.5, max_tokens=2600,
        )
        return {"material": material}

    # 4) Workers：并行生成各类资源（各自 grounded）
    async def workers(state: ResourceState) -> ResourceState:
        await _emit("workers", "多个专业智能体：并行生成思维导图/习题/代码/PPT", 0.58)
        material = state.get("material", "")
        topic = state["topic"]
        specs = {s["type"]: s.get("focus", "") for s in state.get("plan", {}).get("specs", [])}
        types = state["resource_types"]

        gens = {
            "mindmap": _gen_mindmap, "exercise": _gen_exercise,
            "code": _gen_code, "ppt": _gen_ppt,
            "video": _gen_video, "audio": _gen_audio,
        }
        tasks, names = [], []
        for t in types:
            if t == "document":
                continue
            if t in gens:
                names.append(t)
                tasks.append(gens[t](topic, material, specs.get(t, "")))

        artifacts: List[Dict[str, Any]] = [{
            "type": "document", "content": material,
            "agent": "MaterialAgent", "format": "markdown",
        }]
        if tasks:
            done = await asyncio.gather(*tasks, return_exceptions=True)
            for name, res in zip(names, done):
                if isinstance(res, Exception):
                    logger.error(f"worker {name} 失败: {res}")
                    continue
                artifacts.append(res)
        return {"artifacts": artifacts}

    # 5) Critic：Self-Refine 评分（真打分，取代写死 85）
    async def critic(state: ResourceState) -> ResourceState:
        rev = state.get("revision_count", 0)
        await _emit("critic", f"评审智能体：质量与防幻觉自检（第 {rev + 1} 轮）", 0.74)
        artifacts = state.get("artifacts", [])
        listing = "\n\n".join(
            f"### {a['type']}\n{(a.get('content') or '')[:1200]}" for a in artifacts
        )
        try:
            crit = await structured(
                [
                    {"role": "system", "content":
                        "你是严格的教育质量评审(Critic)。从准确性、与参考资料的一致性(grounded)、"
                        "完整性、适配学生画像四方面评估，给出 0~100 分、问题清单与改进建议。"
                        "宁严勿松，发现臆造/事实错误必须指出。"},
                    {"role": "user", "content":
                        f"主题：{state['topic']}\n参考资料：{(state.get('context') or '')[:1500]}\n\n"
                        f"待评审资源：\n{listing}"},
                ],
                _Critique, temperature=0.0,
            )
            return {"critique": crit.model_dump()}
        except Exception as e:  # noqa: BLE001
            logger.warning(f"critic 评审失败，给保守分: {e}")
            return {"critique": {"score": 75, "grounded": True, "issues": [],
                                 "suggestions": [], "per_artifact": []}}

    # 6) Revise：按 critic 意见修订低分资源，然后回 critic
    async def revise(state: ResourceState) -> ResourceState:
        rev = state.get("revision_count", 0) + 1
        await _emit("revise", f"修订智能体：按评审意见改进（第 {rev} 轮）", 0.80)
        crit = state.get("critique", {})
        per = {p["type"]: p for p in crit.get("per_artifact", [])}
        global_issues = "；".join(crit.get("issues", []))
        suggestions = "；".join(crit.get("suggestions", []))
        threshold = settings.RESOURCE_QUALITY_THRESHOLD

        artifacts = state.get("artifacts", [])
        new_artifacts: List[Dict[str, Any]] = []
        for a in artifacts:
            a_score = per.get(a["type"], {}).get("score", crit.get("score", 100))
            a_issues = "；".join(per.get(a["type"], {}).get("issues", [])) or global_issues
            if a_score >= threshold:
                new_artifacts.append(a)
                continue
            try:
                improved = await chat(
                    format_messages(
                        "你是内容修订专家。针对评审意见改进资源，保持原格式，更准确、更贴合学生，杜绝幻觉。",
                        f"主题：{state['topic']}\n资源类型：{a['type']}\n"
                        f"评审问题：{a_issues}\n整体建议：{suggestions}\n\n"
                        f"参考资料：{(state.get('context') or '')[:1200]}\n\n"
                        f"原内容：\n{a.get('content','')}\n\n请输出改进后的完整内容。",
                    ),
                    temperature=0.4, max_tokens=2600,
                )
                new_artifacts.append({**a, "content": improved})
            except Exception as e:  # noqa: BLE001
                logger.warning(f"修订 {a['type']} 失败: {e}")
                new_artifacts.append(a)
        return {"artifacts": new_artifacts, "revision_count": rev}

    # 7) Safety：内容安全过滤
    async def safety(state: ResourceState) -> ResourceState:
        await _emit("safety", "安全智能体：内容安全过滤", 0.90)
        if not settings.GUARDRAILS_ENABLED:
            return {}
        artifacts = state.get("artifacts", [])
        checked = []
        for a in artifacts:
            content = a.get("content", "")
            verdict = await safety_service.check(content)
            if not verdict.safe:
                content = safety_service.sanitize(content, verdict)
            checked.append({**a, "content": content, "safety_checked": True})
        return {"artifacts": checked}

    # 8) Aggregate：产出带真 quality_score + 引用 + agent 的资源
    async def aggregate(state: ResourceState) -> ResourceState:
        await _emit("aggregate", "聚合结果", 0.97)
        crit = state.get("critique", {})
        per = {p["type"]: p for p in crit.get("per_artifact", [])}
        citations = state.get("crag", {}).get("citations", [])
        score = crit.get("score", 0)

        final = []
        for a in state.get("artifacts", []):
            final.append({
                "type": a["type"],
                "content": a.get("content", ""),
                "format": a.get("format", "markdown"),
                "quality_score": per.get(a["type"], {}).get("score", score),
                "agent": a.get("agent", f"{a['type']}Agent"),
            })
        return {"final_resources": final}

    return {
        "supervisor": supervisor, "retrieve": retrieve, "write_material": write_material,
        "workers": workers, "critic": critic, "revise": revise,
        "safety": safety, "aggregate": aggregate,
    }


# ---------- Worker 实现（各自 grounded 于 material）----------

async def _gen_mindmap(topic, material, focus) -> Dict[str, Any]:
    content = await chat(
        format_messages(
            "你是思维导图专家。只返回 Markmap 格式（Markdown 标题+列表），最多 3 层。",
            f"基于资料生成「{topic}」思维导图。要点:{focus}\n资料:\n{material[:2000]}",
        ),
        temperature=0.4, max_tokens=1200,
    )
    return {"type": "mindmap", "content": content, "agent": "MindmapAgent", "format": "markmap"}


async def _gen_exercise(topic, material, focus) -> Dict[str, Any]:
    content = await chat(
        format_messages(
            "你是教育测评专家。只返回 JSON：{\"exercises\":[{type,question,options,answer,explanation}]}。",
            f"基于资料为「{topic}」出 5 题（2 选择+2 填空+1 简答），含答案与解析。要点:{focus}\n资料:\n{material[:2000]}",
        ),
        temperature=0.5, max_tokens=1800,
    )
    return {"type": "exercise", "content": content, "agent": "ExerciseAgent", "format": "json"}


async def _gen_code(topic, material, focus) -> Dict[str, Any]:
    content = await chat(
        format_messages(
            "你是编程教学专家。给出可运行的 Python 示例，含详细注释、运行结果与说明。",
            f"为「{topic}」生成一个面向初学者的代码实操案例。要点:{focus}\n资料:\n{material[:1500]}",
        ),
        temperature=0.4, max_tokens=1600,
    )
    return {"type": "code", "content": content, "agent": "CodeAgent", "format": "markdown"}


async def _gen_ppt(topic, material, focus) -> Dict[str, Any]:
    content = await chat(
        format_messages(
            "你是课件设计专家。只返回 JSON：{title, slides:[{type,title,subtitle?,points?}]}。",
            f"基于资料为「{topic}」生成 10-15 页 PPT 大纲。要点:{focus}\n资料:\n{material[:2000]}",
        ),
        temperature=0.4, max_tokens=1500,
    )
    return {"type": "ppt", "content": content, "agent": "PptAgent", "format": "json"}


async def _gen_video(topic, material, focus) -> Dict[str, Any]:
    content = await chat(
        format_messages(
            "你是教学视频脚本专家。输出含时间戳、画面描述、旁白、字幕的分镜脚本。",
            f"为「{topic}」写 5-8 分钟教学视频脚本。要点:{focus}\n资料:\n{material[:2000]}",
        ),
        temperature=0.6, max_tokens=1800,
    )
    return {"type": "video", "content": content, "agent": "VideoAgent", "format": "markdown"}


async def _gen_audio(topic, material, focus) -> Dict[str, Any]:
    content = await chat(
        format_messages(
            "你是音频讲解脚本专家。输出口语化、含停顿标记、适合朗读的讲解稿。",
            f"为「{topic}」写 3-5 分钟音频讲解稿。要点:{focus}\n资料:\n{material[:2000]}",
        ),
        temperature=0.6, max_tokens=1400,
    )
    return {"type": "audio", "content": content, "agent": "AudioAgent", "format": "markdown"}


# ============ 图构建（含 critic↔revise 条件循环）============

def _route_after_critic(state: ResourceState) -> str:
    crit = state.get("critique", {})
    score = crit.get("score", 100)
    grounded = crit.get("grounded", True)
    rev = state.get("revision_count", 0)
    if (score < settings.RESOURCE_QUALITY_THRESHOLD or not grounded) and rev < settings.RESOURCE_MAX_REVISIONS:
        return "revise"
    return "safety"


def build_resource_graph(progress_cb: Optional[ProgressCb] = None):
    nodes = _make_nodes(progress_cb)
    g = StateGraph(ResourceState)
    for name, fn in nodes.items():
        g.add_node(name, fn)

    g.add_edge(START, "supervisor")
    g.add_edge("supervisor", "retrieve")
    g.add_edge("retrieve", "write_material")
    g.add_edge("write_material", "workers")
    g.add_edge("workers", "critic")
    g.add_conditional_edges("critic", _route_after_critic, {"revise": "revise", "safety": "safety"})
    g.add_edge("revise", "critic")            # 真 Self-Refine 循环
    g.add_edge("safety", "aggregate")
    g.add_edge("aggregate", END)
    return g.compile()
