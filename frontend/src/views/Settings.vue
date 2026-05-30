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
              <option value="deepseek">DeepSeek</option>
              <option value="dashscope">阿里云 DashScope</option>
              <option value="zhipu">智谱 GLM</option>
              <option value="moonshot">月之暗面 (Kimi)</option>
              <option value="doubao">豆包 (字节)</option>
              <option value="wenxin">百度文心</option>
              <option value="hunyuan">腾讯混元</option>
              <option value="siliconflow">硅基流动</option>
              <option value="gemini">Google Gemini</option>
              <option value="minimax">MiniMax</option>
              <option value="openrouter">OpenRouter</option>
              <option value="ollama">Ollama (本地)</option>
              <option value="custom">自定义</option>
            </select>
          </div>

          <div class="form-group">
            <label for="model">模型名称</label>
            <div class="model-select-row" v-if="form.provider !== 'custom'">
              <select id="model" v-model="form.model_name" :disabled="fetchingModels">
                <option 
                  v-if="form.model_name && !providerModels[form.provider]?.some(m => m.value === form.model_name)"
                  :value="form.model_name"
                >
                  {{ form.model_name }} (当前)
                </option>
                <option v-for="m in providerModels[form.provider] || []" :key="m.value" :value="m.value">
                  {{ m.label }}
                </option>
              </select>
              <button 
                type="button" 
                class="btn-refresh-models"
                :disabled="fetchingModels || !form.api_key"
                @click="fetchProviderModels(true)"
                :title="form.api_key ? '从 API 获取最新模型列表' : '请先填写 API Key'"
              >
                {{ fetchingModels ? '...' : '↻' }}
              </button>
            </div>
            <input 
              v-else
              id="model" 
              v-model="form.model_name" 
              type="text" 
              placeholder="输入自定义模型名称"
              required
            />
            <p class="form-hint" v-if="form.provider !== 'custom'">
              {{ fetchingModels ? '正在从 API 获取模型列表...' : '选择' + (providerNames[form.provider] || '') + '的模型（点击 ↻ 从 API 获取最新列表）' }}
            </p>
          </div>

          <div class="form-group">
            <label for="apiKey">API Key</label>
            <div class="input-with-toggle">
              <input 
                id="apiKey" 
                v-model="form.api_key" 
                :type="showApiKey ? 'text' : 'password'"
                :placeholder="hasConfiguredKey ? MASKED_KEY_PLACEHOLDER : (apiKeyPlaceholders[form.provider] || 'sk-...')"
              />
              <button 
                type="button" 
                class="btn-toggle"
                @click="showApiKey = !showApiKey"
              >
                {{ showApiKey ? '隐藏' : '显示' }}
              </button>
            </div>
            <p v-if="hasConfiguredKey && form.api_key === MASKED_KEY_PLACEHOLDER" class="form-hint">已保存的 Key 不会被重新读取，留空则不修改</p>
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
            <span class="config-value" :class="{ 'key-configured': currentConfig.has_api_key }">
              {{ currentConfig.has_api_key ? '✓ 已配置' : '未配置' }}
            </span>
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
const hasConfiguredKey = ref(false)
const MASKED_KEY_PLACEHOLDER = '•••••••• (已配置，留空则不修改)'

const form = ref({
  provider: 'openai',
  model_name: 'gpt-4o',
  api_key: '',
  base_url: '',
  group_id: ''
})

const modelPlaceholders = {
  openai: 'gpt-4.1',
  anthropic: 'claude-sonnet-4-20250514',
  deepseek: 'deepseek-chat',
  dashscope: 'qwen3-max',
  zhipu: 'glm-4.5',
  moonshot: 'moonshot-v1-8k',
  doubao: 'doubao-seed-1.6',
  wenxin: 'ernie-4.5-8k-preview',
  hunyuan: 'hunyuan-turbos-latest',
  siliconflow: 'deepseek-ai/DeepSeek-V3',
  gemini: 'gemini-2.5-pro',
  minimax: 'MiniMax-M2.7',
  openrouter: 'openai/gpt-4.1',
  ollama: 'qwen3',
  custom: '自定义模型名称'
}

const providerNames = {
  openai: 'OpenAI',
  anthropic: 'Anthropic',
  deepseek: 'DeepSeek',
  dashscope: '阿里云 DashScope',
  zhipu: '智谱 GLM',
  moonshot: '月之暗面 (Kimi)',
  doubao: '豆包 (字节)',
  wenxin: '百度文心',
  hunyuan: '腾讯混元',
  siliconflow: '硅基流动',
  gemini: 'Google Gemini',
  minimax: 'MiniMax',
  openrouter: 'OpenRouter',
  ollama: 'Ollama (本地)'
}

const providerModels = ref({
  openai: [
    { value: 'gpt-4.1', label: 'GPT-4.1 (推荐)' },
    { value: 'gpt-4.1-mini', label: 'GPT-4.1 Mini' },
    { value: 'gpt-4o', label: 'GPT-4o' },
    { value: 'gpt-4o-mini', label: 'GPT-4o Mini' },
    { value: 'gpt-4-turbo', label: 'GPT-4 Turbo' }
  ],
  anthropic: [
    { value: 'claude-sonnet-4-20250514', label: 'Claude Sonnet 4 (推荐)' },
    { value: 'claude-opus-4-20250514', label: 'Claude Opus 4' },
    { value: 'claude-3-5-sonnet-20241022', label: 'Claude 3.5 Sonnet' },
    { value: 'claude-3-5-haiku-20241022', label: 'Claude 3.5 Haiku' },
    { value: 'claude-3-opus-20240229', label: 'Claude 3 Opus' }
  ],
  dashscope: [
    { value: 'qwen3-max', label: 'Qwen3 Max (推荐)' },
    { value: 'qwen3-plus', label: 'Qwen3 Plus' },
    { value: 'qwen-plus', label: 'Qwen Plus' },
    { value: 'qwen-max', label: 'Qwen Max' },
    { value: 'qwen-turbo', label: 'Qwen Turbo' }
  ],
  zhipu: [
    { value: 'glm-4.5', label: 'GLM-4.5 (推荐)' },
    { value: 'glm-4-plus', label: 'GLM-4 Plus' },
    { value: 'glm-4-flash', label: 'GLM-4 Flash' }
  ],
  doubao: [
    { value: 'doubao-seed-1.6', label: '豆包 Seed 1.6 (推荐)' },
    { value: 'doubao-pro-32k', label: '豆包 Pro 32K' },
    { value: 'doubao-lite-32k', label: '豆包 Lite 32K' }
  ],
  wenxin: [
    { value: 'ernie-4.5-8k-preview', label: 'ERNIE 4.5 8K (推荐)' },
    { value: 'ernie-4.0-8k-latest', label: 'ERNIE 4.0 8K' },
    { value: 'ernie-3.5-8k', label: 'ERNIE 3.5 8K' }
  ],
  hunyuan: [
    { value: 'hunyuan-turbos-latest', label: '混元 TurboS (推荐)' },
    { value: 'hunyuan-turbo-latest', label: '混元 Turbo' },
    { value: 'hunyuan-pro', label: '混元 Pro' }
  ],
  moonshot: [
    { value: 'moonshot-v1-8k', label: 'Kimi v1 8K (推荐)' },
    { value: 'moonshot-v1-32k', label: 'Kimi v1 32K' },
    { value: 'moonshot-v1-128k', label: 'Kimi v1 128K' }
  ],
  gemini: [
    { value: 'gemini-2.5-pro', label: 'Gemini 2.5 Pro (推荐)' },
    { value: 'gemini-2.5-flash', label: 'Gemini 2.5 Flash' },
    { value: 'gemini-2.0-flash', label: 'Gemini 2.0 Flash' }
  ],
  minimax: [
    { value: 'MiniMax-M2.7', label: 'MiniMax M2.7 (推荐)' },
    { value: 'MiniMax-M2.5', label: 'MiniMax M2.5' },
    { value: 'MiniMax-M2.1', label: 'MiniMax M2.1' }
  ],
  deepseek: [
    { value: 'deepseek-chat', label: 'DeepSeek-V3 (推荐)' },
    { value: 'deepseek-reasoner', label: 'DeepSeek-R1' }
  ],
  siliconflow: [
    { value: 'deepseek-ai/DeepSeek-V3', label: 'DeepSeek-V3 (推荐)' },
    { value: 'deepseek-ai/DeepSeek-R1', label: 'DeepSeek-R1' },
    { value: 'Qwen/Qwen3-235B-A22B', label: 'Qwen3 235B' },
    { value: 'Qwen/QwQ-32B', label: 'QwQ 32B' },
    { value: 'Pro/zai-org/GLM-4.5', label: 'GLM-4.5' }
  ],
  openrouter: [
    { value: 'openai/gpt-4.1', label: 'GPT-4.1 (推荐)' },
    { value: 'anthropic/claude-sonnet-4', label: 'Claude Sonnet 4' },
    { value: 'google/gemini-2.5-pro', label: 'Gemini 2.5 Pro' },
    { value: 'deepseek/deepseek-chat', label: 'DeepSeek-V3' }
  ],
  ollama: [
    { value: 'qwen3', label: 'Qwen3' },
    { value: 'llama3', label: 'Llama 3' },
    { value: 'deepseek-r1', label: 'DeepSeek-R1' },
    { value: 'gemma3', label: 'Gemma 3' },
    { value: 'mistral', label: 'Mistral' }
  ]
})

const fetchingModels = ref(false)

const modelHints = {
  openai: '推荐: <strong>gpt-4.1</strong>, gpt-4o, gpt-4.1-mini',
  anthropic: '推荐: <strong>claude-sonnet-4-20250514</strong>, claude-3-5-sonnet',
  deepseek: '推荐: <strong>deepseek-chat</strong>, deepseek-reasoner',
  dashscope: '推荐: <strong>qwen3-max</strong>, qwen-plus, qwen-max',
  zhipu: '推荐: <strong>glm-4.5</strong>, glm-4-plus, glm-4-flash',
  moonshot: '推荐: <strong>moonshot-v1-8k</strong>, moonshot-v1-32k',
  doubao: '推荐: <strong>doubao-seed-1.6</strong>, doubao-pro-32k',
  wenxin: '推荐: <strong>ernie-4.5-8k-preview</strong>, ernie-4.0-8k',
  hunyuan: '推荐: <strong>hunyuan-turbos-latest</strong>, hunyuan-pro',
  siliconflow: '推荐: <strong>deepseek-ai/DeepSeek-V3</strong>, Qwen/Qwen3-235B',
  gemini: '推荐: <strong>gemini-2.5-pro</strong>, gemini-2.5-flash',
  minimax: '推荐: <strong>MiniMax-M2.7</strong>, MiniMax-M2.5, MiniMax-M2.1',
  openrouter: '推荐: <strong>openai/gpt-4.1</strong>, anthropic/claude-sonnet-4',
  ollama: '请先运行 ollama pull &lt;model&gt; 下载模型',
  custom: '根据你的自定义端点配置填写模型名称'
}

const apiKeyPlaceholders = {
  openai: 'sk-...',
  anthropic: 'sk-ant-...',
  deepseek: 'sk-...',
  dashscope: 'sk-...',
  zhipu: '...',
  moonshot: 'sk-...',
  doubao: '...',
  wenxin: '...',
  hunyuan: '...',
  siliconflow: 'sk-...',
  gemini: 'AIza...',
  minimax: 'sk-cp-...',
  openrouter: 'sk-or-...',
  ollama: 'ollama (本地无需 Key)',
  custom: '你的 API Key'
}

const baseUrlPlaceholders = {
  openai: 'https://api.openai.com/v1',
  anthropic: 'https://api.anthropic.com',
  deepseek: 'https://api.deepseek.com/v1',
  dashscope: 'https://dashscope.aliyuncs.com/compatible-mode/v1',
  zhipu: 'https://open.bigmodel.cn/api/paas/v4',
  moonshot: 'https://api.moonshot.cn/v1',
  doubao: 'https://ark.cn-beijing.volces.com/api/v3',
  wenxin: 'https://qianfan.baidubce.com/v2',
  hunyuan: 'https://api.hunyuan.cloud.tencent.com',
  siliconflow: 'https://api.siliconflow.cn/v1',
  gemini: 'https://generativelanguage.googleapis.com/v1beta/openai/',
  minimax: 'https://api.minimax.chat/v1',
  openrouter: 'https://openrouter.ai/api/v1',
  ollama: 'http://localhost:11434/v1',
  custom: 'https://your-custom-api.com/v1'
}

const canTest = computed(() => {
  return form.value.api_key && form.value.model_name
})

watch(() => form.value.provider, (newProvider) => {
  if (newProvider !== 'custom' && providerModels.value[newProvider]?.length) {
    form.value.model_name = providerModels.value[newProvider][0].value
  } else if (newProvider === 'custom') {
    form.value.model_name = ''
  }
  if (baseUrlPlaceholders[newProvider]) {
    form.value.base_url = baseUrlPlaceholders[newProvider]
  }
  // 切换服务商后清空 key，避免旧提供商的 key 占位符误导
  form.value.api_key = ''
  hasConfiguredKey.value = false
})

let fetchTimer = null

async function fetchProviderModels(showMessage = false) {
  const provider = form.value.provider
  if (provider === 'custom' || !form.value.api_key) return
  
  fetchingModels.value = true
  try {
    const data = await api.providers.models(provider, {
      api_key: form.value.api_key,
      base_url: form.value.base_url
    })
    if (Array.isArray(data) && data.length > 0) {
      providerModels.value = { ...providerModels.value, [provider]: data }
      const currentInList = data.some(m => m.value === form.value.model_name)
      if (!currentInList && data.length > 0) {
        form.value.model_name = data[0].value
      }
      if (showMessage) {
        ElMessage.success(`已获取 ${data.length} 个模型`)
      }
    }
  } catch (e) {
    if (showMessage) {
      ElMessage.warning('无法从 API 获取模型列表，使用默认列表')
    }
  } finally {
    fetchingModels.value = false
  }
}

watch(() => form.value.api_key, () => {
  clearTimeout(fetchTimer)
  if (form.value.api_key && form.value.api_key !== MASKED_KEY_PLACEHOLDER) {
    fetchTimer = setTimeout(() => fetchProviderModels(), 500)
  }
})

onMounted(async () => {
  try {
    const configs = await api.modelConfigs.getAll()
    if (configs.length > 0) {
      const config = configs[0]
      currentConfig.value = config
      hasConfiguredKey.value = !!config.has_api_key
      form.value = {
        provider: config.provider || 'openai',
        model_name: config.model_name || 'gpt-4o',
        api_key: config.has_api_key ? MASKED_KEY_PLACEHOLDER : (config.api_key || ''),
        base_url: config.base_url || '',
        group_id: config.group_id || ''
      }
      // 已有 key 但前端拿不到原文，无法从 API 刷新模型列表，使用本地默认列表
    }
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
})

async function handleSubmit() {
  saving.value = true
  try {
    const submitData = { ...form.value }
    // If api_key is the masked placeholder, omit it to keep the existing key
    if (submitData.api_key === MASKED_KEY_PLACEHOLDER) {
      delete submitData.api_key
    }
    if (!submitData.api_key && !hasConfiguredKey.value) {
      ElMessage.warning('请输入 API Key')
      saving.value = false
      return
    }

    const configs = await api.modelConfigs.getAll()
    if (configs.length > 0) {
      await api.modelConfigs.update(configs[0].id, submitData)
    } else {
      await api.modelConfigs.create({
        ...submitData,
        is_default: true,
        is_active: true
      })
    }
    
    const configs2 = await api.modelConfigs.getAll()
    if (configs2.length > 0) {
      currentConfig.value = configs2[0]
      hasConfiguredKey.value = !!configs2[0].has_api_key
      if (!hasConfiguredKey.value) {
        form.value.api_key = configs2[0].api_key || ''
      }
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

.model-select-row {
  display: flex;
  gap: 8px;
}

.model-select-row select {
  flex: 1;
}

.btn-refresh-models {
  font-family: var(--font-body);
  font-size: 18px;
  width: 44px;
  padding: 0;
  background: var(--color-bg-warm);
  color: var(--color-text-muted);
  border: 1px solid var(--color-border);
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.btn-refresh-models:hover:not(:disabled) {
  background: var(--color-accent);
  color: white;
  border-color: var(--color-accent);
}

.btn-refresh-models:disabled {
  opacity: 0.4;
  cursor: not-allowed;
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

.config-value.key-configured {
  color: #2E7D32;
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