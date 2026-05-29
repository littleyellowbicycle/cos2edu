import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/api'

const TOKEN_KEY = 'cos2edu_token'
const USER_KEY = 'cos2edu_user'

export const useUserStore = defineStore('user', () => {
  const token = ref(localStorage.getItem(TOKEN_KEY) || '')
  const user = ref(JSON.parse(localStorage.getItem(USER_KEY) || 'null'))

  const isLoggedIn = computed(() => !!token.value)
  const userRole = computed(() => user.value?.role || '')
  const isAdmin = computed(() => userRole.value === 'admin')
  const isTeacher = computed(() => userRole.value === 'teacher' || userRole.value === 'admin')
  const displayName = computed(() => user.value?.display_name || user.value?.username || '')

  function setAuth(authData) {
    token.value = authData.access_token
    user.value = authData.user
    localStorage.setItem(TOKEN_KEY, authData.access_token)
    localStorage.setItem(USER_KEY, JSON.stringify(authData.user))
  }

  function clearAuth() {
    token.value = ''
    user.value = null
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(USER_KEY)
  }

  async function register(data) {
    const res = await api.post('/auth/register', data)
    setAuth(res.data)
    return res.data
  }

  async function login(data) {
    const res = await api.post('/auth/login', data)
    setAuth(res.data)
    return res.data
  }

  function logout() {
    clearAuth()
  }

  async function fetchProfile() {
    if (!token.value) return null
    try {
      const res = await api.get('/auth/me')
      user.value = res.data
      localStorage.setItem(USER_KEY, JSON.stringify(res.data))
      return res.data
    } catch {
      clearAuth()
      return null
    }
  }

  async function updateProfile(data) {
    const res = await api.put('/auth/me', data)
    user.value = res.data
    localStorage.setItem(USER_KEY, JSON.stringify(res.data))
    return res.data
  }

  async function changePassword(oldPassword, newPassword) {
    return api.post('/auth/change-password', {
      old_password: oldPassword,
      new_password: newPassword,
    })
  }

  return {
    token,
    user,
    isLoggedIn,
    userRole,
    isAdmin,
    isTeacher,
    displayName,
    register,
    login,
    logout,
    fetchProfile,
    updateProfile,
    changePassword,
  }
})