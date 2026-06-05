<template>
  <div class="chat-input">
    <div class="input-wrapper">
      <textarea
        :value="modelValue"
        @input="$emit('update:modelValue', $event.target.value)"
        @keydown.enter.exact="$emit('send')"
        :placeholder="placeholder"
        rows="1"
        ref="inputRef"
      ></textarea>
      <button class="send-btn" @click="$emit('send')" :disabled="!modelValue.trim() || loading">
        {{ loading ? '发送中...' : '发送' }}
      </button>
    </div>
  </div>
</template>

<script setup>
defineProps({
  modelValue: {
    type: String,
    default: ''
  },
  placeholder: {
    type: String,
    default: '输入您的消息...'
  },
  loading: {
    type: Boolean,
    default: false
  }
})

defineEmits(['update:modelValue', 'send'])
</script>

<style scoped>
.chat-input {
  padding: 20px;
  background: white;
  border-top: 1px solid var(--border-color);
}

.input-wrapper {
  display: flex;
  gap: 12px;
  align-items: flex-end;
}

.input-wrapper textarea {
  flex: 1;
  padding: 12px 16px;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  resize: none;
  font-size: 14px;
  font-family: inherit;
  line-height: 1.5;
  max-height: 120px;
}

.input-wrapper textarea:focus {
  outline: none;
  border-color: var(--primary-color);
}

.send-btn {
  padding: 12px 24px;
  background: var(--primary-color);
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  transition: background 0.3s;
}

.send-btn:hover:not(:disabled) {
  background: #66b1ff;
}

.send-btn:disabled {
  background: var(--bg-color-dark);
  cursor: not-allowed;
}
</style>
