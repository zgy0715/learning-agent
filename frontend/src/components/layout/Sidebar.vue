<template>
  <aside class="sidebar">
    <div class="sidebar-brand">
      <div class="brand-icon">
        <svg width="28" height="28" viewBox="0 0 28 28" fill="none">
          <rect width="28" height="28" rx="8" fill="#2563eb"/>
          <path d="M14 6V22M9 11H19M7 14H21M9 17H19" stroke="white" stroke-width="2" stroke-linecap="round"/>
        </svg>
      </div>
      <div class="brand-text">A3 Learning</div>
    </div>

    <nav class="sidebar-nav">
      <router-link
        v-for="item in navItems"
        :key="item.path"
        :to="item.path"
        class="nav-item"
        :class="{ active: $route.path === item.path }"
      >
        <span class="nav-icon" v-html="item.icon"></span>
        <span class="nav-label">{{ item.label }}</span>
        <div class="nav-active-bar"></div>
      </router-link>
    </nav>

    <div class="sidebar-footer">
      <div class="user-card">
        <div class="user-avatar">🧑‍🎓</div>
        <div class="user-info">
          <span class="user-name">学习者</span>
          <span class="user-status">在线</span>
        </div>
      </div>
    </div>
  </aside>
</template>

<script setup>
const navItems = [
  {
    path: '/chat',
    label: '智能对话',
    icon: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>`
  },
  {
    path: '/resource',
    label: '学习资源',
    icon: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/></svg>`
  },
  {
    path: '/path',
    label: '学习路径',
    icon: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><polygon points="12 2 22 8.5 22 15.5 12 22 2 15.5 2 8.5"/><line x1="12" y1="22" x2="12" y2="15.5"/><polyline points="22 8.5 12 15.5 2 8.5"/></svg>`
  }
]
</script>

<style scoped>
.sidebar {
  width: var(--sidebar-width);
  height: 100vh;
  background: #ffffff;
  border-right: 1px solid #e5e7eb;
  display: flex;
  flex-direction: column;
}

.sidebar-brand {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 20px 18px;
  border-bottom: 1px solid #f3f4f6;
}

.brand-text {
  font-size: 16px;
  font-weight: 700;
  color: #111827;
}

.sidebar-nav {
  flex: 1;
  padding: 12px 10px;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 8px;
  color: #6b7280;
  text-decoration: none;
  font-size: 14px;
  font-weight: 500;
  position: relative;
  transition: all 0.15s ease;
}

.nav-item:hover {
  background: #f9fafb;
  color: #374151;
}

.nav-item.active {
  background: #eff6ff;
  color: #2563eb;
  font-weight: 600;
}

.nav-icon {
  display: flex;
  align-items: center;
  width: 20px;
  height: 20px;
  flex-shrink: 0;
}

.nav-icon :deep(svg) {
  width: 100%;
  height: 100%;
}

.nav-label {
  flex: 1;
}

.nav-active-bar {
  display: none;
}

.nav-item.active .nav-active-bar {
  display: block;
  width: 3px;
  height: 16px;
  background: #2563eb;
  border-radius: 2px;
  position: absolute;
  right: -9px;
}

.sidebar-footer {
  padding: 14px 16px;
  border-top: 1px solid #f3f4f6;
}

.user-card {
  display: flex;
  align-items: center;
  gap: 10px;
}

.user-avatar {
  font-size: 20px;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.user-info {
  display: flex;
  flex-direction: column;
}

.user-name {
  font-size: 13px;
  font-weight: 600;
  color: #111827;
}

.user-status {
  font-size: 11px;
  color: #9ca3af;
}
</style>
