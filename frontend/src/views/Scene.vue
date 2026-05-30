<template>
  <div class="scene-page">
    <div class="scene-header">
      <h1>{{ currentSceneName }}</h1>
      <p class="scene-desc">{{ narrative.world.sceneDescription }}</p>
    </div>

    <div class="scene-info-bar">
      <div class="info-item">
        <span class="info-label">学习进度</span>
        <el-progress :percentage="progressPercent" :stroke-width="8" status="success" />
      </div>
      <div class="info-item">
        <span class="info-label">当前天数</span>
        <span class="info-value">第 {{ narrative.world.currentDay }} / {{ narrative.world.totalDays }} 天</span>
      </div>
      <div class="info-item">
        <span class="info-label">叙事阶段</span>
        <span class="info-value">{{ phaseLabel }}</span>
      </div>
    </div>

    <div class="scene-selector" v-if="availableScenes.length > 0">
      <h3>场景切换</h3>
      <div class="scene-cards">
        <div
          v-for="scene in availableScenes"
          :key="scene.id"
          class="scene-card"
          :class="{ 'scene-active': scene.id === narrative.world.currentScene }"
          @click="handleSwitchScene(scene.id)"
        >
          <div class="scene-card-name">{{ scene.name }}</div>
          <div class="scene-card-desc">{{ scene.description }}</div>
        </div>
      </div>
    </div>

    <div class="action-panel">
      <h3>可用行动</h3>
      <div class="action-buttons">
        <el-button
          v-for="action in narrative.world.allowedActions"
          :key="action"
          :type="actionButtonType(action)"
          @click="handleAction(action)"
          class="action-btn"
        >
          {{ actionLabels[action] || action }}
        </el-button>
      </div>
    </div>

    <div class="current-point" v-if="narrative.progress.currentPoint">
      <h3>当前知识点</h3>
      <div class="point-card">
        <span class="point-name">{{ narrative.progress.currentPointName || narrative.progress.currentPoint }}</span>
        <el-tag size="small" type="info">学习中</el-tag>
      </div>
      <el-button
        type="primary"
        size="small"
        @click="startAssessment"
        v-if="narrative.progress.currentPoint"
      >
        开始考核
      </el-button>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useNarrativeStore } from '@/stores/narrative'
import { useWebSocket } from '@/composables/useWebSocket'

const narrative = useNarrativeStore()
const ws = useWebSocket()
const router = useRouter()

const actionLabels = {
  teach: '讲解',
  question: '提问',
  discuss: '讨论',
  debate: '辩论',
  practice: '练习',
  exam: '考核',
  review: '复习',
  present: '展示',
  vote: '投票',
}

const phaseLabels = {
  prologue: '序章',
  phase_1_basics: '基础篇',
  phase_2_advanced: '进阶篇',
  phase_3_practice: '实战篇',
}

const currentSceneName = computed(() => narrative.world.sceneName || '教室')

const progressPercent = computed(() => {
  const total = narrative.progress.totalPoints || 1
  const completed = narrative.progress.completedPoints || 0
  return Math.round(completed / total * 100)
})

const phaseLabel = computed(() => phaseLabels[narrative.world.narrativePhase] || narrative.world.narrativePhase)

const availableScenes = computed(() => {
  const scenes = []
  const current = narrative.world.currentScene
  const allScenes = [
    { id: 'classroom', name: '教室', description: '明亮的教室，适合讲解和讨论' },
    { id: 'library', name: '图书馆', description: '安静的图书馆，适合自学和阅读' },
    { id: 'exam_room', name: '考核室', description: '正式的考核环境，检验学习成果' },
    { id: 'debate_hall', name: '辩论厅', description: '开放的辩论空间，锻炼思辨能力' },
  ]
  return allScenes
})

function handleSwitchScene(sceneId) {
  ws.switchScene(sceneId)
}

function handleAction(action) {
  if (action === 'exam') {
    startAssessment()
  } else if (action === 'teach' || action === 'question' || action === 'discuss') {
    router.push('/conversations')
  }
}

function actionButtonType(action) {
  if (action === 'exam') return 'danger'
  if (action === 'practice') return 'warning'
  return 'primary'
}

function startAssessment() {
  const pointId = narrative.progress.currentPoint
  if (pointId) {
    ws.startAssessment(pointId)
    router.push('/exam')
  }
}
</script>

<style scoped>
.scene-page {
  max-width: 900px;
  margin: 0 auto;
  padding: 24px;
}

.scene-header {
  text-align: center;
  margin-bottom: 32px;
}

.scene-header h1 {
  font-size: 32px;
  font-weight: 600;
  color: var(--color-ink);
  margin-bottom: 8px;
}

.scene-desc {
  color: var(--color-text-muted);
  font-size: 15px;
}

.scene-info-bar {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 16px;
  margin-bottom: 32px;
  padding: 16px 20px;
  background: var(--color-surface);
  border-radius: 8px;
  border: 1px solid var(--color-border);
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.info-label {
  font-size: 12px;
  color: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.info-value {
  font-size: 15px;
  color: var(--color-ink);
  font-weight: 500;
}

.scene-selector {
  margin-bottom: 32px;
}

.scene-selector h3 {
  font-size: 18px;
  font-weight: 600;
  color: var(--color-ink);
  margin-bottom: 16px;
}

.scene-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
}

.scene-card {
  padding: 16px;
  border: 1px solid var(--color-border);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s;
  background: var(--color-surface);
}

.scene-card:hover {
  border-color: var(--color-accent);
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

.scene-card.scene-active {
  border-color: var(--color-accent);
  background: rgba(var(--color-accent-rgb, 99, 102, 241), 0.1);
}

.scene-card-name {
  font-size: 16px;
  font-weight: 600;
  color: var(--color-ink);
  margin-bottom: 4px;
}

.scene-card-desc {
  font-size: 13px;
  color: var(--color-text-muted);
}

.action-panel {
  margin-bottom: 32px;
}

.action-panel h3 {
  font-size: 18px;
  font-weight: 600;
  color: var(--color-ink);
  margin-bottom: 16px;
}

.action-buttons {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.action-btn {
  min-width: 80px;
}

.current-point {
  margin-bottom: 32px;
}

.current-point h3 {
  font-size: 18px;
  font-weight: 600;
  color: var(--color-ink);
  margin-bottom: 16px;
}

.point-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 8px;
  margin-bottom: 12px;
}

.point-name {
  font-size: 16px;
  font-weight: 500;
}

@media (max-width: 768px) {
  .scene-info-bar {
    grid-template-columns: 1fr;
  }

  .scene-cards {
    grid-template-columns: 1fr;
  }
}
</style>