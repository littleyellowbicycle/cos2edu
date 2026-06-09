<template>
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
    <button class="btn-sidebar" @click="$emit('toggle-sidebar')" :aria-expanded="showSidebar">
      {{ showSidebar ? '隐藏' : '显示' }}历史
    </button>
  </header>
</template>

<script setup>
defineProps({
  characterName: { type: String, default: '' },
  materialTitle: { type: String, default: '' },
  isTyping: { type: Boolean, default: false },
  sending: { type: Boolean, default: false },
  currentScene: { type: String, default: '' },
  moodLabel: { type: String, default: '' },
  moodBadgeClass: { type: String, default: '' },
  showSidebar: { type: Boolean, default: false },
})

defineEmits(['toggle-sidebar'])
</script>

<style scoped>
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

@media (max-width: 768px) {
  .chat-header {
    padding: 16px 20px;
  }
}
</style>
