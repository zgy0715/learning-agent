<template>
  <div class="resource-card">
    <div class="card-header">
      <span class="card-icon">{{ getResourceIcon(resource.resource_type) }}</span>
      <span class="card-type">{{ getResourceTypeName(resource.resource_type) }}</span>
    </div>
    <div class="card-content">
      <div v-if="resource.resource_type === 'document'" class="document-content" v-html="renderMarkdown(resource.content)"></div>
      <div v-else-if="resource.resource_type === 'exercise'" class="exercise-content">
        <pre>{{ resource.content }}</pre>
      </div>
      <div v-else class="other-content">
        <pre>{{ resource.content }}</pre>
      </div>
    </div>
    <div class="card-footer">
      <span class="quality-score">质量评分: {{ resource.metadata?.quality_score || '-' }}</span>
      <button class="copy-btn" @click="copyContent">复制</button>
    </div>
  </div>
</template>

<script setup>
import MarkdownIt from 'markdown-it'

const props = defineProps({
  resource: {
    type: Object,
    required: true
  }
})

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

const copyContent = async () => {
  try {
    await navigator.clipboard.writeText(props.resource.content)
    alert('已复制到剪贴板')
  } catch (error) {
    console.error('Failed to copy:', error)
  }
}
</script>

<style scoped>
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
</style>
