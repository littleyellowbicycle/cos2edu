<template>
  <div class="characters">
    <el-container>
      <el-header>
        <h1>角色管理</h1>
        <el-button @click="$router.push('/')">返回首页</el-button>
      </el-header>
      <el-main>
        <el-button type="primary" @click="showCreateDialog = true">创建角色</el-button>
        <el-row :gutter="20" style="margin-top: 20px">
          <el-col :span="8" v-for="char in characters" :key="char.id">
            <el-card>
              <template #header>
                <span>{{ char.name }}</span>
              </template>
              <div>{{ char.description }}</div>
              <template #footer>
                <el-button size="small" @click="startChat(char)">开始对话</el-button>
                <el-button size="small" type="danger" @click="deleteCharacter(char.id)">删除</el-button>
              </template>
            </el-card>
          </el-col>
        </el-row>
      </el-main>
    </el-container>

    <el-dialog v-model="showCreateDialog" title="创建角色">
      <el-form :model="form">
        <el-form-item label="名称">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" />
        </el-form-item>
        <el-form-item label="性格">
          <el-input v-model="form.personality" type="textarea" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="createCharacter">创建</el-button>
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
const form = ref({
  name: '',
  description: '',
  personality: ''
})

onMounted(async () => {
  await store.fetchAll()
  characters.value = store.characters
})

async function createCharacter() {
  try {
    await store.create(form.value)
    characters.value = store.characters
    showCreateDialog.value = false
    form.value = { name: '', description: '', personality: '' }
    ElMessage.success('创建成功')
  } catch (e) {
    ElMessage.error('创建失败')
  }
}

async function deleteCharacter(id) {
  try {
    await store.delete(id)
    characters.value = store.characters
    ElMessage.success('删除成功')
  } catch (e) {
    ElMessage.error('删除失败')
  }
}

function startChat(char) {
  router.push(`/chat/${char.id}`)
}
</script>

<style scoped>
.characters {
  height: 100vh;
}
.el-header {
  background-color: #409EFF;
  color: white;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>