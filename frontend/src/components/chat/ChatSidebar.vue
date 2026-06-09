<template>
  <aside class="chat-sidebar">
    <h3 class="sidebar-title">对话历史</h3>
    <div class="history-list">
      <button 
        v-for="(conv, index) in conversationHistory" 
        :key="conv.id"
        class="history-item"
        :class="{ active: conv.id === conversationId }"
        @click="$emit('select', conv)"
      >
        <span class="history-title">{{ conv.title || `对话 ${index + 1}` }}</span>
        <span class="history-date">{{ formatDate(conv.created_at) }}</span>
      </button>
    </div>
  </aside>
</template>

<script setup>
defineProps({
  conversationHistory: { type: Array, default: () => [] },
  conversationId: { type: [String, Number], default: null },
})

defineEmits(['select'])

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

@media (max-width: 768px) {
  .chat-sidebar {
    position: fixed;
    right: 0;
    top: 0;
    bottom: 0;
    z-index: 100;
    box-shadow: var(--shadow-lg);
  }
}
</style>
