<template>
  <div class="chat">
    <el-container>
      <el-header>
        <h1>苏格拉底式对话</h1>
        <el-button @click="$router.push('/conversations')">返回</el-button>
      </el-header>
      <el-main>
        <el-card class="chat-container">
          <div class="messages" ref="messagesContainer">
            <div v-for="(msg, index) in messages" :key="index" :class="['message', msg.role]">
              <span class="role-label">{{ msg.role === 'user' ? '你' : 'AI' }}:</span>
              <span class="content">{{ msg.content }}</span>
            </div>
          </div>
          <div class="input-area">
            <el-input
              v-model="inputMessage"
              type="textarea"
              :rows="3"
              placeholder="输入你的问题..."
              @keydown.enter.ctrl="sendMessage"
            />
            <el-button type="primary" @click="sendMessage" :loading="sending">
              发送 (Ctrl+Enter)
            </el-button>
          </div>
        </el-card>
      </el-main>
    </el-container>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import api from '@/api'
import { ElMessage } from 'element-plus'

const route = useRoute()
const messages = ref([])
const inputMessage = ref('')
const sending = ref(false)
const messagesContainer = ref(null)

onMounted(async () => {
  const conversationId = route.query.conversationId
  if (conversationId) {
    // Load existing conversation
  }
})

async function sendMessage() {
  if (!inputMessage.value.trim() || sending.value) return

  const userMessage = inputMessage.value.trim()
  inputMessage.value = ''
  messages.value.push({ role: 'user', content: userMessage })
  scrollToBottom()

  sending.value = true
  try {
    const conversationId = route.query.conversationId
    const characterId = route.params.id

    // For streaming response, we use EventSource
    // But EventSource doesn't support POST, so we'll use fetch with ReadableStream
    const response = await fetch(`/api/v1/chat/${conversationId || characterId}/stream?message=${encodeURIComponent(userMessage)}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    })

    if (!response.ok) {
      throw new Error('请求失败')
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let aiResponse = ''

    messages.value.push({ role: 'assistant', content: '' })
    const aiIndex = messages.value.length - 1

    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      const chunk = decoder.decode(value)
      aiResponse += chunk
      messages.value[aiIndex].content = aiResponse
      scrollToBottom()
    }
  } catch (e) {
    ElMessage.error(e.message || '发送失败')
  } finally {
    sending.value = false
  }
}

function scrollToBottom() {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
}
</script>

<style scoped>
.chat {
  height: 100vh;
}
.el-header {
  background-color: #909399;
  color: white;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.chat-container {
  height: calc(100vh - 100px);
  display: flex;
  flex-direction: column;
}
.messages {
  flex: 1;
  overflow-y: auto;
  padding: 10px;
}
.message {
  margin-bottom: 15px;
  padding: 10px;
  border-radius: 8px;
}
.message.user {
  background-color: #ecf5ff;
  margin-left: 50px;
}
.message.assistant {
  background-color: #f0f9eb;
  margin-right: 50px;
}
.role-label {
  font-weight: bold;
  margin-right: 8px;
}
.content {
  white-space: pre-wrap;
}
.input-area {
  display: flex;
  gap: 10px;
  padding: 10px;
  border-top: 1px solid #eee;
}
</style>