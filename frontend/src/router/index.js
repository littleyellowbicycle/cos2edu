import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { public: true },
  },
  {
    path: '/',
    name: 'Home',
    component: () => import('@/views/Home.vue'),
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: () => import('@/views/Dashboard.vue'),
  },
  {
    path: '/teacher',
    name: 'TeacherDashboard',
    component: () => import('@/views/TeacherDashboard.vue'),
    meta: { requiresRole: 'teacher' },
  },
  {
    path: '/characters',
    name: 'Characters',
    component: () => import('@/views/Characters.vue'),
  },
  {
    path: '/materials',
    name: 'Materials',
    component: () => import('@/views/Materials.vue'),
  },
  {
    path: '/chat/:id',
    name: 'Chat',
    component: () => import('@/views/Chat.vue'),
  },
  {
    path: '/conversations',
    name: 'Conversations',
    component: () => import('@/views/Conversations.vue'),
  },
  {
    path: '/settings',
    name: 'Settings',
    component: () => import('@/views/Settings.vue'),
  },
  {
    path: '/curriculum',
    name: 'Curriculum',
    component: () => import('@/views/Curriculum.vue'),
  },
  {
    path: '/timeline',
    name: 'Timeline',
    component: () => import('@/views/Timeline.vue'),
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('cos2edu_token')
  if (!to.meta.public && !token) {
    next({ name: 'Login', query: { redirect: to.fullPath } })
  } else if (to.meta.public && token && to.name === 'Login') {
    next({ name: 'Home' })
  } else {
    next()
  }
})

export default router