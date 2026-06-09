"""
路径规划API路由
处理学习路径的生成、反馈和进度追踪
"""
from fastapi import APIRouter, HTTPException
from typing import List, Optional
from datetime import datetime
from bson import ObjectId

from app.models.path import PathPlanRequest, FeedbackRequest, FeedbackType
from app.database import get_collection
from app.agents.path_agent import PathAgent

router = APIRouter(prefix="/api/path", tags=["path"])

# 全局PathAgent实例
path_agent = PathAgent()


@router.post("/plan")
async def plan_learning_path(request: PathPlanRequest):
    """生成学习路径"""
    try:
        path_id = str(ObjectId())

        # 调用PathAgent规划路径
        result = await path_agent.plan(
            user_id=request.user_id,
            topic=request.topic
        )

        # 保存学习路径
        path = {
            "user_id": request.user_id,
            "topic": request.topic,
            "version": 1,
            "steps": result.get("steps", []),
            "created_at": datetime.now()
        }
        insert_result = await get_collection("learning_paths").insert_one(path)
        saved_path_id = str(insert_result.inserted_id)

        # 创建进度记录
        for i, step in enumerate(result.get("steps", [])):
            progress = {
                "path_id": saved_path_id,
                "user_id": request.user_id,
                "step_index": i,
                "status": "current" if i == 0 else "pending",
                "start_time": datetime.now() if i == 0 else None,
                "complete_time": None,
                "score": None
            }
            await get_collection("learning_progress").insert_one(progress)

        return {
            "path_id": saved_path_id,
            "steps": result.get("steps", []),
            "message": "学习路径已生成"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("")
async def get_current_path(user_id: str, topic: Optional[str] = None):
    """获取当前学习路径"""
    try:
        query = {"user_id": user_id}
        if topic:
            query["topic"] = topic

        path = await get_collection("learning_paths").find_one(
            query,
            sort=[("version", -1)]
        )
        if not path:
            return {"path": None, "message": "暂无学习路径"}

        # 获取步骤进度
        progress_cursor = get_collection("learning_progress").find(
            {"path_id": str(path["_id"])}
        ).sort("step_index", 1)
        progress_list = await progress_cursor.to_list(50)

        # 合并步骤和进度
        steps_with_progress = []
        for i, step in enumerate(path.get("steps", [])):
            progress = progress_list[i] if i < len(progress_list) else {}
            steps_with_progress.append({
                **step,
                "status": progress.get("status", "pending"),
                "start_time": progress.get("start_time"),
                "complete_time": progress.get("complete_time"),
                "score": progress.get("score")
            })

        return {
            "path_id": str(path["_id"]),
            "topic": path["topic"],
            "version": path.get("version", 1),
            "steps": steps_with_progress,
            "created_at": path.get("created_at")
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/step/{step_id}/resources")
async def get_step_resources(step_id: str, path_id: str):
    """获取步骤关联的资源"""
    try:
        # 获取学习路径
        path = await get_collection("learning_paths").find_one(
            {"_id": ObjectId(path_id)}
        )
        if not path:
            raise HTTPException(status_code=404, detail="学习路径不存在")

        # 查找步骤
        step = None
        for s in path.get("steps", []):
            if s.get("step_id") == step_id:
                step = s
                break

        if not step:
            raise HTTPException(status_code=404, detail="步骤不存在")

        # 获取关联资源
        resource_ids = step.get("resource_ids", [])
        resources = []
        for rid in resource_ids:
            resource = await get_collection("resources").find_one(
                {"_id": ObjectId(rid)}
            )
            if resource:
                resources.append({
                    "id": str(resource["_id"]),
                    "topic": resource["topic"],
                    "resource_type": resource["resource_type"],
                    "content": resource["content"],
                    "metadata": resource.get("metadata", {})
                })

        return {
            "step_id": step_id,
            "resources": resources
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/step/{step_id}/complete")
async def complete_step(step_id: str, path_id: str, score: Optional[float] = None):
    """标记步骤完成"""
    try:
        # 更新进度
        result = await get_collection("learning_progress").update_one(
            {
                "path_id": path_id,
                "step_index": int(step_id.replace("step_", "")) - 1
            },
            {"$set": {
                "status": "completed",
                "complete_time": datetime.now(),
                "score": score
            }}
        )

        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="步骤不存在")

        # 获取下一个步骤
        next_step_index = int(step_id.replace("step_", ""))
        next_progress = await get_collection("learning_progress").find_one(
            {"path_id": path_id, "step_index": next_step_index}
        )

        if next_progress:
            # 更新下一个步骤为当前
            await get_collection("learning_progress").update_one(
                {"_id": next_progress["_id"]},
                {"$set": {
                    "status": "current",
                    "start_time": datetime.now()
                }}
            )
            return {
                "message": "步骤已完成",
                "next_step": f"step_{next_step_index + 1}"
            }
        else:
            return {
                "message": "所有步骤已完成",
                "next_step": None
            }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/feedback")
async def submit_feedback(request: FeedbackRequest):
    """提交用户反馈，触发路径调整"""
    try:
        # 记录反馈
        feedback_doc = {
            "path_id": request.path_id,
            "step_id": request.step_id,
            "feedback_type": request.feedback_type.value,
            "created_at": datetime.now()
        }
        await get_collection("feedback_history").insert_one(feedback_doc)

        # 根据反馈类型，统一交由真 LangGraph 重规划器自适应调整路径并持久化
        adaptive_types = {
            FeedbackType.TOO_HARD: ("too_hard", "已根据「太难」反馈补充前置知识、降低难度并重排路径"),
            FeedbackType.TOO_EASY: ("too_easy", "已根据「太简单」反馈精简步骤并提升后续难度"),
            FeedbackType.NEED_HELP: ("need_help", "已根据「需要帮助」反馈增加示例与练习巩固"),
        }

        if request.feedback_type in adaptive_types:
            fb_value, msg = adaptive_types[request.feedback_type]
            result = await path_agent.handle_feedback(
                path_id=request.path_id,
                step_id=request.step_id,
                feedback_type=fb_value
            )
            if result.get("error"):
                raise HTTPException(status_code=400, detail=result["error"])
            return {
                "message": result.get("notes") or msg,
                "adjusted_path": result
            }

        else:
            return {"message": "反馈已记录"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history")
async def get_path_history(user_id: str, limit: int = 10):
    """获取路径历史"""
    try:
        cursor = get_collection("learning_paths").find(
            {"user_id": user_id}
        ).sort("created_at", -1).limit(limit)
        paths = await cursor.to_list(limit)
        return [
            {
                "path_id": str(p["_id"]),
                "topic": p["topic"],
                "version": p.get("version", 1),
                "steps_count": len(p.get("steps", [])),
                "created_at": p.get("created_at")
            }
            for p in paths
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
