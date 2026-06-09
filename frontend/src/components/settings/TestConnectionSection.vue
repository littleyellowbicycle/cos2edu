<template>
  <section class="settings-section test-section">
    <h2 class="section-title">测试连接</h2>
    <p class="section-description">保存配置后，可以测试 AI 连接是否正常。</p>
    <button
      type="button"
      class="btn-test"
      @click="$emit('test')"
      :disabled="testing || !canTest"
    >
      {{ testing ? '测试中...' : '测试 AI 连接' }}
    </button>
    <div v-if="testResult" class="test-result" :class="testResult.type">
      {{ testResult.message }}
    </div>
  </section>
</template>

<script setup>
defineProps({
  testing: { type: Boolean, default: false },
  canTest: { type: Boolean, default: false },
  testResult: { type: Object, default: null },
})

defineEmits(['test'])
</script>

<style scoped>
.settings-section.test-section {
  margin-top: 24px;
}

.section-title {
  font-family: var(--font-display);
  font-size: 20px;
  font-weight: 600;
  color: var(--color-ink);
  margin: 0 0 8px;
}

.section-description {
  font-size: 14px;
  color: var(--color-text-muted);
  margin: 0 0 16px;
  line-height: 1.6;
}

.btn-test {
  font-family: var(--font-body);
  font-size: 14px;
  font-weight: 600;
  padding: 10px 24px;
  background: var(--color-ink);
  color: white;
  border: 1px solid var(--color-ink);
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-test:hover:not(:disabled) {
  background: var(--color-accent);
  border-color: var(--color-accent);
}

.btn-test:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.test-result {
  margin-top: 12px;
  padding: 12px 16px;
  border-radius: 4px;
  font-size: 14px;
}

.test-result.success {
  background: #f0f9eb;
  color: #67c23a;
  border: 1px solid #e1f3d8;
}

.test-result.error {
  background: #fef0f0;
  color: #f56c6c;
  border: 1px solid #fde2e2;
}

.test-result.info {
  background: #f4f4f5;
  color: var(--color-text-muted);
  border: 1px solid var(--color-border);
}
</style>
