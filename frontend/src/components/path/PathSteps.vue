<template>
  <div class="path-steps">
    <div
      v-for="(step, index) in steps"
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
        <span v-else>{{ index + 1 }}</span>
      </div>
      <div class="step-name">{{ step.name }}</div>
      <div v-if="index < steps.length - 1" class="step-connector"></div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  steps: {
    type: Array,
    default: () => []
  }
})
</script>

<style scoped>
.path-steps {
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
</style>
