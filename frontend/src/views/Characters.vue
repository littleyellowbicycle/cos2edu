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
      <button class="btn-create" @click="showCreateDialog = true">
        <span class="btn-icon">+</span>
        创建角色
      </button>
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
        <button class="btn-primary" @click="showCreateDialog = true">创建角色</button>
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
            </div>
          </div>
          <div class="card-actions">
            <button class="btn-chat" @click="startChat(char)">开始对话</button>
            <button class="btn-edit" @click="editCharacter(char)">编辑</button>
            <button class="btn-delete" @click="deleteCharacter(char.id)">删除</button>
          </div>
        </article>
      </div>
    </main>

    <el-dialog 
      v-model="showCreateDialog" 
      :title="editingCharacter ? '编辑角色' : '创建角色'"
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
            <button type="button" :class="{ active: form.avatar_type === 'image' }" @click="form.avatar_type = 'image'">图片URL</button>
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
          <div v-else class="image-url-input">
            <input 
              v-model="form.avatar" 
              type="text" 
              placeholder="输入图片URL，如: https://..."
            />
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
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useCharacterStore } from '@/stores/character'
import { ElMessage } from 'element-plus'

const router = useRouter()
const store = useCharacterStore()
const characters = ref([])
const showCreateDialog = ref(false)
const editingCharacter = ref(null)
const loading = ref(true)

const form = ref({
  name: '',
  description: '',
  personality: '',
  background: '',
  avatar: '',
  avatar_type: 'emoji'
})

const emojiSuggestions = ['😊', '😎', '🤔', '👍', '🎓', '📚', '💡', '🌟', '😃', '🤓', '🧐', '✨']

function getAvatarDisplay(item) {
  if (item.avatar_type === 'emoji' && item.avatar) {
    return item.avatar
  }
  return item.name ? item.name.charAt(0) : '?'
}

function getAvatarStyle(item) {
  if (item.avatar_type === 'image' && item.avatar) {
    return { backgroundImage: `url(${item.avatar})`, backgroundSize: 'cover', backgroundPosition: 'center' }
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
    if (editingCharacter.value) {
      await store.update(editingCharacter.value.id, form.value)
      ElMessage.success('角色已更新')
    } else {
      await store.create(form.value)
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

function startChat(char) {
  router.push(`/chat/${char.id}`)
}

function closeDialog() {
  showCreateDialog.value = false
  editingCharacter.value = null
  form.value = { name: '', description: '', personality: '', background: '', avatar: '', avatar_type: 'emoji' }
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

.image-url-input input {
  width: 100%;
  padding: 12px 16px;
  font-size: 14px;
  border: 1px solid var(--color-border);
  border-radius: 4px;
  background: var(--color-bg);
  color: var(--color-text);
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
</style>