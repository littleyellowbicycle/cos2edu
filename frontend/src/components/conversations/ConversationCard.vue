<template>
  <article
    class="conversation-card"
    :style="{ animationDelay: `${index * 60}ms` }"
    @click="continueChat"
  >
    <div class="conversation-info">
      <div class="conv-avatar" :style="avatarStyle">{{ avatarDisplay }}</div>
      <div class="conv-details">
        <div class="conv-title-wrapper" @click.stop="startEditTitle" v-if="!isEditing">
          <h3 class="conv-title">{{ conversation.title || '未命名对话' }}</h3>
          <span class="edit-icon">&#9998;</span>
        </div>
        <div class="conv-title-edit" v-else>
          <input
            v-model="editingTitle"
            @keyup.enter="saveTitle"
            @keyup.escape="cancelEditTitle"
            @blur="saveTitle"
            ref="titleInput"
            class="title-input"
          />
        </div>
        <p class="conv-meta">
          <span class="conv-character">{{ conversation.character_name || '未知角色' }}</span>
          <span class="conv-date">{{ formatDate(conversation.updated_at || conversation.created_at) }}</span>
        </p>
        <p v-if="conversation.message_count != null" class="conv-msg-count">{{ conversation.message_count }} 条消息</p>
      </div>
    </div>
    <div class="conversation-actions">
      <button class="btn-continue" @click.stop="continueChat">继续</button>
      <button class="btn-delete" @click.stop="$emit('delete', conversation.id)">删除</button>
    </div>
  </article>
</template>

<script setup>
import { ref, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { useConversationStore } from '@/stores/conversation'

const props = defineProps({
  conversation: { type: Object, required: true },
  avatarDisplay: { type: String, default: '?' },
  avatarStyle: { type: Object, default: () => ({}) },
  index: { type: Number, default: 0 },
})

const emit = defineEmits(['delete', 'update-title'])

const router = useRouter()
const store = useConversationStore()

const isEditing = ref(false)
const editingTitle = ref('')
const titleInput = ref(null)

function startEditTitle() {
  isEditing.value = true
  editingTitle.value = props.conversation.title || ''
  nextTick(() => {
    titleInput.value?.focus()
  })
}

async function saveTitle() {
  if (!editingTitle.value.trim()) {
    cancelEditTitle()
    return
  }
  try {
    await store.update(props.conversation.id, { title: editingTitle.value.trim() })
    emit('update-title', props.conversation.id, editingTitle.value.trim())
  } catch (e) {
    console.error(e)
  }
  cancelEditTitle()
}

function cancelEditTitle() {
  isEditing.value = false
  editingTitle.value = ''
}

function continueChat() {
  router.push(`/chat/${props.conversation.character_id}?conversationId=${props.conversation.id}`)
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
    day: 'numeric',
  })
}
</script>

<style scoped>
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
  content: '\00b7';
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
}
</style>
