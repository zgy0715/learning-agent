<template>
  <div class="feedback-buttons">
    <button class="feedback-btn hard" @click="$emit('feedback', 'too_hard')">
      😰 太难了
    </button>
    <button class="feedback-btn easy" @click="$emit('feedback', 'too_easy')">
      😊 太简单
    </button>
    <button class="feedback-btn help" @click="$emit('feedback', 'need_help')">
      🤔 需要帮助
    </button>
    <button class="feedback-btn complete" @click="$emit('complete')">
      ✓ 完成
    </button>
  </div>
</template>

<script setup>
defineEmits(['feedback', 'complete'])
</script>

<style scoped>
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
</style>
