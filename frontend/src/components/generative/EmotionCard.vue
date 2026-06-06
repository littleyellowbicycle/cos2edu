<template>
  <div class="emotion-card" :class="moodClass">
    <div class="emotion-header">
      <span class="emotion-avatar">{{ avatar }}</span>
      <span class="emotion-name">{{ characterName }}</span>
      <span class="emotion-trend">{{ moodTrend }}</span>
    </div>
    <div class="emotion-bars">
      <div class="emotion-bar-group">
        <span class="emotion-label">心情</span>
        <div class="emotion-bar">
          <div class="emotion-bar-fill mood-fill" :style="{ width: moodPercent + '%' }"></div>
        </div>
        <span class="emotion-value">{{ moodPercent }}%</span>
      </div>
      <div class="emotion-bar-group">
        <span class="emotion-label">信任</span>
        <div class="emotion-bar trust-bar">
          <div class="emotion-bar-fill trust-fill" :style="{ width: trustPercent + '%' }"></div>
        </div>
        <span class="emotion-value">{{ trustPercent }}%</span>
      </div>
    </div>
    <p v-if="reason" class="emotion-reason">{{ reason }}</p>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  mood: { type: Number, default: 0.5 },
  trust: { type: Number, default: 0.5 },
  characterName: { type: String, default: '' },
  reason: { type: String, default: '' },
  moodDirection: { type: String, default: '' },
})

const moodPercent = computed(() => Math.round(Math.max(0, Math.min(1, props.mood)) * 100))
const trustPercent = computed(() => Math.round(Math.max(0, Math.min(1, props.trust)) * 100))
const avatar = computed(() => {
  if (props.mood >= 0.7) return '😊'
  if (props.mood >= 0.4) return '🤔'
  return '😟'
})

const moodClass = computed(() => {
  if (props.mood >= 0.7) return 'mood-positive'
  if (props.mood >= 0.4) return 'mood-neutral'
  return 'mood-negative'
})

const moodTrend = computed(() => {
  if (props.moodDirection === 'up') return '↑'
  if (props.moodDirection === 'down') return '↓'
  if (props.moodDirection === 'stable') return '→'
  return ''
})
</script>

<style scoped>
.emotion-card {
  padding: 14px 16px;
  border-radius: 10px;
  background: var(--color-surface, #fff);
  border: 1px solid var(--color-border, #E5E0D8);
  box-shadow: var(--shadow-sm, 0 1px 3px rgba(44, 36, 22, 0.06));
  transition: all 0.3s ease;
}

.emotion-card.mood-positive {
  border-left: 3px solid #4caf50;
}

.emotion-card.mood-neutral {
  border-left: 3px solid #ff9800;
}

.emotion-card.mood-negative {
  border-left: 3px solid #f44336;
}

.emotion-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
}

.emotion-avatar {
  font-size: 20px;
}

.emotion-name {
  font-weight: 600;
  font-size: 14px;
  color: var(--color-ink, #2C2416);
  flex: 1;
}

.emotion-trend {
  font-size: 16px;
  font-weight: 700;
}

.mood-positive .emotion-trend {
  color: #4caf50;
}

.mood-neutral .emotion-trend {
  color: #ff9800;
}

.mood-negative .emotion-trend {
  color: #f44336;
}

.emotion-bars {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.emotion-bar-group {
  display: flex;
  align-items: center;
  gap: 8px;
}

.emotion-label {
  font-size: 12px;
  font-weight: 600;
  min-width: 32px;
  color: var(--color-text-muted, #6B6B6B);
}

.emotion-bar {
  flex: 1;
  height: 8px;
  border-radius: 4px;
  background: var(--color-bg-warm, #F5F1EB);
  overflow: hidden;
}

.emotion-bar-fill {
  height: 100%;
  border-radius: 4px;
  transition: width 0.4s ease;
}

.mood-fill {
  background: linear-gradient(90deg, #6c5ce7, #a29bfe);
}

.trust-fill {
  background: linear-gradient(90deg, #00b894, #55efc4);
}

.emotion-value {
  font-size: 12px;
  font-weight: 700;
  min-width: 32px;
  text-align: right;
}

.mood-positive .emotion-value {
  color: #4caf50;
}

.mood-neutral .emotion-value {
  color: #ff9800;
}

.mood-negative .emotion-value {
  color: #f44336;
}

.emotion-reason {
  margin-top: 8px;
  font-size: 13px;
  color: var(--color-text-muted, #6B6B6B);
  font-style: italic;
}
</style>