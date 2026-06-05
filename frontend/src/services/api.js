/**
 * API服务层
 * 封装Axios请求和SSE流式接收
 */
import axios from 'axios'

const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: BASE_URL,
  timeout: 60000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    // 可以在这里添加token
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  (response) => {
    return response.data
  },
  (error) => {
    console.error('API Error:', error)
    return Promise.reject(error)
  }
)

// ==================== 对话相关API ====================

/**
 * 发送消息（处理SSE流式响应）
 */
export const sendMessage = async (sessionId, message) => {
  const response = await fetch(`${BASE_URL}/api/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      session_id: sessionId,
      message
    })
  })

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let content = ''
  let profileUpdate = null

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    const chunk = decoder.decode(value)
    const lines = chunk.split('\n')

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        try {
          const data = JSON.parse(line.slice(6))
          if (data.content) {
            content += data.content
          }
          if (data.profile_update) {
            profileUpdate = data.profile_update
          }
        } catch (e) {
          // 忽略解析错误
        }
      }
    }
  }

  return { content, profile_update: profileUpdate }
}

/**
 * 获取画像
 */
export const getProfile = async (userId) => {
  const response = await api.get('/api/profile', {
    params: { user_id: userId }
  })
  return response
}

/**
 * 更新画像维度
 */
export const updateProfile = async (userId, dimension, value) => {
  const response = await api.put('/api/profile', null, {
    params: { user_id: userId, dimension, value }
  })
  return response
}

/**
 * 获取画像历史
 */
export const getProfileHistory = async (userId, limit = 10) => {
  const response = await api.get('/api/profile/history', {
    params: { user_id: userId, limit }
  })
  return response
}

/**
 * 创建会话
 */
export const createSession = async (userId, title = '新对话') => {
  const response = await api.post('/api/sessions', null, {
    params: { user_id: userId, title }
  })
  return response
}

/**
 * 获取会话列表
 */
export const getSessions = async (userId) => {
  const response = await api.get('/api/sessions', {
    params: { user_id: userId }
  })
  return response
}

// ==================== 资源相关API ====================

/**
 * 启动资源生成
 */
export const generateResources = async (userId, topic, resourceTypes) => {
  const response = await api.post('/api/generate', {
    user_id: userId,
    topic,
    resource_types: resourceTypes
  })
  return response
}

/**
 * 查询任务状态
 */
export const getTaskStatus = async (taskId) => {
  const response = await api.get(`/api/task/${taskId}`)
  return response
}

/**
 * 获取资源列表
 */
export const getResources = async (userId, resourceType, topic, limit = 20) => {
  const response = await api.get('/api/resources', {
    params: {
      user_id: userId,
      resource_type: resourceType,
      topic,
      limit
    }
  })
  return response
}

/**
 * 获取资源详情
 */
export const getResource = async (resourceId) => {
  const response = await api.get(`/api/resources/${resourceId}`)
  return response
}

// ==================== 路径相关API ====================

/**
 * 生成学习路径
 */
export const planLearningPath = async (userId, topic) => {
  const response = await api.post('/api/path/plan', {
    user_id: userId,
    topic
  })
  return response
}

/**
 * 获取当前路径
 */
export const getCurrentPath = async (userId, topic) => {
  const response = await api.get('/api/path', {
    params: { user_id: userId, topic }
  })
  return response
}

/**
 * 获取步骤资源
 */
export const getStepResources = async (stepId, pathId) => {
  const response = await api.get(`/api/path/step/${stepId}/resources`, {
    params: { path_id: pathId }
  })
  return response
}

/**
 * 完成步骤
 */
export const completeStep = async (stepId, pathId, score) => {
  const response = await api.post(`/api/path/step/${stepId}/complete`, null, {
    params: { path_id: pathId, score }
  })
  return response
}

/**
 * 提交反馈
 */
export const submitFeedback = async (pathId, stepId, feedbackType) => {
  const response = await api.post('/api/path/feedback', {
    path_id: pathId,
    step_id: stepId,
    feedback_type: feedbackType
  })
  return response
}

/**
 * 获取路径历史
 */
export const getPathHistory = async (userId, limit = 10) => {
  const response = await api.get('/api/path/history', {
    params: { user_id: userId, limit }
  })
  return response
}

export default api
