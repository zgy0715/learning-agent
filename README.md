# A3 - 基于大模型的个性化资源生成与学习多智能体系统

## 项目简介

本系统是一个基于大语言模型的个性化学习平台，通过多智能体协作实现：
1. **对话式学习画像构建** - 通过自然对话自动分析用户学习特征
2. **多智能体协同资源生成** - 自动生成文档、思维导图、习题等多种学习资源
3. **个性化学习路径规划** - 根据用户画像定制专属学习计划

## 技术栈

| 层级 | 技术选型 |
|------|----------|
| 前端 | Vue 3 + Vite + ECharts |
| 后端 | FastAPI + LangGraph |
| 数据库 | MongoDB |
| LLM | 支持OpenAI/DeepSeek/讯飞星火等 |
| Agent框架 | LangGraph (ReAct/Supervisor/Plan-and-Execute) |
| 结构化输出 | instructor + Pydantic |

## 快速启动

### 1. 启动MongoDB

```bash
# 确保MongoDB已安装并运行在默认端口27017
mongod --dbpath ./data/db
```

### 2. 启动后端

```bash
cd backend

# 创建虚拟环境（推荐）
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填入你的 LLM API Key

# 启动服务
python run.py
# 后端运行在 http://localhost:8000
```

### 3. 启动前端

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
# 前端运行在 http://localhost:5173
```

## 项目结构

```
a3-learning-agent/
├── backend/                    # FastAPI 后端
│   ├── app/
│   │   ├── main.py            # FastAPI 入口
│   │   ├── config.py          # 配置管理
│   │   ├── database.py        # MongoDB 连接
│   │   ├── models/            # Pydantic 数据模型
│   │   ├── routers/           # API 路由
│   │   ├── agents/            # LangGraph 智能体
│   │   ├── services/          # 业务服务层
│   │   └── tools/             # Agent 工具
│   ├── knowledge_base/        # 课程知识库
│   ├── requirements.txt       # Python 依赖
│   ├── .env.example           # 环境变量模板
│   └── run.py                 # 启动脚本
│
├── frontend/                   # Vue 3 前端
│   ├── src/
│   │   ├── views/             # 页面组件
│   │   ├── components/        # 可复用组件
│   │   ├── stores/            # Pinia 状态管理
│   │   ├── services/          # API 调用
│   │   └── router/            # 路由配置
│   ├── package.json
│   └── vite.config.js
│
└── docs/                       # 项目文档
```

## 核心功能

### 功能一：对话式学习画像构建
- 通过自然对话提取用户学习特征
- 构建6维度学习画像（知识基础、认知风格、易错点偏好、学习偏好、学习节奏、目标导向）
- 实时更新画像并可视化展示

### 功能二：多智能体协同资源生成
- 主管智能体拆解任务，调度多个专业智能体
- 生成文档、思维导图、习题、PPT、代码、视频、音频等7种资源
- 自动质量检查和内容安全过滤

### 功能三：个性化学习路径规划
- 根据用户画像和目标生成学习计划
- 支持反馈驱动的动态调整
- 逐步推送个性化资源

## 环境变量配置

在 `backend/.env` 中配置：

```bash
# LLM 配置
LLM_PROVIDER=openai
LLM_API_KEY=sk-your-api-key-here
LLM_MODEL=gpt-4o

# MongoDB
MONGODB_URL=mongodb://localhost:27017
MONGODB_DB_NAME=a3_learning_agent

# Embedding（可选）
EMBEDDING_MODEL=BAAI/bge-m3
```

## 开发说明

- 后端使用异步编程（async/await）
- Agent工作流使用LangGraph状态图实现
- 支持SSE流式响应
- 向量检索使用numpy余弦相似度（零依赖方案）

## 许可证

MIT License
