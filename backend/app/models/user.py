"""
用户相关数据模型
包括用户信息、学习画像等
"""
from pydantic import BaseModel, Field
from typing import Dict, Optional, List
from datetime import datetime
from enum import Enum


class KnowledgeLevel(str, Enum):
    """知识水平"""
    BEGINNER = "初学"
    ELEMENTARY = "入门"
    INTERMEDIATE = "进阶"
    ADVANCED = "精通"


class CognitiveStyle(str, Enum):
    """认知风格"""
    VISUAL = "视觉型"
    AUDITORY = "听觉型"
    KINESTHETIC = "动觉型"
    READING = "阅读型"


class ErrorPattern(str, Enum):
    """易错点偏好"""
    CONCEPT_CONFUSION = "概念混淆"
    CALCULATION_CARELESS = "计算粗心"
    LOGIC不清 = "逻辑不清"
    MEMORY_DIFFICULTY = "记忆困难"


class LearningPreference(str, Enum):
    """学习偏好"""
    VIDEO = "视频为主"
    TEXT = "文字为主"
    PRACTICE = "练习为主"
    MIXED = "混合型"


class LearningPace(str, Enum):
    """学习节奏"""
    FAST = "快节奏"
    MODERATE = "适中"
    SLOW = "慢节奏"
    FRAGMENTED = "碎片化"


class GoalOrientation(str, Enum):
    """目标导向"""
    EXAM = "应试取证"
    PRACTICAL = "技能实践"
    INTEREST = "兴趣探索"
    ACADEMIC = "学术研究"


class ProfileDimension(BaseModel):
    """画像维度"""
    value: str = Field(description="维度值")
    confidence: float = Field(ge=0.0, le=1.0, description="置信度 0-1")


class User(BaseModel):
    """用户模型"""
    id: Optional[str] = Field(None, alias="_id")
    username: str = Field(description="用户名")
    created_at: datetime = Field(default_factory=datetime.now)
    last_active: datetime = Field(default_factory=datetime.now)
    settings: Dict = Field(default_factory=dict)

    class Config:
        populate_by_name = True


class UserProfile(BaseModel):
    """用户学习画像"""
    id: Optional[str] = Field(None, alias="_id")
    user_id: str = Field(description="关联用户ID")
    version: int = Field(default=1, description="版本号")
    dimensions: Dict[str, ProfileDimension] = Field(
        description="6维度画像数据",
        default_factory=lambda: {
            "knowledge_base": ProfileDimension(value=KnowledgeLevel.BEGINNER, confidence=0.0),
            "cognitive_style": ProfileDimension(value=CognitiveStyle.VISUAL, confidence=0.0),
            "error_patterns": ProfileDimension(value=ErrorPattern.CONCEPT_CONFUSION, confidence=0.0),
            "learning_preference": ProfileDimension(value=LearningPreference.MIXED, confidence=0.0),
            "learning_pace": ProfileDimension(value=LearningPace.MODERATE, confidence=0.0),
            "goal_orientation": ProfileDimension(value=GoalOrientation.INTEREST, confidence=0.0),
        }
    )
    updated_at: datetime = Field(default_factory=datetime.now)
    update_source: str = Field(default="conversation", description="更新来源")

    class Config:
        populate_by_name = True
