<template>
  <div class="characters">
    <header class="page-header">
      <div class="header-content">
        <router-link to="/" class="back-link">
          <span class="back-icon">←</span>
          <span>返回首页</span>
        </router-link>
        <div class="header-title-group">
          <h1 class="page-title">角色</h1>
          <p class="page-subtitle">管理你的 AI 教学伙伴</p>
        </div>
      </div>
      <div class="header-actions">
        <button class="btn-import" @click="triggerImport">
          <span class="btn-icon">📥</span>
          导入角色卡
        </button>
        <button class="btn-create" @click="router.push('/characters/create')">
          <span class="btn-icon">+</span>
          创建角色
        </button>
      </div>
      <input
        ref="importFileInput"
        type="file"
        accept=".png"
        style="display: none"
        aria-hidden="true"
        @change="handleImportFile"
      />
    </header>

    <main class="characters-content">
      <div v-if="loading" class="loading-state">
        <div class="loading-spinner"></div>
        <p>加载中...</p>
      </div>
      
      <div v-else-if="characters.length === 0" class="empty-state">
        <div class="empty-icon">◈</div>
        <h3>暂无角色</h3>
        <p>创建你的第一个 AI 教学角色，开始苏格拉底式对话</p>
        <button class="btn-primary" @click="router.push('/characters/create')">创建角色</button>
      </div>

      <div v-else class="characters-grid">
        <CharacterCard
          v-for="(char, index) in characters"
          :key="char.id"
          :character="char"
          :mood-label="getCharacterMoodLabel(char)"
          :mood-class="getCharacterMoodClass(char)"
          :animation-delay="`${index * 100}ms`"
          @chat="openMaterialSelector"
          @edit="editCharacter"
          @export="exportCard"
          @delete="deleteCharacter"
        />
      </div>
    </main>

    <el-dialog 
      v-model="showMaterialDialog" 
      title="选择教材"
      width="500px"
      class="material-selector-dialog"
    >
      <div class="material-selector-content">
        <p class="material-selector-hint">为对话选择教材（可选）</p>
        
        <div v-if="materials.length <= 6" class="material-options">
          <label class="material-option" :class="{ active: selectedMaterialId === null }">
            <input type="radio" :value="null" v-model="selectedMaterialId" />
            <span class="option-content">
              <span class="option-title">不使用教材</span>
              <span class="option-desc">直接与角色进行自由对话</span>
            </span>
          </label>
          <label 
            v-for="mat in materials" 
            :key="mat.id" 
            class="material-option" 
            :class="{ active: selectedMaterialId === mat.id }"
          >
            <input type="radio" :value="mat.id" v-model="selectedMaterialId" />
            <span class="option-content">
              <span class="option-title">{{ mat.title }}</span>
              <span class="option-desc">{{ mat.description || '暂无描述' }}</span>
            </span>
          </label>
        </div>

        <div v-else class="material-select-wrapper">
          <div class="material-search">
            <input 
              v-model="materialSearch" 
              type="text" 
              placeholder="搜索教材..."
              class="search-input"
            />
          </div>
          <div class="material-select-list">
            <label class="material-option" :class="{ active: selectedMaterialId === null }">
              <input type="radio" :value="null" v-model="selectedMaterialId" />
              <span class="option-content">
                <span class="option-title">不使用教材</span>
                <span class="option-desc">直接与角色进行自由对话</span>
              </span>
            </label>
            <label 
              v-for="mat in filteredMaterials" 
              :key="mat.id" 
              class="material-option" 
              :class="{ active: selectedMaterialId === mat.id }"
            >
              <input type="radio" :value="mat.id" v-model="selectedMaterialId" />
              <span class="option-content">
                <span class="option-title">{{ mat.title }}</span>
                <span class="option-desc">{{ mat.description || '暂无描述' }}</span>
              </span>
            </label>
            <div v-if="filteredMaterials.length === 0 && materialSearch" class="no-results">
              未找到匹配的教材
            </div>
          </div>
        </div>
      </div>
      <template #footer>
        <button class="btn-cancel" @click="showMaterialDialog = false">取消</button>
        <button class="btn-submit" @click="startChatWithMaterial">开始对话</button>
      </template>
    </el-dialog>

    <el-dialog
      v-model="showImportResult"
      title="角色卡导入结果"
      width="560px"
      class="import-result-dialog"
    >
      <div v-if="importResult" class="import-result-content">
        <div class="import-success-banner">
          <span class="success-icon">✅</span>
          <span>角色「{{ importResult.character.name }}」导入成功</span>
        </div>

        <div class="import-detail-section">
          <h4>已导入字段</h4>
          <div class="imported-fields">
            <div class="field-item" v-if="importResult.character.description">
              <span class="field-label">描述</span>
              <span class="field-value">{{ truncate(importResult.character.description, 80) }}</span>
            </div>
            <div class="field-item" v-if="importResult.character.personality">
              <span class="field-label">性格</span>
              <span class="field-value">{{ truncate(importResult.character.personality, 80) }}</span>
            </div>
            <div class="field-item" v-if="importResult.character.background">
              <span class="field-label">背景</span>
              <span class="field-value">{{ truncate(importResult.character.background, 80) }}</span>
            </div>
            <div class="field-item" v-if="importResult.imported_fields.first_mes">
              <span class="field-label">开场白</span>
              <span class="field-value">{{ truncate(importResult.imported_fields.first_mes, 80) }}</span>
            </div>
            <div class="field-item" v-if="importResult.imported_fields.system_prompt">
              <span class="field-label">系统提示</span>
              <span class="field-value">{{ truncate(importResult.imported_fields.system_prompt, 80) }}</span>
            </div>
            <div class="field-item" v-if="importResult.imported_fields.tags && importResult.imported_fields.tags.length">
              <span class="field-label">标签</span>
              <span class="field-value">{{ importResult.imported_fields.tags.join(', ') }}</span>
            </div>
          </div>
        </div>

        <div v-if="importResult.missing_fields.length" class="import-detail-section missing-section">
          <h4>⚠️ 以下字段在角色卡中为空（已使用默认值）</h4>
          <div class="missing-fields">
            <span v-for="field in importResult.missing_fields" :key="field" class="missing-tag">{{ field }}</span>
          </div>
        </div>
      </div>
      <template #footer>
        <button class="btn-submit" @click="showImportResult = false">确定</button>
      </template>
    </el-dialog>

    <CharacterEditDialog
      :visible="showCreateDialog"
      :character="editingCharacter"
      @update:visible="showCreateDialog = $event"
      @saved="onCharacterSaved"
    />
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useCharacterStore } from '@/stores/character'
import { useNarrativeStore } from '@/stores/narrative'
import { useWebSocket } from '@/composables/useWebSocket'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '@/api'
import CharacterCard from '@/components/characters/CharacterCard.vue'
import CharacterEditDialog from '@/components/characters/CharacterEditDialog.vue'

const router = useRouter()
const store = useCharacterStore()
const narrativeStore = useNarrativeStore()
const ws = useWebSocket()
const characters = ref([])
const showCreateDialog = ref(false)
const editingCharacter = ref(null)
const loading = ref(true)
const materials = ref([])
const showMaterialDialog = ref(false)
const selectedMaterialId = ref(null)
const selectedChar = ref(null)
const materialSearch = ref('')

onMounted(async () => {
  ws.connect()
  ws.requestStateSync()
  try {
    await store.fetchAll()
    characters.value = store.characters
  } finally {
    loading.value = false
  }
})

onUnmounted(() => {
  ws.disconnect()
})

function getCharacterMood(char) {
  return narrativeStore.characters[char.id]?.mood ?? null
}

function getCharacterMoodLabel(char) {
  const m = getCharacterMood(char)
  if (m === null) return ''
  if (m > 0.85) return '非常开心'
  if (m > 0.7) return '温和专注'
  if (m > 0.5) return '平静'
  if (m > 0.3) return '有些严肃'
  return '有些担心'
}

function getCharacterMoodClass(char) {
  const m = getCharacterMood(char)
  if (m === null) return ''
  if (m > 0.7) return 'mood-positive'
  if (m > 0.5) return 'mood-neutral'
  return 'mood-negative'
}

const filteredMaterials = computed(() => {
  if (!materialSearch.value) return materials.value
  const search = materialSearch.value.toLowerCase()
  return materials.value.filter(mat => 
    mat.title.toLowerCase().includes(search) || 
    (mat.description && mat.description.toLowerCase().includes(search))
  )
})

const importFileInput = ref(null)
const showImportResult = ref(false)
const importResult = ref(null)
const importing = ref(false)

function editCharacter(char) {
  editingCharacter.value = char
  showCreateDialog.value = true
}

async function deleteCharacter(id) {
  const target = characters.value.find(c => c.id === id)
  const name = target?.name || '该角色'
  try {
    await ElMessageBox.confirm(
      `确定要删除「${name}」吗？此操作不可恢复。`,
      '删除角色',
      {
        confirmButtonText: '删除',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
  } catch {
    return
  }
  try {
    await store.delete(id)
    characters.value = store.characters
    ElMessage.success('角色已删除')
  } catch (e) {
    ElMessage.error('删除失败')
  }
}

async function openMaterialSelector(char) {
  selectedChar.value = char
  selectedMaterialId.value = null
  try {
    materials.value = await api.materials.getAll()
  } catch (e) {
    materials.value = []
  }
  showMaterialDialog.value = true
}

async function startChatWithMaterial() {
  showMaterialDialog.value = false
  if (!selectedChar.value) return
  
  try {
    const conversation = await api.conversations.create({
      character_id: selectedChar.value.id,
      material_id: selectedMaterialId.value,
      title: `与 ${selectedChar.value.name} 的对话`
    })
    router.push(`/chat/${selectedChar.value.id}?conversationId=${conversation.id}`)
  } catch (e) {
    ElMessage.error('创建对话失败')
  }
}

function closeDialog() {
  showCreateDialog.value = false
  editingCharacter.value = null
}

function onCharacterSaved() {
  characters.value = store.characters
  closeDialog()
}

function triggerImport() {
  importFileInput.value?.click()
}

async function handleImportFile(event) {
  const file = event.target.files[0]
  if (!file) return

  if (!file.name.toLowerCase().endsWith('.png')) {
    ElMessage.error('仅支持 PNG 格式的角色卡文件')
    return
  }

  importing.value = true
  try {
    const formData = new FormData()
    formData.append('file', file)
    const result = await api.characters.importCard(formData)
    importResult.value = result
    showImportResult.value = true
    await store.fetchAll()
    characters.value = store.characters
  } catch (e) {
    const msg = e?.response?.data?.detail || e?.message || '导入角色卡失败'
    ElMessage.error(msg)
  } finally {
    importing.value = false
    if (importFileInput.value) {
      importFileInput.value.value = ''
    }
  }
}

async function exportCard(char) {
  try {
    const blob = await api.characters.exportCard(char.id)
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${char.name}_character_card.png`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    window.URL.revokeObjectURL(url)
    ElMessage.success(`角色「${char.name}」已导出`)
  } catch (e) {
    ElMessage.error('导出角色卡失败')
  }
}

function truncate(str, maxLen) {
  if (!str) return ''
  return str.length > maxLen ? str.substring(0, maxLen) + '...' : str
}
</script>

<style scoped>
.characters {
  min-height: 100vh;
  background: var(--color-bg);
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 40px;
  background: var(--color-surface);
  border-bottom: 1px solid var(--color-border);
}

.back-link {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: var(--color-text-muted);
  text-decoration: none;
  transition: color 0.2s;
  margin-bottom: 16px;
}

.back-link:hover {
  color: var(--color-accent);
}

.back-icon {
  font-size: 18px;
}

.header-title-group {
  margin-top: 12px;
}

.page-title {
  font-family: var(--font-display);
  font-size: 42px;
  font-weight: 600;
  color: var(--color-ink);
  margin-bottom: 4px;
}

.page-subtitle {
  font-size: 16px;
  color: var(--color-text-muted);
}

.btn-create {
  display: flex;
  align-items: center;
  gap: 8px;
  font-family: var(--font-body);
  font-size: 15px;
  font-weight: 600;
  padding: 14px 28px;
  background: var(--color-ink);
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.btn-create:hover {
  background: var(--color-accent);
  transform: translateY(-2px);
}

.btn-icon {
  font-size: 18px;
}

.characters-content {
  padding: 48px 40px;
  max-width: 1400px;
  margin: 0 auto;
}

.loading-state,
.empty-state {
  text-align: center;
  padding: 80px 40px;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 3px solid var(--color-border);
  border-top-color: var(--color-accent);
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 20px;
}

.empty-icon {
  font-size: 64px;
  color: var(--color-border);
  margin-bottom: 24px;
}

.empty-state h3 {
  font-family: var(--font-display);
  font-size: 28px;
  color: var(--color-ink);
  margin-bottom: 12px;
}

.empty-state p {
  color: var(--color-text-muted);
  margin-bottom: 32px;
}

.btn-primary {
  font-family: var(--font-body);
  font-size: 15px;
  font-weight: 600;
  padding: 14px 28px;
  background: var(--color-ink);
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.btn-primary:hover {
  background: var(--color-accent);
}

.characters-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
  gap: 32px;
}

.btn-cancel,
.btn-submit {
  font-family: var(--font-body);
  font-size: 15px;
  font-weight: 600;
  padding: 12px 24px;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-cancel {
  background: transparent;
  color: var(--color-text-muted);
  border: 1px solid var(--color-border);
}

.btn-cancel:hover {
  border-color: var(--color-ink);
  color: var(--color-ink);
}

.btn-submit {
  background: var(--color-ink);
  color: white;
  border: none;
}

.btn-submit:hover {
  background: var(--color-accent);
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    gap: 24px;
    padding: 24px;
  }
  
  .characters-content {
    padding: 24px;
  }
  
  .characters-grid {
    grid-template-columns: 1fr;
  }
}

.material-selector-content {
  padding: 8px 0;
}

.material-selector-hint {
  font-size: 14px;
  color: var(--color-text-muted);
  margin-bottom: 20px;
}

.material-options {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.material-select-wrapper {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.material-search {
  position: relative;
}

.search-input {
  width: 100%;
  padding: 12px 16px;
  font-family: var(--font-body);
  font-size: 14px;
  border: 1px solid var(--color-border);
  border-radius: 6px;
  background: var(--color-bg);
  color: var(--color-text);
  transition: border-color 0.2s;
}

.search-input:focus {
  outline: none;
  border-color: var(--color-accent);
}

.search-input::placeholder {
  color: var(--color-text-muted);
}

.material-select-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 320px;
  overflow-y: auto;
  padding-right: 8px;
}

.material-select-list .material-option {
  padding: 12px 16px;
}

.no-results {
  text-align: center;
  padding: 24px;
  color: var(--color-text-muted);
  font-size: 14px;
}

.material-option {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 16px;
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.material-option:hover {
  border-color: var(--color-accent);
}

.material-option.active {
  border-color: var(--color-accent);
  background: var(--color-bg-warm);
}

.material-option input {
  margin-top: 4px;
  accent-color: var(--color-accent);
}

.option-content {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.option-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--color-ink);
}

.option-desc {
  font-size: 13px;
  color: var(--color-text-muted);
}

.material-selector-dialog :deep(.el-dialog__body) {
  padding: 24px 32px;
}

.header-actions {
  display: flex;
  gap: 12px;
  align-items: center;
}

.btn-import {
  display: flex;
  align-items: center;
  gap: 8px;
  font-family: var(--font-body);
  font-size: 15px;
  font-weight: 600;
  padding: 14px 28px;
  background: transparent;
  color: var(--color-ink);
  border: 1px solid var(--color-border);
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.btn-import:hover {
  border-color: var(--color-accent);
  color: var(--color-accent);
  transform: translateY(-2px);
}


.import-result-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.import-success-banner {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 16px 20px;
  background: #f0fdf4;
  border: 1px solid #bbf7d0;
  border-radius: 6px;
  font-size: 16px;
  font-weight: 600;
  color: #166534;
}

.success-icon {
  font-size: 20px;
}

.import-detail-section h4 {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-ink);
  margin-bottom: 12px;
}

.imported-fields {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.field-item {
  display: flex;
  gap: 12px;
  align-items: baseline;
  padding: 8px 12px;
  background: var(--color-bg);
  border-radius: 4px;
}

.field-label {
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text-muted);
  min-width: 60px;
  flex-shrink: 0;
}

.field-value {
  font-size: 13px;
  color: var(--color-text);
  line-height: 1.5;
}

.missing-section h4 {
  color: #b45309;
}

.missing-fields {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.missing-tag {
  font-size: 12px;
  padding: 4px 12px;
  background: #fef3c7;
  color: #92400e;
  border: 1px solid #fcd34d;
  border-radius: 20px;
}

.import-result-dialog :deep(.el-dialog__body) {
  padding: 24px 32px;
}
</style>