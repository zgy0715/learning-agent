/**
 * 用户画像状态管理
 */
import { defineStore } from 'pinia'
import { ref } from 'vue'
import {
  getProfile as getProfileApi,
  updateProfile as updateProfileApi
} from '../services/api'

export const useProfileStore = defineStore('profile', () => {
  const dimensions = ref({
    knowledge_base: { value: '初学', confidence: 0 },
    cognitive_style: { value: '视觉型', confidence: 0 },
    error_patterns: { value: '概念混淆', confidence: 0 },
    learning_preference: { value: '混合型', confidence: 0 },
    learning_pace: { value: '适中', confidence: 0 },
    goal_orientation: { value: '兴趣探索', confidence: 0 }
  })

  const version = ref(0)
  const updatedAt = ref(null)

  // 获取默认用户ID
  const getDefaultUserId = () => {
    return localStorage.getItem('userId') || 'default_user'
  }

  // 获取画像
  const fetchProfile = async () => {
    try {
      const userId = getDefaultUserId()
      const result = await getProfileApi(userId)
      if (result.dimensions && Object.keys(result.dimensions).length > 0) {
        dimensions.value = result.dimensions
        version.value = result.version
        updatedAt.value = result.updated_at
      }
    } catch (error) {
      console.error('Failed to fetch profile:', error)
    }
  }

  // 更新画像维度
  const updateDimension = async (dimension, value) => {
    try {
      const userId = getDefaultUserId()
      const result = await updateProfileApi(userId, dimension, value)
      if (result.success) {
        // 重新获取画像
        await fetchProfile()
      }
      return result
    } catch (error) {
      console.error('Failed to update dimension:', error)
      throw error
    }
  }

  // 更新画像（从对话分析结果更新）
  const updateFromAnalysis = (newDimensions) => {
    for (const [key, dim] of Object.entries(newDimensions)) {
      if (dimensions.value[key]) {
        // 如果新置信度更高，更新
        if (dim.confidence > dimensions.value[key].confidence) {
          dimensions.value[key] = dim
        }
      }
    }
  }

  return {
    dimensions,
    version,
    updatedAt,
    fetchProfile,
    updateDimension,
    updateFromAnalysis
  }
})
