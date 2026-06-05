<template>
  <div class="code-block">
    <div class="code-header">
      <span class="language">{{ language }}</span>
      <button class="copy-btn" @click="copyCode">复制</button>
    </div>
    <pre class="code-content"><code>{{ code }}</code></pre>
  </div>
</template>

<script setup>
const props = defineProps({
  code: {
    type: String,
    default: ''
  },
  language: {
    type: String,
    default: 'python'
  }
})

const copyCode = async () => {
  try {
    await navigator.clipboard.writeText(props.code)
    alert('代码已复制到剪贴板')
  } catch (error) {
    console.error('Failed to copy:', error)
  }
}
</script>

<style scoped>
.code-block {
  background: #1e1e1e;
  border-radius: 8px;
  overflow: hidden;
}

.code-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 16px;
  background: #2d2d2d;
}

.language {
  font-size: 12px;
  color: #888;
}

.copy-btn {
  padding: 4px 8px;
  background: transparent;
  border: 1px solid #555;
  border-radius: 4px;
  color: #ccc;
  cursor: pointer;
  font-size: 12px;
}

.copy-btn:hover {
  background: #3d3d3d;
}

.code-content {
  padding: 16px;
  margin: 0;
  overflow-x: auto;
}

.code-content code {
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 13px;
  color: #d4d4d4;
  line-height: 1.5;
}
</style>
