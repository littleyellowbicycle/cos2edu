import { defineStore } from 'pinia'
import api from '@/api'

export const useConversationStore = defineStore('conversation', {
  state: () => ({
    conversations: [],
    currentConversation: null,
    messages: [],
    loading: false
  }),
  actions: {
    async fetchAll() {
      this.loading = true
      try {
        this.conversations = await api.conversations.getAll()
      } finally {
        this.loading = false
      }
    },
    async fetchById(id) {
      this.loading = true
      try {
        this.currentConversation = await api.conversations.getById(id)
      } finally {
        this.loading = false
      }
    },
    async create(data) {
      const result = await api.conversations.create(data)
      this.conversations.push(result)
      return result
    },
    async delete(id) {
      await api.conversations.delete(id)
      this.conversations = this.conversations.filter(c => c.id !== id)
    },
    async update(id, data) {
      const result = await api.conversations.update(id, data)
      const index = this.conversations.findIndex(c => c.id === id)
      if (index !== -1) this.conversations[index] = result
      if (this.currentConversation?.id === id) {
        this.currentConversation = result
      }
      return result
    }
  }
})