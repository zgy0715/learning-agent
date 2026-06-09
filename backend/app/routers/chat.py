"""
对话与画像API路由
处理用户对话、画像查询和更新
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from typing import List, Optional
from datetime import datetime
from bson import ObjectId
import json

from app.models.chat import ChatRequest, ChatSession
from app.models.user import UserProfile
from app.database import get_collection
from app.agents.profile_agent import ProfileAgent
from app.services.llm import chat_stream, chat

router = APIRouter(prefix="/api", tags=["chat"])

# 全局ProfileAgent实例
profile_agent = ProfileAgent()


@router.post("/chat")
async def send_message(request: ChatRequest):
    """
    发送消息并获取AI回复
    SSE流式返回：token事件、profile_update事件、done事件
    """
    try:
        # 获取或创建会话
        session = await get_collection("chat_sessions").find_one(
            {"_id": ObjectId(request.session_id)}
        )
        if not session:
            raise HTTPException(status_code=404, detail="会话不存在")

        user_id = session["user_id"]

        # 保存用户消息
        user_message = {
            "session_id": request.session_id,
            "role": "user",
            "content": request.message,
            "timestamp": datetime.now(),
        }
        await get_collection("chat_messages").insert_one(user_message)

        # 获取当前画像
        profile_doc = await get_collection("profiles").find_one(
            {"user_id": user_id},
            sort=[("version", -1)]
        )
        current_profile = profile_doc.get("dimensions", {}) if profile_doc else {}

        # 获取对话历史
        messages_cursor = get_collection("chat_messages").find(
            {"session_id": request.session_id}
        ).sort("timestamp", 1).limit(20)
        messages = await messages_cursor.to_list(20)

        # 调用ProfileAgent分析（真 LangGraph：意图→LLM抽取画像→置信度合并→决策）
        result = await profile_agent.analyze(
            messages=messages,
            current_profile=current_profile,
            user_id=user_id
        )

        # 返回 SSE 真流式响应：逐 token 推送回复，结束后再发画像更新与完成事件
        async def event_generator():
            full_reply = ""
            reply_messages = result.get("reply_messages")

            try:
                if reply_messages:
                    # 真 token 流式：直接消费 LLM 增量输出
                    async for token in chat_stream(reply_messages, temperature=0.7, max_tokens=1500):
                        full_reply += token
                        yield f"data: {json.dumps({'content': token})}\n\n"
                else:
                    # 无 reply_messages（如首条欢迎语）则回退为整段文本
                    full_reply = result.get("response", "")
                    if full_reply:
                        yield f"data: {json.dumps({'content': full_reply})}\n\n"
            except Exception as e:
                err = f"（生成回复时出错：{e}）"
                full_reply = full_reply or err
                yield f"data: {json.dumps({'content': err})}\n\n"

            # 落库完整回复
            assistant_message = {
                "session_id": request.session_id,
                "role": "assistant",
                "content": full_reply,
                "timestamp": datetime.now(),
                "metadata": {
                    "intent": result.get("intent", ""),
                    "profile_updated": result.get("profile_updated", False),
                },
            }
            insert_res = await get_collection("chat_messages").insert_one(assistant_message)

            # 画像更新事件（前端据此刷新雷达图）
            if result.get("profile_updated"):
                yield f"data: {json.dumps({'profile_update': result.get('profile_dimensions', {})})}\n\n"

            # 完成事件
            yield f"data: {json.dumps({'message_id': str(insert_res.inserted_id), 'tokens_used': result.get('tokens_used', 0)})}\n\n"

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/profile")
async def get_profile(user_id: str):
    """获取用户画像"""
    try:
        profile = await get_collection("profiles").find_one(
            {"user_id": user_id},
            sort=[("version", -1)]
        )
        if not profile:
            # 返回默认画像
            return {
                "user_id": user_id,
                "version": 0,
                "dimensions": {},
                "updated_at": None
            }
        return {
            "user_id": profile["user_id"],
            "version": profile.get("version", 1),
            "dimensions": profile.get("dimensions", {}),
            "updated_at": profile.get("updated_at")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/profile")
async def update_profile(user_id: str, dimension: str, value: str):
    """手动修正画像维度"""
    try:
        # 获取最新版本
        profile = await get_collection("profiles").find_one(
            {"user_id": user_id},
            sort=[("version", -1)]
        )
        new_version = (profile.get("version", 0) + 1) if profile else 1

        # 更新维度
        dimensions = profile.get("dimensions", {}) if profile else {}
        dimensions[dimension] = {
            "value": value,
            "confidence": 1.0  # 手动设置，置信度为1
        }

        # 创建新版本
        new_profile = {
            "user_id": user_id,
            "version": new_version,
            "dimensions": dimensions,
            "updated_at": datetime.now(),
            "update_source": "manual"
        }
        await get_collection("profiles").insert_one(new_profile)

        return {
            "success": True,
            "new_version": new_version
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/profile/history")
async def get_profile_history(user_id: str, limit: int = 10):
    """获取画像历史"""
    try:
        cursor = get_collection("profiles").find(
            {"user_id": user_id}
        ).sort("version", -1).limit(limit)
        profiles = await cursor.to_list(limit)
        return [
            {
                "version": p["version"],
                "dimensions": p.get("dimensions", {}),
                "updated_at": p.get("updated_at"),
                "update_source": p.get("update_source")
            }
            for p in profiles
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sessions")
async def create_session(user_id: str, title: str = "新对话"):
    """创建新会话"""
    try:
        session = {
            "user_id": user_id,
            "title": title,
            "created_at": datetime.now(),
            "last_message": None
        }
        result = await get_collection("chat_sessions").insert_one(session)
        return {
            "session_id": str(result.inserted_id)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions")
async def list_sessions(user_id: str):
    """获取会话列表"""
    try:
        cursor = get_collection("chat_sessions").find(
            {"user_id": user_id}
        ).sort("created_at", -1)
        sessions = await cursor.to_list(50)
        return [
            {
                "session_id": str(s["_id"]),
                "title": s.get("title", "新对话"),
                "created_at": s.get("created_at"),
                "last_message": s.get("last_message")
            }
            for s in sessions
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
