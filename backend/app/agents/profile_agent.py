"""
画像分析Agent
使用ReAct（Reasoning + Acting）模式分析用户学习特征
基于LangGraph实现状态图工作流
"""
from typing import List, Dict, Optional, Any
from pydantic import BaseModel
import logging
import json

from app.services.llm import chat, format_messages
from app.services.memory import memory_service

logger = logging.getLogger(__name__)


class AnalysisResult(BaseModel):
    """画像分析结果"""
    knowledge_base: Dict = {"value": "初学", "confidence": 0.0}
    cognitive_style: Dict = {"value": "视觉型", "confidence": 0.0}
    error_patterns: Dict = {"value": "概念混淆", "confidence": 0.0}
    learning_preference: Dict = {"value": "混合型", "confidence": 0.0}
    learning_pace: Dict = {"value": "适中", "confidence": 0.0}
    goal_orientation: Dict = {"value": "兴趣探索", "confidence": 0.0}


class ProfileAgent:
    """
    画像分析Agent

    使用ReAct模式分析用户对话，直接给出实用回复
    """

    def __init__(self):
        self.max_iterations = 3

    async def analyze(
        self,
        messages: List[Dict],
        current_profile: Dict,
        user_id: str
    ) -> Dict:
        """
        分析用户对话，更新学习画像

        Args:
            messages: 对话历史
            current_profile: 当前画像
            user_id: 用户ID

        Returns:
            Dict: 分析结果，包含回复内容和画像更新
        """
        try:
            # 获取核心记忆
            core_memory = await memory_service.get_core_memory(user_id)

            # 提取用户消息
            user_messages = [m for m in messages if m.get("role") == "user"]
            if not user_messages:
                return {
                    "response": "你好！我是你的学习助手。告诉我你想学什么，我来帮你制定学习计划和生成学习资源。",
                    "profile_updated": False,
                    "profile_dimensions": current_profile
                }

            latest_message = user_messages[-1].get("content", "")

            # 分析画像（简化版）
            analysis_result = AnalysisResult()
            confidence_scores = {}

            # 直接提取特征
            extracted = self._extract_features(latest_message, current_profile)

            # 更新画像
            for dim, value in extracted.items():
                if hasattr(analysis_result, dim):
                    analysis_result = analysis_result.copy(update={dim: value})
                    confidence_scores[dim] = value.get("confidence", 0.5)

            # 生成直接有用的回复
            response = await self._generate_direct_response(
                latest_message,
                user_messages,
                analysis_result
            )

            # 更新核心记忆
            await memory_service.core_memory_append(
                user_id,
                "current_profile",
                analysis_result.dict()
            )

            return {
                "response": response,
                "profile_updated": True,
                "profile_dimensions": analysis_result.dict(),
                "confidence_scores": confidence_scores,
                "tokens_used": 0
            }

        except Exception as e:
            logger.error(f"Profile analysis error: {e}")
            return {
                "response": f"抱歉，处理过程中出现了一些问题。请再试一次。",
                "profile_updated": False,
                "profile_dimensions": current_profile
            }

    def _extract_features(self, message: str, current_profile: Dict) -> Dict:
        """从用户消息中提取学习特征"""
        extracted = {}

        # 知识基础检测
        if any(word in message for word in ["初学", "刚学", "入门", "零基础", "新手"]):
            extracted["knowledge_base"] = {"value": "初学", "confidence": 0.8}
        elif any(word in message for word in ["有基础", "学过", "了解", "知道"]):
            extracted["knowledge_base"] = {"value": "入门", "confidence": 0.7}
        elif any(word in message for word in ["精通", "深入", "高级", "熟练"]):
            extracted["knowledge_base"] = {"value": "精通", "confidence": 0.7}

        # 学习偏好检测
        if any(word in message for word in ["视频", "看视频", "教程"]):
            extracted["learning_preference"] = {"value": "视频为主", "confidence": 0.8}
        elif any(word in message for word in ["做题", "刷题", "练习", "真题"]):
            extracted["learning_preference"] = {"value": "练习为主", "confidence": 0.8}
        elif any(word in message for word in ["看书", "文档", "阅读"]):
            extracted["learning_preference"] = {"value": "文字为主", "confidence": 0.8}

        # 目标导向检测
        if any(word in message for word in ["考研", "考试", "408", "备考", "复习"]):
            extracted["goal_orientation"] = {"value": "应试取证", "confidence": 0.9}
        elif any(word in message for word in ["工作", "项目", "实践", "开发"]):
            extracted["goal_orientation"] = {"value": "技能实践", "confidence": 0.8}
        elif any(word in message for word in ["兴趣", "了解", "好奇"]):
            extracted["goal_orientation"] = {"value": "兴趣探索", "confidence": 0.7}

        # 学习节奏检测
        if any(word in message for word in ["快", "高效", "速成"]):
            extracted["learning_pace"] = {"value": "快节奏", "confidence": 0.7}
        elif any(word in message for word in ["慢慢", "详细", "细致"]):
            extracted["learning_pace"] = {"value": "慢节奏", "confidence": 0.7}

        # 认知风格检测
        if any(word in message for word in ["图", "思维导图", "可视化"]):
            extracted["cognitive_style"] = {"value": "视觉型", "confidence": 0.8}
        elif any(word in message for word in ["听", "音频", "讲解"]):
            extracted["cognitive_style"] = {"value": "听觉型", "confidence": 0.8}
        elif any(word in message for word in ["动手", "实践", "敲代码"]):
            extracted["cognitive_style"] = {"value": "动觉型", "confidence": 0.8}

        return extracted

    async def _generate_direct_response(
        self,
        user_message: str,
        user_messages: List[Dict],
        analysis_result: AnalysisResult
    ) -> str:
        """生成直接有用的回复"""

        # 分析用户意图
        intent = self._detect_intent(user_message)

        # 构建上下文
        conversation_history = "\n".join([
            f"用户: {m.get('content', '')}"
            for m in user_messages[-5:]  # 最近5条消息
        ])

        system_prompt = f"""你是一个高效的学习助手。你的任务是帮助用户解决学习问题，而不是反复追问。

用户画像：
- 知识基础：{analysis_result.knowledge_base.get('value', '未知')}
- 学习偏好：{analysis_result.learning_preference.get('value', '未知')}
- 目标导向：{analysis_result.goal_orientation.get('value', '未知')}

## 回复原则
1. 直接行动，不要反复追问
2. 如果用户说"我要学XXX"，直接给出学习方案
3. 如果用户说"给我出题"，直接出题
4. 如果用户说"制定计划"，直接制定计划
5. 回复要简洁、实用、可执行
6. 一次回复解决一个问题，不要贪多

## 用户意图：{intent}

请根据用户消息，给出直接有用的回复。"""

        messages = format_messages(system_prompt, user_message)

        try:
            response = await chat(messages, temperature=0.7, max_tokens=1500)
            return response
        except Exception as e:
            logger.error(f"Generate response error: {e}")
            return self._get_fallback_response(user_message, intent)

    def _detect_intent(self, message: str) -> str:
        """检测用户意图"""
        message_lower = message.lower()

        if any(word in message for word in ["学习", "学", "了解", "掌握"]):
            return "学习请求"
        elif any(word in message for word in ["做题", "出题", "练习", "刷题"]):
            return "练习请求"
        elif any(word in message for word in ["计划", "规划", "安排", "方案"]):
            return "规划请求"
        elif any(word in message for word in ["资料", "资源", "文档", "视频"]):
            return "资源请求"
        elif any(word in message for word in ["帮助", "问题", "不会", "不懂"]):
            return "求助请求"
        else:
            return "一般对话"

    def _get_fallback_response(self, message: str, intent: str) -> str:
        """备用回复"""
        if intent == "学习请求":
            return f"好的，我来帮你学习这个内容。\n\n建议的学习步骤：\n1. 先了解基础概念\n2. 学习核心原理\n3. 通过练习巩固\n\n你可以在"资源"页面输入主题，我会为你生成学习资料。"
        elif intent == "练习请求":
            return "好的，我来给你出一些练习题。\n\n你可以在"资源"页面输入主题，选择"习题"类型，我会自动生成练习题。"
        elif intent == "规划请求":
            return "好的，我来帮你制定学习计划。\n\n你可以在"路径"页面输入主题，我会为你规划个性化学习路径。"
        else:
            return "我明白你的需求。你可以：\n1. 在"资源"页面输入主题生成学习资料\n2. 在"路径"页面规划学习路径\n3. 直接告诉我你想学什么，我来帮你"
