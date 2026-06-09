<template>
  <div class="yaml-editor">
    <header class="page-header">
      <div class="header-content">
        <router-link to="/" class="back-link">
          <span class="back-icon">←</span>
          <span>返回首页</span>
        </router-link>
        <div class="header-title-group">
          <h1 class="page-title">内容编辑器</h1>
          <p class="page-subtitle">编辑课程内容、角色配置和世界观设定</p>
        </div>
      </div>
    </header>

    <main class="editor-content">
      <div class="file-list-panel">
        <div class="panel-header">
          <h3>文件列表</h3>
          <button class="btn-reload" @click="reloadContent" :disabled="reloading">
            {{ reloading ? '重载中...' : '↻ 热重载' }}
          </button>
        </div>
        <div class="category-group" v-for="category in fileCategories" :key="category.key">
          <h4 class="category-label">{{ category.label }}</h4>
          <div
            v-for="file in category.files"
            :key="file.path"
            class="file-item"
            :class="{ active: currentFile?.path === file.path }"
            @click="openFile(file)"
          >
            <span class="file-name">{{ file.name }}</span>
            <span class="file-path">{{ file.path }}</span>
          </div>
        </div>
        <div v-if="!fileCategories.some(c => c.files.length)" class="empty-files">
          <p>未找到内容文件</p>
        </div>
      </div>

      <div class="editor-panel">
        <div v-if="!currentFile" class="editor-placeholder">
          <div class="placeholder-icon">📝</div>
          <h3>选择文件开始编辑</h3>
          <p>从左侧选择 YAML 文件内容进行编辑</p>
        </div>

        <div v-else class="editor-active">
          <div class="editor-toolbar">
            <div class="file-info">
              <span class="current-file-name">{{ currentFile.path }}</span>
              <span v-if="dirty" class="dirty-badge">未保存</span>
            </div>
            <div class="toolbar-actions">
              <button class="btn-save" @click="saveFile" :disabled="saving || !dirty">
                {{ saving ? '保存中...' : '保存' }}
              </button>
            </div>
          </div>

          <div class="editor-tabs">
            <button
              :class="['tab-btn', { active: editMode === 'yaml' }]"
              @click="editMode = 'yaml'"
            >YAML 源码</button>
            <button
              :class="['tab-btn', { active: editMode === 'preview' }]"
              @click="editMode = 'preview'"
            >结构预览</button>
          </div>

          <div v-if="editMode === 'yaml'" class="yaml-textarea-wrapper">
            <textarea
              v-model="yamlContent"
              class="yaml-textarea"
              spellcheck="false"
              @input="onContentChange"
            ></textarea>
          </div>

          <div v-else class="preview-panel">
            <div v-if="parseError" class="parse-error">
              <h4>YAML 解析错误</h4>
              <pre>{{ parseError }}</pre>
            </div>
            <div v-else class="preview-content">
              <yaml-preview :data="parsedData" />
            </div>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import api from '@/api'
import YamlPreview from '@/components/YamlPreview.vue'

const fileCategories = ref([
  { key: 'syllabus', label: '课程大纲', files: [] },
  { key: 'modules', label: '知识模块', files: [] },
  { key: 'characters', label: '角色配置', files: [] },
  { key: 'world', label: '世界观设定', files: [] },
])

const currentFile = ref(null)
const yamlContent = ref('')
const originalContent = ref('')
const dirty = ref(false)
const saving = ref(false)
const reloading = ref(false)
const editMode = ref('yaml')
const parseError = ref('')

const parsedData = computed(() => {
  if (!yamlContent.value) return null
  try {
    return require('js-yaml').load(yamlContent.value)
  } catch {
    return null
  }
})

watch(yamlContent, (val) => {
  if (!val) {
    parseError.value = ''
    return
  }
  try {
    require('js-yaml').load(val)
    parseError.value = ''
  } catch (e) {
    parseError.value = e.message
  }
}, { immediate: true })

async function loadFileList() {
  try {
    const result = await api.content.listYamlFiles()
    const files = result.files
    for (const cat of fileCategories.value) {
      cat.files = files.filter(f => f.category === cat.key)
    }
  } catch (e) {
    console.error(e)
  }
}

async function openFile(file) {
  if (dirty.value) {
    if (!confirm('有未保存的更改，确定要切换文件吗？')) return
  }
  try {
    const result = await api.content.readYamlFile(file.path)
    currentFile.value = result
    yamlContent.value = result.raw
    originalContent.value = result.raw
    dirty.value = false
    editMode.value = 'yaml'
    parseError.value = ''
  } catch (e) {
    ElMessage.error('加载文件失败')
  }
}

function onContentChange() {
  dirty.value = yamlContent.value !== originalContent.value
}

async function saveFile() {
  if (!currentFile.value) return
  saving.value = true
  try {
    await api.content.writeYamlFile(currentFile.value.path, yamlContent.value)
    originalContent.value = yamlContent.value
    dirty.value = false
    ElMessage.success('文件已保存')
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '保存失败')
  } finally {
    saving.value = false
  }
}

async function reloadContent() {
  reloading.value = true
  try {
    const result = await api.content.reloadContent()
    ElMessage.success(`热重载成功：${result.knowledge_points} 知识点, ${result.characters} 角色, ${result.scenes} 场景`)
  } catch (e) {
    ElMessage.error('热重载失败')
  } finally {
    reloading.value = false
  }
}

onMounted(() => {
  loadFileList()
})
</script>

<style scoped>
.yaml-editor {
  min-height: 100vh;
  background: var(--color-bg);
  display: flex;
  flex-direction: column;
}

.page-header {
  padding: 24px 40px;
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
  margin-bottom: 12px;
}

.back-link:hover {
  color: var(--color-accent);
}

.header-title-group {
  margin-top: 4px;
}

.page-title {
  font-family: var(--font-display);
  font-size: 36px;
  font-weight: 600;
  color: var(--color-ink);
  margin-bottom: 4px;
}

.page-subtitle {
  font-size: 15px;
  color: var(--color-text-muted);
}

.editor-content {
  flex: 1;
  display: flex;
  overflow: hidden;
}

.file-list-panel {
  width: 280px;
  border-right: 1px solid var(--color-border);
  background: var(--color-surface);
  overflow-y: auto;
  padding: 16px;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.panel-header h3 {
  font-family: var(--font-display);
  font-size: 16px;
  font-weight: 600;
  color: var(--color-ink);
}

.btn-reload {
  font-family: var(--font-body);
  font-size: 12px;
  font-weight: 600;
  padding: 6px 12px;
  border-radius: 4px;
  border: 1px solid var(--color-accent);
  background: transparent;
  color: var(--color-accent);
  cursor: pointer;
  transition: all 0.2s;
}

.btn-reload:hover:not(:disabled) {
  background: var(--color-accent);
  color: white;
}

.btn-reload:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.category-label {
  font-size: 11px;
  font-weight: 600;
  color: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin: 16px 0 8px;
}

.category-label:first-of-type {
  margin-top: 0;
}

.file-item {
  padding: 10px 12px;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  flex-direction: column;
  gap: 2px;
  margin-bottom: 4px;
}

.file-item:hover {
  background: var(--color-bg);
}

.file-item.active {
  background: var(--color-accent-light, rgba(99, 102, 241, 0.1));
  border-left: 3px solid var(--color-accent);
}

.file-name {
  font-size: 14px;
  font-weight: 500;
  color: var(--color-ink);
}

.file-path {
  font-size: 11px;
  color: var(--color-text-muted);
}

.empty-files {
  text-align: center;
  padding: 40px 16px;
  color: var(--color-text-muted);
}

.editor-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.editor-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: var(--color-text-muted);
}

.placeholder-icon {
  font-size: 48px;
  margin-bottom: 16px;
}

.editor-placeholder h3 {
  font-family: var(--font-display);
  font-size: 24px;
  font-weight: 600;
  color: var(--color-ink);
  margin-bottom: 8px;
}

.editor-placeholder p {
  font-size: 14px;
}

.editor-active {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.editor-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 20px;
  border-bottom: 1px solid var(--color-border);
  background: var(--color-surface);
}

.file-info {
  display: flex;
  align-items: center;
  gap: 10px;
}

.current-file-name {
  font-family: monospace;
  font-size: 13px;
  color: var(--color-ink);
  background: var(--color-bg);
  padding: 4px 10px;
  border-radius: 4px;
}

.dirty-badge {
  font-size: 11px;
  font-weight: 600;
  color: #E5A100;
  background: #FFF8E1;
  padding: 2px 8px;
  border-radius: 4px;
}

.btn-save {
  font-family: var(--font-body);
  font-size: 13px;
  font-weight: 600;
  padding: 8px 20px;
  border-radius: 4px;
  border: none;
  background: var(--color-ink);
  color: white;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-save:hover:not(:disabled) {
  background: var(--color-accent);
}

.btn-save:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.editor-tabs {
  display: flex;
  gap: 0;
  border-bottom: 1px solid var(--color-border);
  background: var(--color-surface);
}

.tab-btn {
  font-family: var(--font-body);
  font-size: 13px;
  font-weight: 600;
  padding: 10px 24px;
  border: none;
  background: transparent;
  color: var(--color-text-muted);
  cursor: pointer;
  border-bottom: 2px solid transparent;
  transition: all 0.2s;
}

.tab-btn.active {
  color: var(--color-accent);
  border-bottom-color: var(--color-accent);
}

.tab-btn:hover {
  color: var(--color-ink);
}

.yaml-textarea-wrapper {
  flex: 1;
  overflow: hidden;
}

.yaml-textarea {
  width: 100%;
  height: 100%;
  min-height: 500px;
  padding: 16px 20px;
  border: none;
  outline: none;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 13px;
  line-height: 1.6;
  color: var(--color-ink);
  background: var(--color-bg);
  resize: none;
  tab-size: 2;
}

.preview-panel {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  background: var(--color-bg);
}

.parse-error {
  background: #FEF2F2;
  border: 1px solid #E5C5C5;
  border-radius: 8px;
  padding: 16px;
}

.parse-error h4 {
  color: #C75050;
  margin-bottom: 8px;
}

.parse-error pre {
  font-size: 12px;
  color: #991B1B;
  white-space: pre-wrap;
}

.preview-content {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 8px;
  padding: 20px;
}

@media (max-width: 768px) {
  .editor-content {
    flex-direction: column;
  }

  .file-list-panel {
    width: 100%;
    max-height: 200px;
    border-right: none;
    border-bottom: 1px solid var(--color-border);
  }
}
</style>