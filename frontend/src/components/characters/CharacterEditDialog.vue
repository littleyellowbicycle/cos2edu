<template>
  <el-dialog
    :model-value="visible"
    :title="character ? '编辑角色' : '创建角色'"
    width="500px"
    class="character-dialog"
    @update:model-value="$emit('update:visible', $event)"
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
            aria-label="选择头像图片"
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
      <button class="btn-cancel" @click="closeDialog">取消</button>
      <button class="btn-submit" @click="handleSubmit">
        {{ character ? '保存' : '创建' }}
      </button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useCharacterStore } from '@/stores/character'
import { ElMessage } from 'element-plus'
import { getAvatarDisplay, getAvatarStyle } from '@/composables/useCharacterAvatar'

const props = defineProps({
  visible: { type: Boolean, default: false },
  character: { type: Object, default: null },
})

const emit = defineEmits(['update:visible', 'saved'])

const store = useCharacterStore()

const form = ref({
  name: '',
  description: '',
  personality: '',
  background: '',
  avatar: '',
  avatar_type: 'emoji',
})

const emojiSuggestions = ['😊', '😎', '🤔', '👍', '🎓', '📚', '💡', '🌟', '😃', '🤓', '🧐', '✨']
const avatarPreview = ref('')
const avatarInput = ref(null)

watch(() => props.visible, (v) => {
  if (v) {
    if (props.character) {
      form.value = {
        name: props.character.name,
        description: props.character.description || '',
        personality: props.character.personality || '',
        background: props.character.background || '',
        avatar: props.character.avatar || '',
        avatar_type: props.character.avatar_type || 'emoji',
      }
      avatarPreview.value = ''
      if (props.character.avatar_type === 'image' && props.character.avatar) {
        if (props.character.avatar.startsWith('data:') || props.character.avatar.startsWith('http')) {
          avatarPreview.value = props.character.avatar
        } else if (props.character.avatar.startsWith('/')) {
          avatarPreview.value = props.character.avatar
        } else {
          avatarPreview.value = `/api/v1/avatars/${props.character.avatar}`
        }
      }
    } else {
      form.value = { name: '', description: '', personality: '', background: '', avatar: '', avatar_type: 'emoji' }
      avatarPreview.value = ''
    }
  }
})

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

    if (props.character) {
      await store.update(props.character.id, data)
      ElMessage.success('角色已更新')
    } else {
      await store.create(data)
      ElMessage.success('角色已创建')
    }
    emit('saved')
    closeDialog()
  } catch {
    ElMessage.error('操作失败')
  }
}

function closeDialog() {
  emit('update:visible', false)
}
</script>

<style scoped>
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
</style>
