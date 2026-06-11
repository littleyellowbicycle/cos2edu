<template>
  <div class="character-creator">
    <header class="page-header">
      <div class="header-content">
        <router-link to="/characters" class="back-link">
          <span class="back-icon">←</span>
          <span>返回角色列表</span>
        </router-link>
        <div class="header-title-group">
          <h1 class="page-title">创建角色</h1>
          <p class="page-subtitle">选择模板或自定义创建教学角色</p>
        </div>
      </div>
    </header>

    <main class="creator-content">
      <div class="step-indicator">
        <div
          v-for="(s, idx) in steps"
          :key="idx"
          :class="['step-dot', { active: currentStep === idx, done: currentStep > idx }]"
          @click="currentStep = idx"
        >
          <span class="step-num">{{ idx + 1 }}</span>
          <span class="step-label">{{ s }}</span>
        </div>
      </div>

      <!-- Step 0: Pick Template -->
      <div v-if="currentStep === 0" class="step-panel">
        <h2 class="step-title">选择角色模板</h2>
        <p class="step-desc">从预设模板开始，或选择空白模板自定义创建。</p>
        <div class="template-grid">
          <div
            v-for="tpl in templates"
            :key="tpl.id"
            :class="['template-card', { selected: form.teaching_style === tpl.teaching_style }]"
            @click="applyTemplate(tpl)"
          >
            <div class="template-name">{{ tpl.name }}</div>
            <div class="template-style">风格：{{ tpl.teaching_style }}</div>
            <div class="template-personality">{{ (tpl.personality || '').slice(0, 60) }}...</div>
          </div>
        </div>
      </div>

      <!-- Step 1: Basic Info -->
      <div v-if="currentStep === 1" class="step-panel">
        <h2 class="step-title">基本信息</h2>
        <div class="form-group">
          <label class="form-label">角色名称</label>
          <input v-model="form.name" class="form-input" placeholder="例如：墨子" />
        </div>
        <div class="form-group">
          <label class="form-label">教学风格</label>
          <select v-model="form.teaching_style" class="form-input">
            <option value="socratic">苏格拉底式（提问引导）</option>
            <option value="hands_on_practice">实践型（做中学）</option>
            <option value="academic_rigorous">学术型（严谨推演）</option>
            <option value="storytelling">故事型（叙事示例）</option>
          </select>
        </div>
        <div class="form-group">
          <label class="form-label">角色性格</label>
          <textarea v-model="form.personality" class="form-textarea" rows="3" placeholder="描述角色的性格特点"></textarea>
        </div>
        <div class="form-group">
          <label class="form-label">角色背景</label>
          <textarea v-model="form.background" class="form-textarea" rows="3" placeholder="描述角色的故事背景"></textarea>
        </div>
      </div>

      <!-- Step 2: Prompt & Emotion -->
      <div v-if="currentStep === 2" class="step-panel">
        <h2 class="step-title">系统提示 & 情感配置</h2>
        <div class="form-group">
          <label class="form-label">系统提示模板</label>
          <textarea v-model="form.system_prompt_template" class="form-textarea wide" rows="8" placeholder="定义角色在教学对话中的行为模式"></textarea>
        </div>
        <div class="form-row">
          <div class="form-group flex-1">
            <label class="form-label">基准情绪 (0-1)</label>
            <input v-model.number="form.emotion_profile.base_mood" type="range" min="0" max="1" step="0.05" class="form-range" />
            <span class="range-value">{{ form.emotion_profile.base_mood?.toFixed(2) }}</span>
          </div>
          <div class="form-group flex-1">
            <label class="form-label">信任增长速率</label>
            <input v-model.number="form.relationship_dynamics.trust_growth_rate" type="range" min="0" max="0.1" step="0.005" class="form-range" />
            <span class="range-value">{{ form.relationship_dynamics.trust_growth_rate?.toFixed(3) }}</span>
          </div>
        </div>
      </div>

      <!-- Step 3: Review & Create -->
      <div v-if="currentStep === 3" class="step-panel">
        <h2 class="step-title">确认创建</h2>
        <div class="review-card">
          <div class="review-row">
            <span class="review-label">名称</span>
            <span class="review-value">{{ form.name || '(未命名)' }}</span>
          </div>
          <div class="review-row">
            <span class="review-label">教学风格</span>
            <span class="review-value">{{ styleLabels[form.teaching_style] || form.teaching_style }}</span>
          </div>
          <div class="review-row">
            <span class="review-label">性格</span>
            <span class="review-value">{{ form.personality?.slice(0, 80) }}{{ form.personality?.length > 80 ? '...' : '' }}</span>
          </div>
          <div class="review-row">
            <span class="review-label">背景</span>
            <span class="review-value">{{ form.background?.slice(0, 80) }}{{ form.background?.length > 80 ? '...' : '' }}</span>
          </div>
          <div class="review-row">
            <span class="review-label">基准情绪</span>
            <span class="review-value">{{ form.emotion_profile?.base_mood?.toFixed(2) }}</span>
          </div>
          <div class="review-row">
            <span class="review-label">信任增长</span>
            <span class="review-value">{{ form.relationship_dynamics?.trust_growth_rate?.toFixed(3) }}</span>
          </div>
        </div>
      </div>

      <div class="step-actions">
        <button v-if="currentStep > 0" class="btn-step prev" @click="currentStep--">← 上一步</button>
        <button v-if="currentStep < steps.length - 1" class="btn-step next" @click="currentStep++">下一步 →</button>
        <button v-if="currentStep === steps.length - 1" class="btn-step create" @click="createCharacter" :disabled="creating">
          {{ creating ? '创建中...' : '创建角色' }}
        </button>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import api from '@/api'

const router = useRouter()
const currentStep = ref(0)
const creating = ref(false)
const templates = ref([])

const steps = ['选择模板', '基本信息', '提示与情感', '确认创建']

const styleLabels = {
  socratic: '苏格拉底式',
  hands_on_practice: '实践型',
  academic_rigorous: '学术型',
  storytelling: '故事型',
}

const form = ref({
  name: '',
  teaching_style: 'socratic',
  personality: '',
  background: '',
  system_prompt_template: '',
  emotion_profile: {
    base_mood: 0.7,
    mood_decay: 0.01,
    event_sensitivity: {
      student_correct: 0.06,
      student_wrong: -0.01,
      student_engaged: 0.10,
      time_pressure: -0.05,
    },
  },
  relationship_dynamics: {
    trust_growth_rate: 0.015,
    trust_decay_rate: 0.008,
    max_trust: 1.0,
  },
})

async function loadTemplates() {
  try {
    const result = await api.content.getCharacterTemplates()
    templates.value = result.templates
  } catch (e) {
    console.error(e)
  }
}

function applyTemplate(tpl) {
  form.value.teaching_style = tpl.teaching_style
  form.value.personality = tpl.personality
  form.value.system_prompt_template = tpl.system_prompt_template
  currentStep.value = 1
}

async function createCharacter() {
  if (!form.value.name.trim()) {
    ElMessage.error('请输入角色名称')
    return
  }
  creating.value = true
  try {
    await api.content.createCharacterFromTemplate({
      name: form.value.name,
      teaching_style: form.value.teaching_style,
      personality: form.value.personality,
      background: form.value.background,
      system_prompt_template: form.value.system_prompt_template,
      emotion_profile: form.value.emotion_profile,
      relationship_dynamics: form.value.relationship_dynamics,
    })
    ElMessage.success(`角色"${form.value.name}"创建成功`)
    router.push('/characters')
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '创建失败')
  } finally {
    creating.value = false
  }
}

onMounted(() => {
  loadTemplates()
})
</script>

<style scoped>
.character-creator {
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

.creator-content {
  max-width: 800px;
  margin: 0 auto;
  padding: 32px 40px;
}

.step-indicator {
  display: flex;
  justify-content: center;
  gap: 24px;
  margin-bottom: 40px;
}

.step-dot {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  transition: all 0.2s;
}

.step-num {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: var(--color-border);
  color: var(--color-text-muted);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 600;
  transition: all 0.2s;
}

.step-dot.active .step-num {
  background: var(--color-accent);
  color: white;
}

.step-dot.done .step-num {
  background: var(--color-ink);
  color: white;
}

.step-label {
  font-size: 12px;
  color: var(--color-text-muted);
}

.step-dot.active .step-label {
  color: var(--color-accent);
}

.step-panel {
  animation: fadeIn 0.3s ease-out;
}

.step-title {
  font-family: var(--font-display);
  font-size: 28px;
  font-weight: 600;
  color: var(--color-ink);
  margin-bottom: 8px;
}

.step-desc {
  color: var(--color-text-muted);
  margin-bottom: 24px;
}

.template-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 16px;
}

.template-card {
  padding: 20px;
  border: 2px solid var(--color-border);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  background: var(--color-surface);
}

.template-card:hover {
  border-color: var(--color-accent-light);
  transform: translateY(-2px);
}

.template-card.selected {
  border-color: var(--color-accent);
  background: rgba(99, 102, 241, 0.05);
}

.template-name {
  font-family: var(--font-display);
  font-size: 18px;
  font-weight: 600;
  color: var(--color-ink);
  margin-bottom: 4px;
}

.template-style {
  font-size: 13px;
  color: var(--color-accent);
  margin-bottom: 8px;
}

.template-personality {
  font-size: 13px;
  color: var(--color-text-muted);
  line-height: 1.5;
}

.form-group {
  margin-bottom: 20px;
}

.form-label {
  display: block;
  font-size: 14px;
  font-weight: 600;
  color: var(--color-ink);
  margin-bottom: 6px;
}

.form-input {
  width: 100%;
  padding: 12px 16px;
  border: 1px solid var(--color-border);
  border-radius: 6px;
  background: var(--color-surface);
  color: var(--color-ink);
  font-size: 15px;
  font-family: var(--font-body);
  outline: none;
  transition: border-color 0.2s;
}

.form-input:focus {
  border-color: var(--color-accent);
}

.form-textarea {
  width: 100%;
  padding: 12px 16px;
  border: 1px solid var(--color-border);
  border-radius: 6px;
  background: var(--color-surface);
  color: var(--color-ink);
  font-size: 14px;
  font-family: var(--font-body);
  outline: none;
  resize: vertical;
  transition: border-color 0.2s;
}

.form-textarea.wide {
  font-family: 'Consolas', monospace;
  font-size: 13px;
  line-height: 1.6;
}

.form-textarea:focus {
  border-color: var(--color-accent);
}

.form-row {
  display: flex;
  gap: 20px;
}

.flex-1 {
  flex: 1;
}

.form-range {
  width: 100%;
  margin: 8px 0;
}

.range-value {
  font-size: 13px;
  font-family: monospace;
  color: var(--color-accent);
}

.review-card {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 8px;
  padding: 24px;
}

.review-row {
  display: flex;
  gap: 16px;
  padding: 12px 0;
  border-bottom: 1px solid var(--color-border);
}

.review-row:last-child {
  border-bottom: none;
}

.review-label {
  width: 120px;
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text-muted);
  flex-shrink: 0;
}

.review-value {
  font-size: 14px;
  color: var(--color-ink);
  flex: 1;
}

.step-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 32px;
  padding-top: 24px;
  border-top: 1px solid var(--color-border);
}

.btn-step {
  font-family: var(--font-body);
  font-size: 15px;
  font-weight: 600;
  padding: 12px 28px;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
  border: none;
}

.btn-step.prev {
  background: var(--color-surface);
  color: var(--color-ink);
  border: 1px solid var(--color-border);
}

.btn-step.prev:hover {
  border-color: var(--color-ink);
}

.btn-step.next {
  background: var(--color-ink);
  color: white;
}

.btn-step.next:hover {
  background: var(--color-accent);
}

.btn-step.create {
  background: var(--color-accent);
  color: white;
}

.btn-step.create:hover:not(:disabled) {
  opacity: 0.9;
}

.btn-step.create:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

@media (max-width: 768px) {
  .page-header {
    padding: 24px;
  }

  .creator-content {
    padding: 16px;
  }

  .template-grid {
    grid-template-columns: 1fr;
  }

  .form-row {
    flex-direction: column;
  }
}
</style>