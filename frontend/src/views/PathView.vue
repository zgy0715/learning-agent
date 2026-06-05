<template>
  <div class="path-view">
    <div class="header">
      <h2>学习路径</h2>
      <p>根据您的画像和目标，AI将为您规划个性化学习路径</p>
    </div>

    <div v-if="!currentPath" class="plan-section">
      <input
        v-model="topic"
        type="text"
        placeholder="请输入学习主题，例如：深度学习基础"
        @keydown.enter="planPath"
      />
      <button @click="planPath" :disabled="!topic.trim() || planning">
        {{ planning ? '规划中...' : '生成学习路径' }}
      </button>
    </div>

    <div v-else class="path-content">
      <div class="path-header">
        <h3>{{ currentPath.topic }}</h3>
        <span class="version">版本 {{ currentPath.version }}</span>
      </div>

      <!-- 步骤条 -->
      <div class="steps-bar">
        <div
          v-for="(step, index) in currentPath.steps"
          :key="step.step_id"
          class="step-item"
          :class="{
            completed: step.status === 'completed',
            current: step.status === 'current',
            pending: step.status === 'pending'
          }"
        >
          <div class="step-icon">
            <span v-if="step.status === 'completed'">✓</span>
            <span v-else-if="step.status === 'current'">{{ index + 1 }}</span>
            <span v-else>{{ index + 1 }}</span>
          </div>
          <div class="step-name">{{ step.name }}</div>
          <div v-if="index < currentPath.steps.length - 1" class="step-connector"></div>
        </div>
      </div>

      <!-- 当前步骤详情 -->
      <div v-if="currentStep" class="step-detail">
        <div class="detail-header">
          <h4>{{ currentStep.name }}</h4>
          <span class="difficulty" :class="currentStep.difficulty">
            {{ currentStep.difficulty }}
          </span>
          <span class="duration">约 {{ currentStep.duration_minutes }} 分钟</span>
        </div>
        <div class="detail-objective">
          <strong>学习目标：</strong>{{ currentStep.objective }}
        </div>

        <!-- 步骤资源 -->
        <div class="step-resources">
          <h5>推荐资源</h5>
          <div class="resource-list">
            <div
              v-for="resourceType in currentStep.resource_types"
              :key="resourceType"
              class="resource-tag"
              @click="generateResource(resourceType)"
            >
              {{ getResourceIcon(resourceType) }} {{ getResourceTypeName(resourceType) }}
            </div>
          </div>
        </div>

        <!-- 反馈按钮 -->
        <div class="feedback-buttons">
          <button class="feedback-btn hard" @click="submitFeedback('too_hard')">
            😰 太难了
          </button>
          <button class="feedback-btn easy" @click="submitFeedback('too_easy')">
            😊 太简单
          </button>
          <button class="feedback-btn help" @click="submitFeedback('need_help')">
            🤔 需要帮助
          </button>
          <button class="feedback-btn complete" @click="completeStep">
            ✓ 完成
          </button>
        </div>
      </div>

      <!-- 进度 -->
      <div class="progress-section">
        <div class="progress-bar">
          <div class="progress-fill" :style="{ width: progressPercent + '%' }"></div>
        </div>
        <div class="progress-text">完成进度: {{ progressPercent }}%</div>
      </div>
    </div>

    <div v-else class="empty-state">
      <div class="empty-icon">🗺️</div>
      <h3>暂无学习路径</h3>
      <p>输入学习主题，AI将为您规划个性化学习路径</p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { usePathStore } from '../stores/path'

const pathStore = usePathStore()

const topic = ref('')
const planning = ref(false)
const currentPath = ref(null)

const currentStep = computed(() => {
  if (!currentPath.value) return null
  return currentPath.value.steps.find(s => s.status === 'current')
})

const progressPercent = computed(() => {
  if (!currentPath.value) return 0
  const completed = currentPath.value.steps.filter(s => s.status === 'completed').length
  return Math.round((completed / currentPath.value.steps.length) * 100)
})

const getResourceIcon = (type) => {
  const icons = {
    document: '📄',
    mindmap: '🧠',
    exercise: '📝',
    code: '💻',
    video: '🎬',
    audio: '🎵',
    ppt: '📊'
  }
  return icons[type] || '📁'
}

const getResourceTypeName = (type) => {
  const names = {
    document: '文档',
    mindmap: '思维导图',
    exercise: '习题',
    code: '代码示例',
    video: '视频',
    audio: '音频',
    ppt: 'PPT'
  }
  return names[type] || type
}

const planPath = async () => {
  if (!topic.value.trim() || planning.value) return

  planning.value = true
  try {
    const result = await pathStore.planPath(topic.value)
    currentPath.value = result
  } catch (error) {
    console.error('Failed to plan path:', error)
    alert('规划失败：' + error.message)
  } finally {
    planning.value = false
  }
}

const submitFeedback = async (type) => {
  if (!currentStep.value) return

  try {
    await pathStore.submitFeedback(
      currentPath.value.path_id,
      currentStep.value.step_id,
      type
    )
    // 重新获取路径
    await loadCurrentPath()
  } catch (error) {
    console.error('Failed to submit feedback:', error)
  }
}

const completeStep = async () => {
  if (!currentStep.value) return

  try {
    await pathStore.completeStep(
      currentPath.value.path_id,
      currentStep.value.step_id
    )
    // 重新获取路径
    await loadCurrentPath()
  } catch (error) {
    console.error('Failed to complete step:', error)
  }
}

const generateResource = async (type) => {
  // TODO: 触发资源生成
  console.log('Generate resource:', type)
  alert('资源生成功能开发中...')
}

const loadCurrentPath = async () => {
  try {
    const path = await pathStore.getCurrentPath()
    currentPath.value = path
  } catch (error) {
    console.error('Failed to load path:', error)
  }
}

onMounted(() => {
  loadCurrentPath()
})
</script>

<style scoped>
.path-view {
  padding: 24px;
  max-width: 1000px;
  margin: 0 auto;
}

.header {
  margin-bottom: 24px;
}

.header h2 {
  margin-bottom: 8px;
  color: var(--text-color);
}

.header p {
  color: var(--text-color-secondary);
}

.plan-section {
  display: flex;
  gap: 12px;
  margin-bottom: 24px;
}

.plan-section input {
  flex: 1;
  padding: 12px 16px;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  font-size: 14px;
}

.plan-section input:focus {
  outline: none;
  border-color: var(--primary-color);
}

.plan-section button {
  padding: 12px 24px;
  background: var(--primary-color);
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  transition: background 0.3s;
}

.plan-section button:hover:not(:disabled) {
  background: #66b1ff;
}

.plan-section button:disabled {
  background: var(--bg-color-dark);
  cursor: not-allowed;
}

.path-content {
  background: white;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

.path-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.path-header h3 {
  color: var(--text-color);
}

.version {
  font-size: 12px;
  color: var(--text-color-secondary);
  background: var(--bg-color);
  padding: 4px 8px;
  border-radius: 4px;
}

.steps-bar {
  display: flex;
  justify-content: space-between;
  margin-bottom: 32px;
  position: relative;
}

.step-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  position: relative;
  flex: 1;
}

.step-icon {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: var(--bg-color-dark);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 500;
  margin-bottom: 8px;
  position: relative;
  z-index: 1;
}

.step-item.completed .step-icon {
  background: var(--success-color);
  color: white;
}

.step-item.current .step-icon {
  background: var(--primary-color);
  color: white;
}

.step-name {
  font-size: 12px;
  color: var(--text-color-secondary);
  text-align: center;
  max-width: 100px;
}

.step-connector {
  position: absolute;
  top: 18px;
  left: 50%;
  width: 100%;
  height: 2px;
  background: var(--bg-color-dark);
  z-index: 0;
}

.step-item.completed .step-connector {
  background: var(--success-color);
}

.step-detail {
  background: var(--bg-color);
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 24px;
}

.detail-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.detail-header h4 {
  margin: 0;
  color: var(--text-color);
}

.difficulty {
  font-size: 12px;
  padding: 4px 8px;
  border-radius: 4px;
  background: var(--bg-color-dark);
}

.difficulty.基础 {
  background: #e1f3d8;
  color: #67c23a;
}

.difficulty.核心 {
  background: #faecd8;
  color: #e6a23c;
}

.difficulty.进阶 {
  background: #fde2e2;
  color: #f56c6c;
}

.duration {
  font-size: 12px;
  color: var(--text-color-secondary);
}

.detail-objective {
  margin-bottom: 16px;
  line-height: 1.6;
}

.step-resources h5 {
  margin-bottom: 12px;
  color: var(--text-color);
}

.resource-list {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.resource-tag {
  padding: 8px 12px;
  background: white;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
  transition: all 0.3s;
}

.resource-tag:hover {
  border-color: var(--primary-color);
  color: var(--primary-color);
}

.feedback-buttons {
  display: flex;
  gap: 12px;
  margin-top: 20px;
}

.feedback-btn {
  flex: 1;
  padding: 10px 16px;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 13px;
  transition: all 0.3s;
}

.feedback-btn.hard {
  background: #fde2e2;
  color: #f56c6c;
}

.feedback-btn.easy {
  background: #e1f3d8;
  color: #67c23a;
}

.feedback-btn.help {
  background: #faecd8;
  color: #e6a23c;
}

.feedback-btn.complete {
  background: var(--primary-color);
  color: white;
}

.feedback-btn:hover {
  opacity: 0.9;
  transform: translateY(-1px);
}

.progress-section {
  margin-top: 24px;
}

.progress-bar {
  height: 8px;
  background: var(--bg-color-dark);
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 8px;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--primary-color), #67c23a);
  transition: width 0.3s;
}

.progress-text {
  font-size: 14px;
  color: var(--text-color-secondary);
  text-align: center;
}

.empty-state {
  text-align: center;
  padding: 60px 20px;
  color: var(--text-color-secondary);
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 16px;
}

.empty-state h3 {
  margin-bottom: 8px;
  color: var(--text-color);
}
</style>
