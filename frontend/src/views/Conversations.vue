<template>
  <div class="conversations">
    <header class="page-header">
      <div class="header-content">
        <router-link to="/" class="back-link">
          <span class="back-icon">←</span>
          <span>返回首页</span>
        </router-link>
        <div class="header-title-group">
          <h1 class="page-title">对话</h1>
          <p class="page-subtitle">回顾你的思考历程</p>
        </div>
      </div>
    </header>

    <main class="conversations-content">
      <div class="search-bar">
        <div class="search-input-wrapper">
          <span class="search-icon">🔍</span>
          <input
            v-model="searchQuery"
            @input="debouncedSearch"
            placeholder="搜索对话标题或内容..."
            class="search-input"
          />
          <button v-if="searchQuery" class="clear-btn" @click="clearSearch">✕</button>
        </div>
        <div class="filter-group">
          <select v-model="filterCharacter" @change="doSearch" class="filter-select">
            <option :value="null">全部角色</option>
            <option v-for="c in characters" :key="c.id" :value="c.id">{{ c.name }}</option>
          </select>
        </div>
      </div>

      <div class="stats-bar">
        <div class="stat-item">
          <span class="stat-value">{{ totalConversations }}</span>
          <span class="stat-label">对话总数</span>
        </div>
        <div class="stat-item">
          <span class="stat-value">{{ totalMessages }}</span>
          <span class="stat-label">消息总数</span>
        </div>
        <div class="stat-item">
          <span class="stat-value">{{ recentCount }}</span>
          <span class="stat-label">近7天</span>
        </div>
      </div>

      <div v-if="loading" class="loading-state">
        <div class="loading-spinner"></div>
        <p>加载中...</p>
      </div>

      <div v-else-if="conversations.length === 0" class="empty-state">
        <div class="empty-icon">○</div>
        <h3>{{ searchQuery ? '未找到匹配的对话' : '暂无对话' }}</h3>
        <p>{{ searchQuery ? '尝试更换关键词或清除筛选' : '开始与 AI 角色对话，记录你的思考和探索' }}</p>
        <router-link v-if="!searchQuery" to="/characters" class="btn-primary">选择角色开始</router-link>
        <button v-else class="btn-primary" @click="clearSearch">清除搜索</button>
      </div>

      <div v-else class="conversations-list">
        <ConversationCard
          v-for="(conv, index) in conversations"
          :key="conv.id"
          :conversation="conv"
          :avatar-display="getAvatarDisplay(conv)"
          :avatar-style="getAvatarStyle(conv)"
          :index="index"
          @delete="deleteConversation"
          @update-title="handleTitleUpdate"
        />
      </div>

      <div v-if="total > conversations.length" class="pagination">
        <button
          v-if="offset > 0"
          class="page-btn"
          @click="prevPage"
        >← 上一页</button>
        <span class="page-info">{{ offset + 1 }}-{{ Math.min(offset + limit, total) }} / {{ total }}</span>
        <button
          v-if="offset + limit < total"
          class="page-btn"
          @click="nextPage"
        >下一页 →</button>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useConversationStore } from '@/stores/conversation'
import { ElMessage } from 'element-plus'
import api from '@/api'
import ConversationCard from '@/components/conversations/ConversationCard.vue'

const store = useConversationStore()
const conversations = ref([])
const loading = ref(true)
const searchQuery = ref('')
const filterCharacter = ref(null)
const characters = ref([])
const total = ref(0)
const offset = ref(0)
const limit = 20
const totalConversations = ref(0)
const totalMessages = ref(0)
const recentCount = ref(0)

let debounceTimer = null

function debouncedSearch() {
  clearTimeout(debounceTimer)
  debounceTimer = setTimeout(() => {
    offset.value = 0
    doSearch()
  }, 300)
}

async function doSearch() {
  loading.value = true
  try {
    const params = new URLSearchParams()
    if (searchQuery.value) params.set('keyword', searchQuery.value)
    if (filterCharacter.value) params.set('character_id', filterCharacter.value)
    params.set('limit', limit)
    params.set('offset', offset.value)

    const result = await api.content.searchConversations(params)
    conversations.value = result.conversations
    total.value = result.total
  } catch {
    // silently ignore
  } finally {
    loading.value = false
  }
}

function clearSearch() {
  searchQuery.value = ''
  filterCharacter.value = null
  offset.value = 0
  doSearch()
}

function nextPage() {
  offset.value += limit
  doSearch()
}

function prevPage() {
  offset.value = Math.max(0, offset.value - limit)
  doSearch()
}

async function loadStats() {
  try {
    const stats = await api.content.conversationStats()
    totalConversations.value = stats.total_conversations
    totalMessages.value = stats.total_messages
    recentCount.value = stats.recent_conversations.length
  } catch {
    // silently ignore
  }
}

function getAvatarDisplay(conv) {
  if (conv.character_avatar_type === 'emoji' && conv.character_avatar) {
    return conv.character_avatar
  }
  return conv.character_name ? conv.character_name.charAt(0) : '?'
}

function getAvatarStyle(conv) {
  if (conv.character_avatar_type === 'image' && conv.character_avatar) {
    return { backgroundImage: `url(${conv.character_avatar})`, backgroundSize: 'cover', backgroundPosition: 'center' }
  }
  return {}
}

function handleTitleUpdate(id, title) {
  const conv = conversations.value.find(c => c.id === id)
  if (conv) conv.title = title
}

async function deleteConversation(id) {
  try {
    await store.delete(id)
    doSearch()
    ElMessage.success('对话已删除')
  } catch {
    ElMessage.error('删除失败')
  }
}

onMounted(async () => {
  try {
    const chars = await api.characters.getAll()
    characters.value = chars
  } catch {
    // silently ignore
  }
  await doSearch()
  await loadStats()
})

onUnmounted(() => {
  clearTimeout(debounceTimer)
})
</script>

<style scoped>
.conversations {
  min-height: 100vh;
  background: var(--color-bg);
}

.page-header {
  padding: 40px;
  background: var(--color-surface);
  border-bottom: 1px solid var(--color-border);
}

.back-link {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: var(--color-text-muted);
  text-decoration: none;
  transition: color 0.2s;
  margin-bottom: 16px;
}

.back-link:hover {
  color: var(--color-accent);
}

.header-title-group {
  margin-top: 12px;
}

.page-title {
  font-family: var(--font-display);
  font-size: 42px;
  font-weight: 600;
  color: var(--color-ink);
  margin-bottom: 4px;
}

.page-subtitle {
  font-size: 16px;
  color: var(--color-text-muted);
}

.conversations-content {
  padding: 24px 40px 48px;
  max-width: 900px;
  margin: 0 auto;
}

.search-bar {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
}

.search-input-wrapper {
  flex: 1;
  position: relative;
  display: flex;
  align-items: center;
}

.search-icon {
  position: absolute;
  left: 14px;
  font-size: 16px;
  color: var(--color-text-muted);
  pointer-events: none;
}

.search-input {
  width: 100%;
  padding: 12px 40px 12px 42px;
  border: 1px solid var(--color-border);
  border-radius: 8px;
  background: var(--color-surface);
  color: var(--color-ink);
  font-size: 15px;
  font-family: var(--font-body);
  outline: none;
  transition: border-color 0.2s;
}

.search-input:focus {
  border-color: var(--color-accent);
}

.clear-btn {
  position: absolute;
  right: 10px;
  background: none;
  border: none;
  cursor: pointer;
  color: var(--color-text-muted);
  font-size: 16px;
  padding: 4px 8px;
}

.clear-btn:hover {
  color: var(--color-ink);
}

.filter-group {
  display: flex;
  gap: 8px;
}

.filter-select {
  padding: 12px 16px;
  border: 1px solid var(--color-border);
  border-radius: 8px;
  background: var(--color-surface);
  color: var(--color-ink);
  font-size: 14px;
  font-family: var(--font-body);
  outline: none;
  cursor: pointer;
  min-width: 120px;
}

.filter-select:focus {
  border-color: var(--color-accent);
}

.stats-bar {
  display: flex;
  gap: 24px;
  margin-bottom: 24px;
  padding: 16px 20px;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 8px;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.stat-value {
  font-family: var(--font-display);
  font-size: 24px;
  font-weight: 600;
  color: var(--color-ink);
}

.stat-label {
  font-size: 12px;
  color: var(--color-text-muted);
}

.loading-state,
.empty-state {
  text-align: center;
  padding: 80px 40px;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 3px solid var(--color-border);
  border-top-color: var(--color-accent);
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 20px;
}

.empty-icon {
  font-size: 64px;
  color: var(--color-border);
  margin-bottom: 24px;
}

.empty-state h3 {
  font-family: var(--font-display);
  font-size: 28px;
  color: var(--color-ink);
  margin-bottom: 12px;
}

.empty-state p {
  color: var(--color-text-muted);
  margin-bottom: 32px;
}

.btn-primary {
  display: inline-block;
  font-family: var(--font-body);
  font-size: 15px;
  font-weight: 600;
  padding: 14px 28px;
  background: var(--color-ink);
  color: white;
  text-decoration: none;
  border-radius: 4px;
  border: none;
  cursor: pointer;
  transition: all 0.3s ease;
}

.btn-primary:hover {
  background: var(--color-accent);
}

.conversations-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 16px;
  margin-top: 24px;
  padding: 16px 0;
}

.page-btn {
  font-family: var(--font-body);
  font-size: 14px;
  font-weight: 600;
  padding: 8px 20px;
  border: 1px solid var(--color-border);
  border-radius: 4px;
  background: var(--color-surface);
  color: var(--color-ink);
  cursor: pointer;
  transition: all 0.2s;
}

.page-btn:hover {
  border-color: var(--color-accent);
  color: var(--color-accent);
}

.page-info {
  font-size: 14px;
  color: var(--color-text-muted);
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

@media (max-width: 768px) {
  .page-header {
    padding: 24px;
  }

  .conversations-content {
    padding: 16px;
  }

  .search-bar {
    flex-direction: column;
  }

  .stats-bar {
    gap: 16px;
    padding: 12px;
  }
}
</style>