"""
资源生成API路由
处理学习资源的生成、查询和进度追踪
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from typing import List, Optional
from datetime import datetime
from bson import ObjectId
import json
import asyncio

from app.models.resource import GenerateRequest, ResourceType
from app.database import get_collection
from app.agents.resource_agent import ResourceAgent

router = APIRouter(prefix="/api", tags=["resource"])

# 全局ResourceAgent实例
resource_agent = ResourceAgent()


@router.post("/generate")
async def generate_resources(request: GenerateRequest):
    """
    启动资源生成任务
    返回task_id，前端用于轮询进度
    """
    try:
        task_id = str(ObjectId())

        # 创建任务记录
        task = {
            "task_id": task_id,
            "user_id": request.user_id,
            "task_type": "resource_generation",
            "status": "pending",
            "current_step": "初始化",
            "progress": 0.0,
            "result": None,
            "error": None,
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        await get_collection("tasks").insert_one(task)

        # 异步启动资源生成工作流
        asyncio.create_task(
            run_generation_workflow(task_id, request)
        )

        return {"task_id": task_id}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def run_generation_workflow(task_id: str, request: GenerateRequest):
    """执行资源生成工作流"""
    try:
        # 更新任务状态为运行中
        await get_collection("tasks").update_one(
            {"task_id": task_id},
            {"$set": {
                "status": "running",
                "current_step": "开始生成",
                "updated_at": datetime.now()
            }}
        )

        # 调用ResourceAgent生成资源
        result = await resource_agent.generate(
            user_id=request.user_id,
            topic=request.topic,
            resource_types=request.resource_types,
            task_id=task_id
        )

        # 保存生成的资源
        resource_ids = []
        for resource in result.get("resources", []):
            resource_doc = {
                "user_id": request.user_id,
                "topic": request.topic,
                "resource_type": resource["type"],
                "content": resource["content"],
                "metadata": {
                    "format": resource.get("format", "markdown"),
                    "quality_score": resource.get("quality_score", 0),
                    "rag_sources": result.get("rag_sources", []),
                    "safety_checked": True,
                    "generated_by": resource.get("agent", "ResourceAgent")
                },
                "created_at": datetime.now()
            }
            insert_result = await get_collection("resources").insert_one(resource_doc)
            resource_ids.append(str(insert_result.inserted_id))

        # 更新任务状态为完成
        await get_collection("tasks").update_one(
            {"task_id": task_id},
            {"$set": {
                "status": "completed",
                "current_step": "完成",
                "progress": 1.0,
                "result": {
                    "resource_ids": resource_ids,
                    "resources": result.get("resources", [])
                },
                "updated_at": datetime.now()
            }}
        )

    except Exception as e:
        # 更新任务状态为失败
        await get_collection("tasks").update_one(
            {"task_id": task_id},
            {"$set": {
                "status": "failed",
                "error": str(e),
                "updated_at": datetime.now()
            }}
        )


@router.get("/task/{task_id}")
async def get_task_status(task_id: str):
    """查询任务进度"""
    try:
        task = await get_collection("tasks").find_one({"task_id": task_id})
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")
        return {
            "task_id": task["task_id"],
            "status": task["status"],
            "current_step": task.get("current_step", ""),
            "progress": task.get("progress", 0),
            "result": task.get("result"),
            "error": task.get("error")
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/task/{task_id}/stream")
async def stream_task_progress(task_id: str):
    """SSE流式推送任务进度"""
    async def event_generator():
        last_status = None
        while True:
            task = await get_collection("tasks").find_one({"task_id": task_id})
            if not task:
                yield f"data: {json.dumps({'error': '任务不存在'})}\n\n"
                break

            current_status = {
                "status": task["status"],
                "current_step": task.get("current_step", ""),
                "progress": task.get("progress", 0)
            }

            # 只在状态变化时推送
            if current_status != last_status:
                yield f"data: {json.dumps(current_status)}\n\n"
                last_status = current_status

            # 任务完成或失败时结束
            if task["status"] in ["completed", "failed"]:
                if task["status"] == "completed":
                    yield f"data: {json.dumps({'resources': task.get('result', {}).get('resources', [])})}\n\n"
                else:
                    yield f"data: {json.dumps({'error': task.get('error', '未知错误')})}\n\n"
                break

            await asyncio.sleep(0.5)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )


@router.get("/resources")
async def list_resources(
    user_id: str,
    resource_type: Optional[str] = None,
    topic: Optional[str] = None,
    limit: int = 20
):
    """获取资源列表"""
    try:
        query = {"user_id": user_id}
        if resource_type:
            query["resource_type"] = resource_type
        if topic:
            query["topic"] = {"$regex": topic, "$options": "i"}

        cursor = get_collection("resources").find(query).sort("created_at", -1).limit(limit)
        resources = await cursor.to_list(limit)
        return [
            {
                "id": str(r["_id"]),
                "topic": r["topic"],
                "resource_type": r["resource_type"],
                "content": r["content"],
                "metadata": r.get("metadata", {}),
                "created_at": r.get("created_at")
            }
            for r in resources
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/resources/{resource_id}")
async def get_resource(resource_id: str):
    """获取资源详情"""
    try:
        resource = await get_collection("resources").find_one(
            {"_id": ObjectId(resource_id)}
        )
        if not resource:
            raise HTTPException(status_code=404, detail="资源不存在")
        return {
            "id": str(resource["_id"]),
            "topic": resource["topic"],
            "resource_type": resource["resource_type"],
            "content": resource["content"],
            "metadata": resource.get("metadata", {}),
            "created_at": resource.get("created_at")
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
