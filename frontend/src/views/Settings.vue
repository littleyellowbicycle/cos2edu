<template>
  <div class="settings">
    <header class="page-header">
      <div class="header-content">
        <router-link to="/" class="back-link">
          <span class="back-icon">←</span>
          <span>返回首页</span>
        </router-link>
        <div class="header-title-group">
          <h1 class="page-title">设置</h1>
          <p class="page-subtitle">配置 AI 模型和 API</p>
        </div>
      </div>
    </header>

    <main class="settings-content">
      <section class="settings-section">
        <h2 class="section-title">模型配置</h2>
        <p class="section-description">
          配置你的 AI 模型提供商。默认使用 OpenAI，你也可以选择其他提供商或自定义 API。
        </p>

        <div v-if="loading" class="loading-state">
          <div class="loading-spinner"></div>
        </div>

        <form v-else class="settings-form" @submit.prevent="handleSubmit">
          <div class="form-group">
            <label for="provider">提供商</label>
            <select id="provider" v-model="form.provider">
              <option value="openai">OpenAI</option>
              <option value="anthropic">Anthropic</option>
              <option value="dashscope">阿里云 DashScope</option>
              <option value="zhipu">智谱 GLM</option>
              <option value="doubao">豆包 (字节)</option>
              <option value="wenxin">百度文心</option>
              <option value="hunyuan">腾讯混元</option>
              <option value="moonshot">月之暗面 (Kimi)</option>
              <option value="gemini">Google Gemini</option>
              <option value="minimax">MiniMax</option>
              <option value="custom">自定义</option>
            </select>
          </div>

          <div class="form-group">
            <label for="model">模型名称</label>
            <input 
              id="model" 
              v-model="form.model_name" 
              type="text" 
              :placeholder="modelPlaceholders[form.provider] || '输入模型名称'"
              required
            />
            <p class="form-hint" v-html="modelHints[form.provider] || ''"></p>
          </div>

          <div class="form-group">
            <label for="apiKey">API Key</label>
            <div class="input-with-toggle">
              <input 
                id="apiKey" 
                v-model="form.api_key" 
                :type="showApiKey ? 'text' : 'password'"
                :placeholder="apiKeyPlaceholders[form.provider] || 'sk-...'"
                required
              />
              <button 
                type="button" 
                class="btn-toggle"
                @click="showApiKey = !showApiKey"
              >
                {{ showApiKey ? '隐藏' : '显示' }}
              </button>
            </div>
          </div>

          <div class="form-group">
            <label for="baseUrl">API Base URL <span class="optional">(通常自动填写)</span></label>
            <input 
              id="baseUrl" 
              v-model="form.base_url" 
              type="text" 
              :placeholder="baseUrlPlaceholders[form.provider] || 'https://...'"
            />
            <p class="form-hint">使用代理或需要特殊端点时填写</p>
          </div>

          <div class="form-group" v-if="form.provider === 'minimax'">
            <label for="groupId">Group ID <span class="optional">(MiniMax 必需)</span></label>
            <input 
              id="groupId" 
              v-model="form.group_id" 
              type="text" 
              placeholder="输入你的 Group ID"
            />
            <p class="form-hint">Group ID 是 MiniMax API 的必需参数</p>
          </div>

          <div class="form-actions">
            <button type="submit" class="btn-submit" :disabled="saving">
              {{ saving ? '保存中...' : '保存配置' }}
            </button>
          </div>
        </form>
      </section>

      <section class="settings-section">
        <h2 class="section-title">当前配置</h2>
        <div class="current-config">
          <div class="config-item">
            <span class="config-label">提供商</span>
            <span class="config-value">{{ currentConfig.provider || '未配置' }}</span>
          </div>
          <div class="config-item">
            <span class="config-label">模型</span>
            <span class="config-value">{{ currentConfig.model_name || '未配置' }}</span>
          </div>
          <div class="config-item">
            <span class="config-label">API Key</span>
            <span class="config-value">{{ currentConfig.id ? '已配置' : '未配置' }}</span>
          </div>
        </div>
      </section>

      <section class="settings-section test-section">
        <h2 class="section-title">测试连接</h2>
        <p class="section-description">保存配置后，可以测试 AI 连接是否正常。</p>
        <button 
          class="btn-test" 
          @click="testConnection"
          :disabled="testing || !canTest"
        >
          {{ testing ? '测试中...' : '测试 AI 连接' }}
        </button>
        <div v-if="testResult" class="test-result" :class="testResult.type">
          {{ testResult.message }}
        </div>
      </section>
    </main>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import api from '@/api'

const router = useRouter()
const loading = ref(true)
const saving = ref(false)
const testing = ref(false)
const showApiKey = ref(false)
const testResult = ref(null)
const currentConfig = ref({})

const form = ref({
  provider: 'openai',
  model_name: 'gpt-4o',
  api_key: '',
  base_url: '',
  group_id: ''
})

const modelPlaceholders = {
  openai: 'gpt-4o',
  anthropic: 'claude-3-opus-20240229',
  dashscope: 'qwen-plus',
  zhipu: 'glm-4',
  doubao: 'doubao-pro-32k',
  wenxin: 'ernie-4.0-8k-latest',
  hunyuan: 'hunyuan-pro',
  moonshot: 'moonshot-v1-8k',
  gemini: 'gemini-1.5-pro',
  minimax: 'MiniMax-M2.7',
  custom: '自定义模型名称'
}

const modelHints = {
  openai: '推荐: <strong>gpt-4o</strong>, gpt-4-turbo, gpt-3.5-turbo',
  anthropic: '推荐: <strong>claude-3-opus-20240229</strong>, claude-3-sonnet-20240229',
  dashscope: '推荐: <strong>qwen-plus</strong>, qwen-turbo, qwen-max',
  zhipu: '推荐: <strong>glm-4</strong>, glm-4-flash, glm-3-turbo',
  doubao: '推荐: <strong>doubao-pro-32k</strong>, doubao-pro-128k',
  wenxin: '推荐: <strong>ernie-4.0-8k-latest</strong>, ernie-3.5-8k',
  hunyuan: '推荐: <strong>hunyuan-pro</strong>, hunyuan-standard',
  moonshot: '推荐: <strong>moonshot-v1-8k</strong>, moonshot-v1-32k',
  gemini: '推荐: <strong>gemini-1.5-pro</strong>, gemini-1.5-flash',
  minimax: '推荐: <strong>MiniMax-M2.7</strong>, MiniMax-M2.5, MiniMax-M2',
  custom: '根据你的自定义端点配置填写模型名称'
}

const apiKeyPlaceholders = {
  openai: 'sk-...',
  anthropic: 'sk-ant-...',
  dashscope: 'sk-...',
  zhipu: '...',
  doubao: '...',
  wenxin: '...',
  hunyuan: '...',
  moonshot: 'sk-...',
  gemini: 'AIza...',
  minimax: 'sk-cp-...',
  custom: '你的 API Key'
}

const baseUrlPlaceholders = {
  openai: 'https://api.openai.com/v1',
  anthropic: 'https://api.anthropic.com',
  dashscope: 'https://dashscope.aliyuncs.com/compatible-mode/v1',
  zhipu: 'https://open.bigmodel.cn/api/paas/v4',
  doubao: 'https://ark.cn-beijing.volces.com/api/v3',
  wenxin: 'https://qianfan.baidubce.com/v2',
  hunyuan: 'https://api.hunyuan.cloud.tencent.com',
  moonshot: 'https://api.moonshot.cn/v1',
  gemini: 'https://generativelanguage.googleapis.com/v1beta/openai/',
  minimax: 'https://api.minimax.chat/v1',
  custom: 'https://your-custom-api.com/v1'
}

const canTest = computed(() => {
  return form.value.api_key && form.value.model_name
})

watch(() => form.value.provider, (newProvider) => {
  if (modelPlaceholders[newProvider]) {
    form.value.model_name = modelPlaceholders[newProvider]
  }
  if (baseUrlPlaceholders[newProvider]) {
    form.value.base_url = baseUrlPlaceholders[newProvider]
  }
})

onMounted(async () => {
  try {
    const configs = await api.modelConfigs.getAll()
    if (configs.length > 0) {
      const config = configs[0]
      currentConfig.value = config
      form.value = {
        provider: config.provider || 'openai',
        model_name: config.model_name || 'gpt-4o',
        api_key: config.api_key || '',
        base_url: config.base_url || '',
        group_id: config.group_id || ''
      }
    }
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
})

async function handleSubmit() {
  if (!form.value.api_key.trim()) {
    ElMessage.warning('请输入 API Key')
    return
  }

  saving.value = true
  try {
    const configs = await api.modelConfigs.getAll()
    if (configs.length > 0) {
      await api.modelConfigs.update(configs[0].id, form.value)
    } else {
      await api.modelConfigs.create({
        ...form.value,
        is_default: true,
        is_active: true
      })
    }
    
    const configs2 = await api.modelConfigs.getAll()
    if (configs2.length > 0) {
      currentConfig.value = configs2[0]
    }
    
    ElMessage.success('配置已保存')
  } catch (e) {
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}

async function testConnection() {
  testing.value = true
  testResult.value = null
  
  try {
    const response = await fetch('/api/v1/crud/ai/test', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        provider: form.value.provider,
        model: form.value.model_name,
        api_key: form.value.api_key,
        base_url: form.value.base_url
      })
    })
    
    const data = await response.json()
    
    if (response.ok && data.success) {
      testResult.value = { type: 'success', message: '连接成功！AI 已准备好。' }
    } else {
      testResult.value = { type: 'error', message: data.error || '连接失败' }
    }
  } catch (e) {
    testResult.value = { type: 'error', message: '无法连接到服务器' }
  } finally {
    testing.value = false
  }
}
</script>

<style scoped>
.settings {
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

.settings-content {
  padding: 48px 40px;
  max-width: 720px;
  margin: 0 auto;
}

.settings-section {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 8px;
  padding: 32px;
  margin-bottom: 32px;
}

.section-title {
  font-family: var(--font-display);
  font-size: 24px;
  font-weight: 600;
  color: var(--color-ink);
  margin-bottom: 8px;
}

.section-description {
  font-size: 15px;
  color: var(--color-text-muted);
  margin-bottom: 24px;
  line-height: 1.6;
}

.loading-state {
  display: flex;
  justify-content: center;
  padding: 40px;
}

.loading-spinner {
  width: 32px;
  height: 32px;
  border: 3px solid var(--color-border);
  border-top-color: var(--color-accent);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

.settings-form {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-group label {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-ink);
}

.form-group input,
.form-group select {
  font-family: var(--font-body);
  font-size: 15px;
  padding: 12px 16px;
  border: 1px solid var(--color-border);
  border-radius: 4px;
  background: var(--color-bg);
  color: var(--color-text);
  transition: border-color 0.2s;
}

.form-group input:focus,
.form-group select:focus {
  outline: none;
  border-color: var(--color-accent);
}

.form-group select {
  cursor: pointer;
}

.form-hint {
  font-size: 13px;
  color: var(--color-text-muted);
  line-height: 1.5;
}

.optional {
  font-weight: 400;
  color: var(--color-text-muted);
}

.input-with-toggle {
  display: flex;
  gap: 8px;
}

.input-with-toggle input {
  flex: 1;
}

.btn-toggle {
  font-family: var(--font-body);
  font-size: 14px;
  padding: 12px 16px;
  background: var(--color-bg-warm);
  color: var(--color-text-muted);
  border: 1px solid var(--color-border);
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-toggle:hover {
  background: var(--color-border);
  color: var(--color-text);
}

.form-actions {
  padding-top: 16px;
}

.btn-submit {
  font-family: var(--font-body);
  font-size: 15px;
  font-weight: 600;
  padding: 14px 32px;
  background: var(--color-ink);
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-submit:hover:not(:disabled) {
  background: var(--color-accent);
}

.btn-submit:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.current-config {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 20px;
  background: var(--color-bg-warm);
  border-radius: 6px;
}

.config-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.config-label {
  font-size: 14px;
  color: var(--color-text-muted);
}

.config-value {
  font-size: 14px;
  font-weight: 500;
  color: var(--color-ink);
}

.test-section {
  text-align: center;
}

.btn-test {
  font-family: var(--font-body);
  font-size: 15px;
  font-weight: 600;
  padding: 14px 32px;
  background: var(--color-surface);
  color: var(--color-ink);
  border: 2px solid var(--color-ink);
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s ease;
  margin-bottom: 20px;
}

.btn-test:hover:not(:disabled) {
  background: var(--color-ink);
  color: white;
}

.btn-test:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.test-result {
  font-size: 14px;
  padding: 12px 20px;
  border-radius: 6px;
  margin-top: 16px;
}

.test-result.success {
  background: #F0F9EB;
  color: #2E7D32;
  border: 1px solid #C8E6C9;
}

.test-result.error {
  background: #FEF2F2;
  color: #C75050;
  border: 1px solid #FFCDD2;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

@media (max-width: 768px) {
  .page-header {
    padding: 24px;
  }
  
  .settings-content {
    padding: 24px;
  }
  
  .settings-section {
    padding: 24px;
  }
}
</style>