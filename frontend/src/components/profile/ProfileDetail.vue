<template>
  <div class="profile-detail">
    <div v-for="(dim, key) in dimensions" :key="key" class="profile-item">
      <span class="label">{{ dimensionLabels[key] }}</span>
      <span class="value">{{ dim.value || '未知' }}</span>
      <div class="confidence-bar">
        <div class="confidence-fill" :style="{ width: ((dim.confidence || 0) * 100) + '%' }"></div>
      </div>
      <span class="confidence-text">{{ ((dim.confidence || 0) * 100).toFixed(0) }}%</span>
    </div>
  </div>
</template>

<script setup>
defineProps({
  dimensions: {
    type: Object,
    default: () => ({})
  }
})

const dimensionLabels = {
  knowledge_base: '知识基础',
  cognitive_style: '认知风格',
  error_patterns: '易错点偏好',
  learning_preference: '学习偏好',
  learning_pace: '学习节奏',
  goal_orientation: '目标导向'
}
</script>

<style scoped>
.profile-detail {
  padding: 16px 0;
}

.profile-item {
  margin-bottom: 16px;
}

.profile-item .label {
  display: block;
  font-size: 12px;
  color: var(--text-color-secondary);
  margin-bottom: 4px;
}

.profile-item .value {
  display: block;
  font-size: 14px;
  font-weight: 500;
  margin-bottom: 4px;
}

.confidence-bar {
  height: 4px;
  background: var(--bg-color-dark);
  border-radius: 2px;
  overflow: hidden;
  margin-bottom: 2px;
}

.confidence-fill {
  height: 100%;
  background: var(--primary-color);
  transition: width 0.3s;
}

.confidence-text {
  font-size: 11px;
  color: var(--text-color-placeholder);
}
</style>
