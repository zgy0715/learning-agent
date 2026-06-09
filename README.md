# A3 - 基于大模型的个性化资源生成与学习多智能体系统

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/FastAPI-0.115-009688?style=flat&logo=fastapi&logoColor=white" alt="FastAPI">
  <img src="https://img.shields.io/badge/Vue_3-5.5-4FC08D?style=flat&logo=vue.js&logoColor=white" alt="Vue 3">
  <img src="https://img.shields.io/badge/LangGraph-%E2%9C%94-1C3C3C?style=flat" alt="LangGraph">
  <img src="https://img.shields.io/badge/MongoDB-7.0-47A248?style=flat&logo=mongodb&logoColor=white" alt="MongoDB">
  <img src="https://img.shields.io/badge/ECharts-5.6-AA344D?style=flat" alt="ECharts">
  <img src="https://img.shields.io/badge/License-MIT-yellow?style=flat" alt="License">
  <img src="https://img.shields.io/badge/PRs-Welcome-brightgreen?style=flat" alt="PRs Welcome">
</p>

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
| 数据库 | MongoDB (Motor 异步驱动) |
| LLM | OpenAI 兼容接口：DeepSeek / 通义 / 智谱 / ollama 等 |
| Agent框架 | LangGraph 真实状态图 (ReAct / Supervisor+Critic / Plan-and-Execute) |
| 检索增强 | 真实向量(ollama bge-m3 / sentence-transformers) + CRAG 防幻觉 |
| 结构化输出 | JSON mode + Pydantic 校验 + 修复重试 |

## 快速启动

### 1. 启动MongoDB

```bash
# 确保MongoDB已安装并运行在默认端口27017
mongod --dbpath ./data/db
```

### 1.5 准备 Embedding（真向量检索，二选一）

```bash
# 方案A（推荐）：本地 ollama，免费离线
ollama pull bge-m3        # 在 .env 中保持 EMBEDDING_PROVIDER=ollama

# 方案B：无 ollama 时，设 EMBEDDING_PROVIDER=sentence_transformers
#        首次运行会自动下载本地模型（约100MB），纯 Python、离线可用
```

> 然后重建知识库索引（用真实向量）：`cd backend && python -m knowledge_base.index`

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

## 多智能体架构（真实实现）

系统的「多智能体大脑」由 **3 张真实的 LangGraph 状态图**驱动，节点间通过状态流转与条件边协作：

### 1. 画像分析图 `agents/graph/profile_graph.py`（ReAct 风格）
```
意图识别 → LLM结构化抽取6维画像(含证据) → 置信度加权合并 → 决策(直接答/追问)
```
- 摒弃关键词匹配，画像由 LLM 真实推断；与历史画像做**信念更新**（belief update）而非覆盖。
- 画像按 version 持久化，前端雷达图实时反映演化。

### 2. 资源生成图 `agents/graph/resource_graph.py`（Supervisor + Critic 自精炼）
```
Supervisor(拆解/定难度风格) → CRAG检索取证 → 撰写核心文档
   → 多Worker并行(思维导图/习题/代码/PPT...) → Critic评分
   → [分数<阈值] → Revise修订 → 回Critic (真Self-Refine循环)
   → 安全过滤 → 聚合(带真质量分+引用)
```
- 对标 MetaGPT/ChatDev 角色化 SOP、Self-Refine 评分驱动修订、CRAG grounded 写作。

### 3. 路径规划图 `agents/graph/path_graph.py`（Plan-and-Execute + Re-Plan）
```
plan : CRAG了解知识结构 → LLM按画像规划步骤 → 补全字段
replan: 按学生反馈(太难/太简单/需帮助) → LLM真重规划下游步骤 → 持久化
```

## 防幻觉机制（CRAG）

`services/rag.py:crag_retrieve` 实现纠错式检索：
**真实向量召回 → LLM逐块相关性评分 → 过滤 → 不足则改写query重试 → 输出 `knowledge_sufficient` 标志**。
当知识库缺乏强相关资料时，系统明确声明「资料不足、以教材为准」而非编造，前端展示防幻觉提示横幅。

## 开发说明

- 后端全异步（async/await），三个 Agent 均为真实 LangGraph `StateGraph.ainvoke` 驱动。
- **真流式**：对话经 `chat_stream` 逐 token SSE 推送，前端逐字渲染。
- **真进度**：资源生成各节点通过 progress 回调写真实步骤，前端进度条同步显示
  `Supervisor→检索→撰写→并行生成→评审→修订→聚合`。
- **真向量检索**：embedding 默认走本地 ollama（`bge-m3`），失败自动回退 sentence-transformers（离线可用）。
- **结构化输出**：JSON mode + Pydantic 校验 + 失败修复重试，跨 provider 健壮（不依赖 function-calling）。

## 使用的开源项目与前沿 AI 工具（致谢与协议）

| 项目/工具 | 用途 | 来源 | 协议 |
|---|---|---|---|
| LangGraph | 多智能体状态图编排 | github.com/langchain-ai/langgraph | MIT |
| FastAPI | 后端 Web 框架 | github.com/fastapi/fastapi | MIT |
| Vue 3 / Vite | 前端框架与构建 | github.com/vuejs | MIT |
| sentence-transformers | 本地文本向量化（回退方案） | github.com/UKPLab/sentence-transformers | Apache-2.0 |
| BGE-M3 / bge-small-zh | Embedding 模型 | huggingface.co/BAAI | MIT |
| Ollama | 本地模型推理（embedding/可选对话） | github.com/ollama/ollama | MIT |
| MongoDB / Motor | 数据存储与异步驱动 | github.com/mongodb | Apache-2.0 / SSPL |

**架构思想借鉴**（致谢）：CRAG / Self-RAG（纠错式检索防幻觉）、Self-Refine（评分驱动修订）、
MetaGPT / ChatDev（角色化多智能体 SOP）、Stanford STORM / GPT-Researcher（多角色协作写作）、
Letta / MemGPT（自编辑记忆）。

> AI Coding 工具说明：本项目在开发过程中使用 Claude Code 辅助编码。

## 许可证

MIT License
