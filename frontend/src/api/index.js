import axios from 'axios'
import { ElMessage } from 'element-plus'

const apiClient = axios.create({
  baseURL: '/api/v1',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

apiClient.interceptors.request.use(
  (config) => {
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

apiClient.interceptors.response.use(
  (response) => {
    return response.data
  },
  (error) => {
    const message = error.response?.data?.detail || error.message || '请求失败'
    ElMessage.error(message)
    return Promise.reject(error)
  }
)

export default {
  characters: {
    getAll: () => apiClient.get('/crud/characters'),
    getById: (id) => apiClient.get(`/crud/characters/${id}`),
    create: (data) => apiClient.post('/crud/characters', data),
    update: (id, data) => apiClient.put(`/crud/characters/${id}`, data),
    delete: (id) => apiClient.delete(`/crud/characters/${id}`)
  },
  materials: {
    getAll: () => apiClient.get('/crud/materials'),
    getById: (id) => apiClient.get(`/crud/materials/${id}`),
    create: (data) => apiClient.post('/crud/materials', data),
    update: (id, data) => apiClient.put(`/crud/materials/${id}`, data),
    delete: (id) => apiClient.delete(`/crud/materials/${id}`)
  },
  conversations: {
    getAll: () => apiClient.get('/crud/conversations'),
    getById: (id) => apiClient.get(`/crud/conversations/${id}`),
    create: (data) => apiClient.post('/crud/conversations', data),
    update: (id, data) => apiClient.put(`/crud/conversations/${id}`, data),
    delete: (id) => apiClient.delete(`/crud/conversations/${id}`)
  },
  modelConfigs: {
    getAll: () => apiClient.get('/crud/model-configs'),
    getById: (id) => apiClient.get(`/crud/model-configs/${id}`),
    create: (data) => apiClient.post('/crud/model-configs', data),
    update: (id, data) => apiClient.put(`/crud/model-configs/${id}`, data),
    delete: (id) => apiClient.delete(`/crud/model-configs/${id}`)
  },
  chat: {
    stream: (conversationId, message) => {
      return new EventSource(`/api/v1/chat/${conversationId}/stream?message=${encodeURIComponent(message)}`)
    }
  },
  upload: {
    avatar: (formData) => apiClient.post('/upload/avatar', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    }),
    background: (formData) => apiClient.post('/upload/background', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  }
}