<template>
  <div class="materials">
    <header class="page-header">
      <div class="header-content">
        <router-link to="/" class="back-link">
          <span class="back-icon">←</span>
          <span>返回首页</span>
        </router-link>
        <div class="header-title-group">
          <h1 class="page-title">教材</h1>
          <p class="page-subtitle">管理教学内容和材料</p>
        </div>
      </div>
      <button class="btn-create" @click="showCreateDialog = true">
        <span class="btn-icon">+</span>
        添加教材
      </button>
    </header>

    <main class="materials-content">
      <div v-if="loading" class="loading-state">
        <div class="loading-spinner"></div>
        <p>加载中...</p>
      </div>
      
      <div v-else-if="materials.length === 0" class="empty-state">
        <div class="empty-icon">◇</div>
        <h3>暂无教材</h3>
        <p>添加教材内容，让 AI 基于材料进行教学</p>
        <button class="btn-primary" @click="showCreateDialog = true">添加教材</button>
      </div>

      <div v-else class="materials-list">
        <article 
          v-for="(mat, index) in materials" 
          :key="mat.id" 
          class="material-card"
          :style="{ animationDelay: `${index * 80}ms` }"
        >
          <div class="material-number">{{ String(index + 1).padStart(2, '0') }}</div>
          <div class="material-content">
            <h3 class="material-title">{{ mat.title }}</h3>
            <p class="material-description">{{ mat.description || '暂无描述' }}</p>
            <p class="material-excerpt" v-if="mat.content">{{ mat.content.substring(0, 120) }}...</p>
          </div>
          <div class="material-actions">
            <button class="btn-edit" @click="editMaterial(mat)">编辑</button>
            <button class="btn-delete" @click="deleteMaterial(mat.id)">删除</button>
          </div>
        </article>
      </div>
    </main>

    <el-dialog 
      v-model="showCreateDialog" 
      :title="editingMaterial ? '编辑教材' : '添加教材'"
      width="600px"
      class="material-dialog"
    >
      <form @submit.prevent="handleSubmit" class="material-form">
        <div class="form-group">
          <label for="title">标题</label>
          <input 
            id="title" 
            v-model="form.title" 
            type="text" 
            placeholder="教材标题"
            required
          />
        </div>
        <div class="form-group">
          <label for="description">描述</label>
          <textarea 
            id="description" 
            v-model="form.description" 
            placeholder="简要描述"
            rows="2"
          ></textarea>
        </div>
        <div class="form-group">
          <label>教材文件</label>
          <div class="file-upload-area">
            <div v-if="uploadedFileName" class="file-preview">
              <div class="file-preview-header">
                <span class="file-icon">📄</span>
                <span class="file-preview-name">{{ uploadedFileName }}</span>
                <button type="button" class="file-remove" @click="removeUploadedFile">✕</button>
              </div>
            </div>
            <div v-else class="file-upload-zone">
              <label class="file-upload-btn">
                <input 
                  type="file" 
                  accept=".txt,.md,.markdown,.text,.pdf" 
                  @change="handleFileUpload" 
                  style="display: none;"
                />
                <span>📄 上传文本文件</span>
              </label>
            </div>
          </div>
        </div>
      </form>
      <template #footer>
        <button class="btn-cancel" @click="closeDialog">取消</button>
        <button class="btn-submit" :disabled="!uploadedFileName && !editingMaterial" @click="handleSubmit">
          {{ editingMaterial ? '保存' : '添加' }}
        </button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/api'
import { ElMessage } from 'element-plus'

const router = useRouter()
const materials = ref([])
const showCreateDialog = ref(false)
const editingMaterial = ref(null)
const loading = ref(true)

const form = ref({
  title: '',
  description: '',
  content_url: ''
})

const uploadedFileName = ref('')

async function handleFileUpload(event) {
  const file = event.target.files[0]
  if (!file) return
  
  uploadedFileName.value = file.name
  
  try {
    const formData = new FormData()
    formData.append('file', file)
    
    const data = await api.materials.upload(formData)
    form.value.content_url = data.content_url || data.filename || ''
    form.value.description = '概括生成中...'
  } catch (e) {
    console.error(e)
    removeUploadedFile()
  }
}

function removeUploadedFile() {
  form.value.content_url = ''
  uploadedFileName.value = ''
}

onMounted(async () => {
  try {
    materials.value = await api.materials.getAll()
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
})

async function handleSubmit() {
  if (!form.value.title.trim()) {
    ElMessage.warning('请输入教材标题')
    return
  }
  
  if (!uploadedFileName.value && !editingMaterial.value) {
    ElMessage.warning('请上传教材文件')
    return
  }
  
  try {
    if (editingMaterial.value) {
      await api.materials.update(editingMaterial.value.id, form.value)
      ElMessage.success('教材已更新')
    } else {
      const created = await api.materials.create(form.value)
      ElMessage.success('教材已添加，概括生成中...')
      if (created.id) {
        api.materials.generateSummary(created.id).catch(console.error)
      }
    }
    materials.value = await api.materials.getAll()
    closeDialog()
  } catch (e) {
    ElMessage.error('操作失败')
  }
}

function editMaterial(mat) {
  editingMaterial.value = mat
  form.value = {
    title: mat.title,
    description: mat.description || '',
    content_url: mat.content_url || ''
  }
  uploadedFileName.value = mat.content_url || mat.title || '已有文件'
  showCreateDialog.value = true
}

async function deleteMaterial(id) {
  try {
    await api.materials.delete(id)
    materials.value = await api.materials.getAll()
    ElMessage.success('教材已删除')
  } catch (e) {
    ElMessage.error('删除失败')
  }
}

function closeDialog() {
  showCreateDialog.value = false
  editingMaterial.value = null
  form.value = { title: '', description: '', content_url: '' }
  uploadedFileName.value = ''
}
</script>

<style scoped>
.materials {
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

.materials-content {
  padding: 48px 40px;
  max-width: 1000px;
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

.materials-list {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.material-card {
  display: grid;
  grid-template-columns: 80px 1fr auto;
  gap: 32px;
  align-items: start;
  padding: 32px;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 8px;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  animation: fadeInUp 0.6s ease-out both;
}

.material-card:hover {
  transform: translateX(4px);
  border-left-color: var(--color-accent);
  box-shadow: var(--shadow-md);
}

.material-number {
  font-family: var(--font-display);
  font-size: 48px;
  font-weight: 700;
  color: var(--color-border);
  line-height: 1;
}

.material-title {
  font-family: var(--font-display);
  font-size: 24px;
  font-weight: 600;
  color: var(--color-ink);
  margin-bottom: 8px;
}

.material-description {
  font-size: 15px;
  color: var(--color-text-muted);
  margin-bottom: 12px;
}

.material-excerpt {
  font-size: 14px;
  line-height: 1.6;
  color: var(--color-text-muted);
  font-style: italic;
  padding-left: 16px;
  border-left: 2px solid var(--color-border);
}

.material-actions {
  display: flex;
  gap: 12px;
  padding-top: 8px;
}

.material-actions button {
  font-family: var(--font-body);
  font-size: 14px;
  font-weight: 600;
  padding: 10px 16px;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s ease;
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

.material-dialog :deep(.el-dialog) {
  border-radius: 8px;
}

.material-dialog :deep(.el-dialog__header) {
  padding: 24px 32px;
  border-bottom: 1px solid var(--color-border);
}

.material-dialog :deep(.el-dialog__title) {
  font-family: var(--font-display);
  font-size: 24px;
  font-weight: 600;
  color: var(--color-ink);
}

.material-dialog :deep(.el-dialog__body) {
  padding: 32px;
}

.material-form {
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

.content-type-tabs {
  display: flex;
  gap: 8px;
}

.content-type-tabs button {
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

.content-type-tabs button.active {
  background: var(--color-ink);
  color: white;
  border-color: var(--color-ink);
}

.form-group input:focus,
.form-group textarea:focus {
  outline: none;
  border-color: var(--color-accent);
}

.form-group textarea {
  resize: vertical;
  min-height: 100px;
}

.file-upload-wrapper {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.file-upload-area {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.file-upload-zone {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.file-upload-divider {
  text-align: center;
  color: var(--color-text-muted);
  font-size: 14px;
}

.file-upload-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.file-upload-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  color: var(--color-text);
  transition: all 0.2s;
}

.file-upload-btn:hover {
  border-color: var(--color-accent);
  color: var(--color-accent);
}

.file-preview {
  border: 1px solid var(--color-border);
  border-radius: 4px;
  overflow: hidden;
}

.file-preview-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  background: var(--color-bg-warm);
  border-bottom: 1px solid var(--color-border);
}

.file-icon {
  font-size: 16px;
}

.file-preview-name {
  flex: 1;
  font-size: 14px;
  color: var(--color-text);
}

.file-remove {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  color: var(--color-text-muted);
  font-size: 14px;
}

.file-remove:hover {
  background: var(--color-border);
  color: var(--color-ink);
}

.file-preview-content {
  padding: 14px;
  font-size: 14px;
  line-height: 1.6;
  color: var(--color-text);
  max-height: 200px;
  overflow-y: auto;
  white-space: pre-wrap;
  background: var(--color-bg);
}

.file-preview-loading {
  padding: 14px;
  font-size: 14px;
  color: var(--color-text-muted);
  text-align: center;
}

.file-name {
  font-size: 13px;
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
  
  .materials-content {
    padding: 24px;
  }
  
  .material-card {
    grid-template-columns: 1fr;
    gap: 16px;
  }
  
  .material-number {
    font-size: 32px;
  }
}
</style>