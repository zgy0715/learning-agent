import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    redirect: '/chat'
  },
  {
    path: '/chat',
    name: 'Chat',
    component: () => import('../views/ChatView.vue')
  },
  {
    path: '/resource',
    name: 'Resource',
    component: () => import('../views/ResourceView.vue')
  },
  {
    path: '/path',
    name: 'Path',
    component: () => import('../views/PathView.vue')
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
