<template>
  <div class="curriculum-page">
    <div class="curriculum-header">
      <h1>📚 课程体系</h1>
      <p class="subtitle">AI 机器学习入门 · 90天学习计划</p>
    </div>

    <div v-if="loading" class="loading">
      <el-icon class="is-loading"><Loading /></el-icon>
      加载课程中...
    </div>

    <div v-else-if="error" class="error">
      <el-empty :description="error">
        <el-button @click="loadCurriculum">重试</el-button>
      </el-empty>
    </div>

    <div v-else class="phases-container">
      <el-collapse v-model="activePhases">
        <el-collapse-item
          v-for="phase in phases"
          :key="phase.name"
          :title="`${phase.name} (第${phase.days[0]}-${phase.days[1]}天)`"
          :name="phase.name"
        >
          <div class="modules-list">
            <div
              v-for="mod in phase.modulesData"
              :key="mod.id"
              class="module-card"
              :class="{ 'module-locked': !isModuleUnlocked(mod) }"
            >
              <div class="module-header">
                <h3>{{ mod.name }}</h3>
                <el-tag :type="isModuleUnlocked(mod) ? 'success' : 'info'" size="small">
                  {{ isModuleUnlocked(mod) ? '可学习' : '未解锁' }}
                </el-tag>
              </div>

              <div class="points-list">
                <div
                  v-for="point in mod.knowledge_points"
                  :key="point.id"
                  class="point-item"
                  :class="{ 'point-mastered': isPointMastered(point.id), 'point-current': isPointCurrent(point.id) }"
                >
                  <div class="point-info">
                    <span class="point-status-icon">
                      {{ isPointMastered(point.id) ? '✅' : isPointCurrent(point.id) ? '📖' : '🔒' }}
                    </span>
                    <span class="point-name">{{ point.name }}</span>
                  </div>
                  <div class="point-meta">
                    <el-rate :model-value="point.difficulty" :max="5" disabled size="small" />
                    <span class="point-time">{{ point.estimated_minutes || 30 }}分钟</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </el-collapse-item>
      </el-collapse>
    </div>

    <div class="progress-summary" v-if="syllabus">
      <el-progress
        :percentage="progressPercent"
        :stroke-width="20"
        :text-inside="true"
        status="success"
      />
      <p>已完成 {{ masteredCount }}/{{ totalPoints }} 个知识点</p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { Loading } from '@element-plus/icons-vue'
import { useNarrativeStore } from '@/stores/narrative'
import api from '@/api'

const narrative = useNarrativeStore()

const loading = ref(true)
const error = ref(null)
const syllabus = ref(null)
const activePhases = ref([])

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

const modules = ref([])
const masteredCount = computed(() => narrative.progress.masteredPoints?.length || 0)
const totalPoints = computed(() => narrative.progress.totalPoints || 0)
const progressPercent = computed(() => {
  if (totalPoints.value === 0) return 0
  return Math.round(masteredCount.value / totalPoints.value * 100)
})

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

async function loadCurriculum() {
  loading.value = true
  error.value = null
  try {
    const res = await api.get('/crud/curriculum/syllabus')
    syllabus.value = res
    const modulesRes = await api.get('/crud/curriculum/modules')
    modules.value = modulesRes
    activePhases.value = phases.value.map(p => p.name)
  } catch (e) {
    error.value = '加载课程失败: ' + (e.message || '未知错误')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadCurriculum()
})
</script>

<style scoped>
.curriculum-page {
  max-width: 900px;
  margin: 0 auto;
  padding: 20px;
}

.curriculum-header {
  text-align: center;
  margin-bottom: 30px;
}

.curriculum-header h1 {
  font-size: 28px;
  margin-bottom: 8px;
}

.subtitle {
  color: #999;
  font-size: 14px;
}

.phases-container {
  margin-bottom: 30px;
}

.module-card {
  border: 1px solid var(--el-border-color-light);
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 12px;
  transition: all 0.3s;
}

.module-locked {
  opacity: 0.6;
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
}

.points-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.point-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  border-radius: 6px;
  background: rgba(255, 255, 255, 0.05);
  transition: all 0.2s;
}

.point-item.point-mastered {
  background: rgba(103, 194, 58, 0.1);
}

.point-item.point-current {
  background: rgba(64, 158, 255, 0.1);
  border-left: 3px solid #409eff;
}

.point-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.point-status-icon {
  font-size: 14px;
}

.point-name {
  font-size: 14px;
}

.point-meta {
  display: flex;
  align-items: center;
  gap: 12px;
}

.point-time {
  font-size: 12px;
  color: #999;
}

.progress-summary {
  margin-top: 24px;
  text-align: center;
}

.progress-summary p {
  margin-top: 8px;
  color: #999;
  font-size: 14px;
}

.loading {
  text-align: center;
  padding: 60px 0;
  color: #999;
}

.error {
  padding: 40px;
}
</style>