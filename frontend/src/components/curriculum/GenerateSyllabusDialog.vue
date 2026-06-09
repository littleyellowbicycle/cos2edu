<template>
  <div
    ref="overlay"
    class="generate-overlay"
    role="dialog"
    aria-modal="true"
    aria-labelledby="generate-syllabus-title"
    tabindex="-1"
    @click.self="$emit('close')"
  >
    <div class="generate-dialog">
      <div class="dialog-header">
        <h3 id="generate-syllabus-title">从教材生成课程大纲</h3>
        <button class="dialog-close" @click="$emit('close')" aria-label="关闭对话框">&times;</button>
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
            @click="$emit('select-material', m.id)"
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
          <h5>
            {{ phase.name }}
            <span class="phase-range-preview" v-if="phase.days">(第{{ phase.days[0] }}-{{ phase.days[1] }}天)</span>
          </h5>
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
        <button v-if="!generatedSyllabus" class="btn-cancel-dialog" @click="$emit('close')">取消</button>
        <button
          v-if="!generatedSyllabus"
          class="btn-generate-start"
          :disabled="!selectedMaterialId"
          @click="$emit('start-generation')"
        >
          {{ startButtonLabel }}
        </button>
        <template v-if="generatedSyllabus">
          <button class="btn-cancel-dialog" @click="$emit('reject')">拒绝</button>
          <button class="btn-confirm" @click="$emit('confirm')">确认大纲</button>
        </template>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, useTemplateRef } from 'vue'

const props = defineProps({
  generatableMaterials: { type: Array, default: () => [] },
  selectedMaterialId: { type: [String, Number], default: null },
  generatingOutline: { type: Boolean, default: false },
  generatedSyllabus: { type: Object, default: null },
})

const emit = defineEmits(['close', 'select-material', 'start-generation', 'reject', 'confirm'])

const statusLabels = {
  draft: '草稿',
  review: '审核中',
  approved: '已通过',
  archived: '已归档',
}

function syllabusStatusText(status) {
  return statusLabels[status] || status
}

const startButtonLabel = computed(() => {
  const m = props.generatableMaterials.find(m => m.id === props.selectedMaterialId)
  return m && m.has_syllabus ? '重新生成' : '开始生成'
})

const overlayRef = useTemplateRef('overlay')

function handleKeydown(e) {
  if (e.key === 'Escape') {
    emit('close')
  }
}

onMounted(() => {
  document.addEventListener('keydown', handleKeydown)
  overlayRef.value?.focus()
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleKeydown)
})
</script>

<style scoped>
.generate-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 20px;
}

.generate-dialog {
  background: var(--color-surface);
  border-radius: 8px;
  width: 100%;
  max-width: 600px;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
}

.dialog-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px;
  border-bottom: 1px solid var(--color-border);
}

.dialog-header h3 {
  font-family: var(--font-display);
  font-size: 20px;
  font-weight: 600;
  color: var(--color-ink);
  margin: 0;
}

.dialog-close {
  background: none;
  border: none;
  font-size: 24px;
  color: var(--color-text-muted);
  cursor: pointer;
  padding: 0;
  line-height: 1;
}

.dialog-body {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
}

.dialog-hint {
  font-size: 14px;
  color: var(--color-text-muted);
  margin-bottom: 16px;
  line-height: 1.6;
}

.empty-materials {
  padding: 40px 20px;
  text-align: center;
  color: var(--color-text-muted);
  background: var(--color-bg-warm);
  border-radius: 6px;
}

.material-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.material-option {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 16px;
  border: 1px solid var(--color-border);
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
  background: var(--color-bg);
}

.material-option:hover {
  border-color: var(--color-ink);
}

.material-option.selected {
  border-color: var(--color-accent);
  background: var(--color-bg-warm);
}

.material-option.has-syllabus {
  border-style: dashed;
}

.material-option-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.material-option-title {
  font-size: 15px;
  font-weight: 500;
  color: var(--color-ink);
}

.material-option-meta {
  font-size: 13px;
  color: var(--color-text-muted);
}

.has-syllabus-badge {
  display: inline-block;
  font-size: 11px;
  padding: 1px 6px;
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  border-radius: 3px;
  margin-left: 4px;
}

.material-badge {
  font-size: 12px;
  color: #2e7d32;
  font-weight: 500;
}

.material-check {
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-accent);
  font-weight: 700;
  font-size: 18px;
}

.dialog-body.generating {
  text-align: center;
  padding: 60px 24px;
}

.generating-spinner {
  width: 40px;
  height: 40px;
  border: 3px solid var(--color-border);
  border-top-color: var(--color-accent);
  border-radius: 50%;
  margin: 0 auto 16px;
  animation: spin 1s linear infinite;
}

.generating-hint {
  font-size: 13px;
  color: var(--color-text-muted);
  margin-top: 4px;
}

.preview-title {
  font-family: var(--font-display);
  font-size: 18px;
  color: var(--color-ink);
  margin: 0 0 4px;
}

.preview-days {
  font-size: 13px;
  color: var(--color-text-muted);
  margin-bottom: 16px;
}

.preview-phase h5 {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-ink);
  margin: 12px 0 8px;
}

.phase-range-preview {
  font-size: 12px;
  color: var(--color-text-muted);
  font-weight: 400;
  margin-left: 6px;
}

.preview-modules {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.preview-module {
  display: flex;
  flex-direction: column;
  padding: 10px 12px;
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  border-radius: 4px;
  gap: 6px;
}

.mod-name {
  font-size: 14px;
  font-weight: 500;
  color: var(--color-ink);
}

.mod-hours {
  font-size: 12px;
  color: var(--color-text-muted);
  align-self: flex-end;
}

.mod-points {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.point-tag {
  font-size: 11px;
  padding: 2px 8px;
  background: var(--color-bg-warm);
  border: 1px solid var(--color-border);
  border-radius: 3px;
  color: var(--color-text);
}

.dialog-footer {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
  padding: 16px 24px;
  border-top: 1px solid var(--color-border);
}

.btn-cancel-dialog,
.btn-generate-start,
.btn-confirm {
  font-family: var(--font-body);
  font-size: 14px;
  font-weight: 600;
  padding: 10px 20px;
  border-radius: 4px;
  border: 1px solid var(--color-border);
  cursor: pointer;
  transition: all 0.2s;
}

.btn-cancel-dialog {
  background: var(--color-bg);
  color: var(--color-text);
}

.btn-cancel-dialog:hover {
  border-color: var(--color-ink);
}

.btn-generate-start,
.btn-confirm {
  background: var(--color-ink);
  color: white;
  border-color: var(--color-ink);
}

.btn-generate-start:hover:not(:disabled),
.btn-confirm:hover {
  background: var(--color-accent);
  border-color: var(--color-accent);
}

.btn-generate-start:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
