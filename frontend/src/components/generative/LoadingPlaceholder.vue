<template>
  <div class="loading-placeholder">
    <div class="loading-shimmer"></div>
  </div>
</template>

<script setup>
</script>

<style scoped>
.loading-placeholder {
  padding: 16px;
  border-radius: 8px;
  background: var(--color-surface, #fff);
  border: 1px solid var(--color-border, #E5E0D8);
  min-height: 80px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.loading-shimmer {
  width: 100%;
  height: 16px;
  border-radius: 4px;
  background: linear-gradient(90deg, var(--color-border, #E5E0D8) 25%, var(--color-bg-warm, #F5F1EB) 50%, var(--color-border, #E5E0D8) 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
}
</style>