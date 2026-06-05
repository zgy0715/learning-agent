<template>
  <div class="step-detail">
    <div class="detail-header">
      <h4>{{ step.name }}</h4>
      <span class="difficulty" :class="step.difficulty">
        {{ step.difficulty }}
      </span>
      <span class="duration">约 {{ step.duration_minutes }} 分钟</span>
    </div>
    <div class="detail-objective">
      <strong>学习目标：</strong>{{ step.objective }}
    </div>
    <div class="step-resources">
      <h5>推荐资源</h5>
      <div class="resource-list">
        <div
          v-for="resourceType in step.resource_types"
          :key="resourceType"
          class="resource-tag"
        >
          {{ getResourceIcon(resourceType) }} {{ getResourceTypeName(resourceType) }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  step: {
    type: Object,
    required: true
  }
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
</script>

<style scoped>
.step-detail {
  background: var(--bg-color);
  border-radius: 8px;
  padding: 20px;
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
  font-size: 13px;
}
</style>
