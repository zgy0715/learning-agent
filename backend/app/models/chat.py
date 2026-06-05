"""
对话相关数据模型
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime
from enum import Enum


class MessageRole(str, Enum):
    """消息角色"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ChatMessage(BaseModel):
    """对话消息"""
    id: Optional[str] = Field(None, alias="_id")
    session_id: str = Field(description="会话ID")
    role: MessageRole = Field(description="消息角色")
    content: str = Field(description="消息内容")
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Dict = Field(default_factory=dict, description="元数据")

    class Config:
        populate_by_name = True


class ChatSession(BaseModel):
    """对话会话"""
    id: Optional[str] = Field(None, alias="_id")
    user_id: str = Field(description="用户ID")
    title: str = Field(default="新对话", description="会话标题")
    created_at: datetime = Field(default_factory=datetime.now)
    last_message: Optional[str] = Field(None, description="最后一条消息预览")

    class Config:
        populate_by_name = True


class ChatRequest(BaseModel):
    """对话请求"""
    session_id: str = Field(description="会话ID")
    message: str = Field(description="用户消息")


class ChatResponse(BaseModel):
    """对话响应"""
    message_id: str = Field(description="消息ID")
    content: str = Field(description="AI回复内容")
    profile_update: Optional[Dict] = Field(None, description="画像更新事件")
    tokens_used: int = Field(default=0, description="Token消耗")
