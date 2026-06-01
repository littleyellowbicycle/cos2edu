import axios from 'axios'
import { ElMessage } from 'element-plus'

const apiClient = axios.create({
  baseURL: '/api/v1',
  timeout: 30000
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

export { apiClient }

export default {
  characters: {
    getAll: () => apiClient.get('/crud/characters'),
    getById: (id) => apiClient.get(`/crud/characters/${id}`),
    create: (data) => apiClient.post('/crud/characters/multipart', data, {
      headers: { 'Content-Type': 'multipart/form-data' }
    }),
    update: (id, data) => apiClient.put(`/crud/characters/${id}/multipart`, data, {
      headers: { 'Content-Type': 'multipart/form-data' }
    }),
    delete: (id) => apiClient.delete(`/crud/characters/${id}`)
  },
  materials: {
    getAll: () => apiClient.get('/crud/materials'),
    getById: (id) => apiClient.get(`/crud/materials/${id}`),
    create: (data) => apiClient.post('/crud/materials', data),
    update: (id, data) => apiClient.put(`/crud/materials/${id}`, data),
    delete: (id) => apiClient.delete(`/crud/materials/${id}`),
    upload: (formData) => apiClient.post('/crud/materials/upload', formData),
    generateSummary: (id) => apiClient.post(`/crud/materials/${id}/generate-summary`)
  },
  conversations: {
    getAll: () => apiClient.get('/crud/conversations'),
    getById: (id) => apiClient.get(`/crud/conversations/${id}`),
    create: (data) => apiClient.post('/crud/conversations', data),
    update: (id, data) => apiClient.put(`/crud/conversations/${id}`, data),
    delete: (id) => apiClient.delete(`/crud/conversations/${id}`),
    search: (params) => apiClient.get('/content/conversations/search', { params }),
    searchMessages: (conversationId, params) => apiClient.get(`/content/conversations/${conversationId}/messages/search`, { params }),
    stats: () => apiClient.get('/content/conversations/stats'),
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
  },
  providers: {
    list: () => apiClient.get('/crud/providers'),
    models: (provider, params) => apiClient.get(`/crud/providers/${provider}/models`, { params })
  },
  content: {
    searchConversations: (params) => apiClient.get('/content/conversations/search', { params }),
    conversationStats: () => apiClient.get('/content/conversations/stats'),
    searchMessages: (conversationId, params) => apiClient.get(`/content/conversations/${conversationId}/messages/search`, { params }),
    listYamlFiles: () => apiClient.get('/content/yaml/list'),
    readYamlFile: (path) => apiClient.get(`/content/yaml/${path}`),
    writeYamlFile: (path, content) => apiClient.put(`/content/yaml/${path}`, { content }),
    createCharacterFromTemplate: (data) => apiClient.post('/content/characters/create', data),
    getCharacterTemplates: () => apiClient.get('/content/characters/templates'),
    reloadContent: () => apiClient.post('/content/reload'),
  },
  curriculum: {
    getSyllabus: (materialId) => apiClient.get('/curriculum/syllabus', { params: materialId ? { material_id: materialId } : {} }),
    getModules: (materialId) => apiClient.get('/curriculum/modules', { params: materialId ? { material_id: materialId } : {} }),
    listSyllabuses: () => apiClient.get('/curriculum/syllabuses'),
    listGeneratableMaterials: () => apiClient.get('/curriculum/materials/generatable'),
  }
}