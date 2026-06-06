<template>
  <div class="knowledge-graph" role="img" :aria-label="title || '知识图谱'">
    <div v-if="title" class="kg-title">{{ title }}</div>
    <div class="kg-container">
      <div class="kg-center-node" :class="{ 'kg-highlight': true }">
        <span class="kg-node-icon">&#128218;</span>
        <span class="kg-node-label">{{ highlight || '当前知识点' }}</span>
        <span class="kg-mastery-bar">
          <progress :value="masteryPercent" max="100" class="kg-progress"></progress>
          <span class="kg-mastery-pct">{{ masteryPercent }}%</span>
        </span>
      </div>
      <div v-if="prerequisites.length" class="kg-section">
        <h4 class="kg-section-title">&#9664; 前置知识</h4>
        <div class="kg-nodes">
          <div
            v-for="pre in prerequisites"
            :key="pre.id || pre.name"
            class="kg-node kg-node-pre"
            :class="{ 'kg-node-done': pre.mastered }"
          >
            <span class="kg-node-dot" :class="{ 'dot-done': pre.mastered }"></span>
            <span class="kg-node-text">{{ pre.name || pre.label }}</span>
          </div>
        </div>
      </div>
      <div v-if="dependencies.length" class="kg-section">
        <h4 class="kg-section-title">&#9654; 后续知识</h4>
        <div class="kg-nodes">
          <div
            v-for="dep in dependencies"
            :key="dep.id || dep.name"
            class="kg-node kg-node-dep"
          >
            <span class="kg-node-dot"></span>
            <span class="kg-node-text">{{ dep.name || dep.label }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  title: { type: String, default: '' },
  highlight: { type: String, default: '' },
  depth: { type: Number, default: 2 },
  prerequisites: { type: Array, default: () => [] },
  dependencies: { type: Array, default: () => [] },
  masteryLevel: { type: Number, default: 0 },
})

const masteryPercent = computed(() => Math.round(Math.max(0, Math.min(1, props.masteryLevel)) * 100))
</script>

<style scoped>
.knowledge-graph {
  margin: 12px 0;
  padding: 16px;
  background: var(--color-surface, white);
  border-radius: 12px;
  border: 2px solid var(--color-accent, #8B4513);
  max-width: 100%;
}

.kg-title {
  font-family: var(--font-display, serif);
  font-size: 16px;
  font-weight: 700;
  color: var(--color-ink, #2C2416);
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 2px solid var(--color-accent, #8B4513);
}

.kg-container {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.kg-center-node {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  padding: 12px;
  background: rgba(139, 69, 19, 0.08);
  border: 2px solid var(--color-accent, #8B4513);
  border-radius: 10px;
}

.kg-node-icon {
  font-size: 24px;
}

.kg-node-label {
  font-weight: 700;
  font-size: 15px;
  color: var(--color-ink, #2C2416);
  text-align: center;
}

.kg-mastery-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  max-width: 200px;
}

.kg-progress {
  flex: 1;
  height: 10px;
  border: 1px solid var(--color-border, #E5E0D8);
  border-radius: 5px;
  overflow: hidden;
  background: var(--color-surface, white);
}

.kg-progress::-webkit-progress-bar {
  background: var(--color-surface, white);
  border-radius: 5px;
}

.kg-progress::-webkit-progress-value {
  background: linear-gradient(90deg, #6c5ce7, #a29bfe);
  border-radius: 5px;
  transition: width 0.4s ease;
}

.kg-progress::-moz-progress-bar {
  background: linear-gradient(90deg, #6c5ce7, #a29bfe);
  border-radius: 5px;
}

.kg-mastery-pct {
  font-size: 12px;
  font-weight: 700;
  color: #6c5ce7;
  min-width: 32px;
  text-align: right;
}

.kg-section {
  margin-top: 4px;
}

.kg-section-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text-muted, #6B6B6B);
  margin: 0 0 6px;
}

.kg-nodes {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.kg-node {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  border-radius: 6px;
  font-size: 13px;
  background: var(--color-bg-warm, #F5F1EB);
  border: 1px solid var(--color-border, #E5E0D8);
  color: var(--color-ink, #2C2416);
  transition: all 0.2s;
}

.kg-node-pre {
  border-left: 3px solid #4caf50;
}

.kg-node-dep {
  border-left: 3px solid #2196f3;
}

.kg-node-done {
  background: #e8f5e9;
}

.kg-node-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--color-border, #E5E0D8);
  flex-shrink: 0;
}

.dot-done {
  background: #4caf50;
}

.kg-node-text {
  line-height: 1.3;
}
</style>