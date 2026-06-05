"""
学习路径相关数据模型
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from enum import Enum


class StepDifficulty(str, Enum):
    """步骤难度"""
    BASIC = "基础"
    CORE = "核心"
    ADVANCED = "进阶"


class StepStatus(str, Enum):
    """步骤状态"""
    PENDING = "pending"
    CURRENT = "current"
    COMPLETED = "completed"
    SKIPPED = "skipped"


class PathStep(BaseModel):
    """学习步骤"""
    step_id: str = Field(description="步骤序号")
    name: str = Field(description="步骤名称")
    objective: str = Field(description="学习目标")
    difficulty: StepDifficulty = Field(description="难度等级")
    duration_minutes: int = Field(description="预估学习时长（分钟）")
    resource_ids: List[str] = Field(default_factory=list, description="关联资源ID列表")
    status: StepStatus = Field(default=StepStatus.PENDING)
    prerequisites: List[str] = Field(default_factory=list, description="前置知识依赖")
    rag_query: str = Field(default="", description="用于检索知识库的查询语句")


class Progress(BaseModel):
    """学习进度"""
    path_id: str = Field(description="学习路径ID")
    user_id: str = Field(description="用户ID")
    step_index: int = Field(description="当前步骤索引")
    status: StepStatus = Field(description="步骤状态")
    start_time: Optional[datetime] = Field(None)
    complete_time: Optional[datetime] = Field(None)
    score: Optional[float] = Field(None, ge=0, le=100)


class LearningPath(BaseModel):
    """学习路径模型"""
    id: Optional[str] = Field(None, alias="_id")
    user_id: str = Field(description="用户ID")
    topic: str = Field(description="学习主题")
    version: int = Field(default=1, description="路径版本")
    steps: List[PathStep] = Field(description="学习步骤列表")
    created_at: datetime = Field(default_factory=datetime.now)

    class Config:
        populate_by_name = True


class FeedbackType(str, Enum):
    """反馈类型"""
    TOO_HARD = "too_hard"           # 太难
    TOO_EASY = "too_easy"           # 太简单
    NEED_HELP = "need_help"         # 需要帮助
    COMPLETED = "completed"         # 完成


class FeedbackRequest(BaseModel):
    """反馈请求"""
    path_id: str = Field(description="学习路径ID")
    step_id: str = Field(description="步骤ID")
    feedback_type: FeedbackType = Field(description="反馈类型")


class PathPlanRequest(BaseModel):
    """路径规划请求"""
    user_id: str = Field(description="用户ID")
    topic: str = Field(description="学习主题")
