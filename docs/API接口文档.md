# A3 多智能体学习系统 — API 接口文档

<p align="center">
  <img src="https://img.shields.io/badge/API-v2.0-blue?style=flat" alt="API Version">
  <img src="https://img.shields.io/badge/Status-Active-success?style=flat" alt="Status">
  <img src="https://img.shields.io/badge/Protocol-REST-ff6b6b?style=flat" alt="Protocol">
  <img src="https://img.shields.io/badge/Streaming-SSE-1DA1F2?style=flat" alt="SSE">
  <img src="https://img.shields.io/badge/Auth-None%20(Dev)-lightgrey?style=flat" alt="Auth">
</p>

## 基础信息

- **Base URL**: `http://localhost:8000`
- **API 版本**: v2.0（LangGraph 多智能体重构版）
- **认证方式**: 无需认证（开发阶段）

---

## 一、对话与画像 API

### 1.1 创建会话

**POST** `/api/sessions`

| 参数 | 类型 | 必填 | 说明 |
|:---|:---|:---|:---|
| user_id | string | 是 | 用户ID（query） |
| title | string | 否 | 会话标题，默认"新对话" |

**响应**:
```json
{ "session_id": "665f1a2b3c4d5e6f7a8b9c0d" }
```

### 1.2 获取会话列表

**GET** `/api/sessions`

| 参数 | 类型 | 必填 | 说明 |
|:---|:---|:---|:---|
| user_id | string | 是 | 用户ID（query） |

### 1.3 发送消息（SSE 真流式）

**POST** `/api/chat`

请求体:
```json
{
  "session_id": "665f1a2b3c4d5e6f7a8b9c0d",
  "message": "我是计算机专业大二学生，想学数据结构"
}
```

**SSE 事件流**（真实 token 级流式，10 字符切片的假流式已废弃）:

```
data: {"content": "你好"}
data: {"content": "！根据"}
data: {"content": "你的专业背景"}
...

data: {"profile_update": {
  "knowledge_base": {"value": "入门", "confidence": 0.75},
  "goal_orientation": {"value": "技能实践", "confidence": 0.70}
}}

data: {"message_id": "66a1b2c3...", "tokens_used": 0}
```

**事件类型**:
| 字段 | 说明 |
|:---|:---|
| `content` | LLM 实时生成的增量 token，前端逐字渲染 |
| `profile_update` | 画像有变更时推送完整 6 维画像，前端刷新雷达图 |
| `message_id` | 落库后的消息 ID（尾事件） |

**内部流程**（LangGraph 画像图驱动）:
```
意图识别 → LLM 结构化抽取 6 维画像（含证据）→ 置信度加权合并 → 决策（直接答/追问）
```

### 1.4 获取画像

**GET** `/api/profile`

| 参数 | 类型 | 必填 | 说明 |
|:---|:---|:---|:---|
| user_id | string | 是 | 用户ID（query） |

响应:
```json
{
  "user_id": "default_user",
  "version": 3,
  "dimensions": {
    "knowledge_base": {"value": "入门", "confidence": 0.75},
    "cognitive_style": {"value": "视觉型", "confidence": 0.60},
    "error_patterns": {"value": "概念混淆", "confidence": 0.55},
    "learning_preference": {"value": "练习为主", "confidence": 0.80},
    "learning_pace": {"value": "适中", "confidence": 0.65},
    "goal_orientation": {"value": "技能实践", "confidence": 0.70}
  },
  "updated_at": "2025-06-09T10:30:00"
}
```

画像按 version 递增持久化（修复了旧版画像写 `core_memory`、路由读 `profiles` 的数据断裂）。

### 1.5 手动修正画像

**PUT** `/api/profile`

| 参数 | 类型 | 必填 | 说明 |
|:---|:---|:---|:---|
| user_id | string | 是 | 用户ID（query） |
| dimension | string | 是 | 维度名（query） |
| value | string | 是 | 维度值（query） |

### 1.6 画像历史

**GET** `/api/profile/history`

| 参数 | 类型 | 必填 | 说明 |
|:---|:---|:---|:---|
| user_id | string | 是 | 用户ID（query） |
| limit | int | 否 | 返回数量，默认 10 |

---

## 二、资源生成 API

### 2.1 启动资源生成

**POST** `/api/generate`

请求体:
```json
{
  "user_id": "default_user",
  "topic": "神经网络反向传播",
  "resource_types": ["document", "mindmap", "exercise", "code", "video", "audio"]
}
```

**resource_types 可选值**（至少 5 种满足赛题要求）:

| 值 | 说明 | 生成智能体 | 格式 |
|:---|:---|:---|:---|
| `document` | 学习文档 | MaterialAgent（Supervisor 主文档） | Markdown |
| `mindmap` | 思维导图 | MindmapAgent | Markmap |
| `exercise` | 练习题 | ExerciseAgent | JSON |
| `code` | 代码实操示例 | CodeAgent | Markdown |
| `video` | 教学视频脚本 | VideoAgent | Markdown |
| `audio` | 音频讲解稿 | AudioAgent | Markdown |
| `ppt` | PPT 课件大纲 | PptAgent | JSON |

响应:
```json
{ "task_id": "665f1a2b3c4d5e6f7a8b9c0d" }
```

### 2.2 查询任务状态（真多步进度）

**GET** `/api/task/{task_id}`

响应:
```json
{
  "task_id": "665f1a2b3c4d5e6f7a8b9c0d",
  "status": "running",
  "current_step": "多个专业智能体：并行生成思维导图/习题/代码/PPT",
  "current_node": "workers",
  "progress": 0.58,
  "result": null,
  "error": null
}
```

**真实进度节点**（按执行顺序，取代旧版 pending→completed 的假跳转）:

| current_node | current_step 示例 | progress |
|:---|:---|:---|
| `supervisor` | 主管智能体：理解需求并拆解任务 | 0.08 |
| `retrieve` | 检索智能体：CRAG 纠错式检索取证 | 0.20 |
| `write_material` | 资料智能体：撰写核心讲解文档 | 0.38 |
| `workers` | 多个专业智能体：并行生成 | 0.58 |
| `critic` | 评审智能体：质量与防幻觉自检（第 N 轮） | 0.74 |
| `revise` | 修订智能体：按评审意见改进（第 N 轮） | 0.80 |
| `safety` | 安全智能体：内容安全过滤 | 0.90 |
| `aggregate` | 聚合结果 | 0.97 |

**任务状态**:
- `pending` — 等待执行
- `running` — 执行中
- `completed` — 已完成
- `failed` — 失败

**任务完成后的 result**:
```json
{
  "resource_ids": ["66a1b2...", "66a1b3..."],
  "resources": [
    {
      "type": "document",
      "content": "## 前置知识\n...",
      "format": "markdown",
      "quality_score": 87,
      "agent": "MaterialAgent"
    }
  ],
  "quality_report": {
    "score": 87,
    "grounded": true,
    "issues": [],
    "suggestions": ["建议增加更多实际应用案例"],
    "passed": true,
    "revisions": 1
  },
  "knowledge_sufficient": true
}
```

**防幻觉关键字段**:
- `quality_report.grounded` — 内容是否忠于参考资料（false 表示存在臆造）
- `quality_report.revisions` — Self-Refine 修订轮数（0=一次过，>0=触发修订循环）
- `knowledge_sufficient` — CRAG 判断知识库是否足以支撑（false 时前端展示防幻觉提示横幅）

### 2.3 SSE 任务进度流

**GET** `/api/task/{task_id}/stream`

与 2.2 相同字段，仅在状态变化时推送；完成后推送完整 `resources` 数组。

### 2.4 获取资源列表

**GET** `/api/resources`

| 参数 | 类型 | 必填 | 说明 |
|:---|:---|:---|:---|
| user_id | string | 是 | 用户ID（query） |
| resource_type | string | 否 | 类型过滤 |
| topic | string | 否 | 主题模糊匹配 |
| limit | int | 否 | 数量，默认 20 |

### 2.5 获取资源详情

**GET** `/api/resources/{resource_id}`

---

## 三、学习路径 API

### 3.1 生成学习路径

**POST** `/api/path/plan`

请求体:
```json
{
  "user_id": "default_user",
  "topic": "计算机组成原理"
}
```

响应:
```json
{
  "path_id": "665f1a2b3c4d5e6f7a8b9c0d",
  "steps": [
    {
      "step_id": "step_1",
      "name": "计算机组成原理基础概念",
      "objective": "了解计算机系统的五大部件及其功能",
      "difficulty": "基础",
      "duration_minutes": 30,
      "resource_types": ["document", "mindmap"],
      "prerequisites": [],
      "rag_query": "计算机组成原理 基础 概念",
      "status": "current"
    }
  ],
  "message": "学习路径已生成"
}
```

内部流程（LangGraph Plan-and-Execute 图）:
```
CRAG 了解知识结构 → LLM 按画像规划 5-8 步（难度/时长/资源类型个性化）→ 补全字段
```

### 3.2 获取当前路径

**GET** `/api/path`

| 参数 | 类型 | 必填 | 说明 |
|:---|:---|:---|:---|
| user_id | string | 是 | 用户ID（query） |
| topic | string | 否 | 主题过滤 |

### 3.3 获取步骤资源

**GET** `/api/path/step/{step_id}/resources`

| 参数 | 类型 | 必填 | 说明 |
|:---|:---|:---|:---|
| path_id | string | 是 | 学习路径ID（query） |

### 3.4 完成步骤

**POST** `/api/path/step/{step_id}/complete`

| 参数 | 类型 | 必填 | 说明 |
|:---|:---|:---|:---|
| path_id | string | 是 | 学习路径ID（query） |
| score | float | 否 | 步骤得分 0-100 |

### 3.5 提交反馈（真 LLM 重规划）

**POST** `/api/path/feedback`

请求体:
```json
{
  "path_id": "665f1a2b3c4d5e6f7a8b9c0d",
  "step_id": "step_2",
  "feedback_type": "too_hard"
}
```

**feedback_type 值**:

| 值 | 处理方式 |
|:---|:---|
| `too_hard` | LLM 重规划：补充前置知识、拆细难点 |
| `too_easy` | LLM 重规划：精简/跳过当前步，提升后续难度 |
| `need_help` | LLM 重规划：增加示例与练习巩固 |
| `completed` | 记录反馈（不触发重规划） |

**关键改进**: 反馈处理不再是机械的列表拼插，而是由 LangGraph Re-Planner 真正用 LLM 重规划下游步骤，结果写回 `learning_paths` 并重建 `learning_progress`。

### 3.6 路径历史

**GET** `/api/path/history`

| 参数 | 类型 | 必填 | 说明 |
|:---|:---|:---|:---|
| user_id | string | 是 | 用户ID（query） |
| limit | int | 否 | 数量，默认 10 |

---

## 四、系统配置

### 4.1 环境变量

```bash
# ===== LLM（OpenAI 兼容接口）=====
LLM_PROVIDER=deepseek
LLM_API_KEY=sk-your-key
LLM_MODEL=deepseek-chat
LLM_BASE_URL=https://api.deepseek.com

# ===== Embedding（真向量检索）=====
# provider: ollama | sentence_transformers | openai_compatible
EMBEDDING_PROVIDER=ollama
EMBEDDING_BASE_URL=http://localhost:11434/v1
EMBEDDING_API_KEY=ollama
EMBEDDING_MODEL=bge-m3
EMBEDDING_ST_MODEL=BAAI/bge-small-zh-v1.5   # sentence_transformers 回退

# ===== Agent 调参 =====
RESOURCE_QUALITY_THRESHOLD=80   # Critic 通过阈值
RESOURCE_MAX_REVISIONS=2        # Self-Refine 最大修订轮数
CRAG_RELEVANCE_THRESHOLD=0.5    # 单块相关性保留阈值
CRAG_MIN_RELEVANT=1             # 低于此数触发 query 改写

# ===== 安全 =====
GUARDRAILS_ENABLED=true
```

---

## 五、资源类型对照

| 类型 | 说明 | 格式 | 生成智能体 |
|:---|:---|:---|:---|
| document | 结构化学习文档 | Markdown（含引用标注） | MaterialAgent |
| mindmap | 思维导图 | Markmap | MindmapAgent |
| exercise | 练习题（选择/填空/简答） | JSON | ExerciseAgent |
| code | Python 代码示例 | Markdown（含注释/运行结果） | CodeAgent |
| video | 教学视频分镜脚本 | Markdown（时间戳+画面+旁白） | VideoAgent |
| audio | 音频讲解稿 | Markdown（口语化+停顿标记） | AudioAgent |
| ppt | 课件大纲 | JSON | PptAgent |

---

## 六、SSE 事件格式总览

### 对话流（`POST /api/chat`）
```
data: {"content": "<增量token>"}
data: {"profile_update": {<完整6维画像>}}
data: {"message_id": "<mongo-id>", "tokens_used": <int>}
```

### 任务进度流（`GET /api/task/{task_id}/stream`）
```
data: {"status": "running", "current_step": "<中文步骤>", "current_node": "<节点名>", "progress": <0~1>}
data: {"resources": [...]}       // 完成时
data: {"error": "<错误信息>"}    // 失败时
```

---

## 七、错误码

| 状态码 | 说明 |
|:---|:---|
| 200 | 成功 |
| 400 | 请求参数错误 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |

---

*文档版本：v2.0 — 基于 LangGraph 真多智能体重构（2025-06）*
