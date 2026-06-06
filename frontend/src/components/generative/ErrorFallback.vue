<template>
  <div class="error-fallback">
    <span class="error-icon">&#9888;</span>
    <span class="error-text">{{ componentName }} 加载失败</span>
    <button v-if="retry" class="error-retry" @click="retry">重试</button>
  </div>
</template>

<script setup>
defineProps({
  componentName: { type: String, default: '组件' },
  error: { type: Error, default: null },
  retry: { type: Function, default: null },
})
</script>

<style scoped>
.error-fallback {
  padding: 12px 16px;
  border-radius: 8px;
  background: #fef2f2;
  border: 1px solid var(--color-error, #C75050);
  color: var(--color-error, #C75050);
  font-size: 14px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.error-icon {
  font-size: 16px;
}

.error-text {
  flex: 1;
}

.error-retry {
  padding: 4px 12px;
  font-size: 12px;
  font-family: var(--font-body);
  background: transparent;
  border: 1px solid var(--color-error, #C75050);
  border-radius: 4px;
  color: var(--color-error, #C75050);
  cursor: pointer;
  transition: all 0.2s;
}

.error-retry:hover {
  background: var(--color-error, #C75050);
  color: white;
}
</style>