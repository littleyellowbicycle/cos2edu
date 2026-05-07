<template>
  <div class="chat" :class="{ 'chat-with-sidebar': showSidebar }">
    <header class="chat-header">
      <button class="btn-back" @click="$router.push('/conversations')" aria-label="返回对话列表">
        <span>←</span>
      </button>
      <div class="header-info">
        <h1 class="chat-title">{{ characterName || '对话' }}</h1>
        <p class="chat-status" aria-live="polite">
          <span v-if="isTyping">正在思考...</span>
          <span v-else-if="sending">发送中...</span>
          <span v-else>苏格拉底式对话中</span>
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
              <div class="message-text" :ref="el => { if (el) messageRefs[msg.timestamp] = el }" v-html="getRenderedContent(msg)"></div>
              <div class="message-time" v-if="msg.timestamp" aria-label="发送时间">
                {{ formatTime(msg.timestamp) }}
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
import { ref, onMounted, nextTick, watch } from 'vue'
import { useRoute } from 'vue-router'
import api from '@/api'
import { ElMessage } from 'element-plus'
import katex from 'katex'
import 'katex/dist/katex.min.css'
import mermaid from 'mermaid'
import { marked } from 'marked'

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
const messages = ref([])
const inputMessage = ref('')
const sending = ref(false)
const isTyping = ref(false)
const messagesContainer = ref(null)
const inputTextarea = ref(null)
const showSidebar = ref(false)
const conversationId = ref(route.query.conversationId || null)
const characterName = ref('')
const characterAvatar = ref('')
const characterAvatarType = ref('emoji')
const conversationHistory = ref([])
const loading = ref(false)
const messageRefs = {}

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
  const characterId = route.params.id
  if (conversationId.value) {
    loading.value = true
    await loadConversation({ id: conversationId.value })
    loading.value = false
  }
  
  try {
    const character = await api.characters.getById(characterId)
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
        character_id: route.params.id,
        title: `与 ${characterName.value} 的对话`
      })
      conversationId.value = conv.id
    }

    const response = await fetch(`/api/v1/chat/${conversationId.value}/stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content: userMessage })
    })

    if (!response.ok) {
      throw new Error('请求失败')
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let aiResponse = ''
    let firstChunk = true

    messages.value.push({ role: 'assistant', content: '', timestamp: new Date() })
    const aiIndex = messages.value.length - 1
    let hasError = false
    let errorMsg = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      
      const chunk = decoder.decode(value)
      const lines = chunk.split('\n')
      
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.slice(6))
            if (data.error) {
              hasError = true
              errorMsg = data.error
            } else if (data.content) {
              if (firstChunk) {
                isTyping.value = false
                firstChunk = false
              }
              aiResponse += data.content
              messages.value[aiIndex].content = aiResponse
            }
          } catch (e) {
            // Ignore parse errors for partial data
          }
        }
      }
    }
    
    if (hasError) {
      messages.value[aiIndex].content = ''
      throw new Error(errorMsg)
    }
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
  } finally {
    sending.value = false
    isTyping.value = false
  }
}

async function loadConversation(conv) {
  conversationId.value = conv.id
  messages.value = []
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
  font-size: 15px;
  line-height: 1.7;
  color: var(--color-text);
  padding: 16px 20px;
  border-radius: 12px;
  white-space: pre-wrap;
  word-break: break-word;
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