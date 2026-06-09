<template>
  <div class="app-container">
    <Sidebar />
    <main class="main-content">
      <router-view v-slot="{ Component, route }">
        <Transition name="page" mode="out-in">
          <component :is="Component" :key="route.path" />
        </Transition>
      </router-view>
    </main>
  </div>
</template>

<script setup>
import Sidebar from './components/layout/Sidebar.vue'
</script>

<style scoped>
.app-container {
  display: flex;
  height: 100vh;
  overflow: hidden;
  position: relative;
}

.main-content {
  flex: 1;
  overflow: auto;
  background: var(--bg);
  position: relative;
  z-index: 1;
}

/* 页面切换过渡 */
.page-enter-active {
  transition: all 0.25s var(--ease-out);
}

.page-leave-active {
  transition: all 0.15s var(--ease-out);
}

.page-enter-from {
  opacity: 0;
  transform: translateY(12px);
}

.page-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}
</style>
