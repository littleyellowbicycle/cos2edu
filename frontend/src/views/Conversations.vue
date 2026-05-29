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
        <article
          v-for="(conv, index) in conversations"
          :key="conv.id"
          class="conversation-card"
          :style="{ animationDelay: `${index * 60}ms` }"
          @click="continueChat(conv)"
        >
          <div class="conversation-info">
            <div class="conv-avatar" :style="getAvatarStyle(conv)">{{ getAvatarDisplay(conv) }}</div>
            <div class="conv-details">
              <div class="conv-title-wrapper" @click.stop="startEditTitle(conv)" v-if="editingConvId !== conv.id">
                <h3 class="conv-title">{{ conv.title || '未命名对话' }}</h3>
                <span class="edit-icon">✎</span>
              </div>
              <div class="conv-title-edit" v-else>
                <input
                  v-model="editingTitle"
                  @keyup.enter="saveTitle(conv)"
                  @keyup.escape="cancelEditTitle"
                  @blur="saveTitle(conv)"
                  ref="titleInput"
                  class="title-input"
                />
              </div>
              <p class="conv-meta">
                <span class="conv-character">{{ conv.character_name || '未知角色' }}</span>
                <span class="conv-date">{{ formatDate(conv.updated_at || conv.created_at) }}</span>
              </p>
              <p v-if="conv.message_count != null" class="conv-msg-count">{{ conv.message_count }} 条消息</p>
            </div>
          </div>
          <div class="conversation-actions">
            <button class="btn-continue" @click.stop="continueChat(conv)">继续</button>
            <button class="btn-delete" @click.stop="deleteConversation(conv.id)">删除</button>
          </div>
        </article>
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
import { ref, onMounted, nextTick, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useConversationStore } from '@/stores/conversation'
import { ElMessage } from 'element-plus'
import api from '@/api'

const router = useRouter()
const store = useConversationStore()
const conversations = ref([])
const loading = ref(true)
const editingConvId = ref(null)
const editingTitle = ref('')
const titleInput = ref(null)
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
  } catch (e) {
    console.error(e)
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
  } catch (e) {
    console.error(e)
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

function startEditTitle(conv) {
  editingConvId.value = conv.id
  editingTitle.value = conv.title || ''
  nextTick(() => {
    if (titleInput.value) {
      titleInput.value.focus()
    }
  })
}

async function saveTitle(conv) {
  if (!editingTitle.value.trim()) {
    cancelEditTitle()
    return
  }
  try {
    await store.update(conv.id, { title: editingTitle.value.trim() })
    conv.title = editingTitle.value.trim()
  } catch (e) {
    console.error(e)
  }
  cancelEditTitle()
}

function cancelEditTitle() {
  editingConvId.value = null
  editingTitle.value = ''
}

function continueChat(conversation) {
  router.push(`/chat/${conversation.character_id}?conversationId=${conversation.id}`)
}

async function deleteConversation(id) {
  try {
    await store.delete(id)
    doSearch()
    ElMessage.success('对话已删除')
  } catch (e) {
    ElMessage.error('删除失败')
  }
}

function formatDate(dateStr) {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  const now = new Date()
  const diff = now - date
  const days = Math.floor(diff / (1000 * 60 * 60 * 24))
  if (days === 0) return '今天'
  if (days === 1) return '昨天'
  if (days < 7) return `${days}天前`
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  })
}

onMounted(async () => {
  try {
    const chars = await api.characters.getAll()
    characters.value = chars
  } catch (e) {
    console.error(e)
  }
  await doSearch()
  await loadStats()
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

.conversation-card {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 8px;
  transition: all 0.3s ease;
  animation: fadeInUp 0.5s ease-out both;
  cursor: pointer;
}

.conversation-card:hover {
  transform: translateX(4px);
  border-left: 3px solid var(--color-accent);
  box-shadow: var(--shadow-sm);
}

.conversation-info {
  display: flex;
  align-items: center;
  gap: 16px;
  flex: 1;
  min-width: 0;
}

.conv-title-wrapper {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}

.conv-title-wrapper:hover .edit-icon {
  opacity: 1;
}

.edit-icon {
  font-size: 14px;
  color: var(--color-text-muted);
  opacity: 0;
  transition: opacity 0.2s;
}

.conv-title-edit {
  display: flex;
  align-items: center;
}

.title-input {
  font-family: var(--font-display);
  font-size: 18px;
  font-weight: 600;
  color: var(--color-ink);
  padding: 4px 8px;
  border: 1px solid var(--color-accent);
  border-radius: 4px;
  background: var(--color-bg);
  outline: none;
  width: 200px;
}

.conv-avatar {
  width: 48px;
  height: 48px;
  background: linear-gradient(135deg, var(--color-accent-light) 0%, var(--color-accent) 100%);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: var(--font-display);
  font-size: 20px;
  font-weight: 600;
  color: white;
  flex-shrink: 0;
}

.conv-details {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.conv-title {
  font-family: var(--font-display);
  font-size: 18px;
  font-weight: 600;
  color: var(--color-ink);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.conv-meta {
  display: flex;
  gap: 12px;
  font-size: 13px;
  color: var(--color-text-muted);
}

.conv-character::after {
  content: '·';
  margin-left: 12px;
}

.conv-msg-count {
  font-size: 12px;
  color: var(--color-text-muted);
}

.conversation-actions {
  display: flex;
  gap: 8px;
  flex-shrink: 0;
  margin-left: 16px;
}

.conversation-actions button {
  font-family: var(--font-body);
  font-size: 13px;
  font-weight: 600;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-continue {
  background: var(--color-ink);
  color: white;
  border: none;
}

.btn-continue:hover {
  background: var(--color-accent);
}

.btn-delete {
  background: transparent;
  color: #C75050;
  border: 1px solid #E5C5C5;
}

.btn-delete:hover {
  background: #FEF2F2;
  border-color: #C75050;
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

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
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

  .conversation-card {
    flex-direction: column;
    align-items: flex-start;
    gap: 16px;
  }

  .conversation-actions {
    width: 100%;
    margin-left: 0;
  }

  .conversation-actions button {
    flex: 1;
  }

  .stats-bar {
    gap: 16px;
    padding: 12px;
  }
}
</style>