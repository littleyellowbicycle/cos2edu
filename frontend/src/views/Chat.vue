<template>
  <div class="chat" :class="{ 'chat-with-sidebar': showSidebar }">
    <header class="chat-header">
      <button class="btn-back" @click="$router.push('/conversations')" aria-label="返回对话列表">
        <span>←</span>
      </button>
      <div class="header-info">
        <h1 class="chat-title">{{ characterName || '对话' }}</h1>
        <p class="chat-status" aria-live="polite">
          <span v-if="materialTitle">教材: {{ materialTitle }}</span>
          <span v-else-if="isTyping">正在思考...</span>
          <span v-else-if="sending">发送中...</span>
          <span v-else>苏格拉底式对话中</span>
          <span v-if="currentScene" class="scene-badge">{{ currentScene }}</span>
          <span v-if="moodLabel" class="mood-badge" :class="moodBadgeClass">{{ moodLabel }}</span>
        </p>
      </div>
      <button class="btn-sidebar" @click="showSidebar = !showSidebar" :aria-expanded="showSidebar">
        {{ showSidebar ? '隐藏' : '显示' }}历史
      </button>
    </header>

    <div class="chat-container">
      <main class="chat-main">
        <div class="messages" ref="messagesContainer" role="log" aria-live="polite" aria-label="对话消息">
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
            @copy="copyMessage(index, msg.content)"
          />
          
          <TypingIndicator
            v-if="isTyping"
            :character-name="characterName"
            :character-avatar="characterAvatar"
            :character-avatar-type="characterAvatarType"
          />

          <QuizForm @interact="handleQuizInteract" />

          <Transition name="event-slide">
            <div v-if="activeEventNotification" class="event-notification" role="alert" aria-live="assertive">
              <div class="event-notification-header">
                <span class="event-notification-icon">&#x1F4E2;</span>
                <h4>{{ activeEventNotification.title }}</h4>
                <button class="event-close" @click="dismissEvent" aria-label="关闭通知">&times;</button>
              </div>
              <p class="event-description">{{ activeEventNotification.description }}</p>
              <div v-if="activeEventNotification.options && activeEventNotification.options.length > 0" class="event-options">
                <button
                  v-for="opt in activeEventNotification.options"
                  :key="opt.id"
                  class="event-option-btn"
                  @click="chooseNarrativeOption(opt.id)"
                >
                  {{ opt.text }}
                </button>
              </div>
              <div v-else class="event-actions">
                <button class="event-dismiss-btn" @click="dismissEvent">知道了</button>
              </div>
            </div>
          </Transition>
        </div>

        <div class="input-area">
          <div class="input-wrapper">
            <label for="message-input" class="visually-hidden">输入消息</label>
            <textarea
              id="message-input"
              v-model="inputMessage"
              placeholder="输入你的问题... (Ctrl+Enter 发送)"
              @keydown.enter.ctrl="sendMessage"
              @keydown.enter.exact.prevent="sendMessage"
              rows="1"
              ref="inputTextarea"
              :disabled="sending"
              aria-describedby="input-hint"
            ></textarea>
            <button 
              class="btn-send" 
              @click="sendMessage" 
              :disabled="!inputMessage.trim() || sending"
              aria-label="发送消息"
            >
              <span v-if="!sending">发送</span>
              <span v-else class="sending-dots" aria-label="发送中">...</span>
            </button>
          </div>
          <p id="input-hint" class="input-hint">按 Enter 发送，Ctrl+Enter 换行</p>
        </div>
      </main>

      <aside v-if="showSidebar" class="chat-sidebar">
        <h3 class="sidebar-title">对话历史</h3>
        <div class="history-list">
          <button 
            v-for="(conv, index) in conversationHistory" 
            :key="conv.id"
            class="history-item"
            :class="{ active: conv.id === conversationId }"
            @click="loadConversation(conv)"
          >
            <span class="history-title">{{ conv.title || `对话 ${index + 1}` }}</span>
            <span class="history-date">{{ formatDate(conv.created_at) }}</span>
          </button>
        </div>
      </aside>
    </div>
    <DynamicRenderer slot-name="overlay" />
    <DynamicRenderer slot-name="panel" />
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick, watch, computed } from 'vue'
import { useRoute } from 'vue-router'
import api from '@/api'
import { ElMessage } from 'element-plus'
import { useWebSocket } from '@/composables/useWebSocket'
import { useNarrativeStore } from '@/stores/narrative'
import DynamicRenderer from '@/components/generative/DynamicRenderer.vue'
import QuizForm from '@/components/generative/QuizForm.vue'
import MessageBubble from '@/components/chat/MessageBubble.vue'
import TypingIndicator from '@/components/chat/TypingIndicator.vue'

function copyMessage(idx, content) {
  navigator.clipboard.writeText(content).then(() => {
    copiedMsgIdx.value = idx
    setTimeout(() => { copiedMsgIdx.value = -1 }, 1500)
  })
}

const route = useRoute()
const ws = useWebSocket()
const narrativeStore = useNarrativeStore()
const messages = ref([])
const inputMessage = ref('')
const sending = ref(false)
const isTyping = ref(false)
const messagesContainer = ref(null)
const inputTextarea = ref(null)
const copiedMsgIdx = ref(-1)
const showSidebar = ref(false)
const conversationId = ref(route.query.conversationId || null)
const characterName = ref('')
const characterAvatar = ref('')
const characterAvatarType = ref('emoji')
const characterId = ref('')
const conversationHistory = ref([])
const loading = ref(false)
const materialTitle = ref('')

const characterMood = computed(() => {
  const cid = characterId.value
  if (cid && narrativeStore.characters[cid]) {
    return narrativeStore.characters[cid].mood
  }
  return null
})

const characterExpression = computed(() => {
  const cid = characterId.value
  if (cid && narrativeStore.characters[cid]) {
    return narrativeStore.characters[cid].lastExpression || ''
  }
  return ''
})

const moodLabel = computed(() => {
  const m = characterMood.value
  if (m === null) return ''
  if (m > 0.85) return '非常开心'
  if (m > 0.7) return '温和专注'
  if (m > 0.5) return '平静'
  if (m > 0.3) return '有些严肃'
  return '有些担心'
})

const moodBadgeClass = computed(() => {
  const m = characterMood.value
  if (m === null) return ''
  if (m > 0.7) return 'mood-positive'
  if (m > 0.5) return 'mood-neutral'
  return 'mood-negative'
})

const currentScene = computed(() => narrativeStore.world.sceneName || '')

let wsUnsubFns = []

const activeEventNotification = ref(null)

function handleQuizInteract(eventData) {
  if (eventData?.action === 'submit' && eventData?.value) {
    const { pointId, answers } = eventData.value
    ws.submitAssessment(pointId, characterId.value, answers, conversationId.value)
  }
}

function dismissEvent() {
  activeEventNotification.value = null
}

function chooseNarrativeOption(optionId) {
  if (!activeEventNotification.value) return
  ws.send({
    type: 'action.choose',
    payload: {
      event_id: activeEventNotification.value.event_id,
      option_id: optionId,
    },
  })
  activeEventNotification.value = null
}

onMounted(async () => {
  characterId.value = route.params.id
  if (conversationId.value) {
    loading.value = true
    await loadConversation({ id: conversationId.value })
    loading.value = false
  }
  
  try {
    const character = await api.characters.getById(characterId.value)
    characterName.value = character.name
    characterAvatar.value = character.avatar || ''
    characterAvatarType.value = character.avatar_type || 'emoji'
  } catch (e) {
    console.error(e)
  }
  
  try {
    const convs = await api.conversations.getAll()
    conversationHistory.value = convs
  } catch (e) {
    console.error(e)
  }

  ws.connect()
  wsUnsubFns.push(ws.on('chat.token', (msg) => {
    const content = msg.content || ''
    if (content.startsWith('data:')) return
    const lastIdx = messages.value.length - 1
    if (lastIdx >= 0 && messages.value[lastIdx].role === 'assistant') {
      messages.value[lastIdx].content += content
    }
  }))
  wsUnsubFns.push(ws.on('chat.complete', () => {
    sending.value = false
    isTyping.value = false
  }))
  wsUnsubFns.push(ws.on('error', (msg) => {
    sending.value = false
    isTyping.value = false
    const errContent = msg.content || msg.payload?.content || '通信错误'
    if (errContent.includes('API Key') || errContent.includes('模型')) {
      ElMessage({
        type: 'warning',
        message: '请先配置 AI 模型。点击右上角「设置」进行配置。',
        duration: 0,
        showClose: true
      })
    } else {
      ElMessage.error(errContent)
    }
  }))
  wsUnsubFns.push(ws.on('emotion.update', (msg) => {
    narrativeStore.updateEmotion(msg.payload)
  }))
  wsUnsubFns.push(ws.on('scene.change', (msg) => {
    narrativeStore.updateSceneChange(msg.payload)
  }))
  wsUnsubFns.push(ws.on('event.trigger', (msg) => {
    if (msg.payload) {
      narrativeStore.activeEvents.push(msg.payload)
      activeEventNotification.value = msg.payload
    }
  }))
  wsUnsubFns.push(ws.on('narrative.options', (msg) => {
    if (msg.payload) {
      narrativeStore.narrativeChoices = msg.payload
      activeEventNotification.value = msg.payload
    }
  }))
  wsUnsubFns.push(ws.on('event.resolved', () => {
    activeEventNotification.value = null
    narrativeStore.narrativeChoices = null
  }))
  wsUnsubFns.push(ws.on('state.full', (msg) => {
    narrativeStore.overwriteState(msg.payload)
  }))
  wsUnsubFns.push(ws.on('assessment.start', (msg) => {
    const p = msg.payload
    messages.value.push({
      role: 'assistant',
      content: p.message || '让我们来做个小测验，检验一下你的理解。',
      timestamp: new Date(),
    })
  }))
  wsUnsubFns.push(ws.on('assessment.quiz', (msg) => {
    narrativeStore.setAssessment(msg.payload)
  }))
  wsUnsubFns.push(ws.on('assessment.result', (msg) => {
    narrativeStore.setAssessmentResult(msg.payload)
  }))
  wsUnsubFns.push(ws.on('time.advanced', (msg) => {
    narrativeStore.applyTimeAdvance(msg.payload)
  }))

  narrativeStore.setConnectionState(ws.connectionState.value)
  watch(() => ws.connectionState.value, (state) => {
    narrativeStore.setConnectionState(state)
  })
})

onUnmounted(() => {
  wsUnsubFns.forEach(fn => fn())
  wsUnsubFns = []
  ws.disconnect()
})

watch(messages, async () => {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
}, { deep: true })

async function sendMessage() {
  if (!inputMessage.value.trim() || sending.value) return

  const userMessage = inputMessage.value.trim()
  inputMessage.value = ''
  
  messages.value.push({
    role: 'user',
    content: userMessage,
    timestamp: new Date()
  })
  
  sending.value = true
  isTyping.value = true

  try {
    if (!conversationId.value) {
      const conv = await api.conversations.create({
        character_id: characterId.value,
        title: `与 ${characterName.value} 的对话`
      })
      conversationId.value = conv.id
    }

    messages.value.push({ role: 'assistant', content: '', timestamp: new Date() })
    isTyping.value = true

    ws.sendChat(conversationId.value, userMessage, characterId.value)
  } catch (e) {
    let errorMsg = e.message || '发送失败'
    
    if (errorMsg.includes('API Key') || errorMsg.includes('模型')) {
      errorMsg = '请先配置 AI 模型。点击右上角「设置」进行配置。'
      ElMessage({
        type: 'warning',
        message: errorMsg,
        duration: 0,
        showClose: true
      })
    } else {
      ElMessage.error(errorMsg)
    }
    messages.value.pop()
    sending.value = false
    isTyping.value = false
  }
}

async function loadConversation(conv) {
  conversationId.value = conv.id
  messages.value = []
  
  try {
    const convData = await api.conversations.getById(conv.id)
    if (convData.material) {
      materialTitle.value = convData.material.title
    }
    if (convData.character) {
      characterName.value = convData.character.name
      characterAvatar.value = convData.character.avatar || ''
      characterAvatarType.value = convData.character.avatar_type || 'emoji'
    }
    messages.value = convData.messages || []
  } catch (e) {
    console.error('Failed to load conversation details:', e)
  }
}

function formatDate(dateStr) {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN', {
    month: 'short',
    day: 'numeric'
  })
}
</script>

<style scoped>
.chat {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--color-bg);
}

.chat-header {
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 20px 32px;
  background: var(--color-surface);
  border-bottom: 1px solid var(--color-border);
}

.btn-back {
  width: 44px;
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  border-radius: 50%;
  cursor: pointer;
  transition: all 0.2s ease;
  font-size: 18px;
}

.btn-back:hover {
  background: var(--color-ink);
  color: white;
  border-color: var(--color-ink);
}

.header-info {
  flex: 1;
}

.chat-title {
  font-family: var(--font-display);
  font-size: 24px;
  font-weight: 600;
  color: var(--color-ink);
}

.chat-status {
  font-size: 14px;
  color: var(--color-text-muted);
}

.scene-badge {
  display: inline-block;
  font-size: 12px;
  padding: 2px 8px;
  margin-left: 8px;
  background: var(--color-bg-warm);
  border: 1px solid var(--color-border);
  border-radius: 12px;
  color: var(--color-text);
}

.mood-badge {
  display: inline-block;
  font-size: 12px;
  padding: 2px 8px;
  margin-left: 6px;
  border-radius: 12px;
}

.mood-positive {
  background: #e8f5e9;
  color: #2e7d32;
  border: 1px solid #a5d6a7;
}

.mood-neutral {
  background: #fff3e0;
  color: #e65100;
  border: 1px solid #ffcc80;
}

.mood-negative {
  background: #ffebee;
  color: #c62828;
  border: 1px solid #ef9a9a;
}

.event-notification {
  margin: 16px 0;
  padding: 20px;
  background: linear-gradient(135deg, #fff8e1 0%, #fff3e0 100%);
  border: 2px solid #ff9800;
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
  color: #e65100;
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
  border: 2px solid #ff9800;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  color: #e65100;
}

.event-option-btn:hover {
  background: #fff3e0;
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
  background: #ff9800;
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

.btn-sidebar {
  font-family: var(--font-body);
  font-size: 14px;
  font-weight: 600;
  padding: 10px 20px;
  background: transparent;
  color: var(--color-text-muted);
  border: 1px solid var(--color-border);
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-sidebar:hover {
  border-color: var(--color-ink);
  color: var(--color-ink);
}

.chat-container {
  flex: 1;
  display: flex;
  overflow: hidden;
}

.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

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

.visually-hidden {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

.input-area {
  padding: 20px 32px 24px;
  background: var(--color-surface);
  border-top: 1px solid var(--color-border);
}

.input-wrapper {
  display: flex;
  gap: 12px;
  align-items: stretch;
  position: relative;
}

.input-wrapper textarea {
  flex: 1;
  font-family: var(--font-body);
  font-size: 15px;
  line-height: 1.5;
  padding: 14px 18px;
  border: 1px solid var(--color-border);
  border-radius: 8px;
  background: var(--color-bg);
  color: var(--color-text);
  resize: none;
  min-height: 52px;
  max-height: 150px;
  transition: border-color 0.2s;
  pointer-events: auto;
  z-index: 1;
  width: 100%;
}

.input-wrapper textarea:focus {
  outline: none;
  border-color: var(--color-accent);
}

.input-wrapper textarea::placeholder {
  color: var(--color-text-muted);
}

.input-wrapper textarea:disabled {
  background: var(--color-bg-warm);
  cursor: not-allowed;
}

.btn-send {
  height: 52px;
  padding: 0 28px;
  font-family: var(--font-body);
  font-size: 15px;
  font-weight: 600;
  background: var(--color-ink);
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-send:hover:not(:disabled) {
  background: var(--color-accent);
}

.btn-send:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.sending-dots {
  animation: pulse 1s infinite;
}

.input-hint {
  font-size: 12px;
  color: var(--color-text-muted);
  margin-top: 8px;
  text-align: center;
}

.chat-sidebar {
  width: 300px;
  background: var(--color-surface);
  border-left: 1px solid var(--color-border);
  display: flex;
  flex-direction: column;
}

.sidebar-title {
  font-family: var(--font-display);
  font-size: 18px;
  font-weight: 600;
  color: var(--color-ink);
  padding: 20px 24px;
  border-bottom: 1px solid var(--color-border);
}

.history-list {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
}

.history-item {
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 4px;
  padding: 14px 16px;
  background: transparent;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s ease;
  text-align: left;
}

.history-item:hover {
  background: var(--color-bg);
}

.history-item.active {
  background: var(--color-bg-warm);
  border-left: 3px solid var(--color-accent);
}

.history-title {
  font-size: 14px;
  font-weight: 500;
  color: var(--color-text);
}

.history-date {
  font-size: 12px;
  color: var(--color-text-muted);
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

@media (max-width: 768px) {
  .chat-header {
    padding: 16px 20px;
  }
  
  .messages {
    padding: 20px;
  }
  
  .message {
    max-width: 90%;
  }
  
  .input-area {
    padding: 16px 20px;
  }
  
  .chat-sidebar {
    position: fixed;
    right: 0;
    top: 0;
    bottom: 0;
    z-index: 100;
    box-shadow: var(--shadow-lg);
  }
}
</style>