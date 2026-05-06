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
      <div v-if="loading" class="loading-state">
        <div class="loading-spinner"></div>
        <p>加载中...</p>
      </div>
      
      <div v-else-if="conversations.length === 0" class="empty-state">
        <div class="empty-icon">○</div>
        <h3>暂无对话</h3>
        <p>开始与 AI 角色对话，记录你的思考和探索</p>
        <router-link to="/characters" class="btn-primary">选择角色开始</router-link>
      </div>

      <div v-else class="conversations-list">
        <article 
          v-for="(conv, index) in conversations" 
          :key="conv.id" 
          class="conversation-card"
          :style="{ animationDelay: `${index * 60}ms` }"
        >
          <div class="conversation-info">
            <div class="conv-avatar">{{ conv.character_name?.charAt(0) || '?' }}</div>
            <div class="conv-details">
              <h3 class="conv-title">{{ conv.title || '未命名对话' }}</h3>
              <p class="conv-meta">
                <span class="conv-character">{{ conv.character_name || '未知角色' }}</span>
                <span class="conv-date">{{ formatDate(conv.created_at) }}</span>
              </p>
            </div>
          </div>
          <div class="conversation-actions">
            <button class="btn-continue" @click="continueChat(conv)">继续</button>
            <button class="btn-delete" @click="deleteConversation(conv.id)">删除</button>
          </div>
        </article>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useConversationStore } from '@/stores/conversation'
import { ElMessage } from 'element-plus'

const router = useRouter()
const store = useConversationStore()
const conversations = ref([])
const loading = ref(true)

onMounted(async () => {
  try {
    await store.fetchAll()
    conversations.value = store.conversations
  } finally {
    loading.value = false
  }
})

function continueChat(conversation) {
  router.push(`/chat/${conversation.character_id}?conversationId=${conversation.id}`)
}

async function deleteConversation(id) {
  try {
    await store.delete(id)
    conversations.value = store.conversations
    ElMessage.success('对话已删除')
  } catch (e) {
    ElMessage.error('删除失败')
  }
}

function formatDate(dateStr) {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  })
}
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
  padding: 48px 40px;
  max-width: 900px;
  margin: 0 auto;
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
  transition: all 0.3s ease;
}

.btn-primary:hover {
  background: var(--color-accent);
}

.conversations-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.conversation-card {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 24px 28px;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 8px;
  transition: all 0.3s ease;
  animation: fadeInUp 0.5s ease-out both;
}

.conversation-card:hover {
  transform: translateX(4px);
  border-left: 3px solid var(--color-accent);
  box-shadow: var(--shadow-sm);
}

.conversation-info {
  display: flex;
  align-items: center;
  gap: 20px;
}

.conv-avatar {
  width: 52px;
  height: 52px;
  background: linear-gradient(135deg, var(--color-accent-light) 0%, var(--color-accent) 100%);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: var(--font-display);
  font-size: 22px;
  font-weight: 600;
  color: white;
}

.conv-details {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.conv-title {
  font-family: var(--font-display);
  font-size: 20px;
  font-weight: 600;
  color: var(--color-ink);
}

.conv-meta {
  display: flex;
  gap: 16px;
  font-size: 14px;
  color: var(--color-text-muted);
}

.conv-character {
  position: relative;
}

.conv-character::after {
  content: '·';
  margin-left: 16px;
}

.conversation-actions {
  display: flex;
  gap: 12px;
}

.conversation-actions button {
  font-family: var(--font-body);
  font-size: 14px;
  font-weight: 600;
  padding: 10px 20px;
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
    padding: 24px;
  }
  
  .conversation-card {
    flex-direction: column;
    align-items: flex-start;
    gap: 20px;
  }
  
  .conversation-actions {
    width: 100%;
  }
  
  .conversation-actions button {
    flex: 1;
  }
}
</style>