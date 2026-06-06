<template>
  <Transition name="scene-fade">
    <div v-if="sceneId" class="scene-card-overlay" @click.self="$emit('dismiss')">
      <div class="scene-card" :class="[`scene-${transition}`]">
        <div class="scene-card-bg" :style="bgStyle"></div>
        <div class="scene-card-overlay-inner">
          <div class="scene-badge">{{ phaseLabel }}</div>
          <h2 class="scene-name">{{ displayName }}</h2>
          <p v-if="description" class="scene-desc">{{ description }}</p>
          <div v-if="allowedActions && allowedActions.length" class="scene-actions">
            <span v-for="action in allowedActions" :key="action" class="action-tag">{{ actionLabel(action) }}</span>
          </div>
        </div>
        <button class="scene-close" @click="$emit('dismiss')" aria-label="关闭场景">&#10005;</button>
      </div>
    </div>
  </Transition>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  sceneId: { type: String, default: '' },
  sceneName: { type: String, default: '' },
  description: { type: String, default: '' },
  transition: { type: String, default: 'fade' },
  phase: { type: String, default: '' },
  allowedActions: { type: Array, default: () => [] },
})

defineEmits(['dismiss'])

const displayName = computed(() => props.sceneName || props.sceneId)

const phaseLabel = computed(() => {
  const labels = {
    morning: '早晨',
    afternoon: '下午',
    evening: '傍晚',
    night: '夜晚',
    study: '学习中',
    review: '复习',
    exam: '考核',
    break: '休息',
  }
  return labels[props.phase] || props.phase || ''
})

const bgStyle = computed(() => {
  const gradients = {
    morning: 'linear-gradient(135deg, #FFF3E0 0%, #FFCC80 100%)',
    afternoon: 'linear-gradient(135deg, #E3F2FD 0%, #90CAF9 100%)',
    evening: 'linear-gradient(135deg, #FBE9E7 0%, #FFAB91 100%)',
    night: 'linear-gradient(135deg, #1A237E 0%, #3F51B5 100%)',
    study: 'linear-gradient(135deg, #E8F5E9 0%, #81C784 100%)',
    review: 'linear-gradient(135deg, #FFF8E1 0%, #FFD54F 100%)',
    exam: 'linear-gradient(135deg, #FFEBEE 0%, #EF9A9A 100%)',
    break: 'linear-gradient(135deg, #F3E5F5 0%, #CE93D8 100%)',
  }
  return { background: gradients[props.phase] || 'linear-gradient(135deg, #F5F1EB 0%, #E5E0D8 100%)' }
})

function actionLabel(action) {
  const labels = {
    ask: '提问',
    answer: '回答',
    think: '思考',
    review: '复习',
    explore: '探索',
    quiz: '测验',
    discuss: '讨论',
  }
  return labels[action] || action
}
</script>

<style scoped>
.scene-card-overlay {
  position: fixed;
  inset: 0;
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(44, 36, 22, 0.5);
  backdrop-filter: blur(4px);
}

.scene-card {
  position: relative;
  width: 400px;
  max-width: 90vw;
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 12px 40px rgba(44, 36, 22, 0.2);
}

.scene-card-bg {
  position: absolute;
  inset: 0;
  z-index: 0;
}

.scene-card-overlay-inner {
  position: relative;
  z-index: 1;
  padding: 32px 24px 24px;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  min-height: 180px;
}

.scene-badge {
  display: inline-block;
  font-size: 12px;
  font-weight: 600;
  padding: 2px 10px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.7);
  color: var(--color-ink, #2C2416);
  margin-bottom: 8px;
}

.scene-name {
  font-family: var(--font-display, serif);
  font-size: 22px;
  font-weight: 700;
  color: var(--color-ink, #2C2416);
  margin: 0 0 6px;
}

.scene-desc {
  font-size: 14px;
  color: var(--color-text, #1A1A1A);
  opacity: 0.85;
  margin: 0 0 12px;
  line-height: 1.5;
}

.scene-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  justify-content: center;
}

.action-tag {
  font-size: 12px;
  padding: 3px 10px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.6);
  color: var(--color-ink, #2C2416);
  border: 1px solid rgba(44, 36, 22, 0.15);
}

.scene-close {
  position: absolute;
  top: 10px;
  right: 10px;
  z-index: 2;
  width: 28px;
  height: 28px;
  border: none;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.7);
  color: var(--color-ink, #2C2416);
  font-size: 16px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.2s;
}

.scene-close:hover {
  background: rgba(255, 255, 255, 0.95);
}

.scene-fade-enter-active {
  transition: opacity 0.4s ease;
}

.scene-fade-leave-active {
  transition: opacity 0.3s ease;
}

.scene-fade-enter-from,
.scene-fade-leave-to {
  opacity: 0;
}
</style>