# A3 — 基于大模型的个性化学习多智能体系统

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/FastAPI-0.115-009688?style=flat&logo=fastapi&logoColor=white" alt="FastAPI">
  <img src="https://img.shields.io/badge/MongoDB-7.0-47A248?style=flat&logo=mongodb&logoColor=white" alt="MongoDB">
  <img src="https://img.shields.io/badge/Vue_3-5.5-4FC08D?style=flat&logo=vue.js&logoColor=white" alt="Vue 3">
  <img src="https://img.shields.io/badge/ECharts-5.6-AA344D?style=flat" alt="ECharts">
  <img src="https://img.shields.io/badge/Pinia-2.2-FFD859?style=flat" alt="Pinia">
  <img src="https://img.shields.io/badge/LangGraph-%E2%9C%94-1C3C3C?style=flat" alt="LangGraph">
  <img src="https://img.shields.io/badge/LLM-OpenAI%20Compat-412991?style=flat" alt="LLM">
  <img src="https://img.shields.io/badge/License-MIT-yellow?style=flat" alt="License">
  <img src="https://img.shields.io/badge/PRs-Welcome-brightgreen?style=flat" alt="PRs Welcome">
</p>

<p align="center">
  <b>对话式画像构建 · 多智能体资源生成 · 个性化路径规划</b><br>
  基于 LangGraph 真实状态图编排，支持 DeepSeek / 通义 / 智谱 / ollama 等多种 LLM
</p>

---

## 项目简介

本系统是一个基于大语言模型的**个性化学习平台**，通过多智能体协作实现从对话到学习的完整闭环：

1. **🗣️ 对话式画像构建** — 自然对话自动分析 6 维学习画像（知识基础、认知风格、易错点偏好、学习偏好、学习节奏、目标导向）
2. **🤖 多智能体资源生成** — Supervisor 调度多 Agent 并行生成文档 / 思维导图 / 习题 / 代码 / 视频 / 音频 / PPT
3. **🗺️ 个性化路径规划** — 根据画像定制学习计划，支持反馈驱动的 LLM 真重规划

---

## 技术栈

### 前端

| 技术 | 用途 | 版本 |
|:---|:---|---:|
| Vue 3 | 前端框架（Composition API + `<script setup>`） | ^3.5 |
| Vite | 构建工具 / HMR 开发服务器 | ^6.0 |
| Pinia | 状态管理（chat / profile / resource / path 四个 Store） | ^2.2 |
| Vue Router | SPA 路由（chat / resource / path 三页面） | ^4.4 |
| ECharts | 可视化图表（雷达图 / 仪表盘 / 柱状图 / 饼图） | ^5.6 |
| Axios | HTTP 客户端 | ^1.7 |
| Markdown-it | Markdown 渲染 | ^14.0 |

### 后端

| 技术 | 用途 | 版本 |
|:---|:---|---:|
| FastAPI | Web 框架（全异步） | 0.115+ |
| LangGraph | 多智能体状态图编排（3 张真实 StateGraph） | latest |
| MongoDB + Motor | 数据存储（异步驱动） | 7.0 / Motor 3.x |
| Pydantic v2 | 数据模型与校验 | ^2.0 |
| Sentence-Transformers | 本地文本向量化（回退方案） | latest |
| Ollama | 本地 LLM / Embedding 推理 | latest |

### LLM 支持

| 提供商 | 兼容性 | 备注 |
|:---|:---|:---|
| DeepSeek | ✅ OpenAI 兼容 | 生产推荐 |
| 通义千问 | ✅ OpenAI 兼容 | |
| 智谱 GLM | ✅ OpenAI 兼容 | |
| OpenAI GPT | ✅ | |
| Ollama 本地模型 | ✅ | 开发/离线可用 |

---

## 快速启动

### 前置条件

- Python 3.11+
- Node.js 18+
- MongoDB 7.0+（运行在 `localhost:27017`）

### 1. 准备 Embedding（二选一）

```bash
# 方案 A（推荐）：本地 ollama，免费离线
ollama pull bge-m3
# .env 中保持 EMBEDDING_PROVIDER=ollama

# 方案 B：纯 Python 离线
# .env 中设 EMBEDDING_PROVIDER=sentence_transformers
# 首次运行自动下载模型（约 100MB）
```

```bash
# 重建知识库索引
cd backend && python -m knowledge_base.index
```

### 2. 启动后端

```bash
cd backend

# 创建虚拟环境
python -m venv venv
# Windows: venv\Scripts\activate
# Linux/Mac: source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env，填入 LLM API Key

# 启动服务（默认 http://localhost:8000）
python run.py
```

### 3. 启动前端

```bash
cd frontend
npm install
npm run dev
# 默认 http://localhost:5173
```

---

## 项目结构

```
learning-agent/
├── backend/                          # FastAPI 后端
│   ├── app/
│   │   ├── main.py                   # FastAPI 入口，CORS / 路由挂载
│   │   ├── config.py                 # 配置管理（Pydantic Settings）
│   │   ├── database.py               # MongoDB 连接与索引
│   │   ├── models/                   # Pydantic 数据模型
│   │   │   ├── chat.py               # 会话 / 消息模型
│   │   │   ├── resource.py           # 资源生成请求 & 资源模型
│   │   │   └── user.py               # 用户画像模型
│   │   ├── routers/                  # API 路由
│   │   │   ├── chat.py               # 对话 / 画像 / 会话管理
│   │   │   ├── resource.py           # 资源生成 / 任务轮询
│   │   │   └── path.py               # 学习路径 / 反馈
│   │   ├── agents/                   # LangGraph 智能体
│   │   │   ├── chat_agent.py         # 对话 Agent
│   │   │   ├── profile_agent.py      # 画像分析 Agent
│   │   │   ├── resource_agent.py     # 资源生成 Agent
│   │   │   ├── path_agent.py         # 路径规划 Agent
│   │   │   ├── __init__.py
│   │   │   └── graph/               # 真实 LangGraph 状态图
│   │   │       ├── state.py          # 共享状态定义
│   │   │       ├── profile_graph.py  # 画像分析图（ReAct）
│   │   │       ├── resource_graph.py # 资源生成图（Supervisor+Critic）
│   │   │       └── path_graph.py     # 路径规划图（Plan-and-Execute）
│   │   └── services/                 # 业务服务层
│   │       ├── llm.py                # LLM 调用（流式 / 非流式）
│   │       ├── rag.py                # CRAG 纠错式检索增强
│   │       ├── embedding.py          # 向量化服务
│   │       └── safety.py             # 内容安全过滤
│   ├── knowledge_base/               # 课程知识库
│   │   ├── index.py                  # 知识库索引构建
│   │   └── courses/                  # 课程原始资料
│   ├── requirements.txt
│   ├── .env.example
│   └── run.py                        # 启动脚本
│
├── frontend/                         # Vue 3 前端
│   ├── src/
│   │   ├── App.vue                   # 根组件（Sidebar + RouterView）
│   │   ├── main.js                   # 入口文件
│   │   ├── router/
│   │   │   └── index.js              # 路由配置（/chat /resource /path）
│   │   ├── views/
│   │   │   ├── ChatView.vue          # 智能对话 + 画像面板
│   │   │   ├── ResourceView.vue      # 学习资源生成与展示
│   │   │   └── PathView.vue          # 学习路径规划
│   │   ├── components/
│   │   │   ├── layout/
│   │   │   │   └── Sidebar.vue       # 侧边导航栏
│   │   │   └── profile/
│   │   │       ├── ProfileRadar.vue  # 画像雷达图（ECharts）
│   │   │       └── ProfileGauge.vue  # 综合评分仪表盘（ECharts）
│   │   ├── stores/                   # Pinia 状态管理
│   │   │   ├── chat.js               # 对话状态
│   │   │   ├── profile.js            # 画像状态
│   │   │   ├── resource.js           # 资源状态
│   │   │   └── path.js               # 路径状态
│   │   ├── services/
│   │   │   └── api.js                # Axios + SSE 流式 API 封装
│   │   └── assets/
│   │       └── styles/
│   │           └── main.css          # 全局样式（DeepSeek 蓝白主题）
│   ├── .env                          # 环境变量
│   ├── package.json
│   └── vite.config.js
│
└── docs/                             # 项目文档
    └── API接口文档.md                 # API 参考（v2.0）
```

---

## 核心功能

### 🗣️ 功能一：对话式学习画像构建

通过自然对话自动提取 6 维学习画像，摒弃传统问卷形式：

- LLM 从对话中**结构化抽取**画像维度（含证据）
- 与历史画像做**置信度加权合并**（belief update），而非简单覆盖
- 画像按 version 持久化，前端雷达图实时反映演化
- 前端 Blue-White DeepSeek 风格面板：仪表盘（综合评分）+ 雷达图（维度分布）+ 维度卡片（置信度进度条）

### 🤖 功能二：多智能体协同资源生成

Supervisor 拆解任务，调度多个专业 Agent 并行工作：

| 资源类型 | 生成智能体 | 格式 |
|:---|:---|---:|
| 📄 文档 | MaterialAgent | Markdown |
| 🧠 思维导图 | MindmapAgent | Markmap |
| 📝 习题 | ExerciseAgent | JSON |
| 💻 代码 | CodeAgent | Markdown |
| 🎬 视频脚本 | VideoAgent | Markdown |
| 🎵 音频讲稿 | AudioAgent | Markdown |
| 📊 PPT 大纲 | PptAgent | JSON |

**质量保障**：Critic 智能体评分 → 低分触发 Revise 修订循环（Self-Refine）→ 安全过滤 → 聚合输出

**防幻觉**：CRAG 纠错式检索 — 知识不足时明确声明"以教材为准"而非编造

### 🗺️ 功能三：个性化学习路径规划

- CRAG 了解知识结构 → LLM 按画像规划 5-8 步（个性化难度 / 时长 / 资源类型）
- 学生反馈（太难 / 太简单 / 需帮助）→ Re-Planner **真 LLM 重规划**下游步骤
- 路径持久化，逐步推送资源

---

## 多智能体架构

系统的「多智能体大脑」由 **3 张真实的 LangGraph 状态图**驱动，节点间通过状态流转与条件边协作：

### 1. 画像分析图 `agents/graph/profile_graph.py`（ReAct 风格）

```
意图识别 → LLM 结构化抽取 6 维画像（含证据）→ 置信度加权合并 → 决策（直接答 / 追问）
```

### 2. 资源生成图 `agents/graph/resource_graph.py`（Supervisor + Critic 自精炼）

```
Supervisor（拆解 / 定难度风格）→ CRAG 检索取证 → 撰写核心文档
  → 多 Worker 并行（思维导图 / 习题 / 代码 / PPT…）→ Critic 评分
  → [分数 < 阈值] → Revise 修订 → 回 Critic（真 Self-Refine 循环）
  → 安全过滤 → 聚合（带真质量分 + 引用）
```

### 3. 路径规划图 `agents/graph/path_graph.py`（Plan-and-Execute + Re-Plan）

```
plan:   CRAG 了解知识结构 → LLM 按画像规划步骤 → 补全字段
replan: 按学生反馈（太难 / 太简单 / 需帮助）→ LLM 真重规划下游步骤 → 持久化
```

---

## 环境变量配置

在 `backend/.env` 中配置：

```bash
# ===== LLM（OpenAI 兼容接口）=====
LLM_PROVIDER=deepseek
LLM_API_KEY=sk-your-key-here
LLM_MODEL=deepseek-chat
LLM_BASE_URL=https://api.deepseek.com

# ===== MongoDB =====
MONGODB_URL=mongodb://localhost:27017
MONGODB_DB_NAME=a3_learning_agent

# ===== Embedding =====
EMBEDDING_PROVIDER=ollama
EMBEDDING_MODEL=bge-m3
EMBEDDING_ST_MODEL=BAAI/bge-small-zh-v1.5

# ===== Agent 调参 =====
RESOURCE_QUALITY_THRESHOLD=80
RESOURCE_MAX_REVISIONS=2
CRAG_RELEVANCE_THRESHOLD=0.5
CRAG_MIN_RELEVANT=1

# ===== 安全 =====
GUARDRAILS_ENABLED=true
```

---

## 开发说明

- ⚡ **全异步**：后端 async/await，三个 Agent 均为真实 LangGraph `StateGraph.ainvoke` 驱动
- 🔄 **真流式**：对话经 `chat_stream` 逐 token SSE 推送，前端逐字渲染
- 📊 **真进度**：资源生成各节点通过 progress 回调写真实步骤，前端进度条同步显示 `Supervisor → 检索 → 撰写 → 并行生成 → 评审 → 修订 → 聚合`
- 🔍 **真向量检索**：embedding 默认走本地 ollama（`bge-m3`），失败自动回退 sentence-transformers（离线可用）
- 🧩 **结构化输出**：JSON mode + Pydantic 校验 + 失败修复重试，跨 provider 健壮（不依赖 function-calling）
- 🛡️ **防幻觉**：CRAG 纠错式检索 + Self-Refine 评分驱动修订 + `knowledge_sufficient` 标志
- 🎨 **前端主题**：DeepSeek 蓝白风格（CSS 变量体系），ECharts 高级图表（雷达图 / 仪表盘 / 柱状图 / 饼图）

---

## 防幻觉机制（CRAG）

`services/rag.py:crag_retrieve` 实现纠错式检索：

**真实向量召回 → LLM 逐块相关性评分 → 过滤 → 不足则改写 query 重试 → 输出 `knowledge_sufficient` 标志**

当知识库缺乏强相关资料时，系统明确声明「资料不足、以教材为准」而非编造，前端展示防幻觉提示横幅。

---

## 使用的开源项目与前沿 AI 工具

| 项目 / 工具 | 用途 | 来源 | 协议 |
|---|---|---|---|
| LangGraph | 多智能体状态图编排 | github.com/langchain-ai/langgraph | MIT |
| FastAPI | 后端 Web 框架 | github.com/fastapi/fastapi | MIT |
| Vue 3 / Vite | 前端框架与构建 | github.com/vuejs | MIT |
| ECharts | 数据可视化 | github.com/apache/echarts | Apache-2.0 |
| Pinia | Vue 状态管理 | github.com/vuejs/pinia | MIT |
| MongoDB / Motor | 数据存储与异步驱动 | github.com/mongodb | Apache-2.0 |
| Sentence-Transformers | 本地文本向量化 | github.com/UKPLab/sentence-transformers | Apache-2.0 |
| BGE-M3 / bge-small-zh | Embedding 模型 | huggingface.co/BAAI | MIT |
| Ollama | 本地模型推理 | github.com/ollama/ollama | MIT |
| Markdown-it | Markdown 渲染 | github.com/markdown-it | MIT |

**架构思想借鉴**：CRAG / Self-RAG（纠错式检索防幻觉）、Self-Refine（评分驱动修订）、MetaGPT / ChatDev（角色化多智能体 SOP）、Stanford STORM / GPT-Researcher（多角色协作写作）、Letta / MemGPT（自编辑记忆）。

> AI Coding 工具说明：本项目在开发过程中使用 Claude Code 辅助编码。

---

## 许可证

MIT License © 2025 zgy0715
