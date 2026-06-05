"""
LLM调用服务
统一封装所有LLM调用，屏蔽Provider差异
支持OpenAI、DeepSeek、讯飞星火等多种模型
"""
from openai import AsyncOpenAI
from typing import List, Dict, Optional, AsyncIterator
from pydantic import BaseModel
import logging

from app.config import settings

logger = logging.getLogger(__name__)

# 异步OpenAI客户端
_client: Optional[AsyncOpenAI] = None


def get_client() -> AsyncOpenAI:
    """获取OpenAI客户端"""
    global _client
    if _client is None:
        _client = AsyncOpenAI(
            api_key=settings.LLM_API_KEY,
            base_url=settings.LLM_BASE_URL
        )
    return _client


async def chat(
    messages: List[Dict[str, str]],
    model: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 2000
) -> str:
    """
    调用LLM

    Args:
        messages: 消息列表，格式 [{"role": "user", "content": "..."}]
        model: 模型名称，默认使用配置中的模型
        temperature: 温度参数
        max_tokens: 最大token数

    Returns:
        str: LLM回复内容
    """
    try:
        client = get_client()
        response = await client.chat.completions.create(
            model=model or settings.LLM_MODEL,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"LLM chat error: {e}")
        raise


async def chat_stream(
    messages: List[Dict[str, str]],
    model: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 2000
) -> AsyncIterator[str]:
    """
    流式调用LLM

    Args:
        messages: 消息列表
        model: 模型名称
        temperature: 温度参数
        max_tokens: 最大token数

    Yields:
        str: LLM回复的每个token
    """
    try:
        client = get_client()
        response = await client.chat.completions.create(
            model=model or settings.LLM_MODEL,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True
        )
        async for chunk in response:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
    except Exception as e:
        logger.error(f"LLM stream error: {e}")
        raise


async def structured_output(
    messages: List[Dict[str, str]],
    response_model: type[BaseModel],
    model: Optional[str] = None,
    temperature: float = 0.7,
    max_retries: int = 3
) -> BaseModel:
    """
    结构化输出调用

    Args:
        messages: 消息列表
        response_model: 期望的输出模型
        model: 模型名称
        temperature: 温度参数
        max_retries: 最大重试次数

    Returns:
        BaseModel: 符合模型的输出
    """
    try:
        import instructor
        client = instructor.from_openai(get_client())
        result = client.chat.completions.create(
            model=model or settings.LLM_MODEL,
            messages=messages,
            response_model=response_model,
            temperature=temperature,
            max_retries=max_retries
        )
        return result
    except Exception as e:
        logger.error(f"Structured output error: {e}")
        raise


def format_messages(
    system_prompt: str,
    user_message: str,
    history: Optional[List[Dict[str, str]]] = None
) -> List[Dict[str, str]]:
    """
    格式化消息列表

    Args:
        system_prompt: 系统提示词
        user_message: 用户消息
        history: 历史对话

    Returns:
        List[Dict]: 格式化后的消息列表
    """
    messages = [{"role": "system", "content": system_prompt}]
    if history:
        messages.extend(history)
    messages.append({"role": "user", "content": user_message})
    return messages
