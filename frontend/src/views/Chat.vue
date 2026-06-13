<template>
  <div class="chat" :class="{ 'chat-with-sidebar': showSidebar }">
    <ChatHeader
      :character-name="characterName"
      :material-title="materialTitle"
      :is-typing="isTyping"
      :sending="sending"
      :current-scene="currentScene"
      :mood-label="moodLabel"
      :mood-badge-class="moodBadgeClass"
      :show-sidebar="showSidebar"
      @toggle-sidebar="showSidebar = !showSidebar"
    />

    <div class="chat-container">
      <main class="chat-main">
        <ChatMessages
          :messages="messages"
          :loading="loading"
          :is-typing="isTyping"
          :character-name="characterName"
          :character-avatar="characterAvatar"
          :character-avatar-type="characterAvatarType"
          :copied-msg-idx="copiedMsgIdx"
          :active-event-notification="activeEventNotification"
          @copy="handleCopy"
          @quiz-interact="handleQuizInteract"
          @dismiss-event="dismissEvent"
          @choose-narrative-option="chooseNarrativeOption"
        />

        <ChatInput v-model="inputMessage" :sending="sending" @send="handleChatInputSend" />
      </main>

      <ChatSidebar
        v-if="showSidebar"
        :conversation-history="conversationHistory"
        :conversation-id="conversationId"
        @select="loadConversation"
      />
    </div>
    <DynamicRenderer slot-name="overlay" />
    <DynamicRenderer slot-name="panel" />
    <DynamicRenderer slot-name="sidebar" />
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch, computed } from 'vue'
import { useRoute } from 'vue-router'
import api from '@/api'
import { ElMessage } from 'element-plus'
import { useWebSocket } from '@/composables/useWebSocket'
import { useNarrativeStore } from '@/stores/narrative'
import DynamicRenderer from '@/components/generative/DynamicRenderer.vue'
import ChatInput from '@/components/chat/ChatInput.vue'
import ChatHeader from '@/components/chat/ChatHeader.vue'
import ChatSidebar from '@/components/chat/ChatSidebar.vue'
import ChatMessages from '@/components/chat/ChatMessages.vue'

function handleCopy({ index, content }) {
  navigator.clipboard.writeText(content).then(() => {
    copiedMsgIdx.value = index
    setTimeout(() => { copiedMsgIdx.value = -1 }, 1500)
  }).catch(() => {})
}

const route = useRoute()
const ws = useWebSocket()
const narrativeStore = useNarrativeStore()
const messages = ref([])
const inputMessage = ref('')
const sending = ref(false)
const isTyping = ref(false)
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
  const stopWatch = watch(() => ws.connectionState.value, (state) => {
    narrativeStore.setConnectionState(state)
  })
  wsUnsubFns.push(stopWatch)
})

onUnmounted(() => {
  wsUnsubFns.forEach(fn => typeof fn === 'function' && fn())
  wsUnsubFns = []
  ws.disconnect()
})

async function handleChatInputSend() {
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

    if (!ws.connected.value) {
      ws.connect()
      await new Promise(resolve => {
        const unsub = ws.on('*', () => {
          if (ws.connected.value) {
            unsub()
            resolve()
          }
        })
        setTimeout(resolve, 5000)
      })
    }
    ws.sendChat(conversationId.value, userMessage, characterId.value)

    setTimeout(() => {
      if (sending.value) {
        sending.value = false
        isTyping.value = false
      }
    }, 30000)
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
</script>

<style scoped>
.chat {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--color-bg);
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
</style>