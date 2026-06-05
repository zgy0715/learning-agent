# A3 多智能体学习系统 API接口文档

## 基础信息

- **Base URL**: `http://localhost:8000`
- **API版本**: v1.0
- **认证方式**: 无需认证（开发阶段）

---

## 一、对话与画像 API

### 1.1 创建会话

**POST** `/api/sessions`

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| user_id | string | 是 | 用户ID（query参数） |
| title | string | 否 | 会话标题，默认"新对话" |

**响应示例**:
```json
{
  "session_id": "665f1a2b3c4d5e6f7a8b9c0d"
}
```

### 1.2 获取会话列表

**GET** `/api/sessions`

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| user_id | string | 是 | 用户ID（query参数） |

**响应示例**:
```json
[
  {
    "session_id": "665f1a2b3c4d5e6f7a8b9c0d",
    "title": "新对话",
    "created_at": "2024-01-01T00:00:00",
    "last_message": "你好"
  }
]
```

### 1.3 发送消息

**POST** `/api/chat`

**请求体**:
```json
{
  "session_id": "665f1a2b3c4d5e6f7a8b9c0d",
  "message": "我想学习计算机组成原理"
}
```

**响应**: SSE流式响应
```
data: {"content": "你好！"}

data: {"content": "很高兴"}

data: {"profile_update": {"knowledge_base": {"value": "初学", "confidence": 0.7}}}

data: {"message_id": "xxx", "tokens_used": 150}
```

### 1.4 获取画像

**GET** `/api/profile`

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| user_id | string | 是 | 用户ID（query参数） |

**响应示例**:
```json
{
  "user_id": "default_user",
  "version": 1,
  "dimensions": {
    "knowledge_base": {"value": "初学", "confidence": 0.7},
    "cognitive_style": {"value": "视觉型", "confidence": 0.5},
    "learning_preference": {"value": "练习为主", "confidence": 0.8},
    "goal_orientation": {"value": "应试取证", "confidence": 0.9}
  },
  "updated_at": "2024-01-01T00:00:00"
}
```

### 1.5 更新画像

**PUT** `/api/profile`

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| user_id | string | 是 | 用户ID（query参数） |
| dimension | string | 是 | 维度名称（query参数） |
| value | string | 是 | 维度值（query参数） |

**响应示例**:
```json
{
  "success": true,
  "new_version": 2
}
```

### 1.6 画像历史

**GET** `/api/profile/history`

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| user_id | string | 是 | 用户ID（query参数） |
| limit | int | 否 | 返回数量，默认10 |

---

## 二、资源生成 API

### 2.1 启动资源生成

**POST** `/api/generate`

**请求体**:
```json
{
  "user_id": "default_user",
  "topic": "神经网络反向传播",
  "resource_types": ["document", "mindmap", "exercise", "code"]
}
```

**响应示例**:
```json
{
  "task_id": "665f1a2b3c4d5e6f7a8b9c0d"
}
```

### 2.2 查询任务状态

**GET** `/api/task/{task_id}`

**响应示例**:
```json
{
  "task_id": "665f1a2b3c4d5e6f7a8b9c0d",
  "status": "running",
  "current_step": "资料生成智能体工作中",
  "progress": 0.6,
  "result": null,
  "error": null
}
```

**任务状态**:
- `pending` - 等待执行
- `running` - 执行中
- `completed` - 已完成
- `failed` - 失败

### 2.3 获取资源列表

**GET** `/api/resources`

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| user_id | string | 是 | 用户ID（query参数） |
| resource_type | string | 否 | 资源类型过滤 |
| topic | string | 否 | 主题过滤 |
| limit | int | 否 | 返回数量，默认20 |

### 2.4 获取资源详情

**GET** `/api/resources/{resource_id}`

---

## 三、学习路径 API

### 3.1 生成学习路径

**POST** `/api/path/plan`

**请求体**:
```json
{
  "user_id": "default_user",
  "topic": "计算机组成原理"
}
```

**响应示例**:
```json
{
  "path_id": "665f1a2b3c4d5e6f7a8b9c0d",
  "steps": [
    {
      "step_id": "step_1",
      "name": "计算机组成原理基础概念",
      "objective": "理解计算机系统的基本组成",
      "difficulty": "基础",
      "duration_minutes": 30,
      "resource_types": ["document", "mindmap"],
      "prerequisites": []
    }
  ],
  "message": "学习路径已生成"
}
```

### 3.2 获取当前路径

**GET** `/api/path`

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| user_id | string | 是 | 用户ID（query参数） |
| topic | string | 否 | 主题过滤 |

### 3.3 完成步骤

**POST** `/api/path/step/{step_id}/complete`

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| path_id | string | 是 | 学习路径ID（query参数） |
| score | float | 否 | 步骤得分（query参数） |

### 3.4 提交反馈

**POST** `/api/path/feedback`

**请求体**:
```json
{
  "path_id": "665f1a2b3c4d5e6f7a8b9c0d",
  "step_id": "step_1",
  "feedback_type": "too_hard"
}
```

**反馈类型**:
- `too_hard` - 太难
- `too_easy` - 太简单
- `need_help` - 需要帮助
- `completed` - 完成

### 3.5 路径历史

**GET** `/api/path/history`

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| user_id | string | 是 | 用户ID（query参数） |
| limit | int | 否 | 返回数量，默认10 |

---

## 四、资源类型说明

| 类型 | 说明 | 格式 |
|------|------|------|
| document | 学习文档 | Markdown |
| mindmap | 思维导图 | Markmap |
| exercise | 练习题 | JSON |
| code | 代码示例 | Python |
| video | 视频脚本 | 文本 |
| audio | 音频脚本 | 文本 |
| ppt | PPT大纲 | JSON |

---

## 五、错误码说明

| 状态码 | 说明 |
|--------|------|
| 200 | 成功 |
| 400 | 请求参数错误 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |

---

## 六、SSE事件格式

### 对话SSE事件
```
event: token
data: {"content": "回复内容"}

event: profile_update
data: {"profile_update": {"dimension": "value"}}

event: done
data: {"message_id": "xxx", "tokens_used": 100}
```

### 任务进度SSE事件
```
event: step
data: {"step": "rag_retrieving", "message": "正在检索知识库..."}

event: resource_ready
data: {"type": "document", "preview": "..."}

event: done
data: {"task_id": "xxx", "resources": [...]}
```
