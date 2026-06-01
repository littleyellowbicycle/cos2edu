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
        <article 
          v-for="(char, index) in characters" 
          :key="char.id" 
          class="character-card"
          :style="{ animationDelay: `${index * 100}ms` }"
        >
          <div class="card-avatar">
            <div class="avatar-placeholder" :style="getAvatarStyle(char)">{{ getAvatarDisplay(char) }}</div>
          </div>
          <div class="card-content">
            <h3 class="card-title">{{ char.name }}</h3>
            <p class="card-description">{{ char.description || '暂无描述' }}</p>
            <div class="card-tags">
              <span class="tag" v-if="char.personality">{{ char.personality }}</span>
              <span class="mood-tag" :class="getCharacterMoodClass(char)" v-if="getCharacterMoodLabel(char)">{{ getCharacterMoodLabel(char) }}</span>
            </div>
          </div>
          <div class="card-actions">
            <button class="btn-chat" @click="openMaterialSelector(char)">开始对话</button>
            <button class="btn-edit" @click="editCharacter(char)">编辑</button>
            <button class="btn-export" @click="exportCard(char)" title="导出角色卡">📤</button>
            <button class="btn-delete" @click="deleteCharacter(char.id)">删除</button>
          </div>
        </article>
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

    <el-dialog 
      title="编辑角色"
      width="500px"
      class="character-dialog"
    >
      <form @submit.prevent="handleSubmit" class="character-form">
        <div class="form-group avatar-group">
          <label>头像</label>
          <div class="avatar-preview">
            <div class="avatar-placeholder avatar-preview-img" :style="getAvatarStyle(form)">{{ getAvatarDisplay(form) }}</div>
          </div>
          <div class="avatar-type-tabs">
            <button type="button" :class="{ active: form.avatar_type === 'emoji' }" @click="form.avatar_type = 'emoji'">Emoji</button>
            <button type="button" :class="{ active: form.avatar_type === 'image' }" @click="form.avatar_type = 'image'">上传图片</button>
          </div>
          <div v-if="form.avatar_type === 'emoji'" class="emoji-picker">
            <input 
              v-model="form.avatar" 
              type="text" 
              placeholder="输入一个emoji，如: 😊"
              maxlength="10"
            />
            <div class="emoji-suggestions">
              <span v-for="e in emojiSuggestions" :key="e" @click="form.avatar = e" class="emoji-item">{{ e }}</span>
            </div>
          </div>
          <div v-else class="image-upload-input">
            <input 
              type="file" 
              accept="image/*"
              @change="handleAvatarUpload" 
              ref="avatarInput"
            />
            <div v-if="avatarPreview" class="avatar-upload-preview">
              <img :src="avatarPreview" alt="头像预览" />
              <button type="button" class="remove-avatar" @click="removeAvatar">✕</button>
            </div>
            <p v-else class="upload-hint">点击选择图片文件（支持 JPG、PNG、GIF、WebP）</p>
          </div>
        </div>
        <div class="form-group">
          <label for="name">名称</label>
          <input 
            id="name" 
            v-model="form.name" 
            type="text" 
            placeholder="例如：苏格拉底"
            required
          />
        </div>
        <div class="form-group">
          <label for="description">描述</label>
          <textarea 
            id="description" 
            v-model="form.description" 
            placeholder="角色的简要描述"
            rows="3"
          ></textarea>
        </div>
        <div class="form-group">
          <label for="personality">性格特点</label>
          <input 
            id="personality" 
            v-model="form.personality" 
            type="text" 
            placeholder="例如：善于提问、循循善诱"
          />
        </div>
        <div class="form-group">
          <label for="background">背景故事</label>
          <textarea 
            id="background" 
            v-model="form.background" 
            placeholder="角色的背景故事（可选）"
            rows="4"
          ></textarea>
        </div>
      </form>
      <template #footer>
        <button class="btn-cancel" @click="showCreateDialog = false">取消</button>
        <button class="btn-submit" @click="handleSubmit">
          {{ editingCharacter ? '保存' : '创建' }}
        </button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useCharacterStore } from '@/stores/character'
import { useNarrativeStore } from '@/stores/narrative'
import { useWebSocket } from '@/composables/useWebSocket'
import { ElMessage } from 'element-plus'
import api from '@/api'

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

const form = ref({
  name: '',
  description: '',
  personality: '',
  background: '',
  avatar: '',
  avatar_type: 'emoji'
})

const importFileInput = ref(null)
const showImportResult = ref(false)
const importResult = ref(null)
const importing = ref(false)

const emojiSuggestions = ['😊', '😎', '🤔', '👍', '🎓', '📚', '💡', '🌟', '😃', '🤓', '🧐', '✨']
const avatarPreview = ref('')
const avatarInput = ref(null)

function handleAvatarUpload(event) {
  const file = event.target.files[0]
  if (!file) return

  if (file.size > 5 * 1024 * 1024) {
    ElMessage.error('图片大小不能超过 5MB')
    return
  }

  const reader = new FileReader()
  reader.onload = (e) => {
    form.value.avatar = file
    avatarPreview.value = e.target.result
  }
  reader.onerror = () => {
    ElMessage.error('文件读取失败')
  }
  reader.readAsDataURL(file)
}

function removeAvatar() {
  form.value.avatar = ''
  avatarPreview.value = ''
  if (avatarInput.value) {
    avatarInput.value.value = ''
  }
}

function getAvatarDisplay(item) {
  if (item.avatar_type === 'emoji' && item.avatar) {
    return item.avatar
  }
  if (item.avatar_type === 'image') {
    return ''
  }
  return item.name ? item.name.charAt(0) : '?'
}

function getAvatarStyle(item) {
  if (item.avatar_type === 'image' && item.avatar) {
    if (typeof item.avatar === 'string') {
      if (item.avatar.startsWith('data:') || item.avatar.startsWith('http')) {
        return { backgroundImage: `url(${item.avatar})`, backgroundSize: 'cover', backgroundPosition: 'center' }
      }
      if (item.avatar.startsWith('/')) {
        return { backgroundImage: `url(${item.avatar})`, backgroundSize: 'cover', backgroundPosition: 'center' }
      }
      return { backgroundImage: `url(/api/v1/crud/avatars/${item.avatar})`, backgroundSize: 'cover', backgroundPosition: 'center' }
    }
  }
  return {}
}

onMounted(async () => {
  try {
    await store.fetchAll()
    characters.value = store.characters
  } finally {
    loading.value = false
  }
})

async function handleSubmit() {
  if (!form.value.name.trim()) {
    ElMessage.warning('请输入角色名称')
    return
  }
  
  try {
    const data = new FormData()
    data.append('name', form.value.name)
    data.append('description', form.value.description || '')
    data.append('personality', form.value.personality || '')
    data.append('background', form.value.background || '')
    data.append('avatar_type', form.value.avatar_type)
    
    if (form.value.avatar_type === 'image' && form.value.avatar instanceof File) {
      data.append('avatar', form.value.avatar)
    } else if (form.value.avatar_type === 'emoji') {
      data.append('avatar', form.value.avatar)
    }
    
    if (editingCharacter.value) {
      await store.update(editingCharacter.value.id, data)
      ElMessage.success('角色已更新')
    } else {
      await store.create(data)
      ElMessage.success('角色已创建')
    }
    characters.value = store.characters
    closeDialog()
  } catch (e) {
    ElMessage.error('操作失败')
  }
}

function editCharacter(char) {
  editingCharacter.value = char
  form.value = {
    name: char.name,
    description: char.description || '',
    personality: char.personality || '',
    background: char.background || '',
    avatar: char.avatar || '',
    avatar_type: char.avatar_type || 'emoji'
  }
  avatarPreview.value = ''
  if (char.avatar_type === 'image' && char.avatar) {
    if (char.avatar.startsWith('data:') || char.avatar.startsWith('http')) {
      avatarPreview.value = char.avatar
    } else if (char.avatar.startsWith('/')) {
      avatarPreview.value = char.avatar
    } else {
      avatarPreview.value = `/api/v1/avatars/${char.avatar}`
    }
  }
  showCreateDialog.value = true
}

async function deleteCharacter(id) {
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

function startChat(char) {
  router.push(`/chat/${char.id}`)
}

function closeDialog() {
  showCreateDialog.value = false
  editingCharacter.value = null
  form.value = { name: '', description: '', personality: '', background: '', avatar: '', avatar_type: 'emoji' }
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

.character-card {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 8px;
  padding: 32px;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  animation: fadeInUp 0.6s ease-out both;
}

.character-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-lg);
  border-color: var(--color-accent-light);
}

.card-avatar {
  margin-bottom: 24px;
}

.avatar-placeholder {
  width: 72px;
  height: 72px;
  background: linear-gradient(135deg, var(--color-accent) 0%, var(--color-accent-light) 100%);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: var(--font-display);
  font-size: 32px;
  font-weight: 600;
  color: white;
}

.avatar-placeholder.avatar-preview-img {
  background: none;
}

.avatar-group {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.avatar-preview {
  display: flex;
  justify-content: center;
  margin-bottom: 8px;
}

.avatar-preview .avatar-placeholder {
  width: 96px;
  height: 96px;
  font-size: 48px;
}

.avatar-type-tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 8px;
}

.avatar-type-tabs button {
  flex: 1;
  padding: 10px 16px;
  font-size: 14px;
  font-weight: 600;
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
}

.avatar-type-tabs button.active {
  background: var(--color-ink);
  color: white;
  border-color: var(--color-ink);
}

.emoji-picker input {
  width: 100%;
  padding: 12px 16px;
  font-size: 18px;
  text-align: center;
  border: 1px solid var(--color-border);
  border-radius: 4px;
  background: var(--color-bg);
  color: var(--color-text);
}

.emoji-suggestions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 12px;
}

.emoji-item {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  background: var(--color-bg-warm);
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
}

.emoji-item:hover {
  background: var(--color-border);
  transform: scale(1.1);
}

.image-upload-input input[type="file"] {
  width: 100%;
  padding: 12px 16px;
  font-size: 14px;
  border: 1px dashed var(--color-border);
  border-radius: 4px;
  background: var(--color-bg);
  color: var(--color-text);
  cursor: pointer;
}

.image-upload-input input[type="file"]:hover {
  border-color: var(--color-accent);
}

.avatar-upload-preview {
  position: relative;
  display: inline-block;
  margin-top: 12px;
}

.avatar-upload-preview img {
  width: 96px;
  height: 96px;
  border-radius: 50%;
  object-fit: cover;
  border: 2px solid var(--color-border);
}

.remove-avatar {
  position: absolute;
  top: -6px;
  right: -6px;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: #C75050;
  color: white;
  border: none;
  cursor: pointer;
  font-size: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.remove-avatar:hover {
  background: #a03939;
}

.upload-hint {
  margin-top: 12px;
  font-size: 13px;
  color: var(--color-text-muted);
  text-align: center;
}

.card-title {
  font-family: var(--font-display);
  font-size: 26px;
  font-weight: 600;
  color: var(--color-ink);
  margin-bottom: 8px;
}

.card-description {
  font-size: 15px;
  line-height: 1.6;
  color: var(--color-text-muted);
  margin-bottom: 16px;
}

.card-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 24px;
}

.tag {
  font-size: 12px;
  padding: 4px 12px;
  background: var(--color-bg-warm);
  color: var(--color-text-muted);
  border-radius: 20px;
  border: 1px solid var(--color-border);
}

.mood-tag {
  font-size: 12px;
  padding: 4px 12px;
  border-radius: 20px;
  font-weight: 500;
}

.mood-tag.mood-positive {
  background: #e8f5e9;
  color: #2e7d32;
  border: 1px solid #a5d6a7;
}

.mood-tag.mood-neutral {
  background: #fff3e0;
  color: #e65100;
  border: 1px solid #ffcc80;
}

.mood-tag.mood-negative {
  background: #ffebee;
  color: #c62828;
  border: 1px solid #ef9a9a;
}

.card-actions {
  display: flex;
  gap: 12px;
  padding-top: 20px;
  border-top: 1px solid var(--color-border);
}

.card-actions button {
  flex: 1;
  font-family: var(--font-body);
  font-size: 14px;
  font-weight: 600;
  padding: 12px 16px;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-chat {
  background: var(--color-ink);
  color: white;
  border: none;
}

.btn-chat:hover {
  background: var(--color-accent);
}

.btn-edit {
  background: transparent;
  color: var(--color-text-muted);
  border: 1px solid var(--color-border);
}

.btn-edit:hover {
  border-color: var(--color-ink);
  color: var(--color-ink);
}

.btn-delete {
  background: transparent;
  color: #C75050;
  border: 1px solid #E5C5C5;
}

.btn-delete:hover {
  background: #FEF2F2;
  border-color: #C75050;
}

.character-dialog :deep(.el-dialog) {
  border-radius: 8px;
}

.character-dialog :deep(.el-dialog__header) {
  padding: 24px 32px;
  border-bottom: 1px solid var(--color-border);
}

.character-dialog :deep(.el-dialog__title) {
  font-family: var(--font-display);
  font-size: 24px;
  font-weight: 600;
  color: var(--color-ink);
}

.character-dialog :deep(.el-dialog__body) {
  padding: 32px;
}

.character-dialog :deep(.el-dialog__footer) {
  padding: 20px 32px;
  border-top: 1px solid var(--color-border);
}

.character-form {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-group label {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-ink);
}

.form-group input,
.form-group textarea {
  font-family: var(--font-body);
  font-size: 15px;
  padding: 12px 16px;
  border: 1px solid var(--color-border);
  border-radius: 4px;
  background: var(--color-bg);
  color: var(--color-text);
  transition: border-color 0.2s;
}

.form-group input:focus,
.form-group textarea:focus {
  outline: none;
  border-color: var(--color-accent);
}

.form-group input::placeholder,
.form-group textarea::placeholder {
  color: var(--color-text-muted);
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

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
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

.btn-export {
  font-size: 16px;
  padding: 10px 14px;
  background: transparent;
  border: 1px solid var(--color-border);
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s ease;
  line-height: 1;
}

.btn-export:hover {
  border-color: var(--color-accent);
  background: var(--color-bg-warm);
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