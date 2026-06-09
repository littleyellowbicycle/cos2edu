<template>
  <router-link :to="to" class="feature-card" :aria-label="ariaLabel">
    <div class="feature-icon" aria-hidden="true">{{ icon }}</div>
    <h3>{{ title }}</h3>
    <p>{{ description }}</p>
    <span class="feature-arrow" aria-hidden="true">→</span>
  </router-link>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  icon: { type: String, required: true },
  title: { type: String, required: true },
  description: { type: String, required: true },
  to: { type: String, required: true },
})

const ariaLabel = computed(() => `前往${props.title}：${props.description}`)
</script>

<style scoped>
.feature-card {
  position: relative;
  display: block;
  padding: 40px 32px;
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  border-radius: 8px;
  cursor: pointer;
  text-decoration: none;
  color: inherit;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  overflow: hidden;
}

.feature-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 3px;
  background: var(--color-accent);
  transform: scaleX(0);
  transform-origin: left;
  transition: transform 0.4s ease;
}

.feature-card:hover::before,
.feature-card:focus-visible::before {
  transform: scaleX(1);
}

.feature-card:hover,
.feature-card:focus-visible {
  transform: translateY(-4px);
  box-shadow: var(--shadow-lg);
  border-color: var(--color-accent-light);
  outline: none;
}

.feature-icon {
  font-size: 32px;
  color: var(--color-accent);
  margin-bottom: 20px;
}

.feature-card h3 {
  font-family: var(--font-display);
  font-size: 24px;
  font-weight: 600;
  color: var(--color-ink);
  margin-bottom: 12px;
}

.feature-card p {
  font-size: 15px;
  line-height: 1.6;
  color: var(--color-text-muted);
}

.feature-arrow {
  display: inline-block;
  margin-top: 20px;
  font-size: 20px;
  color: var(--color-accent);
  transition: transform 0.3s ease;
}

.feature-card:hover .feature-arrow,
.feature-card:focus-visible .feature-arrow {
  transform: translateX(8px);
}
</style>
