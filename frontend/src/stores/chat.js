/**
 * 对话状态管理
 */
import { defineStore } from 'pinia'
import { ref } from 'vue'
import {
  createSession as createSessionApi,
  getSessions as getSessionsApi,
  sendMessage as sendMessageApi
} from '../services/api'

export const useChatStore = defineStore('chat', () => {
  const sessions = ref([])
  const currentSession = ref(null)
  const messages = ref([])
  const loading = ref(false)

  // 获取默认用户ID（简化实现）
  const getDefaultUserId = () => {
    return localStorage.getItem('userId') || 'default_user'
  }

  // 创建会话
  const createSession = async (title = '新对话') => {
    try {
      const userId = getDefaultUserId()
      const result = await createSessionApi(userId, title)
      const newSession = {
        session_id: result.session_id,
        title,
        created_at: new Date().toISOString()
      }
      sessions.value.unshift(newSession)
      currentSession.value = newSession
      messages.value = []
      return newSession
    } catch (error) {
      console.error('Failed to create session:', error)
      throw error
    }
  }

  // 获取会话列表
  const fetchSessions = async () => {
    try {
      const userId = getDefaultUserId()
      const result = await getSessionsApi(userId)
      sessions.value = result
      if (result.length > 0 && !currentSession.value) {
        currentSession.value = result[0]
      }
    } catch (error) {
      console.error('Failed to fetch sessions:', error)
    }
  }

  // 发送消息（支持 onToken 逐字回调，实现真流式渲染）
  const sendMessage = async (content, onToken = null) => {
    if (!currentSession.value) {
      await createSession()
    }

    loading.value = true
    try {
      const sessionId = currentSession.value.session_id
      const response = await sendMessageApi(sessionId, content, onToken)
      return response
    } catch (error) {
      console.error('Failed to send message:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  // 选择会话
  const selectSession = (session) => {
    currentSession.value = session
    messages.value = []
  }

  return {
    sessions,
    currentSession,
    messages,
    loading,
    createSession,
    fetchSessions,
    sendMessage,
    selectSession
  }
})
