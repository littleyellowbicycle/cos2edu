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
          
          <div 
            v-for="(msg, index) in messages"
            :key="index"
            class="message"
            :class="msg.role"
            role="article"
          >
            <div class="message-avatar" :style="msg.role === 'assistant' ? getAvatarStyle() : {}" :aria-label="msg.role === 'user' ? '我' : characterName">
              {{ msg.role === 'user' ? '我' : getAvatarDisplay() }}
            </div>
            <div class="message-content">
              <div class="message-text" :class="{ 'is-streaming': isTyping && index === messages.length - 1 && msg.role === 'assistant' }" :ref="el => { if (el) messageRefs[msg.timestamp] = el }" v-html="getRenderedContent(msg)"></div>
              <div class="message-footer" v-if="msg.role === 'assistant'">
                <button class="msg-action-btn" title="复制消息" @click="copyMessage(index, msg.content)">
                  <span v-if="copiedMsgIdx === index">✓</span>
                  <span v-else>📋</span>
                </button>
              </div>
              <div class="message-time" v-if="msg.timestamp" aria-label="发送时间">
                {{ formatTime(msg.timestamp) }} · {{ countWords(msg.content) }} 字
              </div>
            </div>
          </div>
          
          <div v-if="isTyping" class="message assistant typing" role="status">
            <div class="message-avatar" :style="getAvatarStyle()" aria-hidden="true">{{ getAvatarDisplay() }}</div>
            <div class="message-content">
              <div class="message-text typing-indicator" aria-label="正在输入">
                <span></span><span></span><span></span>
              </div>
            </div>
          </div>

          <div v-if="assessmentQuiz" class="assessment-panel" role="region" aria-label="知识点测验">
            <div class="assessment-header">
              <span class="assessment-icon">&#9733;</span>
              <h3>知识点测验：{{ assessmentQuiz.point_name }}</h3>
            </div>
            <div v-for="(q, qi) in assessmentQuiz.quiz?.questions || []" :key="qi" class="assessment-question">
              <p class="question-text">{{ q.question_text }}</p>
              <div v-if="q.question_type === 'choice'" class="question-options">
                <label v-for="(opt, oi) in q.options" :key="oi" class="option-label"
                  :class="{ 'option-selected': assessmentAnswers[qi] === opt }">
                  <input type="radio" :name="`q-${qi}`" :value="opt" v-model="assessmentAnswers[qi]" />
                  {{ opt }}
                </label>
              </div>
              <div v-else class="question-open">
                <textarea v-model="assessmentAnswers[qi]" placeholder="请输入你的答案..." rows="2"></textarea>
              </div>
            </div>
            <button class="btn-submit-assessment" @click="submitAssessment" :disabled="!allQuestionsAnswered">
              提交答案
            </button>
          </div>

          <div v-if="assessmentResultData" class="assessment-result" role="region" aria-label="考核结果">
            <div class="result-header" :class="{ 'result-passed': assessmentResultData.passed, 'result-failed': !assessmentResultData.passed }">
              <span class="result-icon">{{ assessmentResultData.passed ? '&#10004;' : '&#10008;' }}</span>
              <h3>{{ assessmentResultData.passed ? '考核通过！' : '继续努力' }}</h3>
            </div>
            <p class="result-feedback">{{ assessmentResultData.feedback }}</p>
            <div class="result-stats">
              <span>掌握度: {{ Math.round(assessmentResultData.mastery_level * 100) }}%</span>
              <span>状态: {{ masteryStatusLabel }}</span>
            </div>
            <button class="btn-continue" @click="continueAfterAssessment">继续学习</button>
          </div>
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
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick, watch, computed } from 'vue'
import { useRoute } from 'vue-router'
import api from '@/api'
import { ElMessage } from 'element-plus'
import katex from 'katex'
import 'katex/dist/katex.min.css'
import mermaid from 'mermaid'
import { marked } from 'marked'
import { useWebSocket } from '@/composables/useWebSocket'
import { useNarrativeStore } from '@/stores/narrative'

marked.setOptions({
  breaks: true,
  gfm: true
})

function escapeHtml(text) {
  const div = document.createElement('div')
  div.textContent = text
  return div.innerHTML
}

function renderLatex(text) {
  text = text.replace(/\$\$(.*?)\$\$/gs, (_, math) => {
    try {
      return `<div class="math-block">${katex.renderToString(math, { displayMode: true, throwOnError: false })}</div>`
    } catch (e) {
      return `<div class="math-block math-error">${escapeHtml(math)}</div>`
    }
  })
  text = text.replace(/\$(.*?)\$/g, (_, math) => {
    try {
      return katex.renderToString(math, { displayMode: false, throwOnError: false })
    } catch (e) {
      return `<span class="math-error">${escapeHtml(math)}</span>`
    }
  })
  return text
}

function preprocessMarkdown(text) {
  text = renderLatex(text)
  return text
}

function copyMessage(idx, content) {
  navigator.clipboard.writeText(content).then(() => {
    copiedMsgIdx.value = idx
    setTimeout(() => { copiedMsgIdx.value = -1 }, 1500)
  })
}

function countWords(text) {
  const clean = text.replace(/<[^>]*>/g, '').trim()
  if (!clean) return 0
  return clean.length
}

async function renderMermaid(element) {
  const mermaidBlocks = element.querySelectorAll('pre.mermaid')
  for (const block of mermaidBlocks) {
    const code = block.textContent
    try {
      const id = 'mermaid-' + Math.random().toString(36).substr(2, 9)
      const { svg } = await mermaid.render(id, code)
      const wrapper = document.createElement('div')
      wrapper.className = 'mermaid-svg'
      wrapper.innerHTML = svg
      block.replaceWith(wrapper)
    } catch (e) {
      block.className = 'mermaid-error'
      block.textContent = code
    }
  }
}

function getRenderedContent(msg) {
  if (!msg.content) return ''
  let text = msg.content
  // 将 <think>...</think> 转为可折叠的思考过程
  text = text.replace(/<think>([\s\S]*?)<\/think>/gi, (_, thought) => {
    const preview = thought.trim().slice(0, 60)
    return `<details class="think-block"><summary>💭 思考过程 · ${preview}${thought.trim().length > 60 ? '…' : ''}</summary><div class="think-content">${marked.parse(preprocessMarkdown(thought.trim()))}</div></details>`
  })
  text = preprocessMarkdown(text)
  let html = marked.parse(text)
  return html
}

mermaid.initialize({
  startOnLoad: false,
  theme: 'default',
  securityLevel: 'loose'
})

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
const messageRefs = {}
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

const assessmentQuiz = computed(() => narrativeStore.currentAssessment)
const assessmentResultData = computed(() => narrativeStore.assessmentResult)
const assessmentAnswers = ref({})
const allQuestionsAnswered = computed(() => {
  if (!assessmentQuiz.value?.quiz?.questions) return false
  const questions = assessmentQuiz.value.quiz.questions
  return questions.every((q, i) => {
    const answer = assessmentAnswers.value[i]
    return answer && String(answer).trim().length > 0
  })
})

const masteryStatusLabel = computed(() => {
  const s = assessmentResultData.value?.status
  if (s === 'mastered') return '已掌握'
  if (s === 'learning') return '学习中'
  if (s === 'review_needed') return '需要复习'
  return s || ''
})

function submitAssessment() {
  const quiz = assessmentQuiz.value
  if (!quiz) return
  const answers = (quiz.quiz?.questions || []).map((q, i) => ({
    question: q,
    answer: assessmentAnswers.value[i] || '',
  }))
  ws.submitAssessment(quiz.point_id, characterId.value, answers, conversationId.value)
}

function continueAfterAssessment() {
  narrativeStore.clearAssessment()
  assessmentAnswers.value = {}
}

function getAvatarDisplay() {
  if (characterAvatarType.value === 'emoji' && characterAvatar.value) {
    return characterAvatar.value
  }
  return characterName.value ? characterName.value.charAt(0) : '?'
}

function getAvatarStyle() {
  if (characterAvatarType.value === 'image' && characterAvatar.value) {
    return { backgroundImage: `url(${characterAvatar.value})`, backgroundSize: 'cover', backgroundPosition: 'center' }
  }
  return {}
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
    }
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
    assessmentAnswers.value = {}
  }))
  wsUnsubFns.push(ws.on('assessment.result', (msg) => {
    narrativeStore.setAssessmentResult(msg.payload)
  }))
  wsUnsubFns.push(ws.on('time.advanced', (msg) => {
    narrativeStore.applyTimeAdvance(msg.payload)
  }))

  narrativeStore.setConnectionState(ws.connectionState.value)
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
    Object.values(messageRefs).forEach(el => {
      if (el) {
        renderMermaid(el)
      }
    })
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
    isTyping.value = false

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
  } catch (e) {
    console.error('Failed to load conversation details:', e)
  }
}

function formatTime(date) {
  return new Date(date).toLocaleTimeString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit'
  })
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

.assessment-panel {
  margin: 16px 0;
  padding: 20px;
  background: linear-gradient(135deg, #f3e5f5 0%, #e8eaf6 100%);
  border: 2px solid #7c4dff;
  border-radius: 12px;
}

.assessment-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 16px;
}

.assessment-header h3 {
  font-size: 18px;
  font-weight: 600;
  color: var(--color-ink);
  margin: 0;
}

.assessment-icon {
  font-size: 22px;
  color: #7c4dff;
}

.assessment-question {
  margin-bottom: 16px;
  padding: 12px;
  background: white;
  border-radius: 8px;
  border: 1px solid var(--color-border);
}

.question-text {
  font-weight: 500;
  margin-bottom: 10px;
  color: var(--color-ink);
}

.question-options {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.option-label {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  border: 1px solid var(--color-border);
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 14px;
}

.option-label:hover {
  border-color: #7c4dff;
  background: #f3e5f5;
}

.option-selected {
  border-color: #7c4dff;
  background: #e8daf5;
}

.question-open textarea {
  width: 100%;
  padding: 10px;
  border: 1px solid var(--color-border);
  border-radius: 6px;
  font-family: var(--font-body);
  font-size: 14px;
  resize: vertical;
}

.btn-submit-assessment {
  display: block;
  width: 100%;
  padding: 12px;
  font-family: var(--font-body);
  font-size: 15px;
  font-weight: 600;
  background: #7c4dff;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.2s;
}

.btn-submit-assessment:hover:not(:disabled) {
  background: #651fff;
}

.btn-submit-assessment:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.assessment-result {
  margin: 16px 0;
  padding: 20px;
  background: white;
  border-radius: 12px;
  border: 2px solid var(--color-border);
}

.result-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 12px;
}

.result-header.result-passed {
  border-bottom: 2px solid #4caf50;
}

.result-header.result-failed {
  border-bottom: 2px solid #ff9800;
}

.result-icon {
  font-size: 24px;
}

.result-passed .result-icon {
  color: #4caf50;
}

.result-failed .result-icon {
  color: #ff9800;
}

.result-header h3 {
  margin: 0;
  font-size: 18px;
}

.result-feedback {
  margin: 10px 0;
  font-size: 15px;
  line-height: 1.6;
  color: var(--color-text);
}

.result-stats {
  display: flex;
  gap: 20px;
  margin: 12px 0;
  font-size: 14px;
  color: var(--color-text-muted);
}

.btn-continue {
  padding: 10px 24px;
  font-family: var(--font-body);
  font-size: 14px;
  font-weight: 600;
  background: var(--color-ink);
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  transition: background 0.2s;
}

.btn-continue:hover {
  background: var(--color-accent);
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
  background: var(--color-ink);
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

.think-block {
  background: var(--color-bg-warm);
  border: 1px solid var(--color-border);
  border-radius: 6px;
  padding: 8px 12px;
  margin-bottom: 12px;
  font-size: 14px;
}

.think-block summary {
  cursor: pointer;
  color: var(--color-text-muted);
  font-weight: 500;
  user-select: none;
}

.think-block summary:hover {
  color: var(--color-ink);
}

.think-content {
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px dashed var(--color-border);
  color: var(--color-text-muted);
  font-size: 13px;
  line-height: 1.6;
}

.message-text.is-streaming::after {
  content: '▍';
  display: inline;
  animation: cursor-blink 0.8s step-end infinite;
  color: var(--color-accent);
  margin-left: 1px;
}

@keyframes cursor-blink {
  50% { opacity: 0; }
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

.message.user .message-text {
  background: var(--color-ink);
  color: white;
  border-bottom-right-radius: 4px;
}

.message.assistant .message-text {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-bottom-left-radius: 4px;
}

.message-time {
  font-size: 12px;
  color: var(--color-text-muted);
}

.message.user .message-time {
  text-align: right;
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

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

@keyframes typing {
  0%, 60%, 100% { transform: translateY(0); }
  30% { transform: translateY(-4px); }
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

.math-block {
  margin: 12px 0;
  overflow-x: auto;
}

.math-error {
  color: #C75050;
  background: #FEF2F2;
  padding: 4px 8px;
  border-radius: 4px;
}

.mermaid-svg {
  margin: 16px 0;
  display: flex;
  justify-content: center;
}

.mermaid-svg svg {
  max-width: 100%;
  height: auto;
}

.mermaid-error {
  background: #FEF2F2;
  color: #C75050;
  padding: 12px 16px;
  border-radius: 4px;
  border: 1px solid #FFCDD2;
  font-family: monospace;
  font-size: 13px;
}

.message-text code {
  background: var(--color-bg-warm);
  padding: 2px 6px;
  border-radius: 4px;
  font-family: 'Fira Code', 'Monaco', monospace;
  font-size: 0.9em;
}

.message-text h1,
.message-text h2,
.message-text h3,
.message-text h4,
.message-text h5,
.message-text h6 {
  margin: 16px 0 8px;
  font-weight: 600;
  color: var(--color-ink);
}

.message-text h1 { font-size: 1.5em; }
.message-text h2 { font-size: 1.3em; }
.message-text h3 { font-size: 1.1em; }

.message-text p {
  margin: 8px 0;
  line-height: 1.6;
}

.message-text ul,
.message-text ol {
  margin: 8px 0;
  padding-left: 24px;
}

.message-text li {
  margin: 4px 0;
}

.message-text blockquote {
  margin: 12px 0;
  padding: 8px 16px;
  border-left: 4px solid var(--color-accent);
  background: var(--color-bg-warm);
  color: var(--color-text-muted);
}

.message-text table {
  width: 100%;
  border-collapse: collapse;
  margin: 12px 0;
}

.message-text th,
.message-text td {
  border: 1px solid var(--color-border);
  padding: 8px 12px;
  text-align: left;
}

.message-text th {
  background: var(--color-bg-warm);
  font-weight: 600;
}

.message-text hr {
  border: none;
  border-top: 1px solid var(--color-border);
  margin: 16px 0;
}

.message-text a {
  color: var(--color-accent);
  text-decoration: underline;
}

.message-text a:hover {
  color: var(--color-ink);
}

.message-text img {
  max-width: 100%;
  height: auto;
  border-radius: 4px;
  margin: 8px 0;
}
</style>