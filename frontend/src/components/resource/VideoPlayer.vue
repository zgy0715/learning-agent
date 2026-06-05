<template>
  <div class="video-player">
    <video
      v-if="src"
      :src="src"
      controls
      class="video-element"
    >
      您的浏览器不支持视频播放
    </video>
    <div v-else class="video-placeholder">
      <span class="placeholder-icon">🎬</span>
      <span class="placeholder-text">视频内容生成中...</span>
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
.video-player {
  width: 100%;
  border-radius: 8px;
  overflow: hidden;
  background: #000;
}

.video-element {
  width: 100%;
  display: block;
}

.video-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px;
  color: #888;
}

.placeholder-icon {
  font-size: 48px;
  margin-bottom: 12px;
}

.placeholder-text {
  font-size: 14px;
}
</style>
