"""
学习资源相关数据模型
"""
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict
from datetime import datetime
from enum import Enum


class ResourceType(str, Enum):
    """资源类型"""
    DOCUMENT = "document"           # 文档
    MINDMAP = "mindmap"             # 思维导图
    EXERCISE = "exercise"           # 习题
    CODE = "code"                   # 代码
    VIDEO = "video"                 # 视频
    AUDIO = "audio"                 # 音频
    PPT = "ppt"                     # PPT


class ResourceMetadata(BaseModel):
    """资源元数据"""
    format: str = Field(description="格式: markdown/json/url/base64")
    quality_score: float = Field(default=0.0, ge=0, le=100, description="质量评分 0-100")
    rag_sources: List[str] = Field(default_factory=list, description="RAG参考文档列表")
    safety_checked: bool = Field(default=False, description="是否通过安全检查")
    generated_by: str = Field(default="", description="生成该资源的Agent名称")


class Resource(BaseModel):
    """学习资源模型"""
    id: Optional[str] = Field(None, alias="_id")
    user_id: str = Field(description="所属用户ID")
    topic: str = Field(description="知识点/主题")
    resource_type: ResourceType = Field(description="资源类型")
    content: str = Field(description="资源内容")
    metadata: ResourceMetadata = Field(default_factory=ResourceMetadata)
    created_at: datetime = Field(default_factory=datetime.now)
    expire_at: Optional[datetime] = Field(None, description="过期时间")

    class Config:
        populate_by_name = True


class QualityReport(BaseModel):
    """质量检查报告"""
    score: float = Field(ge=0, le=100, description="质量评分")
    issues: List[str] = Field(default_factory=list, description="发现的问题")
    suggestions: List[str] = Field(default_factory=list, description="改进建议")
    passed: bool = Field(description="是否通过检查")


class GenerateRequest(BaseModel):
    """资源生成请求"""
    user_id: str = Field(description="用户ID")
    topic: str = Field(description="学习主题")
    resource_types: Optional[List[ResourceType]] = Field(
        default_factory=lambda: [
            ResourceType.DOCUMENT,
            ResourceType.MINDMAP,
            ResourceType.EXERCISE,
            ResourceType.CODE,
            ResourceType.VIDEO,
            ResourceType.AUDIO,
        ],
        description="要生成的资源类型，不传或传 null 则使用默认类型列表"
    )

    @field_validator('resource_types', mode='before')
    @classmethod
    def default_resource_types(cls, v):
        if v is None:
            return [
                ResourceType.DOCUMENT,
                ResourceType.MINDMAP,
                ResourceType.EXERCISE,
                ResourceType.CODE,
                ResourceType.VIDEO,
                ResourceType.AUDIO,
            ]
        return v
