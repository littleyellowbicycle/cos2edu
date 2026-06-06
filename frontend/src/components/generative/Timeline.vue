<template>
  <div class="timeline-generative">
    <div v-if="title" class="timeline-title">{{ title }}</div>
    <div class="timeline-track">
      <div
        v-for="(event, idx) in normalizedEvents"
        :key="idx"
        class="timeline-item"
        :class="{ 'timeline-item-active': event.active }"
      >
        <div class="timeline-dot-wrapper">
          <div class="timeline-dot" :class="{ 'dot-active': event.active }"></div>
          <div v-if="idx < normalizedEvents.length - 1" class="timeline-line"></div>
        </div>
        <div class="timeline-content">
          <span class="timeline-year">{{ event.year || event.date || '' }}</span>
          <p class="timeline-label">{{ event.label || event.name || '' }}</p>
          <p v-if="event.detail" class="timeline-detail">{{ event.detail }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  title: { type: String, default: '' },
  events: { type: Array, default: () => [] },
  activeIndex: { type: Number, default: -1 },
})

const normalizedEvents = computed(() =>
  (props.events || []).map((e, i) => ({
    ...e,
    active: i === props.activeIndex,
  }))
)
</script>

<style scoped>
.timeline-generative {
  margin: 12px 0;
  padding: 16px;
  background: var(--color-surface, white);
  border-radius: 12px;
  border: 1px solid var(--color-border, #E5E0D8);
  max-width: 100%;
}

.timeline-title {
  font-family: var(--font-display, serif);
  font-size: 16px;
  font-weight: 700;
  color: var(--color-ink, #2C2416);
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 2px solid var(--color-accent, #8B4513);
}

.timeline-track {
  display: flex;
  flex-direction: column;
  gap: 0;
}

.timeline-item {
  display: flex;
  gap: 12px;
  min-height: 48px;
}

.timeline-dot-wrapper {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 20px;
  flex-shrink: 0;
}

.timeline-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: var(--color-border, #E5E0D8);
  border: 2px solid var(--color-ink, #2C2416);
  flex-shrink: 0;
  margin-top: 4px;
  transition: all 0.3s;
}

.dot-active {
  background: var(--color-accent, #8B4513);
  box-shadow: 0 0 0 3px rgba(139, 69, 19, 0.25);
}

.timeline-line {
  width: 2px;
  flex: 1;
  background: var(--color-border, #E5E0D8);
  min-height: 20px;
}

.timeline-item-active .timeline-line {
  background: var(--color-accent, #8B4513);
}

.timeline-content {
  flex: 1;
  padding-bottom: 12px;
}

.timeline-year {
  display: inline-block;
  font-family: var(--font-mono, monospace);
  font-size: 12px;
  font-weight: 700;
  color: var(--color-accent, #8B4513);
  background: rgba(139, 69, 19, 0.1);
  padding: 1px 8px;
  border-radius: 4px;
  margin-bottom: 2px;
}

.timeline-label {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-ink, #2C2416);
  margin: 2px 0 0;
  line-height: 1.4;
}

.timeline-detail {
  font-size: 12px;
  color: var(--color-text-muted, #6B6B6B);
  margin: 2px 0 0;
  line-height: 1.4;
}

.timeline-item-active .timeline-label {
  color: var(--color-accent, #8B4513);
}
</style>