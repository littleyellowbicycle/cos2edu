<template>
  <div class="curriculum-page">
    <div class="curriculum-header">
      <h1>&#x1F4DA; 课程体系</h1>
      <p class="subtitle">AI 机器学习入门 · 学习进度 {{ progressPercent }}%</p>
      <button class="btn-sync" @click="syncState">&#x1F504; 同步</button>
    </div>

    <div v-if="loading" class="loading">
      <div class="loading-spinner"></div>
      <p>加载课程中...</p>
    </div>

    <div v-else-if="error" class="error">
      <p>{{ error }}</p>
      <button class="btn-retry" @click="loadCurriculum">重试</button>
    </div>

    <div v-else>
      <div class="progress-bar-container">
        <div class="progress-track">
          <div class="progress-fill" :style="{ width: progressPercent + '%' }"></div>
        </div>
        <div class="progress-labels">
          <span>{{ masteredCount }} / {{ totalPoints }} 知识点已掌握</span>
          <span>{{ progressPercent }}%</span>
        </div>
      </div>

      <div v-for="phase in phases" :key="phase.name" class="phase-section">
        <div class="phase-header" @click="togglePhase(phase.name)">
          <h2>{{ phase.name }}</h2>
          <span class="phase-range">第{{ phase.days[0] }}-{{ phase.days[1] }}天</span>
          <span class="toggle-icon">{{ activePhases.includes(phase.name) ? '&#x25B2;' : '&#x25BC;' }}</span>
        </div>

        <div v-show="activePhases.includes(phase.name)" class="modules-container">
          <div
            v-for="mod in phase.modulesData"
            :key="mod.id"
            class="module-card"
            :class="{ 'module-locked': !isModuleUnlocked(mod) }"
          >
            <div class="module-header">
              <h3>{{ mod.name }}</h3>
              <span class="module-status" :class="getModuleStatus(mod)">
                {{ getModuleStatusLabel(mod) }}
              </span>
            </div>

            <div class="points-list">
              <div
                v-for="point in mod.knowledge_points"
                :key="point.id"
                class="point-item"
                :class="{
                  'point-mastered': isPointMastered(point.id),
                  'point-current': isPointCurrent(point.id),
                  'point-locked': !isPointUnlocked(point, mod),
                }"
                @click="isPointUnlocked(point, mod) && triggerAssessment(point)"
              >
                <div class="point-info">
                  <span class="point-icon">{{ getPointIcon(point, mod) }}</span>
                  <span class="point-name">{{ point.name }}</span>
                </div>
                <div class="point-meta">
                  <span class="point-difficulty">
                    {{ '&#x2B50;'.repeat(Math.min(point.difficulty || 1, 5)) }}
                  </span>
                  <span v-if="isPointMastered(point.id)" class="point-mastery">
                    {{ Math.round((getPointMastery(point.id) || 0) * 100) }}%
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div v-if="phases.length === 0 && modules.length > 0" class="flat-modules">
        <div
          v-for="mod in modules"
          :key="mod.id"
          class="module-card"
          :class="{ 'module-locked': !isModuleUnlocked(mod) }"
        >
          <div class="module-header">
            <h3>{{ mod.name }}</h3>
            <span class="module-status" :class="getModuleStatus(mod)">
              {{ getModuleStatusLabel(mod) }}
            </span>
          </div>
          <div class="points-list">
            <div
              v-for="point in mod.knowledge_points"
              :key="point.id"
              class="point-item"
              :class="{
                'point-mastered': isPointMastered(point.id),
                'point-current': isPointCurrent(point.id),
              }"
            >
              <div class="point-info">
                <span class="point-icon">{{ isPointMastered(point.id) ? '&#x2705;' : isPointCurrent(point.id) ? '&#x1F4D6;' : '&#x1F512;' }}</span>
                <span class="point-name">{{ point.name }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useNarrativeStore } from '@/stores/narrative'
import { useWebSocket } from '@/composables/useWebSocket'
import api from '@/api'

const narrative = useNarrativeStore()
const ws = useWebSocket()

const loading = ref(true)
const error = ref(null)
const syllabus = ref(null)
const activePhases = ref([])
const modules = ref([])

const masteredCount = computed(() => narrative.progress.masteredPoints?.length || 0)
const totalPoints = computed(() => narrative.progress.totalPoints || 0)
const progressPercent = computed(() => {
  if (totalPoints.value === 0) return 0
  return Math.round(masteredCount.value / totalPoints.value * 100)
})

const phases = computed(() => {
  if (!syllabus.value) return []
  return (syllabus.value.course?.phases || []).map(p => ({
    ...p,
    modulesData: p.modules?.map(mid => modulesMap.value[mid]).filter(Boolean) || []
  }))
})

const modulesMap = computed(() => {
  const map = {}
  modules.value.forEach(m => { map[m.id] = m })
  return map
})

function togglePhase(name) {
  const idx = activePhases.value.indexOf(name)
  if (idx >= 0) {
    activePhases.value.splice(idx, 1)
  } else {
    activePhases.value.push(name)
  }
}

function isModuleUnlocked(mod) {
  if (!mod.prerequisites?.length) return true
  return mod.prerequisites.every(pre => {
    const points = modules.value.find(m => m.id === pre)?.knowledge_points || []
    return points.every(p => isPointMastered(p.id))
  })
}

function isPointMastered(pointId) {
  return narrative.progress.masteredPoints?.includes(pointId) || false
}

function isPointCurrent(pointId) {
  return narrative.progress.currentPoint === pointId
}

function isPointUnlocked(point, mod) {
  if (!point.prerequisites?.length) return isModuleUnlocked(mod)
  return point.prerequisites.every(pre => isPointMastered(pre))
}

function getPointMastery(pointId) {
  return narrative.progress.mastery || 0
}

function getPointIcon(point, mod) {
  if (isPointMastered(point.id)) return '\u2705'
  if (isPointCurrent(point.id)) return '\uD83D\uDCD6'
  if (!isPointUnlocked(point, mod)) return '\uD83D\uDD12'
  return '\uD83D\uDFE1'
}

function getModuleStatus(mod) {
  const pts = mod.knowledge_points || []
  if (pts.length === 0) return 'empty'
  const mastered = pts.filter(p => isPointMastered(p.id)).length
  if (mastered === pts.length) return 'mastered'
  if (isModuleUnlocked(mod)) return 'available'
  return 'locked'
}

function getModuleStatusLabel(mod) {
  const status = getModuleStatus(mod)
  const labels = { mastered: '已完成', available: '可学习', locked: '未解锁', empty: '空' }
  return labels[status] || status
}

function triggerAssessment(point) {
  ws.generateAssessment(point.id, '')
}

function syncState() {
  ws.requestStateSync()
}

async function loadCurriculum() {
  loading.value = true
  error.value = null
  try {
    syllabus.value = await api.get('/crud/curriculum/syllabus')
    modules.value = await api.get('/crud/curriculum/modules')
    activePhases.value = phases.value.map(p => p.name)
  } catch (e) {
    error.value = '加载课程失败: ' + (e.message || '未知错误')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadCurriculum()
  ws.connect()
  ws.requestStateSync()
})
</script>

<style scoped>
.curriculum-page {
  max-width: 900px;
  margin: 0 auto;
  padding: 24px 20px;
}

.curriculum-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 28px;
  flex-wrap: wrap;
}

.curriculum-header h1 {
  font-size: 28px;
  font-weight: 600;
  color: var(--color-ink);
  margin: 0;
}

.subtitle {
  color: var(--color-text-muted);
  font-size: 14px;
  margin: 0;
}

.btn-sync {
  margin-left: auto;
  padding: 6px 14px;
  font-size: 13px;
  font-weight: 600;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-sync:hover {
  border-color: var(--color-accent);
}

.progress-bar-container {
  margin-bottom: 28px;
}

.progress-track {
  height: 10px;
  background: var(--color-bg);
  border-radius: 5px;
  overflow: hidden;
  border: 1px solid var(--color-border);
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #7c4dff, #b388ff);
  border-radius: 5px;
  transition: width 0.5s ease;
}

.progress-labels {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: var(--color-text-muted);
  margin-top: 4px;
}

.phase-section {
  margin-bottom: 8px;
}

.phase-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.phase-header:hover {
  border-color: var(--color-accent);
}

.phase-header h2 {
  font-size: 16px;
  font-weight: 600;
  color: var(--color-ink);
  margin: 0;
  flex: 1;
}

.phase-range {
  font-size: 13px;
  color: var(--color-text-muted);
}

.toggle-icon {
  font-size: 12px;
  color: var(--color-text-muted);
}

.modules-container {
  padding: 8px 0 16px 0;
}

.module-card {
  border: 1px solid var(--color-border);
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 10px;
  background: var(--color-surface);
  transition: all 0.2s;
}

.module-card.module-locked {
  opacity: 0.55;
}

.module-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.module-header h3 {
  margin: 0;
  font-size: 16px;
  color: var(--color-ink);
}

.module-status {
  font-size: 12px;
  padding: 2px 10px;
  border-radius: 10px;
  font-weight: 600;
}

.module-status.mastered { background: #e8f5e9; color: #2e7d32; }
.module-status.available { background: #e3f2fd; color: #1565c0; }
.module-status.locked { background: #eceff1; color: #78909c; }

.points-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.point-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 14px;
  border-radius: 6px;
  background: var(--color-bg);
  cursor: pointer;
  transition: all 0.2s;
}

.point-item:hover:not(.point-locked) {
  background: var(--color-bg-warm);
  transform: translateX(4px);
}

.point-item.point-mastered {
  background: rgba(103, 194, 58, 0.08);
}

.point-item.point-current {
  background: rgba(124, 77, 255, 0.08);
  border-left: 3px solid #7c4dff;
}

.point-item.point-locked {
  opacity: 0.5;
  cursor: not-allowed;
}

.point-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.point-icon {
  font-size: 14px;
}

.point-name {
  font-size: 14px;
  color: var(--color-text);
}

.point-meta {
  display: flex;
  align-items: center;
  gap: 12px;
}

.point-difficulty {
  font-size: 10px;
}

.point-mastery {
  font-size: 12px;
  font-weight: 600;
  color: #4caf50;
}

.flat-modules {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.loading {
  text-align: center;
  padding: 60px 0;
  color: var(--color-text-muted);
}

.loading-spinner {
  width: 32px;
  height: 32px;
  border: 3px solid var(--color-border);
  border-top-color: var(--color-accent);
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 12px;
}

.error {
  text-align: center;
  padding: 40px;
  color: var(--color-text-muted);
}

.btn-retry {
  margin-top: 12px;
  padding: 8px 20px;
  font-weight: 600;
  background: var(--color-ink);
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

@media (max-width: 600px) {
  .curriculum-header {
    flex-direction: column;
    align-items: flex-start;
  }
  .btn-sync {
    margin-left: 0;
  }
}
</style>