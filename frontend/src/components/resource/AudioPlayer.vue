<template>
  <div class="audio-player">
    <audio
      v-if="src"
      :src="src"
      controls
      class="audio-element"
    >
      您的浏览器不支持音频播放
    </audio>
    <div v-else class="audio-placeholder">
      <span class="placeholder-icon">🎵</span>
      <span class="placeholder-text">音频内容生成中...</span>
    </div>
  </div>
</template>

<script setup>
defineProps({
  src: {
    type: String,
    default: ''
  }
})
</script>

<style scoped>
.audio-player {
  width: 100%;
  padding: 16px;
  background: var(--bg-color);
  border-radius: 8px;
}

.audio-element {
  width: 100%;
}

.audio-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 20px;
  color: #888;
}

.placeholder-icon {
  font-size: 36px;
  margin-bottom: 8px;
}

.placeholder-text {
  font-size: 14px;
}
</style>
