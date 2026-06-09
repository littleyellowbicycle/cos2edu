<template>
  <div v-if="editorModules.length === 0" class="editor-empty">
    <p>暂无模块可编辑</p>
  </div>
  <div v-for="mod in editorModules" :key="mod.id" class="editor-module">
    <div class="editor-module-header">
      <h3>{{ mod.name }}</h3>
      <span class="editor-module-order">顺序: {{ mod.order || '-' }}</span>
    </div>
    <div class="editor-points-list">
      <div
        v-for="(point, pIdx) in mod.knowledge_points"
        :key="point.id"
        class="editor-point"
        :class="{ 'editor-point-dragging': dragState.draggingPointId === point.id }"
        draggable="true"
        @dragstart="onPointDragStart($event, mod.id, pIdx, point)"
        @dragover.prevent="onPointDragOver"
        @drop="onPointDrop($event, mod.id, pIdx)"
        @dragend="onPointDragEnd"
      >
        <span class="editor-point-drag-handle" title="拖拽排序">&#x2630;</span>
        <div class="editor-point-content">
          <div class="editor-point-name-row">
            <input
              class="editor-point-name-input"
              :value="point.name"
              @change="updatePointField(mod.id, pIdx, 'name', $event.target.value)"
              placeholder="知识点名称"
            />
            <select
              class="editor-point-difficulty"
              :value="point.difficulty || 1"
              @change="updatePointField(mod.id, pIdx, 'difficulty', parseInt($event.target.value))"
            >
              <option v-for="d in 5" :key="d" :value="d">{{ '&#x2B50;'.repeat(d) }}</option>
            </select>
          </div>
          <div class="editor-point-deps">
            <label class="editor-deps-label">前置依赖:</label>
            <div class="editor-deps-tags">
              <span
                v-for="depId in (point.prerequisites || [])"
                :key="depId"
                class="editor-dep-tag"
              >
                {{ getPointNameById(depId) || depId }}
                <button class="editor-dep-remove" @click="removePrerequisite(mod.id, pIdx, depId)">&times;</button>
              </span>
              <select
                class="editor-dep-add"
                @change="addPrerequisite(mod.id, pIdx, $event.target.value); $event.target.value = ''"
                value=""
              >
                <option value="" disabled>+ 添加依赖</option>
                <option
                  v-for="availPoint in getAvailablePrerequisites(mod.id, point)"
                  :key="availPoint.id"
                  :value="availPoint.id"
                >
                  {{ availPoint.name }}
                </option>
              </select>
            </div>
          </div>
          <div class="editor-point-concepts">
            <label class="editor-concepts-label">核心概念:</label>
            <input
              class="editor-concepts-input"
              :value="(point.key_concepts || []).join(', ')"
              @change="updatePointField(mod.id, pIdx, 'key_concepts', $event.target.value.split(',').map(s => s.trim()).filter(Boolean))"
              placeholder="用逗号分隔"
            />
          </div>
        </div>
      </div>
    </div>
  </div>
  <div class="editor-actions" v-if="editorModules.length > 0">
    <button class="btn-editor-save" @click="saveEditorChanges" :disabled="editorSaving">
      {{ editorSaving ? '保存中...' : '&#x1F4BE; 保存修改' }}
    </button>
    <button class="btn-editor-reset" @click="resetEditorChanges">&#x1F504; 重置</button>
  </div>
</template>

<script setup>
import { ref, reactive, watch } from 'vue'
import api from '@/api'

const props = defineProps({
  modules: { type: Array, required: true },
})

const emit = defineEmits(['saved', 'cancel'])

const editorModules = ref([])
const editorSaving = ref(false)
const dragState = reactive({
  draggingPointId: null,
  sourceModuleId: null,
  sourceIndex: null,
})

watch(() => props.modules, (val) => {
  editorModules.value = JSON.parse(JSON.stringify(val))
}, { immediate: true, deep: true })

function getPointNameById(pointId) {
  for (const mod of editorModules.value) {
    const pt = (mod.knowledge_points || []).find(p => p.id === pointId)
    if (pt) return pt.name
  }
  return null
}

function getAvailablePrerequisites(modId, point) {
  const currentDeps = new Set(point.prerequisites || [])
  currentDeps.add(point.id)
  const available = []
  for (const mod of editorModules.value) {
    for (const pt of (mod.knowledge_points || [])) {
      if (!currentDeps.has(pt.id)) {
        available.push({ id: pt.id, name: pt.name })
      }
    }
  }
  return available
}

function updatePointField(modId, pointIdx, field, value) {
  const mod = editorModules.value.find(m => m.id === modId)
  if (!mod || !mod.knowledge_points[pointIdx]) return
  mod.knowledge_points[pointIdx][field] = value
}

function addPrerequisite(modId, pointIdx, depId) {
  if (!depId) return
  const mod = editorModules.value.find(m => m.id === modId)
  if (!mod || !mod.knowledge_points[pointIdx]) return
  const point = mod.knowledge_points[pointIdx]
  if (!point.prerequisites) point.prerequisites = []
  if (!point.prerequisites.includes(depId)) {
    point.prerequisites.push(depId)
  }
}

function removePrerequisite(modId, pointIdx, depId) {
  const mod = editorModules.value.find(m => m.id === modId)
  if (!mod || !mod.knowledge_points[pointIdx]) return
  const point = mod.knowledge_points[pointIdx]
  if (point.prerequisites) {
    point.prerequisites = point.prerequisites.filter(d => d !== depId)
  }
}

function onPointDragStart(event, modId, idx, point) {
  dragState.draggingPointId = point.id
  dragState.sourceModuleId = modId
  dragState.sourceIndex = idx
  event.dataTransfer.effectAllowed = 'move'
  event.dataTransfer.setData('text/plain', point.id)
}

function onPointDragOver(event) {
  event.dataTransfer.dropEffect = 'move'
}

function onPointDrop(event, targetModId, targetIdx) {
  event.preventDefault()
  const srcModId = dragState.sourceModuleId
  const srcIdx = dragState.sourceIndex
  if (srcModId == null || srcIdx == null) return

  const srcMod = editorModules.value.find(m => m.id === srcModId)
  const tgtMod = editorModules.value.find(m => m.id === targetModId)
  if (!srcMod || !tgtMod) return

  const [movedPoint] = srcMod.knowledge_points.splice(srcIdx, 1)
  if (srcModId === targetModId && srcIdx < targetIdx) {
    tgtMod.knowledge_points.splice(targetIdx, 0, movedPoint)
  } else {
    tgtMod.knowledge_points.splice(targetIdx, 0, movedPoint)
  }

  dragState.draggingPointId = null
  dragState.sourceModuleId = null
  dragState.sourceIndex = null
}

function onPointDragEnd() {
  dragState.draggingPointId = null
  dragState.sourceModuleId = null
  dragState.sourceIndex = null
}

async function saveEditorChanges() {
  editorSaving.value = true
  try {
    for (const mod of editorModules.value) {
      const pointsYaml = (mod.knowledge_points || []).map((pt, idx) => {
        const lines = [
          `  - id: "${pt.id}"`,
          `    name: "${pt.name}"`,
          `    difficulty: ${pt.difficulty || 1}`,
          `    sort_order: ${idx}`,
        ]
        if (pt.key_concepts && pt.key_concepts.length > 0) {
          lines.push(`    key_concepts:`)
          pt.key_concepts.forEach(c => lines.push(`      - "${c}"`))
        }
        if (pt.prerequisites && pt.prerequisites.length > 0) {
          lines.push(`    prerequisites:`)
          pt.prerequisites.forEach(p => lines.push(`      - "${p}"`))
        }
        return lines.join('\n')
      }).join('\n')

      const yamlContent = `id: "${mod.id}"\nname: "${mod.name}"\nknowledge_points:\n${pointsYaml}\n`
      const yamlPath = `modules/${mod.id}.yaml`
      await api.content.writeYamlFile(yamlPath, yamlContent)
    }
    await api.content.reloadContent()
    emit('saved')
  } catch (e) {
    console.error('Save editor error:', e)
  } finally {
    editorSaving.value = false
  }
}

function resetEditorChanges() {
  editorModules.value = JSON.parse(JSON.stringify(props.modules))
  emit('cancel')
}
</script>

<style scoped>
.editor-empty {
  text-align: center;
  padding: 40px;
  color: var(--color-text-muted);
}

.editor-module {
  margin-bottom: 24px;
  background: var(--color-surface);
  border-radius: 12px;
  border: 1px solid var(--color-border);
  overflow: hidden;
}

.editor-module-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 18px;
  background: var(--color-bg);
  border-bottom: 1px solid var(--color-border);
}

.editor-module-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--color-ink);
}

.editor-module-order {
  font-size: 12px;
  color: var(--color-text-muted);
}

.editor-points-list {
  padding: 12px;
}

.editor-point {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 12px;
  margin-bottom: 8px;
  background: white;
  border: 2px solid var(--color-border);
  border-radius: 8px;
  transition: all 0.2s;
  cursor: grab;
}

.editor-point:hover {
  border-color: var(--color-accent);
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}

.editor-point-dragging {
  opacity: 0.5;
  border-style: dashed;
}

.editor-point-drag-handle {
  cursor: grab;
  font-size: 16px;
  color: var(--color-text-muted);
  padding-top: 4px;
  user-select: none;
}

.editor-point-content {
  flex: 1;
  min-width: 0;
}

.editor-point-name-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.editor-point-name-input {
  flex: 1;
  padding: 6px 10px;
  font-family: var(--font-body);
  font-size: 14px;
  font-weight: 600;
  border: 1px solid var(--color-border);
  border-radius: 6px;
  background: var(--color-bg);
  color: var(--color-ink);
}

.editor-point-name-input:focus {
  outline: none;
  border-color: var(--color-accent);
}

.editor-point-difficulty {
  padding: 4px 8px;
  font-size: 12px;
  border: 1px solid var(--color-border);
  border-radius: 6px;
  background: var(--color-bg);
  cursor: pointer;
}

.editor-point-deps {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  margin-bottom: 6px;
}

.editor-deps-label {
  font-size: 12px;
  color: var(--color-text-muted);
  white-space: nowrap;
  padding-top: 4px;
  min-width: 60px;
}

.editor-deps-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  align-items: center;
}

.editor-dep-tag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 8px;
  font-size: 12px;
  background: #e3f2fd;
  color: #1565c0;
  border-radius: 12px;
}

.editor-dep-remove {
  background: none;
  border: none;
  color: #90a4ae;
  font-size: 14px;
  cursor: pointer;
  padding: 0 2px;
  line-height: 1;
}

.editor-dep-remove:hover {
  color: #e53935;
}

.editor-dep-add {
  padding: 2px 8px;
  font-size: 12px;
  border: 1px dashed var(--color-border);
  border-radius: 12px;
  background: var(--color-bg);
  color: var(--color-text-muted);
  cursor: pointer;
}

.editor-dep-add:hover {
  border-color: var(--color-accent);
}

.editor-point-concepts {
  display: flex;
  align-items: center;
  gap: 8px;
}

.editor-concepts-label {
  font-size: 12px;
  color: var(--color-text-muted);
  white-space: nowrap;
  min-width: 60px;
}

.editor-concepts-input {
  flex: 1;
  padding: 4px 8px;
  font-size: 12px;
  border: 1px solid var(--color-border);
  border-radius: 4px;
  background: var(--color-bg);
  color: var(--color-text);
}

.editor-concepts-input:focus {
  outline: none;
  border-color: var(--color-accent);
}

.editor-actions {
  display: flex;
  gap: 12px;
  justify-content: center;
  padding: 20px 0;
}

.btn-editor-save {
  padding: 10px 28px;
  font-family: var(--font-body);
  font-size: 14px;
  font-weight: 600;
  background: var(--color-accent);
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.2s;
}

.btn-editor-save:hover:not(:disabled) {
  background: var(--color-ink);
}

.btn-editor-save:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-editor-reset {
  padding: 10px 28px;
  font-family: var(--font-body);
  font-size: 14px;
  font-weight: 600;
  background: var(--color-bg);
  color: var(--color-text);
  border: 1px solid var(--color-border);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-editor-reset:hover {
  border-color: var(--color-accent);
}
</style>
