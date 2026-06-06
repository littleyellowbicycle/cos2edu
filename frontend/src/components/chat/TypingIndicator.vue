<template>
  <div class="message assistant typing" role="status">
    <div class="message-avatar" :style="avatarStyle" aria-hidden="true">{{ avatarDisplay }}</div>
    <div class="message-content">
      <div class="message-text typing-indicator" aria-label="正在输入">
        <span></span><span></span><span></span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  characterName: { type: String, default: '' },
  characterAvatar: { type: String, default: '' },
  characterAvatarType: { type: String, default: 'emoji' },
})

const avatarStyle = computed(() => {
  if (props.characterAvatarType === 'image' && props.characterAvatar) {
    const avatarUrl = props.characterAvatar.startsWith('/') || props.characterAvatar.startsWith('data:') || props.characterAvatar.startsWith('http')
      ? props.characterAvatar
      : `/api/v1/crud/avatars/${props.characterAvatar}`
    return { backgroundImage: `url(${avatarUrl})`, backgroundSize: 'cover', backgroundPosition: 'center' }
  }
  return {}
})

const avatarDisplay = computed(() => {
  if (props.characterAvatarType === 'emoji' && props.characterAvatar) {
    return props.characterAvatar
  }
  if (props.characterAvatarType === 'image') {
    return ''
  }
  return props.characterName ? props.characterName.charAt(0) : '?'
})
</script>

<style scoped>
.message {
  display: flex;
  gap: 16px;
  max-width: 80%;
  animation: fadeIn 0.3s ease;
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

.typing-indicator {
  display: flex;
  gap: 4px;
  padding: 20px 24px;
}

.typing-indicator span {
  width: 8px;
  height: 8px;
  background: var(--color-text-muted);
  border-radius: 50%;
  animation: typing 1.4s infinite;
}

.typing-indicator span:nth-child(2) {
  animation-delay: 0.2s;
}

.typing-indicator span:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

@keyframes typing {
  0%, 60%, 100% { transform: translateY(0); }
  30% { transform: translateY(-4px); }
}
</style>
