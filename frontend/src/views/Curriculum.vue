<template>
  <div class="curriculum-page">
    <div class="curriculum-header">
      <h1>&#x1F4DA; 课程体系</h1>
      <p class="subtitle">{{ currentSyllabusName }} · 学习进度 {{ progressPercent }}%</p>
      <button class="btn-sync" @click="syncState">&#x1F504; 同步</button>
      <button class="btn-generate" @click="openGenerateDialog">&#x2728; 根据教材生成</button>
    </div>

    <div class="syllabus-tabs" v-if="syllabusList.length > 0">
      <div
        class="syllabus-tab"
        :class="{ active: !activeMaterialId }"
        @click="switchSyllabus(null)"
      >
        &#x1F4C4; 默认大纲
      </div>
      <div
        v-for="s in syllabusList"
        :key="s.material_id"
        class="syllabus-tab"
        :class="{ active: activeMaterialId === s.material_id }"
        @click="switchSyllabus(s.material_id)"
      >
        &#x1F4D6; {{ s.material_title || s.name }}
        <span class="tab-status" :class="s.review_status">{{ statusLabels[s.review_status] || s.review_status }}</span>
      </div>
    </div>

    <div class="view-toggle" v-if="!loading && !error">
      <button class="toggle-btn" :class="{ active: viewMode === 'list' }" @click="viewMode = 'list'">&#x1F4CB; 列表</button>
      <button class="toggle-btn" :class="{ active: viewMode === 'mindmap' }" @click="viewMode = 'mindmap'">&#x1F9E0; 脑图</button>
    </div>

    <div v-if="showGenerateDialog" class="generate-overlay" @click.self="closeGenerateDialog">
      <div class="generate-dialog">
        <div class="dialog-header">
          <h3>从教材生成课程大纲</h3>
          <button class="dialog-close" @click="closeGenerateDialog">&times;</button>
        </div>

        <div v-if="!generatingOutline && !generatedSyllabus" class="dialog-body">
          <p class="dialog-hint">选择一本已上传的教材，AI 将自动分析内容并生成结构化学习大纲。</p>
          <div v-if="generatableMaterials.length === 0" class="empty-materials">
            <p>暂无可以生成大纲的教材。请先在「教材管理」中上传一份教材。</p>
          </div>
          <div v-else class="material-list">
            <div
              v-for="m in generatableMaterials"
              :key="m.id"
              class="material-option"
              :class="{
                selected: selectedMaterialId === m.id,
                'has-syllabus': m.has_syllabus,
              }"
              @click="selectedMaterialId = m.id"
            >
              <div class="material-option-info">
                <span class="material-option-title">{{ m.title }}</span>
                <span class="material-option-meta">
                  {{ m.char_count }} 字
                  <template v-if="m.has_syllabus">
                    · <span class="has-syllabus-badge">{{ syllabusStatusText(m.syllabus_status) }}</span>
                  </template>
                </span>
              </div>
              <span v-if="m.has_syllabus" class="material-badge">&#x2705; 已有大纲</span>
              <span v-else class="material-check">{{ selectedMaterialId === m.id ? '&#x2713;' : '' }}</span>
            </div>
          </div>
        </div>

        <div v-if="generatingOutline" class="dialog-body generating">
          <div class="generating-spinner"></div>
          <p>AI 正在分析教材内容并生成大纲...</p>
          <p class="generating-hint">这可能需要 30-60 秒</p>
        </div>

        <div v-if="generatedSyllabus" class="dialog-body preview">
          <h4 class="preview-title">{{ generatedSyllabus.name || '生成的大纲' }}</h4>
          <p class="preview-days">计划 {{ generatedSyllabus.total_days || 60 }} 天</p>
          <div v-for="phase in (generatedSyllabus.phases || [])" :key="phase.name" class="preview-phase">
            <h5>{{ phase.name }} <span class="phase-range-preview" v-if="phase.days">(第{{ phase.days[0] }}-{{ phase.days[1] }}天)</span></h5>
            <div class="preview-modules">
              <div v-for="mod in (generatedSyllabus.modules || [])" :key="mod.id" class="preview-module">
                <span class="mod-name">{{ mod.name }}</span>
                <span class="mod-hours">{{ mod.estimated_hours }}h</span>
                <div class="mod-points">
                  <span v-for="kp in (mod.knowledge_points || [])" :key="kp.id" class="point-tag">{{ kp.name }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div v-if="!generatingOutline" class="dialog-footer">
          <button v-if="!generatedSyllabus" class="btn-cancel-dialog" @click="closeGenerateDialog">取消</button>
          <button v-if="!generatedSyllabus" class="btn-generate-start" :disabled="!selectedMaterialId" @click="startGeneration">
            {{ selectedMaterialId && generatableMaterials.find(m => m.id === selectedMaterialId)?.has_syllabus ? '重新生成' : '开始生成' }}
          </button>
          <template v-if="generatedSyllabus">
            <button class="btn-cancel-dialog" @click="rejectGenerated">拒绝</button>
            <button class="btn-confirm" @click="confirmGenerated">确认大纲</button>
          </template>
        </div>
      </div>
    </div>

    <div v-if="loading" class="loading">
      <div class="loading-spinner"></div>
      <p>加载课程中...</p>
    </div>

    <div v-else-if="error" class="error">
      <p>{{ error }}</p>
      <button class="btn-retry" @click="loadCurriculum">重试</button>
    </div>

    <div v-else-if="viewMode === 'list'">
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
          <span class="phase-range">{{ phase.days ? `第${phase.days[0]}-${phase.days[1]}天` : '' }}</span>
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

    <div v-else-if="viewMode === 'mindmap'" class="mindmap-container">
      <div ref="mindmapEl" class="mindmap-render"></div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import { useNarrativeStore } from '@/stores/narrative'
import { useWebSocket } from '@/composables/useWebSocket'
import api, { apiClient } from '@/api'
import mermaid from 'mermaid'

mermaid.initialize({ startOnLoad: false, theme: 'default' })

const narrative = useNarrativeStore()
const ws = useWebSocket()

const loading = ref(true)
const error = ref(null)
const syllabus = ref(null)
const activePhases = ref([])
const modules = ref([])
const viewMode = ref('list')
const mindmapEl = ref(null)

const activeMaterialId = ref(null)
const syllabusList = ref([])

const showGenerateDialog = ref(false)
const generatableMaterials = ref([])
const selectedMaterialId = ref(null)
const generatingOutline = ref(false)
const generatedSyllabus = ref(null)

const statusLabels = {
  pending: '待审核',
  approved: '已确认',
  rejected: '已拒绝',
}

const currentSyllabusName = computed(() => {
  if (!activeMaterialId.value) {
    return syllabus.value?.course?.name || syllabus.value?.name || '课程大纲'
  }
  const found = syllabusList.value.find(s => s.material_id === activeMaterialId.value)
  return found?.material_title || found?.name || '课程大纲'
})

const masteredCount = computed(() => narrative.progress.masteredPoints?.length || 0)
const totalPoints = computed(() => narrative.progress.totalPoints || 0)
const progressPercent = computed(() => {
  if (totalPoints.value === 0) return 0
  return Math.round(masteredCount.value / totalPoints.value * 100)
})

const phases = computed(() => {
  if (!syllabus.value) return []
  const rawPhases = syllabus.value.course?.phases || syllabus.value.phases || []
  return rawPhases.filter(p => p && p.name).map(p => ({
    ...p,
    modulesData: p.modules?.map(mid => modulesMap.value[mid]).filter(Boolean) || []
  }))
})

const modulesMap = computed(() => {
  const map = {}
  const nameMap = {}
  modules.value.forEach(m => {
    map[m.id] = m
    if (m.name) nameMap[m.name] = m
  })
  return { ...map, ...nameMap }
})

function syllabusStatusText(status) {
  return statusLabels[status] || status || ''
}

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

async function switchSyllabus(materialId) {
  activeMaterialId.value = materialId
  await loadCurriculum()
}

async function loadSyllabusList() {
  try {
    syllabusList.value = await api.curriculum.listSyllabuses()
  } catch (e) {
    console.error('Failed to load syllabus list:', e)
  }
}

async function openGenerateDialog() {
  showGenerateDialog.value = true
  selectedMaterialId.value = null
  generatedSyllabus.value = null
  try {
    generatableMaterials.value = await api.curriculum.listGeneratableMaterials()
  } catch (e) {
    console.error('generatable error:', e)
    generatableMaterials.value = []
  }
}

function closeGenerateDialog() {
  showGenerateDialog.value = false
  generatedSyllabus.value = null
  generatingOutline.value = false
}

async function startGeneration() {
  if (!selectedMaterialId.value) return
  generatingOutline.value = true
  const url = `/api/v1/curriculum/materials/${selectedMaterialId.value}/generate-outline`
  try {
    const res = await fetch(url, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{}' })
    const data = await res.json()
    if (!res.ok) {
      throw new Error(data.detail || `HTTP ${res.status} ${res.statusText}`)
    }
    generatedSyllabus.value = data.syllabus
  } catch (e) {
    console.error('Generation error:', e)
    error.value = '生成大纲失败: ' + e.message
    closeGenerateDialog()
  } finally {
    generatingOutline.value = false
  }
}

async function confirmGenerated() {
  try {
    await apiClient.post(`/curriculum/materials/${selectedMaterialId.value}/confirm-syllabus`)
    showGenerateDialog.value = false
    generatedSyllabus.value = null
    activeMaterialId.value = selectedMaterialId.value
    await loadSyllabusList()
    await loadCurriculum()
  } catch (e) {
    error.value = '确认大纲失败: ' + (e.response?.data?.detail || e.message || '未知错误')
  }
}

async function rejectGenerated() {
  try {
    await apiClient.post(`/curriculum/materials/${selectedMaterialId.value}/reject-syllabus`)
    showGenerateDialog.value = false
    generatedSyllabus.value = null
  } catch (e) {
    error.value = '操作失败: ' + (e.response?.data?.detail || e.message || '未知错误')
  }
}

function syncState() {
  ws.requestStateSync()
}

async function loadCurriculum() {
  loading.value = true
  error.value = null
  try {
    syllabus.value = await api.curriculum.getSyllabus(activeMaterialId.value)
    modules.value = await api.curriculum.getModules(activeMaterialId.value)
    activePhases.value = phases.value.map(p => p.name)
  } catch (e) {
    error.value = '加载课程失败: ' + (e.message || '未知错误')
  } finally {
    loading.value = false
  }
}

function buildMermaidCode() {
  if (!syllabus.value && modules.value.length === 0) return 'graph LR\n  A[暂无大纲数据]'

  const lines = ['graph LR']
  const syllabusName = syllabus.value?.course?.name || syllabus.value?.name || '课程大纲'
  lines.push(`  root["${syllabusName}"]`)

  const rawPhases = syllabus.value?.course?.phases || syllabus.value?.phases || []
  const phaseIds = []
  rawPhases.filter(p => p && p.name).forEach((phase, i) => {
    const pid = `p${i}`
    const label = phase.days ? `${phase.name}<br/>第${phase.days[0]}-${phase.days[1]}天` : phase.name
    lines.push(`  ${pid}["${label}"]`)
    lines.push(`  root --> ${pid}`)
    phaseIds.push({ id: pid, phase })
  })

  if (phaseIds.length === 0 && modules.value.length > 0) {
    modules.value.forEach((mod, mi) => {
      const mid = `m${mi}`
      lines.push(`  ${mid}["${mod.name}"]`)
      lines.push(`  root --> ${mid}`)
      ;(mod.knowledge_points || []).forEach((kp, ki) => {
        const kid = `kp${mi}_${ki}`
        lines.push(`  ${kid}("${kp.name}")`)
        lines.push(`  ${mid} --> ${kid}`)
      })
    })
  } else {
    phaseIds.forEach(({ id: pid, phase }) => {
      const phaseModules = phase.modules?.map(mid => modulesMap.value[mid]).filter(Boolean) || []
      phaseModules.forEach((mod, mi) => {
        const mid = `${pid}_m${mi}`
        lines.push(`  ${mid}["${mod.name}"]`)
        lines.push(`  ${pid} --> ${mid}`)
        ;(mod.knowledge_points || []).forEach((kp, ki) => {
          const kid = `${mid}_kp${ki}`
          lines.push(`  ${kid}("${kp.name}")`)
          lines.push(`  ${mid} --> ${kid}`)
        })
      })
    })
  }

  return lines.join('\n')
}

async function renderMindmap() {
  if (!mindmapEl.value) return
  const code = buildMermaidCode()
  try {
    const id = 'mermaid-' + Date.now()
    const { svg } = await mermaid.render(id, code)
    mindmapEl.value.innerHTML = svg
  } catch (e) {
    console.error('Mermaid render error:', e)
    mindmapEl.value.innerHTML = '<p style="color:var(--color-text-muted);text-align:center;padding:40px;">脑图渲染失败，请切换到列表视图</p>'
  }
}

watch(viewMode, async (v) => {
  if (v === 'mindmap') {
    await nextTick()
    renderMindmap()
  }
})

watch([syllabus, modules], async () => {
  if (viewMode.value === 'mindmap') {
    await nextTick()
    renderMindmap()
  }
})

onMounted(async () => {
  await loadSyllabusList()
  await loadCurriculum()
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
  margin-bottom: 16px;
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

.btn-generate {
  margin-left: 8px;
  padding: 6px 14px;
  font-size: 13px;
  font-weight: 600;
  background: linear-gradient(135deg, #7c4dff, #b388ff);
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-generate:hover {
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(124, 77, 255, 0.3);
}

.syllabus-tabs {
  display: flex;
  gap: 6px;
  margin-bottom: 12px;
  overflow-x: auto;
  padding-bottom: 4px;
}

.syllabus-tab {
  padding: 6px 14px;
  font-size: 13px;
  font-weight: 500;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 20px;
  cursor: pointer;
  white-space: nowrap;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  gap: 6px;
}

.syllabus-tab:hover {
  border-color: var(--color-accent);
}

.syllabus-tab.active {
  background: #7c4dff;
  color: white;
  border-color: #7c4dff;
}

.tab-status {
  font-size: 10px;
  padding: 1px 6px;
  border-radius: 8px;
  font-weight: 600;
}

.tab-status.pending { background: #fff3e0; color: #e65100; }
.tab-status.approved { background: #e8f5e9; color: #2e7d32; }
.tab-status.rejected { background: #fce4ec; color: #c62828; }
.syllabus-tab.active .tab-status { background: rgba(255,255,255,0.25); color: white; }

.view-toggle {
  display: flex;
  gap: 4px;
  margin-bottom: 20px;
}

.toggle-btn {
  padding: 6px 16px;
  font-size: 13px;
  font-weight: 600;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
}

.toggle-btn.active {
  background: var(--color-ink);
  color: white;
  border-color: var(--color-ink);
}

.generate-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.4);
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
}

.generate-dialog {
  background: var(--color-surface);
  border-radius: 12px;
  width: 600px;
  max-width: 90vw;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
}

.dialog-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 18px 20px;
  border-bottom: 1px solid var(--color-border);
}

.dialog-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
}

.dialog-close {
  background: none;
  border: none;
  font-size: 22px;
  color: var(--color-text-muted);
  cursor: pointer;
  padding: 0 4px;
}

.dialog-body {
  padding: 20px;
  overflow-y: auto;
  flex: 1;
}

.dialog-hint {
  color: var(--color-text-muted);
  font-size: 13px;
  margin: 0 0 16px;
}

.empty-materials {
  text-align: center;
  padding: 32px;
  color: var(--color-text-muted);
}

.material-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.material-option {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 14px;
  border: 1px solid var(--color-border);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.material-option:hover {
  border-color: var(--color-accent);
}

.material-option.selected {
  border-color: #7c4dff;
  background: rgba(124, 77, 255, 0.06);
}

.material-option.has-syllabus {
  border-left: 3px solid #4caf50;
}

.material-option-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.material-option-title {
  font-weight: 600;
  font-size: 14px;
}

.material-option-meta {
  font-size: 12px;
  color: var(--color-text-muted);
}

.has-syllabus-badge {
  color: #4caf50;
  font-weight: 600;
}

.material-badge {
  font-size: 12px;
  padding: 2px 10px;
  background: #e8f5e9;
  color: #2e7d32;
  border-radius: 10px;
  font-weight: 600;
  white-space: nowrap;
}

.material-check {
  color: #7c4dff;
  font-weight: 700;
  font-size: 16px;
}

.dialog-body.generating {
  text-align: center;
  padding: 48px 20px;
}

.generating-spinner {
  width: 36px;
  height: 36px;
  border: 3px solid var(--color-border);
  border-top-color: #7c4dff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 16px;
}

.generating-hint {
  color: var(--color-text-muted);
  font-size: 13px;
  margin-top: 8px;
}

.preview-title {
  margin: 0 0 4px;
  font-size: 18px;
}

.preview-days {
  color: var(--color-text-muted);
  font-size: 13px;
  margin: 0 0 16px;
}

.preview-phase {
  margin-bottom: 16px;
}

.preview-phase h5 {
  margin: 0 0 8px;
  font-size: 14px;
  color: var(--color-ink);
}

.phase-range-preview {
  font-weight: 400;
  font-size: 12px;
  color: var(--color-text-muted);
}

.preview-modules {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.preview-module {
  padding: 10px 12px;
  background: var(--color-bg);
  border-radius: 6px;
}

.mod-name {
  font-weight: 600;
  font-size: 13px;
}

.mod-hours {
  float: right;
  font-size: 12px;
  color: var(--color-text-muted);
}

.mod-points {
  margin-top: 6px;
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.point-tag {
  font-size: 11px;
  padding: 2px 8px;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 10px;
  color: var(--color-text-muted);
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  padding: 14px 20px;
  border-top: 1px solid var(--color-border);
}

.btn-cancel-dialog {
  padding: 8px 18px;
  font-size: 13px;
  font-weight: 600;
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  border-radius: 6px;
  cursor: pointer;
}

.btn-generate-start {
  padding: 8px 18px;
  font-size: 13px;
  font-weight: 600;
  background: #7c4dff;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
}

.btn-generate-start:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.btn-confirm {
  padding: 8px 18px;
  font-size: 13px;
  font-weight: 600;
  background: #4caf50;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
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

.mindmap-container {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 12px;
  padding: 24px;
  min-height: 400px;
  overflow: auto;
}

.mindmap-render {
  display: flex;
  justify-content: center;
}

.mindmap-render :deep(svg) {
  max-width: 100%;
  height: auto;
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
  .syllabus-tabs {
    flex-wrap: nowrap;
  }
}
</style>
