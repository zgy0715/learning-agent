<template>
  <div class="resource-view">
    <div class="header">
      <h2>资源生成</h2>
      <p>输入学习主题，AI将为您生成多种学习资源</p>
    </div>

    <div class="input-section">
      <input
        v-model="topic"
        type="text"
        placeholder="请输入学习主题，例如：神经网络反向传播算法"
        @keydown.enter="generateResources"
      />
      <button @click="generateResources" :disabled="!topic.trim() || generating">
        {{ generating ? '生成中...' : '开始生成' }}
      </button>
    </div>

    <div v-if="generating" class="progress-section">
      <div class="progress-bar">
        <div class="progress-fill" :style="{ width: progress + '%' }"></div>
      </div>
      <div class="progress-text">{{ currentStep }}</div>
    </div>

    <div v-if="resources.length > 0" class="resources-grid">
      <div v-for="resource in resources" :key="resource.id" class="resource-card">
        <div class="card-header">
          <span class="card-icon">{{ getResourceIcon(resource.resource_type) }}</span>
          <span class="card-type">{{ getResourceTypeName(resource.resource_type) }}</span>
        </div>
        <div class="card-content">
          <div v-if="resource.resource_type === 'document'" class="document-content" v-html="renderMarkdown(resource.content)"></div>
          <div v-else-if="resource.resource_type === 'mindmap'" class="mindmap-content">
            <div ref="mindmapContainer" class="mindmap-container"></div>
          </div>
          <div v-else-if="resource.resource_type === 'exercise'" class="exercise-content">
            <pre>{{ resource.content }}</pre>
          </div>
          <div v-else class="other-content">
            <pre>{{ resource.content }}</pre>
          </div>
        </div>
        <div class="card-footer">
          <span class="quality-score">质量评分: {{ resource.metadata?.quality_score || '-' }}</span>
          <button class="copy-btn" @click="copyContent(resource.content)">复制</button>
        </div>
      </div>
    </div>

    <div v-else-if="!generating" class="empty-state">
      <div class="empty-icon">📚</div>
      <h3>暂无资源</h3>
      <p>输入学习主题，AI将为您生成多种学习资源</p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick, watch } from 'vue'
import { useResourceStore } from '../stores/resource'
import MarkdownIt from 'markdown-it'

const resourceStore = useResourceStore()

const topic = ref('')
const generating = ref(false)
const progress = ref(0)
const currentStep = ref('')
const resources = ref([])

const md = new MarkdownIt()

const renderMarkdown = (text) => {
  return md.render(text || '')
}

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

const copyContent = async (content) => {
  try {
    await navigator.clipboard.writeText(content)
    alert('已复制到剪贴板')
  } catch (error) {
    console.error('Failed to copy:', error)
  }
}

const generateResources = async () => {
  if (!topic.value.trim() || generating.value) return

  generating.value = true
  progress.value = 0
  currentStep.value = '准备生成...'
  resources.value = []

  try {
    const taskId = await resourceStore.startGeneration(topic.value)

    // 轮询任务状态
    const pollInterval = setInterval(async () => {
      const status = await resourceStore.getTaskStatus(taskId)
      progress.value = status.progress * 100
      currentStep.value = status.current_step

      if (status.status === 'completed') {
        clearInterval(pollInterval)
        resources.value = status.result?.resources || []
        generating.value = false
      } else if (status.status === 'failed') {
        clearInterval(pollInterval)
        currentStep.value = '生成失败：' + (status.error || '未知错误')
        generating.value = false
      }
    }, 1000)
  } catch (error) {
    console.error('Failed to generate resources:', error)
    currentStep.value = '生成失败：' + error.message
    generating.value = false
  }
}
</script>

<style scoped>
.resource-view {
  padding: 24px;
  max-width: 1400px;
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

.input-section {
  display: flex;
  gap: 12px;
  margin-bottom: 24px;
}

.input-section input {
  flex: 1;
  padding: 12px 16px;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  font-size: 14px;
}

.input-section input:focus {
  outline: none;
  border-color: var(--primary-color);
}

.input-section button {
  padding: 12px 24px;
  background: var(--primary-color);
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  transition: background 0.3s;
}

.input-section button:hover:not(:disabled) {
  background: #66b1ff;
}

.input-section button:disabled {
  background: var(--bg-color-dark);
  cursor: not-allowed;
}

.progress-section {
  margin-bottom: 24px;
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

.resources-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 20px;
}

.resource-card {
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.card-header {
  padding: 16px 20px;
  background: var(--bg-color);
  display: flex;
  align-items: center;
  gap: 8px;
  border-bottom: 1px solid var(--border-color-light);
}

.card-icon {
  font-size: 20px;
}

.card-type {
  font-weight: 500;
  color: var(--text-color);
}

.card-content {
  flex: 1;
  padding: 16px 20px;
  max-height: 400px;
  overflow-y: auto;
}

.document-content {
  line-height: 1.6;
}

.document-content :deep(h1),
.document-content :deep(h2),
.document-content :deep(h3) {
  margin-top: 16px;
  margin-bottom: 8px;
}

.document-content :deep(p) {
  margin-bottom: 12px;
}

.document-content :deep(code) {
  background: var(--bg-color);
  padding: 2px 6px;
  border-radius: 4px;
  font-family: monospace;
}

.mindmap-container {
  min-height: 300px;
}

.exercise-content pre,
.other-content pre {
  white-space: pre-wrap;
  word-wrap: break-word;
  font-family: monospace;
  font-size: 13px;
  line-height: 1.5;
}

.card-footer {
  padding: 12px 20px;
  border-top: 1px solid var(--border-color-light);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.quality-score {
  font-size: 12px;
  color: var(--text-color-secondary);
}

.copy-btn {
  padding: 6px 12px;
  background: white;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  cursor: pointer;
  font-size: 12px;
  transition: all 0.3s;
}

.copy-btn:hover {
  background: var(--bg-color);
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
