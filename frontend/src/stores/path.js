/**
 * 学习路径状态管理
 */
import { defineStore } from 'pinia'
import { ref } from 'vue'
import {
  planLearningPath as planLearningPathApi,
  getCurrentPath as getCurrentPathApi,
  submitFeedback as submitFeedbackApi,
  completeStep as completeStepApi,
  getPathHistory as getPathHistoryApi
} from '../services/api'

export const usePathStore = defineStore('path', () => {
  const currentPath = ref(null)
  const loading = ref(false)

  // 获取默认用户ID
  const getDefaultUserId = () => {
    return localStorage.getItem('userId') || 'default_user'
  }

  // 规划学习路径
  const planPath = async (topic) => {
    loading.value = true
    try {
      const userId = getDefaultUserId()
      const result = await planLearningPathApi(userId, topic)
      currentPath.value = {
        path_id: result.path_id,
        topic,
        version: 1,
        steps: result.steps
      }
      return currentPath.value
    } catch (error) {
      console.error('Failed to plan path:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  // 获取当前路径
  const getCurrentPath = async (topic = null) => {
    loading.value = true
    try {
      const userId = getDefaultUserId()
      const result = await getCurrentPathApi(userId, topic)
      if (result && result.path_id) {
        currentPath.value = result
      } else {
        currentPath.value = null
      }
      return currentPath.value
    } catch (error) {
      console.error('Failed to get current path:', error)
      currentPath.value = null
      return null
    } finally {
      loading.value = false
    }
  }

  // 获取路径历史
  const getHistory = async (limit = 10) => {
    try {
      const userId = getDefaultUserId()
      const result = await getPathHistoryApi(userId, limit)
      return result || []
    } catch (error) {
      console.error('Failed to get path history:', error)
      return []
    }
  }

  // 提交反馈
  const submitFeedback = async (pathId, stepId, feedbackType) => {
    try {
      const result = await submitFeedbackApi(pathId, stepId, feedbackType)
      // 重新获取路径
      await getCurrentPath()
      return result
    } catch (error) {
      console.error('Failed to submit feedback:', error)
      throw error
    }
  }

  // 完成步骤
  const completeStep = async (pathId, stepId, score = null) => {
    try {
      const result = await completeStepApi(stepId, pathId, score)
      // 重新获取路径
      await getCurrentPath()
      return result
    } catch (error) {
      console.error('Failed to complete step:', error)
      throw error
    }
  }

  return {
    currentPath,
    loading,
    planPath,
    getCurrentPath,
    getHistory,
    submitFeedback,
    completeStep
  }
})
