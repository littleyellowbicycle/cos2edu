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
    }
  }
})