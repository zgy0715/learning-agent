<template>
  <div class="resource-view">
    <!-- 页面头部 -->
    <div class="page-header">
      <div>
        <h1 class="page-title">学习资源</h1>
        <p class="page-desc">输入学习主题，AI 将生成文档、思维导图、习题等多种资源</p>
      </div>
    </div>

    <!-- 输入区 -->
    <div class="search-section">
      <div class="search-box">
        <svg class="search-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
        <input
          v-model="topic"
          type="text"
          placeholder="输入学习主题，例如：神经网络反向传播算法"
          @keydown.enter="generateResources"
        />
        <button @click="generateResources" :disabled="!topic.trim() || generating" class="btn-primary">
          <template v-if="generating">
            <span class="spinner"></span>
            生成中...
          </template>
          <template v-else>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><polygon points="23 7 16 12 23 17 23 7"/><rect x="1" y="5" width="15" height="14" rx="2" ry="2"/></svg>
            生成资源
          </template>
        </button>
      </div>
    </div>

    <!-- 生成进度 -->
    <div v-if="generating" class="progress-panel">
      <div class="progress-header">
        <span class="progress-label">{{ currentStep }}</span>
        <span class="progress-pct">{{ Math.round(progress) }}%</span>
      </div>
      <div class="progress-track">
        <div class="progress-fill" :style="{ width: progress + '%' }"></div>
      </div>
      <div class="step-indicators">
        <div
          v-for="(node, i) in progressNodes"
          :key="node.key"
          class="step-dot"
          :class="{ active: node.active, done: node.done }"
        >
          <span>{{ node.done ? '✓' : node.active ? '●' : '' }}</span>
          <div class="step-dot-label">{{ node.label }}</div>
        </div>
      </div>
    </div>

    <!-- 防幻觉横幅 -->
    <div v-if="knowledgeSufficient === false && !generating" class="hallucination-warning">
      <div class="warning-icon">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
      </div>
      <div>
        <strong>防幻觉提示</strong>
        <p>知识库中缺乏与该主题强相关的资料，以下内容基于通用常识生成，请以教材为准。</p>
      </div>
    </div>

    <!-- 空状态 -->
    <div v-if="!generating && resources.length === 0" class="empty-state">
      <div class="empty-graphic">
        <svg width="80" height="80" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1" stroke-linecap="round">
          <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/>
          <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>
          <line x1="8" y1="7" x2="16" y2="7"/><line x1="8" y1="11" x2="14" y2="11"/>
        </svg>
      </div>
      <h3>暂无资源</h3>
      <p>输入学习主题，AI 将为您生成多种学习资源</p>
    </div>

    <!-- 资源选项卡 -->
    <div v-if="resources.length > 0 && !generating" class="resources-section">
      <div class="tabs-header">
        <button
          v-for="tab in resourceTabs"
          :key="tab.type"
          class="tab-btn"
          :class="{ active: activeTab === tab.type }"
          @click="activeTab = tab.type"
        >
          <span>{{ tab.icon }}</span>
          {{ tab.label }}
          <span v-if="tab.count" class="tab-count">{{ tab.count }}</span>
        </button>
      </div>

      <!-- ECharts 仪表盘 -->
      <div class="dashboard-grid">
        <div class="dashboard-card">
          <div class="dashboard-card-title">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>
            质量评分概览
          </div>
          <div class="quality-chart" ref="qualityChartRef"></div>
        </div>
        <div class="dashboard-card">
          <div class="dashboard-card-title">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M12 20h9M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"/></svg>
            资源类型分布
          </div>
          <div class="type-chart" ref="typeChartRef"></div>
        </div>
      </div>

      <!-- 当前 Tab 内容 -->
      <div v-for="res in filteredResources" :key="res.id" class="resource-card-wrapper">
        <div class="resource-card" :class="'type-' + res.resource_type">
          <div class="card-accent"></div>
          <div class="card-body">
            <div class="card-top">
              <div class="card-type-badge">
                <span>{{ getResourceIcon(res.resource_type) }}</span>
                {{ getResourceTypeName(res.resource_type) }}
              </div>
              <div class="card-quality" v-if="res.metadata?.quality_score">
                <div class="quality-ring">
                  <svg width="36" height="36" viewBox="0 0 36 36">
                    <path d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                      fill="none" stroke="var(--border)" stroke-width="3" />
                    <path d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                      fill="none" :stroke="qualityColor(res.metadata.quality_score)" stroke-width="3"
                      :stroke-dasharray="qualityScorePercent(res.metadata.quality_score) + ', 100'" stroke-linecap="round" />
                    <text x="18" y="20.5" text-anchor="middle" font-size="7" font-weight="800"
                      :fill="qualityColor(res.metadata.quality_score)">{{ res.metadata.quality_score }}</text>
                  </svg>
                </div>
              </div>
            </div>

            <div class="card-content" :class="{ collapsed: !expanded[res.id] }">
              <div v-if="res.resource_type === 'document'" class="content-render markdown" v-html="renderMarkdown(res.content)"></div>
              <div v-else class="content-render pre-wrap"><pre>{{ res.content }}</pre></div>
            </div>

            <button v-if="contentLength(res.content) > 500" class="expand-btn" @click="toggleExpand(res.id)">
              {{ expanded[res.id] ? '收起' : '展开全部' }}
              <svg :class="{ rotated: expanded[res.id] }" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 12 15 18 9"/></svg>
            </button>

            <div class="card-footer">
              <span class="footer-agent" v-if="res.agent">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg>
                {{ res.agent }}
              </span>
              <button class="copy-btn" @click="copyContent(res.content, res.resource_type)">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
                复制
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick, watch, onBeforeUnmount } from 'vue'
import { useResourceStore } from '../stores/resource'
import { useRoute } from 'vue-router'
import MarkdownIt from 'markdown-it'
import * as echarts from 'echarts'

const resourceStore = useResourceStore()
const route = useRoute()

const topic = ref('')
const generating = ref(false)
const progress = ref(0)
const currentStep = ref('')
const resources = ref([])
const knowledgeSufficient = ref(null)
const activeTab = ref('all')
const expanded = ref({})
const qualityChartRef = ref(null)
const typeChartRef = ref(null)
let qualityChart = null
let typeChart = null

const md = new MarkdownIt({ html: true })

const progressNodes = ref([
  { key: 'supervisor', label: '拆解', done: false, active: false },
  { key: 'retrieve', label: '检索', done: false, active: false },
  { key: 'write_material', label: '撰写', done: false, active: false },
  { key: 'workers', label: '并行', done: false, active: false },
  { key: 'critic', label: '评审', done: false, active: false },
  { key: 'aggregate', label: '完成', done: false, active: false }
])

const resourceTabs = computed(() => {
  const types = {}
  resources.value.forEach(r => {
    const t = r.resource_type || 'other'
    types[t] = (types[t] || 0) + 1
  })
  const tabs = [{ type: 'all', label: '全部', icon: '📋', count: resources.value.length }]
  const typeNames = { document: '📄 文档', mindmap: '🧠 思维导图', exercise: '📝 习题', code: '💻 代码', video: '🎬 视频', audio: '🎵 音频', ppt: '📊 PPT' }
  Object.entries(types).forEach(([type, count]) => {
    tabs.push({ type, label: (typeNames[type] || type), icon: '', count })
  })
  return tabs
})

const filteredResources = computed(() => {
  if (activeTab.value === 'all') return resources.value
  return resources.value.filter(r => r.resource_type === activeTab.value)
})

const getResourceIcon = (type) => {
  const icons = { document: '📄', mindmap: '🧠', exercise: '📝', code: '💻', video: '🎬', audio: '🎵', ppt: '📊' }
  return icons[type] || '📁'
}

const getResourceTypeName = (type) => {
  const names = { document: '文档', mindmap: '思维导图', exercise: '习题', code: '代码示例', video: '视频', audio: '音频', ppt: 'PPT' }
  return names[type] || type
}

const renderMarkdown = (text) => md.render(text || '')

const contentLength = (content) => (content || '').length

const toggleExpand = (id) => {
  expanded.value[id] = !expanded.value[id]
}

const qualityScorePercent = (score) => {
  return Math.round((score || 0) / 100 * 100)
}

const qualityColor = (score) => {
  if (score >= 85) return 'var(--success)'
  if (score >= 70) return 'var(--warning)'
  return 'var(--danger)'
}

const copyContent = async (content, type) => {
  try {
    await navigator.clipboard.writeText(content || '')
    alert('已复制到剪贴板')
  } catch (error) {
    console.error('Failed to copy:', error)
  }
}

// ===== ECharts 图表 =====
const initCharts = () => {
  initQualityChart()
  initTypeChart()
}

const initQualityChart = () => {
  if (!qualityChartRef.value) return
  qualityChart = echarts.init(qualityChartRef.value)
  updateQualityChart()
}

const initTypeChart = () => {
  if (!typeChartRef.value) return
  typeChart = echarts.init(typeChartRef.value)
  updateTypeChart()
}

const updateQualityChart = () => {
  if (!qualityChart || resources.value.length === 0) return

  const data = resources.value.map(r => ({
    name: getResourceTypeName(r.resource_type),
    value: r.metadata?.quality_score || 0,
    type: r.resource_type
  }))

  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      backgroundColor: 'var(--bg-card)',
      borderColor: 'var(--border)',
      borderWidth: 1,
      textStyle: { color: 'var(--text-primary)', fontSize: 12 },
      formatter: (params) => {
        const p = params[0]
        return `<strong>${p.name}</strong><br/>质量评分: <strong style="color:${qualityColor(p.value)}">${p.value}</strong>`
      }
    },
    grid: {
      left: 40, right: 10, top: 10, bottom: 25
    },
    xAxis: {
      type: 'category',
      data: data.map(d => d.name),
      axisLabel: { color: 'var(--text-tertiary)', fontSize: 11 },
      axisLine: { lineStyle: { color: 'var(--border)' } },
      axisTick: { show: false }
    },
    yAxis: {
      type: 'value',
      min: 0,
      max: 100,
      splitLine: { lineStyle: { color: 'var(--border-light)', type: 'dashed' } },
      axisLabel: { color: 'var(--text-tertiary)', fontSize: 11 },
      axisLine: { show: false }
    },
    series: [{
      type: 'bar',
      data: data.map(d => ({
        value: d.value,
        itemStyle: {
          color: {
            type: 'linear',
            x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [
              { offset: 0, color: qualityColor(d.value) },
              { offset: 1, color: qualityColor(d.value) + '80' }
            ]
          },
          borderRadius: [4, 4, 0, 0]
        }
      })),
      barWidth: '55%',
      animationDuration: 800,
      animationEasing: 'cubicOut',
      label: {
        show: true,
        position: 'top',
        formatter: (p) => p.value,
        fontSize: 11,
        fontWeight: 600,
        color: (p) => qualityColor(p.value)
      }
    }]
  }

  qualityChart.setOption(option)
}

const updateTypeChart = () => {
  if (!typeChart || resources.value.length === 0) return

  const typeMap = {}
  resources.value.forEach(r => {
    const t = r.resource_type || 'other'
    typeMap[t] = (typeMap[t] || 0) + 1
  })

  const colors = {
    document: '#2563eb', mindmap: '#10b981', exercise: '#f59e0b',
    code: '#3b82f6', video: '#ef4444', audio: '#8b5cf6', ppt: '#ec4899'
  }

  const option = {
    tooltip: {
      trigger: 'item',
      backgroundColor: 'var(--bg-card)',
      borderColor: 'var(--border)',
      borderWidth: 1,
      textStyle: { color: 'var(--text-primary)', fontSize: 12 },
      formatter: (params) => `<strong>${params.name}</strong><br/>${params.value} 个 (${params.percent}%)`
    },
    series: [{
      type: 'pie',
      radius: ['45%', '70%'],
      center: ['50%', '55%'],
      avoidLabelOverlap: false,
      label: {
        show: true,
        position: 'outside',
        formatter: '{b}',
        fontSize: 11,
        color: 'var(--text-secondary)'
      },
      emphasis: {
        label: { show: true, fontSize: 13, fontWeight: 'bold' },
        itemStyle: { shadowBlur: 10, shadowOffsetX: 0, shadowColor: 'rgba(0, 0, 0, 0.2)' }
      },
      data: Object.keys(typeMap).map(t => ({
        value: typeMap[t],
        name: getResourceTypeName(t),
        itemStyle: { color: colors[t] || '#94a3b8' }
      }))
    }]
  }

  typeChart.setOption(option)
}

const handleResize = () => {
  qualityChart && qualityChart.resize()
  typeChart && typeChart.resize()
}

const generateResources = async () => {
  if (!topic.value.trim() || generating.value) return

  generating.value = true
  progress.value = 0
  currentStep.value = '准备生成...'
  resources.value = []
  knowledgeSufficient.value = null
  progressNodes.value.forEach(n => { n.done = false; n.active = false })

  try {
    const taskId = await resourceStore.startGeneration(topic.value)

    const pollInterval = setInterval(async () => {
      const status = await resourceStore.getTaskStatus(taskId)
      progress.value = (status.progress || 0) * 100
      currentStep.value = status.current_step || ''

      const nodeOrder = ['supervisor', 'retrieve', 'write_material', 'workers', 'critic', 'revise', 'safety', 'aggregate']
      const currentNode = status.current_node
      progressNodes.value.forEach(n => {
        const idx = nodeOrder.indexOf(n.key)
        const curIdx = nodeOrder.indexOf(currentNode)
        n.done = idx < curIdx && curIdx > 0
        n.active = idx === curIdx
        if (currentNode === 'aggregate' || status.status === 'completed') {
          n.done = true
          n.active = false
        }
      })

      if (status.status === 'completed') {
        clearInterval(pollInterval)
        resources.value = status.result?.resources || []
        knowledgeSufficient.value = status.result?.knowledge_sufficient ?? null
        generating.value = false
        progressNodes.value.forEach(n => { n.done = true; n.active = false })
        await nextTick()
        initCharts()
      } else if (status.status === 'failed') {
        clearInterval(pollInterval)
        currentStep.value = '生成失败：' + (status.error || '未知错误')
        generating.value = false
      }
    }, 1200)
  } catch (error) {
    console.error('Failed to generate resources:', error)
    currentStep.value = '生成失败：' + error.message
    generating.value = false
  }
}

watch(resources, () => {
  nextTick(() => {
    updateQualityChart()
    updateTypeChart()
  })
}, { deep: true })

onMounted(() => {
  if (route.query.taskId) {
    // 可以自动拉取资源
  }
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  qualityChart && qualityChart.dispose()
  typeChart && typeChart.dispose()
})
</script>

<style scoped>
.resource-view {
  height: 100%;
  overflow-y: auto;
  padding: 32px 40px;
  max-width: 1100px;
  margin: 0 auto;
  animation: fadeIn 0.3s var(--ease-out);
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

/* 页面头部 */
.page-header {
  margin-bottom: 24px;
}
.page-title {
  font-size: 24px;
  font-weight: 800;
  margin-bottom: 4px;
  letter-spacing: -0.02em;
}
.page-desc {
  color: var(--text-secondary);
  font-size: 14px;
}

/* 搜索区 */
.search-section {
  margin-bottom: 24px;
}

.search-box {
  display: flex;
  align-items: center;
  gap: 10px;
  background: var(--bg-card);
  border: 2px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 6px 6px 6px 18px;
  transition: all 0.2s var(--ease-out);
  box-shadow: var(--shadow-sm);
}

.search-box:focus-within {
  border-color: var(--primary);
  box-shadow: 0 0 0 4px var(--primary-bg), var(--shadow-md);
}

.search-icon {
  color: var(--text-tertiary);
  flex-shrink: 0;
}

.search-box input {
  flex: 1;
  border: none;
  outline: none;
  font-size: 14px;
  background: transparent;
  color: var(--text-primary);
  padding: 8px 0;
}

.search-box input::placeholder {
  color: var(--text-placeholder);
}

.search-box button {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 24px;
  background: linear-gradient(135deg, var(--primary), var(--primary-dark));
  color: white;
  border: none;
  border-radius: var(--radius-sm);
  font-size: 14px;
  font-weight: 600;
  white-space: nowrap;
  transition: all 0.2s var(--ease-out);
  box-shadow: 0 2px 8px var(--primary-glow);
}

.search-box button:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 16px var(--primary-glow);
}

.search-box button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  box-shadow: none;
}

/* 进度面板 */
.progress-panel {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 24px 28px;
  margin-bottom: 20px;
  box-shadow: var(--shadow-md);
}

.progress-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 12px;
}

.progress-label {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}

.progress-pct {
  font-size: 14px;
  font-weight: 700;
  color: var(--primary);
}

.progress-track {
  height: 6px;
  background: var(--border-light);
  border-radius: 3px;
  overflow: hidden;
  margin-bottom: 16px;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--primary), var(--primary-light));
  border-radius: 3px;
  transition: width 0.5s var(--ease-out);
}

.step-indicators {
  display: flex;
  justify-content: space-between;
}

.step-dot {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  position: relative;
  flex: 1;
}

.step-dot span {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 700;
  background: var(--bg);
  color: var(--text-tertiary);
  border: 2px solid var(--border);
  transition: all 0.3s var(--ease-spring);
}

.step-dot.active span {
  background: linear-gradient(135deg, var(--primary), var(--primary-dark));
  color: white;
  border-color: var(--primary);
  box-shadow: 0 0 0 4px var(--primary-bg), 0 0 12px var(--primary-glow);
}

.step-dot.done span {
  background: linear-gradient(135deg, var(--success), #059669);
  color: white;
  border-color: var(--success);
  box-shadow: 0 0 0 4px var(--success-bg);
}

.step-dot-label {
  font-size: 11px;
  color: var(--text-tertiary);
  text-align: center;
}

.step-dot.active .step-dot-label {
  color: var(--primary);
  font-weight: 600;
}

/* 防幻觉 */
.hallucination-warning {
  display: flex;
  gap: 12px;
  padding: 16px 20px;
  background: var(--warning-bg);
  border: 1px solid rgba(245, 158, 11, 0.3);
  border-radius: var(--radius-md);
  margin-bottom: 20px;
  align-items: flex-start;
}

.warning-icon {
  color: var(--warning);
  flex-shrink: 0;
  margin-top: 2px;
}

.hallucination-warning strong {
  display: block;
  font-size: 14px;
  color: var(--warning);
  margin-bottom: 2px;
}

.hallucination-warning p {
  font-size: 13px;
  color: #7c6a3a;
  line-height: 1.5;
}

/* 空状态 */
.empty-state {
  text-align: center;
  padding: 80px 20px;
  color: var(--text-secondary);
}

.empty-graphic {
  margin-bottom: 16px;
  opacity: 0.3;
}

.empty-graphic svg {
  stroke: var(--text-tertiary);
}

.empty-state h3 {
  margin-bottom: 8px;
  color: var(--text-primary);
  font-size: 18px;
  font-weight: 700;
}

.empty-state p {
  color: var(--text-tertiary);
}

/* 资源区域 */
.resources-section {
  animation: slideUp 0.35s var(--ease-out);
}

@keyframes slideUp {
  from { opacity: 0; transform: translateY(16px); }
  to { opacity: 1; transform: translateY(0); }
}

/* 选项卡 */
.tabs-header {
  display: flex;
  gap: 4px;
  margin-bottom: 20px;
  background: var(--bg);
  padding: 4px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--border-light);
  flex-wrap: wrap;
}

.tab-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 8px 16px;
  border: none;
  border-radius: 4px;
  background: transparent;
  color: var(--text-secondary);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s var(--ease-out);
}

.tab-btn.active {
  background: var(--bg-card);
  color: var(--text-primary);
  box-shadow: var(--shadow-sm);
}

.tab-btn:hover:not(.active) {
  color: var(--text-primary);
}

.tab-count {
  font-size: 11px;
  background: var(--border-light);
  padding: 1px 6px;
  border-radius: var(--radius-full);
  color: var(--text-tertiary);
}

.tab-btn.active .tab-count {
  background: var(--primary-bg);
  color: var(--primary);
}

/* ===== ECharts 仪表盘 ===== */
.dashboard-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-bottom: 20px;
}

.dashboard-card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  padding: 16px;
  box-shadow: var(--shadow-sm);
}

.dashboard-card-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-secondary);
  margin-bottom: 8px;
  display: flex;
  align-items: center;
  gap: 6px;
}

.dashboard-card-title svg {
  color: var(--primary);
}

.quality-chart {
  width: 100%;
  height: 160px;
}

.type-chart {
  width: 100%;
  height: 160px;
}

/* 资源卡片 */
.resource-card-wrapper {
  margin-bottom: 20px;
}

.resource-card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  overflow: hidden;
  transition: all 0.25s var(--ease-out);
}

.resource-card:hover {
  box-shadow: var(--shadow-md);
  transform: translateY(-1px);
}

.card-accent {
  height: 3px;
  background: linear-gradient(90deg, var(--primary), var(--primary-light));
}

.type-document .card-accent { background: linear-gradient(90deg, #2563eb, #60a5fa); }
.type-mindmap .card-accent { background: linear-gradient(90deg, #10b981, #34d399); }
.type-exercise .card-accent { background: linear-gradient(90deg, #f59e0b, #fbbf24); }
.type-code .card-accent { background: linear-gradient(90deg, #3b82f6, #60a5fa); }
.type-video .card-accent { background: linear-gradient(90deg, #ef4444, #f87171); }
.type-audio .card-accent { background: linear-gradient(90deg, #8b5cf6, #a78bfa); }
.type-ppt .card-accent { background: linear-gradient(90deg, #ec4899, #f472b6); }

.card-body {
  padding: 20px 24px;
}

.card-top {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 14px;
}

.card-type-badge {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}

.quality-ring {
  flex-shrink: 0;
}

.card-content {
  max-height: 300px;
  overflow-y: auto;
  margin-bottom: 8px;
}

.card-content.collapsed {
  max-height: 200px;
  position: relative;
}

.card-content.collapsed::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 40px;
  background: linear-gradient(transparent, var(--bg-card));
  pointer-events: none;
}

.content-render {
  font-size: 13px;
  line-height: 1.7;
  color: var(--text-primary);
}

.content-render.pre-wrap pre {
  white-space: pre-wrap;
  word-break: break-word;
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
  font-size: 13px;
  background: var(--bg);
  padding: 16px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--border-light);
  overflow-x: auto;
}

.markdown :deep(h1),
.markdown :deep(h2),
.markdown :deep(h3) {
  margin: 16px 0 8px;
  font-weight: 700;
}

.markdown :deep(h1) { font-size: 18px; }
.markdown :deep(h2) { font-size: 16px; }
.markdown :deep(h3) { font-size: 14px; }

.markdown :deep(p) { margin-bottom: 10px; }

.markdown :deep(code) {
  background: var(--bg);
  padding: 2px 6px;
  border-radius: 4px;
  font-family: monospace;
  font-size: 13px;
}

.markdown :deep(pre) {
  background: var(--bg);
  padding: 16px;
  border-radius: var(--radius-sm);
  overflow-x: auto;
  margin: 12px 0;
  border: 1px solid var(--border-light);
}

.markdown :deep(pre code) {
  background: none;
  padding: 0;
}

.markdown :deep(ul), .markdown :deep(ol) {
  padding-left: 20px;
  margin-bottom: 10px;
}

.markdown :deep(blockquote) {
  border-left: 3px solid var(--primary);
  padding-left: 12px;
  margin: 12px 0;
  color: var(--text-secondary);
}

.expand-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  border: none;
  background: none;
  color: var(--primary);
  font-size: 13px;
  font-weight: 500;
  padding: 4px 0;
  cursor: pointer;
}

.expand-btn svg {
  transition: transform 0.2s;
}

.expand-btn svg.rotated {
  transform: rotate(180deg);
}

.expand-btn:hover {
  color: var(--primary-dark);
}

.card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid var(--border-light);
}

.footer-agent {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: var(--text-tertiary);
}

.copy-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 14px;
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  color: var(--text-secondary);
  font-size: 12px;
  cursor: pointer;
  transition: all 0.15s;
}

.copy-btn:hover {
  background: var(--primary-bg);
  border-color: var(--primary);
  color: var(--primary);
}

.spinner {
  display: inline-block;
  width: 14px;
  height: 14px;
  border: 2px solid rgba(255,255,255,0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
