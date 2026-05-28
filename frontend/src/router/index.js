import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: () => import('@/views/Home.vue')
  },
  {
    path: '/characters',
    name: 'Characters',
    component: () => import('@/views/Characters.vue')
  },
  {
    path: '/materials',
    name: 'Materials',
    component: () => import('@/views/Materials.vue')
  },
  {
    path: '/chat/:id',
    name: 'Chat',
    component: () => import('@/views/Chat.vue')
  },
  {
    path: '/conversations',
    name: 'Conversations',
    component: () => import('@/views/Conversations.vue')
  },
  {
    path: '/settings',
    name: 'Settings',
    component: () => import('@/views/Settings.vue')
  },
  {
    path: '/curriculum',
    name: 'Curriculum',
    component: () => import('@/views/Curriculum.vue')
  },
  {
    path: '/timeline',
    name: 'Timeline',
    component: () => import('@/views/Timeline.vue')
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router