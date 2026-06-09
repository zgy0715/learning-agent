"""
内容安全 / 防幻觉过滤服务

题目非功能需求 #3：完善的「防幻觉」与内容安全过滤机制。

两道防线：
1. 快速关键词黑名单（敏感/违规词）—— 零延迟兜底。
2. LLM 审查（可选）—— 判断学术内容是否含明显事实性错误或不当信息。
被判不安全时对内容做最小化处理（打标提示），不静默丢弃，保证可追溯。
"""
from typing import List
import logging
import re

from pydantic import BaseModel

from app.config import settings
from app.services.llm import structured

logger = logging.getLogger(__name__)

# 基础敏感词（可按需扩充；仅作快速兜底，主判定交给 LLM）
_BLOCKLIST = [
    "暴力", "色情", "赌博", "毒品", "枪支", "诈骗",
    "自杀", "恐怖主义", "政治敏感",
]


class SafetyVerdict(BaseModel):
    safe: bool = True
    categories: List[str] = []
    reason: str = ""


class _LLMVerdict(BaseModel):
    safe: bool
    categories: List[str] = []
    reason: str = ""


class SafetyService:
    """内容安全过滤服务"""

    async def check(self, content: str, use_llm: bool = False) -> SafetyVerdict:
        """检查内容安全性。默认仅关键词快检；use_llm=True 时叠加 LLM 审查。"""
        if not content or not content.strip():
            return SafetyVerdict(safe=True)

        # 1) 关键词快检
        hits = [w for w in _BLOCKLIST if w in content]
        if hits:
            return SafetyVerdict(safe=False, categories=["敏感词"], reason=f"命中敏感词: {hits}")

        # 2) LLM 审查（默认关闭以控制延迟；安全门节点可显式开启）
        if use_llm and settings.GUARDRAILS_ENABLED:
            try:
                v = await structured(
                    [
                        {"role": "system", "content":
                            "你是教育内容安全审查员。判断文本是否含违规信息或明显学术事实错误。"},
                        {"role": "user", "content": content[:2000]},
                    ],
                    _LLMVerdict, temperature=0.0,
                )
                return SafetyVerdict(safe=v.safe, categories=v.categories, reason=v.reason)
            except Exception as e:  # noqa: BLE001
                logger.warning(f"LLM 安全审查失败，放行（已过关键词快检）: {e}")

        return SafetyVerdict(safe=True)

    def sanitize(self, content: str, verdict: SafetyVerdict) -> str:
        """对不安全内容做最小化处理：打标提示 + 屏蔽命中词，保留可追溯性。"""
        cleaned = content
        for w in _BLOCKLIST:
            cleaned = re.sub(re.escape(w), "***", cleaned)
        notice = f"\n\n> ⚠️ 内容安全提示：本资源经安全过滤（{verdict.reason or '命中规则'}），部分内容已处理。"
        return cleaned + notice


# 全局单例
safety_service = SafetyService()
