<template>
  <div class="messages" ref="messagesContainer" role="log" aria-live="polite" aria-label="对话消息" @scroll="onScroll">
    <div v-if="messages.length === 0 && !loading" class="welcome-message">
      <div class="welcome-icon" aria-hidden="true">❧</div>
      <h2>开始探索</h2>
      <p>输入你的问题，开启苏格拉底式对话</p>
    </div>

    <div v-if="loading" class="loading-messages">
      <div class="loading-spinner"></div>
      <p>加载对话历史...</p>
    </div>

    <MessageBubble
      v-for="(msg, index) in messages"
      :key="index"
      :message="msg"
      :is-streaming="isTyping && index === messages.length - 1 && msg.role === 'assistant'"
      :is-copied="copiedMsgIdx === index"
      :character-name="characterName"
      :character-avatar="characterAvatar"
      :character-avatar-type="characterAvatarType"
      @copy="$emit('copy', { index, content: msg.content })"
    />

    <TypingIndicator
      v-if="isTyping && !hasStreamingAssistant"
      :character-name="characterName"
      :character-avatar="characterAvatar"
      :character-avatar-type="characterAvatarType"
    />

    <QuizForm @interact="$emit('quizInteract', $event)" />

    <Transition name="event-slide">
      <div v-if="activeEventNotification" class="event-notification" role="alert" aria-live="assertive">
        <div class="event-notification-header">
          <span class="event-notification-icon">&#x1F4E2;</span>
          <h4>{{ activeEventNotification.title }}</h4>
          <button class="event-close" @click="$emit('dismissEvent')" aria-label="关闭通知">&times;</button>
        </div>
        <p class="event-description">{{ activeEventNotification.description }}</p>
        <div v-if="activeEventNotification.options && activeEventNotification.options.length > 0" class="event-options">
          <button
            v-for="opt in activeEventNotification.options"
            :key="opt.id"
            class="event-option-btn"
            @click="$emit('chooseNarrativeOption', opt.id)"
          >
            {{ opt.text }}
          </button>
        </div>
        <div v-else class="event-actions">
          <button class="event-dismiss-btn" @click="$emit('dismissEvent')">知道了</button>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue'
import MessageBubble from '@/components/chat/MessageBubble.vue'
import TypingIndicator from '@/components/chat/TypingIndicator.vue'
import QuizForm from '@/components/generative/QuizForm.vue'

const props = defineProps({
  messages: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
  isTyping: { type: Boolean, default: false },
  characterName: { type: String, default: '' },
  characterAvatar: { type: String, default: '' },
  characterAvatarType: { type: String, default: 'emoji' },
  copiedMsgIdx: { type: Number, default: -1 },
  activeEventNotification: { type: Object, default: null },
})

defineEmits(['copy', 'quizInteract', 'dismissEvent', 'chooseNarrativeOption'])

const messagesContainer = ref(null)
let stickyBottom = true

const hasStreamingAssistant = computed(() => {
  const len = props.messages.length
  return len > 0 && props.messages[len - 1].role === 'assistant'
})

function onScroll() {
  const el = messagesContainer.value
  if (!el) return
  const distanceFromBottom = el.scrollHeight - el.scrollTop - el.clientHeight
  stickyBottom = distanceFromBottom < 80
}

watch(() => props.messages, () => {
  nextTick(() => {
    if (!messagesContainer.value) return
    if (stickyBottom) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
}, { deep: true, flush: 'post' })
</script>

<style scoped>
.messages {
  flex: 1;
  overflow-y: auto;
  padding: 32px;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.welcome-message {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  color: var(--color-text-muted);
}

.welcome-icon {
  font-size: 64px;
  color: var(--color-accent);
  margin-bottom: 24px;
  opacity: 0.6;
}

.welcome-message h2 {
  font-family: var(--font-display);
  font-size: 32px;
  font-weight: 600;
  color: var(--color-ink);
  margin-bottom: 12px;
}

.loading-messages {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  color: var(--color-text-muted);
}

.loading-spinner {
  width: 32px;
  height: 32px;
  border: 3px solid var(--color-border);
  border-top-color: var(--color-accent);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

.event-notification {
  margin: 16px 0;
  padding: 20px;
    background: linear-gradient(135deg, var(--color-warning-bg) 0%, var(--color-warning-bg) 100%);
    border: 2px solid var(--color-warning-border);
    border-radius: 12px;
    box-shadow: 0 4px 16px rgba(255, 152, 0, 0.15);
}

.event-notification-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
}

.event-notification-header h4 {
  flex: 1;
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--color-warning);
}

.event-notification-icon {
  font-size: 20px;
}

.event-close {
  background: none;
  border: none;
  font-size: 20px;
  color: var(--color-text-muted);
  cursor: pointer;
  padding: 0 4px;
  line-height: 1;
}

.event-close:hover {
  color: var(--color-ink);
}

.event-description {
  margin: 8px 0 14px;
  font-size: 14px;
  line-height: 1.6;
  color: var(--color-text);
}

.event-options {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.event-option-btn {
  display: block;
  width: 100%;
  padding: 12px 16px;
  font-family: var(--font-body);
  font-size: 14px;
  font-weight: 600;
  text-align: left;
  background: white;
  border: 2px solid var(--color-warning-border);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  color: var(--color-warning);
}

.event-option-btn:hover {
  background: var(--color-warning-bg);
  border-color: #f57c00;
  transform: translateX(4px);
}

.event-actions {
  display: flex;
  justify-content: flex-end;
}

.event-dismiss-btn {
  padding: 8px 20px;
  font-family: var(--font-body);
  font-size: 13px;
  font-weight: 600;
  background: var(--color-warning-border);
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  transition: background 0.2s;
}

.event-dismiss-btn:hover {
  background: #f57c00;
}

.event-slide-enter-active {
  animation: eventSlideIn 0.4s ease;
}

.event-slide-leave-active {
  animation: eventSlideOut 0.3s ease;
}

@keyframes eventSlideIn {
  from {
    opacity: 0;
    transform: translateY(-20px) scale(0.95);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

@keyframes eventSlideOut {
  from {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
  to {
    opacity: 0;
    transform: translateY(-10px) scale(0.95);
  }
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

@media (max-width: 768px) {
  .messages {
    padding: 20px;
  }
}
</style>
