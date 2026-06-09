"""
LLM 调用服务
统一封装所有 LLM 调用，屏蔽 Provider 差异（OpenAI / DeepSeek / 通义 / 智谱 / ollama 等 OpenAI 兼容接口）。

相比旧版改进：
- 结构化输出不再依赖 instructor 的 function-calling（DeepSeek/ollama 支持不稳），改为
  「JSON mode → JSON 抽取 → Pydantic 校验 → 失败带错误修复重试」，跨 provider 更健壮。
- 新增 chat_with_usage：返回真实 token 消耗，供前端展示。
"""
from openai import AsyncOpenAI
from typing import List, Dict, Optional, AsyncIterator, Tuple, Type, TypeVar
from pydantic import BaseModel, ValidationError
import logging
import json
import re

from app.config import settings

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

# 异步 OpenAI 客户端（兼容所有 OpenAI 协议的服务）
_client: Optional[AsyncOpenAI] = None


def get_client() -> AsyncOpenAI:
    """获取（懒加载）OpenAI 兼容客户端"""
    global _client
    if _client is None:
        _client = AsyncOpenAI(
            api_key=settings.LLM_API_KEY,
            base_url=settings.LLM_BASE_URL or None,
        )
    return _client


async def chat(
    messages: List[Dict[str, str]],
    model: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 2000,
) -> str:
    """调用 LLM，返回回复文本"""
    content, _ = await chat_with_usage(messages, model, temperature, max_tokens)
    return content


async def chat_with_usage(
    messages: List[Dict[str, str]],
    model: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 2000,
    response_format: Optional[Dict] = None,
) -> Tuple[str, int]:
    """调用 LLM，返回 (回复文本, token 消耗)"""
    try:
        client = get_client()
        kwargs = dict(
            model=model or settings.LLM_MODEL,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        if response_format:
            kwargs["response_format"] = response_format
        response = await client.chat.completions.create(**kwargs)
        content = response.choices[0].message.content or ""
        usage = getattr(response, "usage", None)
        tokens = getattr(usage, "total_tokens", 0) if usage else 0
        return content, tokens
    except Exception as e:
        logger.error(f"LLM chat error: {e}")
        raise


async def chat_stream(
    messages: List[Dict[str, str]],
    model: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 2000,
) -> AsyncIterator[str]:
    """流式调用 LLM，逐 token 产出（真实流式）"""
    try:
        client = get_client()
        response = await client.chat.completions.create(
            model=model or settings.LLM_MODEL,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
        )
        async for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
    except Exception as e:
        logger.error(f"LLM stream error: {e}")
        raise


async def structured(
    messages: List[Dict[str, str]],
    schema: Type[T],
    model: Optional[str] = None,
    temperature: float = 0.2,
    max_tokens: int = 2500,
    max_retries: int = 2,
) -> T:
    """
    结构化输出：让 LLM 产出 JSON 并校验为给定的 Pydantic 模型。

    流程：JSON mode 请求 → 抽取 JSON → Pydantic 校验 → 失败则把错误反馈给模型修复重试。
    跨 provider 健壮，不依赖 function-calling。
    """
    # 在消息中注入 schema 说明与 JSON 指令（DeepSeek JSON mode 要求 prompt 含 "json"）
    schema_hint = _schema_hint(schema)
    work_messages = list(messages)
    work_messages.append({
        "role": "system",
        "content": (
            "你必须只输出一个合法的 JSON 对象，不要包含任何解释、前后缀或 markdown 代码块标记。\n"
            f"JSON 必须严格符合以下结构：\n{schema_hint}"
        ),
    })

    last_err: Optional[str] = None
    raw = ""
    for attempt in range(max_retries + 1):
        # 优先尝试 JSON mode；失败（provider 不支持）则退化为纯文本 + 抽取
        try:
            raw, _ = await chat_with_usage(
                work_messages, model=model, temperature=temperature,
                max_tokens=max_tokens, response_format={"type": "json_object"},
            )
        except Exception:  # noqa: BLE001
            raw, _ = await chat_with_usage(
                work_messages, model=model, temperature=temperature, max_tokens=max_tokens,
            )

        try:
            obj = _extract_json(raw)
            return schema.model_validate(obj)
        except (ValueError, ValidationError) as e:
            last_err = str(e)
            logger.warning(f"structured 第 {attempt + 1} 次校验失败: {last_err}")
            # 带着错误信息让模型自我修复
            work_messages.append({"role": "assistant", "content": raw})
            work_messages.append({
                "role": "user",
                "content": f"上面的 JSON 不符合要求：{last_err}\n请只输出修正后的合法 JSON。",
            })

    raise ValueError(f"结构化输出在 {max_retries + 1} 次尝试后仍失败: {last_err}\n原始输出: {raw[:500]}")


def _extract_json(text: str) -> dict:
    """从模型输出中稳健抽取 JSON 对象（容忍代码块围栏与前后噪声）"""
    if not text or not text.strip():
        raise ValueError("空输出")
    s = text.strip()
    # 去掉 ```json ... ``` 围栏
    fence = re.search(r"```(?:json)?\s*(.+?)\s*```", s, re.DOTALL)
    if fence:
        s = fence.group(1).strip()
    # 直接尝试
    try:
        return json.loads(s)
    except json.JSONDecodeError:
        pass
    # 截取首个 { 到末个 } 之间的内容
    start, end = s.find("{"), s.rfind("}")
    if start != -1 and end != -1 and end > start:
        return json.loads(s[start:end + 1])
    raise ValueError("未找到合法 JSON 对象")


def _schema_hint(schema: Type[BaseModel]) -> str:
    """生成精简的 JSON Schema 提示"""
    try:
        js = schema.model_json_schema()
        return json.dumps(js.get("properties", js), ensure_ascii=False, indent=2)
    except Exception:  # noqa: BLE001
        return schema.__name__


def format_messages(
    system_prompt: str,
    user_message: str,
    history: Optional[List[Dict[str, str]]] = None,
) -> List[Dict[str, str]]:
    """格式化消息列表"""
    messages = [{"role": "system", "content": system_prompt}]
    if history:
        messages.extend(history)
    messages.append({"role": "user", "content": user_message})
    return messages
