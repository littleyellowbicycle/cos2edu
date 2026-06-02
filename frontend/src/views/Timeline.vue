<template>
  <div class="timeline-page">
    <div class="timeline-header">
      <h1>&#x1F4C5; 学习时间线</h1>
      <p class="subtitle">
        第 {{ narrative.world.currentDay }} 天 / 共 {{ narrative.world.totalDays }} 天
        <span v-if="narrative.world.activeSyllabusName" class="active-syllabus-badge">{{ narrative.world.activeSyllabusName }}</span>
      </p>
    </div>

    <div class="progress-bar-container">
      <div class="progress-track">
        <div class="progress-fill" :style="{ width: (narrative.world.progressPercent || 0) + '%' }"></div>
      </div>
      <p class="progress-text">{{ narrative.world.progressPercent || 0 }}% 完成</p>
    </div>

    <div class="current-scene-card" :style="{ backgroundImage: sceneBg }">
      <div class="scene-overlay">
        <div class="scene-badge">{{ phaseLabel }}</div>
        <h2 class="scene-name">{{ narrative.world.sceneName }}</h2>
        <p class="scene-desc">{{ narrative.world.sceneDescription }}</p>
        <div class="scene-actions">
          <span v-for="action in narrative.world.allowedActions" :key="action" class="action-tag">{{ actionLabel(action) }}</span>
        </div>
      </div>
    </div>

    <div class="scenes-section">
      <h3 class="section-title">&#x1F3AF; 场景切换</h3>
      <div class="scenes-grid">
        <div
          v-for="scene in availableScenes"
          :key="scene.id"
          class="scene-card"
          :class="{ 'scene-active': scene.id === narrative.world.currentScene }"
          @click="switchScene(scene.id)"
        >
          <div class="scene-card-name">{{ scene.name }}</div>
          <div class="scene-card-desc">{{ scene.description }}</div>
          <div class="scene-card-actions">{{ scene.allowed_actions.join(' / ') }}</div>
        </div>
      </div>
    </div>

    <div class="current-progress" v-if="narrative.progress.currentPoint">
      <div class="progress-header">
        <h3>&#x1F4D6; 当前学习</h3>
        <span class="status-label" :class="'status-' + narrative.progress.status">{{ statusLabel }}</span>
      </div>
      <div class="progress-detail">
        <span class="point-name">{{ narrative.progress.currentPointName || narrative.progress.currentPoint }}</span>
        <div class="mastery-bar">
          <div class="mastery-fill" :style="{ width: Math.round((narrative.progress.mastery || 0) * 100) + '%' }"></div>
        </div>
        <span class="mastery-pct">{{ Math.round((narrative.progress.mastery || 0) * 100) }}%</span>
      </div>
    </div>

    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-value">{{ narrative.progress.completedPoints }}</div>
        <div class="stat-label">已完成知识点</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ narrative.progress.totalPoints }}</div>
        <div class="stat-label">总知识点</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ narrative.world.currentDay }}</div>
        <div class="stat-label">学习天数</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ phaseLabel }}</div>
        <div class="stat-label">当前阶段</div>
      </div>
    </div>

    <div class="time-advance" v-if="canAdvanceTime">
      <button class="btn-advance" @click="advanceTime">&#x23E9; 推进时间 (+1天)</button>
    </div>

    <div class="actions">
      <button class="btn-primary" @click="$router.push('/conversations')">&#x1F4AC; 继续学习</button>
      <button class="btn-secondary" @click="$router.push('/curriculum')">&#x1F4DA; 查看课程</button>
      <button class="btn-secondary" @click="syncState">&#x1F504; 同步状态</button>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useNarrativeStore } from '@/stores/narrative'
import { useWebSocket } from '@/composables/useWebSocket'

const narrative = useNarrativeStore()
const ws = useWebSocket()

const scenes = [
  { id: 'classroom', name: '教室', description: '明亮的教室，黑板显示着知识点', allowed_actions: ['teach', 'question', 'discuss', 'practice'] },
  { id: 'debate_hall', name: '辩论厅', description: '圆形辩论场，全息投影显示争议主题', allowed_actions: ['debate', 'present', 'question'] },
  { id: 'exam_room', name: '考核室', description: '安静的考核室，倒计时跳动中', allowed_actions: ['exam', 'review'] },
  { id: 'lounge', name: '休息区', description: '舒适的休息区，壁画隐约浮现知识', allowed_actions: ['question', 'discuss', 'review'] },
]

const availableScenes = computed(() => scenes)

const sceneBg = computed(() => {
  const colors = {
    classroom: 'linear-gradient(135deg, #1a1a2e 0%, #16213e 100%)',
    debate_hall: 'linear-gradient(135deg, #16213e 0%, #0f3460 100%)',
    exam_room: 'linear-gradient(135deg, #0f3460 0%, #1a1a2e 100%)',
    lounge: 'linear-gradient(135deg, #1a2a1a 0%, #1a1a2e 100%)',
  }
  return colors[narrative.world.currentScene] || colors.classroom
})

const phaseLabel = computed(() => {
  const phase = narrative.world.narrativePhase
  if (phase === 'phase_1_basics') return '基础阶段'
  if (phase === 'phase_2_advanced') return '进阶阶段'
  if (phase === 'phase_3_practice') return '实践阶段'
  if (phase === 'prologue') return '序章'
  return phase
})

const statusLabel = computed(() => {
  const s = narrative.progress.status
  if (s === 'mastered') return '已掌握'
  if (s === 'learning') return '学习中'
  if (s === 'review_needed') return '需要复习'
  if (s === 'locked') return '未解锁'
  return s || '空闲'
})

const canAdvanceTime = computed(() => {
  return narrative.world.currentDay < narrative.world.totalDays
})

function actionLabel(action) {
  const labels = { teach: '教学', question: '提问', discuss: '讨论', practice: '练习', debate: '辩论', present: '展示', exam: '考核', review: '复习' }
  return labels[action] || action
}

function switchScene(sceneId) {
  ws.switchScene(sceneId)
}

function advanceTime() {
  ws.send({ type: 'time.advance', payload: { days: 1 } })
}

function syncState() {
  ws.requestStateSync()
}
</script>

<style scoped>
.timeline-page {
  max-width: 900px;
  margin: 0 auto;
  padding: 24px 20px;
}

.timeline-header {
  text-align: center;
  margin-bottom: 24px;
}

.timeline-header h1 {
  font-size: 28px;
  font-weight: 600;
  color: var(--color-ink);
  margin-bottom: 4px;
}

.subtitle {
  color: var(--color-text-muted);
  font-size: 14px;
}

.active-syllabus-badge {
  display: inline-block;
  margin-left: 8px;
  padding: 2px 10px;
  font-size: 12px;
  font-weight: 600;
  color: #1565c0;
  background: #e3f2fd;
  border-radius: 12px;
  vertical-align: middle;
}

.progress-bar-container {
  margin-bottom: 28px;
}

.progress-track {
  height: 12px;
  background: var(--color-bg);
  border-radius: 6px;
  overflow: hidden;
  border: 1px solid var(--color-border);
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #4caf50, #66bb6a);
  border-radius: 6px;
  transition: width 0.5s ease;
}

.progress-text {
  text-align: center;
  font-size: 13px;
  color: var(--color-text-muted);
  margin-top: 6px;
}

.current-scene-card {
  border-radius: 12px;
  overflow: hidden;
  margin-bottom: 28px;
  min-height: 140px;
}

.scene-overlay {
  padding: 24px;
  color: white;
}

.scene-badge {
  display: inline-block;
  font-size: 12px;
  padding: 3px 10px;
  background: rgba(255,255,255,0.2);
  border-radius: 12px;
  margin-bottom: 8px;
}

.scene-name {
  font-size: 22px;
  font-weight: 600;
  margin: 0 0 6px 0;
}

.scene-desc {
  font-size: 14px;
  opacity: 0.85;
  margin: 0 0 12px 0;
  line-height: 1.5;
}

.scene-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.action-tag {
  font-size: 12px;
  padding: 3px 10px;
  background: rgba(255,255,255,0.15);
  border-radius: 10px;
  border: 1px solid rgba(255,255,255,0.25);
}

.scenes-section {
  margin-bottom: 28px;
}

.section-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--color-ink);
  margin-bottom: 12px;
}

.scenes-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

.scene-card {
  padding: 16px;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.scene-card:hover {
  border-color: var(--color-accent);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}

.scene-card.scene-active {
  border-color: #7c4dff;
  border-width: 2px;
  background: #f3e5f5;
}

.scene-card-name {
  font-weight: 600;
  font-size: 15px;
  color: var(--color-ink);
  margin-bottom: 4px;
}

.scene-card-desc {
  font-size: 13px;
  color: var(--color-text-muted);
  line-height: 1.4;
  margin-bottom: 8px;
}

.scene-card-actions {
  font-size: 12px;
  color: var(--color-accent);
}

.current-progress {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 24px;
}

.progress-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 14px;
}

.progress-header h3 {
  font-size: 16px;
  font-weight: 600;
  color: var(--color-ink);
  margin: 0;
}

.status-label {
  font-size: 12px;
  padding: 3px 10px;
  border-radius: 10px;
  font-weight: 600;
}

.status-mastered { background: #e8f5e9; color: #2e7d32; }
.status-learning { background: #fff3e0; color: #e65100; }
.status-review_needed { background: #ffebee; color: #c62828; }
.status-locked { background: #eceff1; color: #78909c; }
.status-idle { background: #eceff1; color: #78909c; }

.progress-detail {
  display: flex;
  align-items: center;
  gap: 12px;
}

.point-name {
  font-weight: 600;
  min-width: 120px;
  font-size: 14px;
  color: var(--color-text);
}

.mastery-bar {
  flex: 1;
  height: 8px;
  background: var(--color-bg);
  border-radius: 4px;
  overflow: hidden;
}

.mastery-fill {
  height: 100%;
  background: linear-gradient(90deg, #4caf50, #66bb6a);
  border-radius: 4px;
  transition: width 0.5s;
}

.mastery-pct {
  font-size: 14px;
  font-weight: 600;
  color: #4caf50;
  min-width: 36px;
  text-align: right;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
  margin-bottom: 24px;
}

.stat-card {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 12px;
  padding: 20px;
  text-align: center;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: #7c4dff;
}

.stat-label {
  color: var(--color-text-muted);
  font-size: 13px;
  margin-top: 4px;
}

.time-advance {
  text-align: center;
  margin-bottom: 16px;
}

.btn-advance {
  padding: 10px 24px;
  font-size: 14px;
  font-weight: 600;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-advance:hover {
  border-color: var(--color-accent);
  background: var(--color-bg-warm);
}

.actions {
  display: flex;
  justify-content: center;
  gap: 12px;
  margin-top: 8px;
}

.btn-primary, .btn-secondary {
  padding: 12px 24px;
  font-size: 14px;
  font-weight: 600;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  border: none;
}

.btn-primary {
  background: var(--color-ink);
  color: white;
}

.btn-primary:hover {
  background: #7c4dff;
}

.btn-secondary {
  background: transparent;
  color: var(--color-text-muted);
  border: 1px solid var(--color-border);
}

.btn-secondary:hover {
  border-color: var(--color-ink);
  color: var(--color-ink);
}

@media (max-width: 600px) {
  .scenes-grid {
    grid-template-columns: 1fr;
  }
  .stats-grid {
    grid-template-columns: 1fr;
  }
}
</style>