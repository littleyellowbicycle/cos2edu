<template>
  <div class="message" :class="message.role" role="article">
    <div class="message-avatar" :style="avatarStyle" :aria-label="avatarLabel">
      {{ avatarDisplay }}
    </div>
    <div class="message-content">
      <MarkdownContent :content="message.content" :streaming="isStreaming" />
      <DynamicRenderer v-if="message.role === 'assistant'" slot-name="inline" />
      <div class="message-footer" v-if="message.role === 'assistant'">
        <button class="msg-action-btn" title="复制消息" @click="$emit('copy')">
          <span v-if="isCopied">✓</span>
          <span v-else>📋</span>
        </button>
      </div>
      <div class="message-time" v-if="message.timestamp">
        {{ formatTime(message.timestamp) }} · {{ countWords(message.content) }} 字
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import MarkdownContent from './MarkdownContent.vue'
import DynamicRenderer from '@/components/generative/DynamicRenderer.vue'

const props = defineProps({
  message: { type: Object, required: true },
  isStreaming: { type: Boolean, default: false },
  isCopied: { type: Boolean, default: false },
  characterName: { type: String, default: '' },
  characterAvatar: { type: String, default: '' },
  characterAvatarType: { type: String, default: 'emoji' },
})

defineEmits(['copy'])

const avatarStyle = computed(() => {
  if (props.message.role === 'assistant' && props.characterAvatarType === 'image' && props.characterAvatar) {
    const avatarUrl = props.characterAvatar.startsWith('/') || props.characterAvatar.startsWith('data:') || props.characterAvatar.startsWith('http')
      ? props.characterAvatar
      : `/api/v1/crud/avatars/${props.characterAvatar}`
    return { backgroundImage: `url(${avatarUrl})`, backgroundSize: 'cover', backgroundPosition: 'center' }
  }
  return {}
})

const avatarDisplay = computed(() => {
  if (props.message.role === 'user') return '❧'
  if (props.characterAvatarType === 'emoji' && props.characterAvatar) {
    return props.characterAvatar
  }
  if (props.characterAvatarType === 'image') {
    return ''
  }
  return props.characterName ? props.characterName.charAt(0) : '?'
})

const avatarLabel = computed(() => props.message.role === 'user' ? '❧' : props.characterName)

function countWords(text) {
  const clean = text.replace(/<[^>]*>/g, '').trim()
  if (!clean) return 0
  return clean.length
}

function formatTime(date) {
  return new Date(date).toLocaleTimeString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit'
  })
}
</script>

<style scoped>
.message {
  display: flex;
  gap: 16px;
  max-width: 80%;
  animation: fadeIn 0.3s ease;
}

.message.user {
  align-self: flex-end;
  flex-direction: row-reverse;
}

.message.assistant {
  align-self: flex-start;
}

.message-avatar {
  width: 40px;
  height: 40px;
  min-width: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: var(--font-display);
  font-size: 14px;
  font-weight: 600;
}

.message.user .message-avatar {
  background: var(--color-accent);
  color: white;
}

.message.assistant .message-avatar {
  background: var(--color-accent);
  color: white;
}

.message-content {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.message-text {
  line-height: 1.8;
  font-size: 15px;
  color: var(--color-ink);
  word-wrap: break-word;
  overflow-wrap: break-word;
}

.message-footer {
  display: flex;
  gap: 4px;
  margin-top: 8px;
  opacity: 0;
  transition: opacity 0.2s;
}

.message-content:hover .message-footer {
  opacity: 1;
}

.msg-action-btn {
  background: none;
  border: 1px solid var(--color-border);
  border-radius: 4px;
  padding: 2px 8px;
  font-size: 12px;
  cursor: pointer;
  color: var(--color-text-muted);
  transition: all 0.15s;
}

.msg-action-btn:hover {
  background: var(--color-bg-warm);
  color: var(--color-ink);
}

.message-time {
  font-size: 12px;
  color: var(--color-text-muted);
}

.message.user .message-time {
  text-align: right;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
