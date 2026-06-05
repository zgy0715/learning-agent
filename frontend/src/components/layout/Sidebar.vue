<template>
  <aside class="sidebar">
    <div class="logo">
      <h1>A3 Learning</h1>
    </div>
    <nav class="nav-menu">
      <router-link to="/chat" class="nav-item" :class="{ active: $route.path === '/chat' }">
        <span class="nav-icon">💬</span>
        <span class="nav-text">对话</span>
      </router-link>
      <router-link to="/resource" class="nav-item" :class="{ active: $route.path === '/resource' }">
        <span class="nav-icon">📚</span>
        <span class="nav-text">资源</span>
      </router-link>
      <router-link to="/path" class="nav-item" :class="{ active: $route.path === '/path' }">
        <span class="nav-icon">🗺️</span>
        <span class="nav-text">路径</span>
      </router-link>
    </nav>
    <div class="sidebar-footer">
      <div class="user-info">
        <span class="user-avatar">👤</span>
        <span class="user-name">学习者</span>
      </div>
    </div>
  </aside>
</template>

<style scoped>
.sidebar {
  width: var(--sidebar-width);
  height: 100vh;
  background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%);
  display: flex;
  flex-direction: column;
  color: white;
}

.logo {
  padding: 20px;
  text-align: center;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.logo h1 {
  font-size: 20px;
  font-weight: 600;
}

.nav-menu {
  flex: 1;
  padding: 20px 10px;
}

.nav-item {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  margin-bottom: 8px;
  border-radius: 8px;
  color: rgba(255, 255, 255, 0.7);
  text-decoration: none;
  transition: all 0.3s ease;
}

.nav-item:hover {
  background: rgba(255, 255, 255, 0.1);
  color: white;
}

.nav-item.active {
  background: var(--primary-color);
  color: white;
}

.nav-icon {
  font-size: 20px;
  margin-right: 12px;
}

.nav-text {
  font-size: 14px;
}

.sidebar-footer {
  padding: 20px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.user-info {
  display: flex;
  align-items: center;
}

.user-avatar {
  font-size: 24px;
  margin-right: 12px;
}

.user-name {
  font-size: 14px;
}
</style>
