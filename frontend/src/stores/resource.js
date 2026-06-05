/**
 * 资源状态管理
 */
import { defineStore } from 'pinia'
import { ref } from 'vue'
import {
  generateResources as generateResourcesApi,
  getTaskStatus as getTaskStatusApi,
  getResources as getResourcesApi
} from '../services/api'

export const useResourceStore = defineStore('resource', () => {
  const resources = ref([])
  const currentTask = ref(null)
  const loading = ref(false)

  // 获取默认用户ID
  const getDefaultUserId = () => {
    return localStorage.getItem('userId') || 'default_user'
  }

  // 启动资源生成
  const startGeneration = async (topic, resourceTypes = null) => {
    loading.value = true
    try {
      const userId = getDefaultUserId()
      const result = await generateResourcesApi(userId, topic, resourceTypes)
      currentTask.value = {
        task_id: result.task_id,
        status: 'pending',
        progress: 0
      }
      return result.task_id
    } catch (error) {
      console.error('Failed to start generation:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  // 获取任务状态
  const getTaskStatus = async (taskId) => {
    try {
      const result = await getTaskStatusApi(taskId)
      currentTask.value = result
      return result
    } catch (error) {
      console.error('Failed to get task status:', error)
      throw error
    }
  }

  // 获取资源列表
  const fetchResources = async (resourceType = null, topic = null) => {
    loading.value = true
    try {
      const userId = getDefaultUserId()
      const result = await getResourcesApi(userId, resourceType, topic)
      resources.value = result
      return result
    } catch (error) {
      console.error('Failed to fetch resources:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  return {
    resources,
    currentTask,
    loading,
    startGeneration,
    getTaskStatus,
    fetchResources
  }
})
