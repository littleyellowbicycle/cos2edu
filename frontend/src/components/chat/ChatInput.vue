<template>
  <div class="input-area">
    <div class="input-wrapper">
      <label for="message-input" class="visually-hidden">输入消息</label>
      <textarea
        id="message-input"
        v-model="text"
        placeholder="输入你的问题... (Ctrl+Enter 发送)"
        @keydown.enter.ctrl="handleSend"
        @keydown.enter.exact.prevent="handleSend"
        rows="1"
        ref="inputTextarea"
        :disabled="sending"
        aria-describedby="input-hint"
        @input="autoResize"
      ></textarea>
      <button 
        class="btn-send" 
        @click="handleSend" 
        :disabled="!text.trim() || sending"
        aria-label="发送消息"
      >
        <span v-if="!sending">发送</span>
        <span v-else class="sending-dots" aria-label="发送中">...</span>
      </button>
    </div>
    <p id="input-hint" class="input-hint">按 Enter 发送，Ctrl+Enter 换行</p>
  </div>
</template>

<script setup>
import { ref, computed, nextTick, watch } from 'vue'

const props = defineProps({
  modelValue: { type: String, default: '' },
  sending: { type: Boolean, default: false },
})

const emit = defineEmits(['update:modelValue', 'send'])

const inputTextarea = ref(null)

const text = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val),
})

function handleSend() {
  if (!text.value.trim() || props.sending) return
  emit('send', text.value.trim())
}

function autoResize() {
  const el = inputTextarea.value
  if (!el) return
  el.style.height = 'auto'
  el.style.height = Math.min(el.scrollHeight, 150) + 'px'
}

function focus() {
  inputTextarea.value?.focus()
}

defineExpose({ focus })

watch(() => props.modelValue, () => {
  nextTick(autoResize)
})
</script>

<style scoped>
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

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

@media (max-width: 768px) {
  .input-area {
    padding: 16px 20px;
  }
}
</style>
