"""
FastAPI应用入口
配置CORS、路由挂载、启动/关闭事件
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import settings
from app.database import connect_db, close_db
from app.routers import chat, resource, path


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时连接数据库
    await connect_db()
    yield
    # 关闭时断开数据库
    await close_db()


# 创建FastAPI应用
app = FastAPI(
    title="A3 多智能体学习系统",
    description="基于大模型的个性化资源生成与学习多智能体系统",
    version="1.0.0",
    lifespan=lifespan
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载路由
app.include_router(chat.router)
app.include_router(resource.router)
app.include_router(path.router)


@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "A3 多智能体学习系统 API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health():
    """健康检查"""
    return {"status": "healthy"}
