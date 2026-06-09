<template>
  <article class="character-card" :style="{ animationDelay }">
    <div class="card-avatar">
      <div class="avatar-placeholder" :style="avatarStyle">{{ avatarDisplay }}</div>
    </div>
    <div class="card-content">
      <h3 class="card-title">{{ character.name }}</h3>
      <p class="card-description">{{ character.description || '暂无描述' }}</p>
      <div class="card-tags">
        <span class="tag" v-if="character.personality">{{ character.personality }}</span>
        <span
          class="mood-tag"
          :class="moodClass"
          v-if="moodLabel"
        >{{ moodLabel }}</span>
      </div>
    </div>
    <div class="card-actions">
      <button class="btn-chat" @click="$emit('chat', character)">开始对话</button>
      <button class="btn-edit" @click="$emit('edit', character)">编辑</button>
      <button class="btn-export" @click="$emit('export', character)" title="导出角色卡">📤</button>
      <button class="btn-delete" @click="$emit('delete', character.id)">删除</button>
    </div>
  </article>
</template>

<script setup>
import { computed } from 'vue'
import { getAvatarDisplay, getAvatarStyle } from '@/composables/useCharacterAvatar'

const props = defineProps({
  character: { type: Object, required: true },
  moodLabel: { type: String, default: '' },
  moodClass: { type: String, default: '' },
  animationDelay: { type: String, default: '0ms' },
})

defineEmits(['chat', 'edit', 'export', 'delete'])

const avatarDisplay = computed(() => getAvatarDisplay(props.character))
const avatarStyle = computed(() => getAvatarStyle(props.character))
</script>

<style scoped>
.character-card {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 8px;
  padding: 24px;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  animation: fadeInUp 0.5s ease-out backwards;
}

.character-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-lg);
  border-color: var(--color-accent-light);
}

.card-avatar {
  margin-bottom: 16px;
}

.avatar-placeholder {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  background: var(--color-bg-warm);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 36px;
  color: var(--color-accent);
  border: 2px solid var(--color-border);
  font-family: var(--font-display);
}

.card-content {
  flex: 1;
  width: 100%;
}

.card-title {
  font-family: var(--font-display);
  font-size: 20px;
  font-weight: 600;
  color: var(--color-ink);
  margin-bottom: 8px;
}

.card-description {
  font-size: 14px;
  line-height: 1.6;
  color: var(--color-text-muted);
  margin-bottom: 12px;
  min-height: 44px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.card-tags {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
  justify-content: center;
  margin-bottom: 16px;
}

.tag,
.mood-tag {
  display: inline-block;
  font-size: 12px;
  padding: 2px 10px;
  border-radius: 12px;
  background: var(--color-bg-warm);
  border: 1px solid var(--color-border);
  color: var(--color-text);
}

.mood-tag.mood-positive {
  background: #e8f5e9;
  color: #2e7d32;
  border-color: #a5d6a7;
}

.mood-tag.mood-neutral {
  background: #fff3e0;
  color: #e65100;
  border-color: #ffcc80;
}

.mood-tag.mood-negative {
  background: #ffebee;
  color: #c62828;
  border-color: #ef9a9a;
}

.card-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  justify-content: center;
  width: 100%;
}

.card-actions button {
  font-family: var(--font-body);
  font-size: 13px;
  padding: 8px 14px;
  border-radius: 4px;
  border: 1px solid var(--color-border);
  background: var(--color-bg);
  color: var(--color-text);
  cursor: pointer;
  transition: all 0.2s;
}

.card-actions button:hover {
  background: var(--color-bg-warm);
  border-color: var(--color-ink);
}

.btn-chat {
  background: var(--color-ink) !important;
  color: white !important;
  border-color: var(--color-ink) !important;
}

.btn-chat:hover {
  background: var(--color-accent) !important;
  border-color: var(--color-accent) !important;
}

.btn-delete:hover {
  background: #ffebee !important;
  border-color: #c62828 !important;
  color: #c62828 !important;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
