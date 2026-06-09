<template>
  <div class="path-view">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="page-header-text">
        <h1 class="page-title">学习路径</h1>
        <p class="page-desc">根据您的画像和目标，AI 将为您规划个性化学习路径</p>
      </div>
      <div v-if="currentPath" class="header-actions">
        <button class="btn-ghost" @click="goBack">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><polyline points="15 18 9 12 15 6"/></svg>
          返回
        </button>
        <button class="btn-ghost" @click="showStats = !showStats">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M18 20V10M12 20V4M6 20v-6"/></svg>
          {{ showStats ? '隐藏统计' : '查看统计' }}
        </button>
      </div>
    </div>

    <!-- 状态 A：无路径 → 规划入口 -->
    <div v-if="!currentPath" class="plan-hero">
      <div class="plan-card">
        <div class="plan-icon">
          <div class="plan-icon-ring">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round">
              <polygon points="12 2 22 8.5 22 15.5 12 22 2 15.5 2 8.5"/>
              <line x1="12" y1="22" x2="12" y2="15.5"/>
              <polyline points="22 8.5 12 15.5 2 8.5"/>
              <circle cx="12" cy="12" r="3" fill="currentColor"/>
            </svg>
          </div>
        </div>
        <h2>开始规划你的学习路径</h2>
        <p>输入你想学习的方向，AI 将根据你的画像拆解为可执行的步骤</p>
        <div class="plan-input-group">
          <input
            v-model="topic"
            type="text"
            placeholder="例如：深度学习基础、数据结构与算法..."
            @keydown.enter="planPath"
          />
          <button @click="planPath" :disabled="!topic.trim() || planning" class="btn-primary">
            <template v-if="planning">
              <span class="spinner"></span>
              规划中...
            </template>
            <template v-else>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg>
              生成路径
            </template>
          </button>
        </div>
      </div>

      <!-- 历史路径 -->
      <div v-if="pathHistory.length > 0" class="history-section">
        <h3 class="section-title">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
          历史路径
        </h3>
        <div class="history-list">
          <div
            v-for="item in pathHistory"
            :key="item.path_id"
            class="history-item"
            @click="selectHistory(item)"
          >
            <div class="history-icon">🗺️</div>
            <div class="history-info">
              <span class="history-topic">{{ item.topic }}</span>
              <span class="history-meta">版本 {{ item.version }} · {{ item.steps?.length || 0 }} 步</span>
            </div>
            <div class="history-arrow">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="9 18 15 12 9 6"/></svg>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 状态 B：有路径 → 路径详情 -->
    <div v-else class="path-detail">
      <!-- 路径头部与进度 -->
      <div class="detail-header">
        <div class="detail-title-row">
          <div class="detail-icon">🗺️</div>
          <div>
            <h2>{{ currentPath.topic }}</h2>
            <div class="path-meta-group">
              <span class="path-meta-item">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 20h9M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"/></svg>
                版本 {{ currentPath.version || 1 }}
              </span>
              <span class="path-meta-item">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>
                {{ currentPath.steps?.length || 0 }} 个步骤
              </span>
              <span class="path-meta-item">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
                {{ progressPercent }}% 完成
              </span>
            </div>
          </div>
        </div>
        <div class="path-progress-ring">
          <svg width="60" height="60" viewBox="0 0 36 36">
            <path d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
              fill="none" stroke="var(--border)" stroke-width="3" />
            <path d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
              fill="none" stroke="url(#progressGrad)" stroke-width="3"
              :stroke-dasharray="`${progressPercent}, 100`" stroke-linecap="round" />
            <text x="18" y="20.5" text-anchor="middle" font-size="7" font-weight="800" fill="var(--text-primary)">{{ progressPercent }}%</text>
            <defs>
              <linearGradient id="progressGrad" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stop-color="#2563eb" />
                <stop offset="100%" stop-color="#60a5fa" />
              </linearGradient>
            </defs>
          </svg>
        </div>
      </div>

      <!-- ECharts 统计面板 -->
      <div v-if="showStats" class="stats-panel">
        <div class="stats-chart-wrapper">
          <div class="stats-chart-title">进度概览</div>
          <div ref="progressChartRef" class="stats-chart"></div>
        </div>
        <div class="stats-chart-wrapper">
          <div class="stats-chart-title">难度分布</div>
          <div ref="difficultyChartRef" class="stats-chart"></div>
        </div>
      </div>

      <!-- 步骤时间线 -->
      <div class="timeline">
        <div
          v-for="(step, index) in currentPath.steps"
          :key="step.step_id"
          class="timeline-item"
          :class="{
            'is-current': step.status === 'current',
            'is-completed': step.status === 'completed',
            'is-pending': step.status === 'pending'
          }"
          @click="step.status === 'current' && scrollToDetail(step)"
        >
          <div class="timeline-marker">
            <div class="marker-dot">
              <span v-if="step.status === 'completed'">✓</span>
              <span v-else-if="step.status === 'current'">●</span>
              <span v-else>{{ index + 1 }}</span>
            </div>
            <div v-if="index < currentPath.steps.length - 1" class="marker-line"></div>
          </div>
          <div class="timeline-content" :class="{ clickable: step.status === 'current' }">
            <div class="timeline-header">
              <span class="timeline-name">{{ step.name }}</span>
              <div class="timeline-tags">
                <span class="timeline-difficulty" :class="step.difficulty">
                  {{ step.difficulty }}
                </span>
                <span v-if="step.status === 'completed'" class="timeline-status completed-badge">已完成</span>
                <span v-else-if="step.status === 'current'" class="timeline-status current-badge">进行中</span>
              </div>
            </div>
            <div class="timeline-objective">{{ step.objective }}</div>
            <div class="timeline-meta" v-if="step.duration_minutes">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
              约 {{ step.duration_minutes }} 分钟
            </div>
          </div>
        </div>
      </div>

      <!-- 当前步骤详情与操作 -->
      <div v-if="currentStep" ref="detailRef" class="step-action-panel">
        <div class="panel-header">
          <div class="panel-header-left">
            <h3>当前步骤</h3>
            <span class="step-badge" :class="currentStep.difficulty">{{ currentStep.difficulty }}</span>
          </div>
        </div>
        <h4 class="panel-step-name">{{ currentStep.name }}</h4>
        <p class="panel-objective">{{ currentStep.objective }}</p>

        <!-- 推荐资源 -->
        <div class="panel-section">
          <div class="section-label">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/></svg>
            推荐资源
          </div>
          <div class="resource-chips">
            <button
              v-for="resType in currentStep.resource_types"
              :key="resType"
              class="resource-chip"
              @click="generateResource(resType)"
              :disabled="generatingRes"
            >
              <span>{{ getResourceIcon(resType) }}</span>
              {{ getResourceTypeName(resType) }}
            </button>
          </div>
          <div v-if="generatingRes" class="res-generating">
            <span class="spinner-sm"></span>
            正在生成资源...
          </div>
        </div>

        <!-- 操作按钮 -->
        <div class="panel-actions">
          <button class="action-btn primary" @click="completeStep">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><polyline points="20 6 9 17 4 12"/></svg>
            标记完成
          </button>
          <button class="action-btn ghost" @click="submitFeedback('need_help')">
            🤔 需要帮助
          </button>
          <button class="action-btn ghost" @click="submitFeedback('too_hard')">
            😰 太难
          </button>
          <button class="action-btn ghost" @click="submitFeedback('too_easy')">
            😊 太简单
          </button>
        </div>

        <!-- 反馈提示 -->
        <Transition name="fade">
          <div v-if="feedbackMsg" class="feedback-toast" :class="feedbackType">
            {{ feedbackMsg }}
          </div>
        </Transition>
      </div>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="loading-overlay">
      <div class="loading-spinner">
        <span class="spinner-lg"></span>
      </div>
      <p>加载中...</p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick, watch, onBeforeUnmount } from 'vue'
import { usePathStore } from '../stores/path'
import { useResourceStore } from '../stores/resource'
import { useRouter } from 'vue-router'
import * as echarts from 'echarts'

const pathStore = usePathStore()
const resourceStore = useResourceStore()
const router = useRouter()

const topic = ref('')
const planning = ref(false)
const loading = ref(false)
const currentPath = ref(null)
const pathHistory = ref([])
const generatingRes = ref(false)
const feedbackMsg = ref('')
const feedbackType = ref('')
const detailRef = ref(null)
const showStats = ref(false)

// ECharts refs
const progressChartRef = ref(null)
const difficultyChartRef = ref(null)
let progressChart = null
let difficultyChart = null

const currentStep = computed(() => {
  if (!currentPath.value?.steps) return null
  return currentPath.value.steps.find(s => s.status === 'current')
})

const progressPercent = computed(() => {
  if (!currentPath.value?.steps?.length) return 0
  const completed = currentPath.value.steps.filter(s => s.status === 'completed').length
  return Math.round((completed / currentPath.value.steps.length) * 100)
})

const getResourceIcon = (type) => {
  const icons = { document: '📄', mindmap: '🧠', exercise: '📝', code: '💻', video: '🎬', audio: '🎵', ppt: '📊' }
  return icons[type] || '📁'
}

const getResourceTypeName = (type) => {
  const names = { document: '文档', mindmap: '思维导图', exercise: '习题', code: '代码示例', video: '视频', audio: '音频', ppt: 'PPT' }
  return names[type] || type
}

const showFeedback = (msg, type = 'success') => {
  feedbackMsg.value = msg
  feedbackType.value = type
  setTimeout(() => { feedbackMsg.value = '' }, 3000)
}

const planPath = async () => {
  if (!topic.value.trim() || planning.value) return
  planning.value = true
  try {
    const result = await pathStore.planPath(topic.value)
    currentPath.value = result
    showFeedback('🎉 学习路径已生成！')
  } catch (error) {
    showFeedback('规划失败：' + (error.message || '未知错误'), 'error')
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
    await loadCurrentPath()
    const msgs = { too_hard: '已补充前置知识，降低难度', too_easy: '已加快进度，提升难度', need_help: '已增加示例和练习' }
    showFeedback('✅ ' + (msgs[type] || '已重新规划'))
  } catch (error) {
    showFeedback('提交失败：' + (error.message || '未知错误'), 'error')
  }
}

const completeStep = async () => {
  if (!currentStep.value) return
  try {
    await pathStore.completeStep(currentPath.value.path_id, currentStep.value.step_id)
    await loadCurrentPath()
    showFeedback('✅ 步骤已完成，继续前进！')
    await nextTick()
    updateAllCharts()
    if (!currentStep.value) {
      showFeedback('🎉 恭喜！你已完成所有步骤！', 'success')
    }
  } catch (error) {
    showFeedback('提交失败：' + (error.message || '未知错误'), 'error')
  }
}

const generateResource = async (type) => {
  generatingRes.value = true
  try {
    const taskId = await resourceStore.startGeneration(currentPath.value.topic, [type])
    router.push({ path: '/resource', query: { taskId } })
  } catch (error) {
    showFeedback('资源生成失败', 'error')
    generatingRes.value = false
  }
}

const goBack = () => {
  currentPath.value = null
  loadHistory()
}

const selectHistory = async (item) => {
  loading.value = true
  try {
    const fullPath = await pathStore.getCurrentPath(item.topic)
    if (fullPath && fullPath.path_id) {
      currentPath.value = fullPath
    } else {
      currentPath.value = item
    }
  } catch (error) {
    currentPath.value = item
  } finally {
    loading.value = false
  }
}

const loadCurrentPath = async () => {
  try {
    const path = await pathStore.getCurrentPath()
    if (path && path.path_id) {
      currentPath.value = path
    }
  } catch (error) {
    console.error('Failed to load path:', error)
  }
}

const loadHistory = async () => {
  try {
    const history = await pathStore.getHistory()
    pathHistory.value = history || []
  } catch (error) {
    console.error('Failed to load history:', error)
  }
}

const scrollToDetail = () => {
  if (detailRef.value) {
    detailRef.value.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }
}

// ===== ECharts 图表 =====
const initCharts = () => {
  initProgressChart()
  initDifficultyChart()
}

const initProgressChart = () => {
  if (!progressChartRef.value) return
  progressChart = echarts.init(progressChartRef.value)
  updateProgressChart()
}

const initDifficultyChart = () => {
  if (!difficultyChartRef.value) return
  difficultyChart = echarts.init(difficultyChartRef.value)
  updateDifficultyChart()
}

const updateAllCharts = () => {
  updateProgressChart()
  updateDifficultyChart()
}

const updateProgressChart = () => {
  if (!progressChart || !currentPath.value?.steps) return

  const steps = currentPath.value.steps
  const completed = steps.filter(s => s.status === 'completed').length
  const current = steps.filter(s => s.status === 'current').length
  const pending = steps.filter(s => s.status === 'pending').length

  const option = {
    tooltip: {
      trigger: 'item',
      backgroundColor: 'var(--bg-card)',
      borderColor: 'var(--border)',
      borderWidth: 1,
      textStyle: { color: 'var(--text-primary)', fontSize: 12 },
      formatter: (params) => `<strong>${params.name}</strong><br/>${params.value} 步 (${params.percent}%)`
    },
    series: [{
      type: 'pie',
      radius: ['55%', '75%'],
      avoidLabelOverlap: false,
      label: {
        show: true,
        position: 'outside',
        formatter: '{name|{b}}\n{d|{d}%}',
        rich: {
          name: { fontSize: 12, color: 'var(--text-secondary)', lineHeight: 18 },
          d: { fontSize: 14, fontWeight: 700, color: 'var(--text-primary)', lineHeight: 20 }
        }
      },
      emphasis: {
        label: { show: true, fontSize: 14, fontWeight: 'bold' },
        itemStyle: { shadowBlur: 10, shadowOffsetX: 0, shadowColor: 'rgba(0, 0, 0, 0.2)' }
      },
      data: [
        { value: completed, name: '已完成', itemStyle: { color: '#10b981' } },
        { value: current, name: '进行中', itemStyle: { color: '#2563eb' } },
        { value: pending, name: '待开始', itemStyle: { color: '#94a3b8' } }
      ].filter(d => d.value > 0)
    }]
  }

  progressChart.setOption(option)
}

const updateDifficultyChart = () => {
  if (!difficultyChart || !currentPath.value?.steps) return

  const steps = currentPath.value.steps
  const diffMap = {}

  steps.forEach(step => {
    const d = step.difficulty || '其他'
    diffMap[d] = (diffMap[d] || 0) + 1
  })

  const diffColors = {
    '基础': '#10b981',
    '核心': '#3b82f6',
    '进阶': '#f59e0b',
    '高级': '#ef4444',
    '挑战': '#ec4899'
  }

  const option = {
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'var(--bg-card)',
      borderColor: 'var(--border)',
      borderWidth: 1,
      textStyle: { color: 'var(--text-primary)', fontSize: 12 },
      axisPointer: { type: 'shadow' }
    },
    grid: {
      left: 10,
      right: 20,
      top: 10,
      bottom: 20,
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: Object.keys(diffMap),
      axisLabel: {
        color: 'var(--text-secondary)',
        fontSize: 11,
        fontWeight: 500
      },
      axisLine: { show: false },
      axisTick: { show: false }
    },
    yAxis: {
      type: 'value',
      min: 0,
      splitLine: {
        lineStyle: { color: 'var(--border-light)', type: 'dashed' }
      },
      axisLabel: { color: 'var(--text-tertiary)', fontSize: 11 },
      axisLine: { show: false },
      axisTick: { show: false }
    },
    series: [{
      type: 'bar',
      data: Object.keys(diffMap).map(d => ({
        value: diffMap[d],
        itemStyle: {
          color: diffColors[d] || '#94a3b8',
          borderRadius: [4, 4, 0, 0]
        }
      })),
      barWidth: '50%',
      animationDuration: 600,
      animationEasing: 'cubicOut'
    }]
  }

  difficultyChart.setOption(option)
}

const handleResize = () => {
  progressChart && progressChart.resize()
  difficultyChart && difficultyChart.resize()
}

watch(showStats, (val) => {
  if (val) {
    nextTick(() => {
      initCharts()
    })
  }
})

watch(currentPath, () => {
  if (showStats.value) {
    nextTick(() => updateAllCharts())
  }
}, { deep: true })

onMounted(async () => {
  loading.value = true
  await loadCurrentPath()
  await loadHistory()
  loading.value = false
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  progressChart && progressChart.dispose()
  difficultyChart && difficultyChart.dispose()
})
</script>

<style scoped>
.path-view {
  height: 100%;
  overflow-y: auto;
  padding: 32px 40px;
  max-width: 960px;
  margin: 0 auto;
  animation: fadeIn 0.3s var(--ease-out);
}

/* 页面头部 */
.page-header {
  margin-bottom: 28px;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.page-title {
  font-size: 24px;
  font-weight: 800;
  color: var(--text-primary);
  margin-bottom: 4px;
  letter-spacing: -0.02em;
}

.page-desc {
  color: var(--text-secondary);
  font-size: 14px;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.btn-ghost {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--bg-card);
  color: var(--text-secondary);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s;
}

.btn-ghost:hover {
  background: var(--primary-bg);
  border-color: var(--primary);
  color: var(--primary);
}

/* ===== 规划入口 ===== */
.plan-hero {
  display: flex;
  flex-direction: column;
  gap: 28px;
}

.plan-card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius-xl);
  padding: 48px 40px;
  text-align: center;
  box-shadow: var(--shadow-md);
  position: relative;
  overflow: hidden;
}

.plan-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, var(--primary), var(--primary-lighter), #60a5fa);
}

.plan-icon {
  margin-bottom: 20px;
  display: inline-flex;
}

.plan-icon-ring {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  background: var(--primary-bg);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--primary);
  position: relative;
}

.plan-icon-ring::before {
  content: '';
  position: absolute;
  inset: -2px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--primary), var(--primary-lighter));
  opacity: 0.15;
}

.plan-card h2 {
  font-size: 22px;
  font-weight: 800;
  margin-bottom: 8px;
  color: var(--text-primary);
}

.plan-card > p {
  color: var(--text-secondary);
  margin-bottom: 28px;
  max-width: 420px;
  margin-left: auto;
  margin-right: auto;
}

.plan-input-group {
  display: flex;
  gap: 10px;
  max-width: 540px;
  margin: 0 auto;
}

.plan-input-group input {
  flex: 1;
  padding: 14px 20px;
  border: 2px solid var(--border);
  border-radius: var(--radius-md);
  font-size: 14px;
  background: var(--bg);
  color: var(--text-primary);
  outline: none;
  transition: border-color 0.2s, box-shadow 0.2s;
}

.plan-input-group input:focus {
  border-color: var(--primary);
  box-shadow: 0 0 0 4px var(--primary-bg), var(--shadow-sm);
}

.plan-input-group button {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 14px 28px;
  background: linear-gradient(135deg, var(--primary), var(--primary-dark));
  color: white;
  border: none;
  border-radius: var(--radius-md);
  font-size: 14px;
  font-weight: 600;
  transition: all 0.2s var(--ease-out);
  white-space: nowrap;
  box-shadow: 0 4px 12px var(--primary-glow);
}

.plan-input-group button:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 6px 20px var(--primary-glow);
}

.plan-input-group button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  box-shadow: none;
}

/* 历史路径 */
.history-section {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 20px 24px;
  box-shadow: var(--shadow-sm);
}

.section-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-tertiary);
  margin-bottom: 12px;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  display: flex;
  align-items: center;
  gap: 6px;
}

.section-title svg {
  color: var(--primary);
}

.history-list {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.history-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 14px;
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: all 0.15s;
}

.history-item:hover {
  background: var(--primary-bg);
  transform: translateX(2px);
}

.history-icon {
  font-size: 22px;
}

.history-info {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.history-topic {
  font-weight: 600;
  color: var(--text-primary);
  font-size: 14px;
}

.history-meta {
  font-size: 12px;
  color: var(--text-tertiary);
}

.history-arrow {
  color: var(--text-tertiary);
  flex-shrink: 0;
  opacity: 0;
  transition: opacity 0.15s;
}

.history-item:hover .history-arrow {
  opacity: 1;
}

/* ===== 路径详情 ===== */
.path-detail {
  animation: slideUp 0.35s var(--ease-out);
}

@keyframes slideUp {
  from { opacity: 0; transform: translateY(16px); }
  to { opacity: 1; transform: translateY(0); }
}

.detail-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 20px 24px;
  box-shadow: var(--shadow-sm);
}

.detail-title-row {
  display: flex;
  align-items: center;
  gap: 14px;
}

.detail-icon {
  font-size: 32px;
}

.detail-title-row h2 {
  font-size: 20px;
  font-weight: 700;
  margin-bottom: 4px;
}

.path-meta-group {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
}

.path-meta-item {
  font-size: 13px;
  color: var(--text-tertiary);
  display: flex;
  align-items: center;
  gap: 4px;
}

.path-meta-item svg {
  color: var(--text-tertiary);
}

/* 进度环 */
.path-progress-ring {
  flex-shrink: 0;
  filter: drop-shadow(0 0 8px var(--primary-glow));
}

/* ===== 统计面板 ===== */
.stats-panel {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-bottom: 24px;
}

.stats-chart-wrapper {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 16px;
  box-shadow: var(--shadow-sm);
}

.stats-chart-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-secondary);
  margin-bottom: 8px;
}

.stats-chart {
  width: 100%;
  height: 180px;
}

/* ===== 时间线 ===== */
.timeline {
  margin-bottom: 24px;
}

.timeline-item {
  display: flex;
  gap: 16px;
  cursor: default;
}

.timeline-marker {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 36px;
  flex-shrink: 0;
}

.marker-dot {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  font-weight: 700;
  flex-shrink: 0;
  transition: all 0.3s var(--ease-spring);
}

.timeline-item.is-pending .marker-dot {
  background: var(--bg);
  color: var(--text-tertiary);
  border: 2px solid var(--border);
}

.timeline-item.is-current .marker-dot {
  background: linear-gradient(135deg, var(--primary), var(--primary-dark));
  color: white;
  box-shadow: 0 0 0 4px var(--primary-bg), 0 0 20px var(--primary-glow);
}

.timeline-item.is-completed .marker-dot {
  background: linear-gradient(135deg, var(--success), #059669);
  color: white;
  box-shadow: 0 0 0 4px var(--success-bg);
}

.marker-line {
  width: 2px;
  flex: 1;
  min-height: 24px;
  margin: 4px 0;
  background: var(--border);
}

.timeline-item.is-completed .marker-line {
  background: linear-gradient(to bottom, var(--success), var(--border));
}

.timeline-item.is-current .marker-line {
  background: linear-gradient(to bottom, var(--primary), var(--border));
}

.timeline-content {
  flex: 1;
  padding-bottom: 24px;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  padding: 16px 20px;
  transition: all 0.2s var(--ease-out);
  margin-bottom: 4px;
}

.timeline-content.clickable {
  cursor: pointer;
}

.timeline-content.clickable:hover {
  border-color: var(--primary);
  box-shadow: 0 0 0 2px var(--primary-bg), var(--shadow-md);
  transform: translateX(4px);
}

.timeline-item.is-completed .timeline-content {
  opacity: 0.75;
}

.timeline-item.is-completed .timeline-content:hover {
  opacity: 1;
}

.timeline-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 6px;
}

.timeline-name {
  font-weight: 600;
  font-size: 15px;
  color: var(--text-primary);
}

.timeline-tags {
  display: flex;
  gap: 6px;
  align-items: center;
  margin-left: auto;
}

.timeline-difficulty {
  font-size: 11px;
  padding: 2px 10px;
  border-radius: var(--radius-full);
  font-weight: 600;
}

.timeline-difficulty.基础 {
  background: var(--success-bg);
  color: var(--success);
}

.timeline-difficulty.核心,
.timeline-difficulty.进阶 {
  background: var(--warning-bg);
  color: var(--warning);
}

.timeline-difficulty.高级,
.timeline-difficulty.挑战 {
  background: var(--danger-bg);
  color: var(--danger);
}

.timeline-status {
  font-size: 11px;
  padding: 2px 10px;
  border-radius: var(--radius-full);
  font-weight: 600;
}

.completed-badge {
  background: var(--success-bg);
  color: var(--success);
}

.current-badge {
  background: var(--primary-bg);
  color: var(--primary);
}

.timeline-objective {
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.5;
  margin-bottom: 8px;
}

.timeline-meta {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: var(--text-tertiary);
}

.timeline-meta svg {
  flex-shrink: 0;
}

/* ===== 步骤操作面板 ===== */
.step-action-panel {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 24px 28px;
  box-shadow: var(--shadow-lg);
  position: relative;
  overflow: hidden;
  margin-bottom: 32px;
}

.step-action-panel::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 4px;
  height: 100%;
  background: linear-gradient(to bottom, var(--primary), var(--primary-light));
  border-radius: 0 2px 2px 0;
}

.panel-header {
  display: flex;
  align-items: center;
  margin-bottom: 12px;
}

.panel-header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.panel-header h3 {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-tertiary);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.step-badge {
  font-size: 11px;
  padding: 2px 10px;
  border-radius: var(--radius-full);
  font-weight: 600;
}

.step-badge.基础 { background: var(--success-bg); color: var(--success); }
.step-badge.核心,
.step-badge.进阶 { background: var(--warning-bg); color: var(--warning); }
.step-badge.高级,
.step-badge.挑战 { background: var(--danger-bg); color: var(--danger); }

.panel-step-name {
  font-size: 18px;
  font-weight: 700;
  margin-bottom: 8px;
}

.panel-objective {
  font-size: 14px;
  color: var(--text-secondary);
  line-height: 1.6;
  margin-bottom: 20px;
  padding-bottom: 20px;
  border-bottom: 1px solid var(--border-light);
}

.panel-section {
  margin-bottom: 20px;
}

.section-label {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-secondary);
  margin-bottom: 10px;
  display: flex;
  align-items: center;
  gap: 6px;
}

.section-label svg {
  color: var(--primary);
}

.resource-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.resource-chip {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border: 1.5px solid var(--border);
  border-radius: var(--radius-full);
  background: var(--bg);
  color: var(--text-secondary);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s var(--ease-out);
}

.resource-chip:hover:not(:disabled) {
  border-color: var(--primary);
  background: var(--primary-bg);
  color: var(--primary);
  transform: translateY(-1px);
}

.resource-chip:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.res-generating {
  margin-top: 8px;
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: var(--text-tertiary);
}

.panel-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.action-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 20px;
  border-radius: var(--radius-sm);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s var(--ease-out);
}

.action-btn.primary {
  background: linear-gradient(135deg, var(--primary), var(--primary-dark));
  color: white;
  border: none;
  box-shadow: 0 2px 8px var(--primary-glow);
}

.action-btn.primary:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 16px var(--primary-glow);
}

.action-btn.ghost {
  background: transparent;
  border: 1.5px solid var(--border);
  color: var(--text-secondary);
}

.action-btn.ghost:hover {
  border-color: var(--text-tertiary);
  background: var(--bg);
  color: var(--text-primary);
}

/* 反馈提示 */
.feedback-toast {
  margin-top: 16px;
  padding: 12px 18px;
  border-radius: var(--radius-sm);
  font-size: 13px;
  font-weight: 500;
  animation: slideUp 0.2s var(--ease-out);
}

.feedback-toast.success {
  background: var(--success-bg);
  color: var(--success);
  border: 1px solid var(--success);
}

.feedback-toast.error {
  background: var(--danger-bg);
  color: var(--danger);
  border: 1px solid var(--danger);
}

/* ===== 加载动画 ===== */
.loading-overlay {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 100px 0;
  gap: 16px;
  color: var(--text-tertiary);
}

.loading-spinner {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background: var(--bg-card);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: var(--shadow-md);
}

.spinner,
.spinner-lg,
.spinner-sm {
  display: inline-block;
  border: 2px solid var(--border);
  border-top-color: var(--primary);
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}

.spinner { width: 14px; height: 14px; }
.spinner-sm { width: 12px; height: 12px; }
.spinner-lg { width: 28px; height: 28px; border-width: 3px; }

@keyframes spin {
  to { transform: rotate(360deg); }
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes slideUp {
  from { opacity: 0; transform: translateY(12px); }
  to { opacity: 1; transform: translateY(0); }
}

/* Transition */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s, transform 0.2s;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
  transform: translateY(4px);
}
</style>
