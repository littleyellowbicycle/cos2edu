import { defineStore } from 'pinia'
import api from '@/api'

export const useCharacterStore = defineStore('character', {
  state: () => ({
    characters: [],
    currentCharacter: null,
    loading: false
  }),
  actions: {
    async fetchAll() {
      this.loading = true
      try {
        this.characters = await api.characters.getAll()
      } finally {
        this.loading = false
      }
    },
    async fetchById(id) {
      this.loading = true
      try {
        this.currentCharacter = await api.characters.getById(id)
      } finally {
        this.loading = false
      }
    },
    async create(data) {
      const result = await api.characters.create(data)
      this.characters.push(result)
      return result
    },
    async update(id, data) {
      const result = await api.characters.update(id, data)
      const index = this.characters.findIndex(c => c.id === id)
      if (index !== -1) {
        this.characters[index] = result
      }
      return result
    },
    async delete(id) {
      await api.characters.delete(id)
      this.characters = this.characters.filter(c => c.id !== id)
    }
  }
})