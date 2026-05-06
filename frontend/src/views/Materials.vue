<template>
  <div class="materials">
    <el-container>
      <el-header>
        <h1>教材管理</h1>
        <el-button @click="$router.push('/')">返回首页</el-button>
      </el-header>
      <el-main>
        <el-button type="primary" @click="showCreateDialog = true">创建教材</el-button>
        <el-row :gutter="20" style="margin-top: 20px">
          <el-col :span="8" v-for="mat in materials" :key="mat.id">
            <el-card>
              <template #header>
                <span>{{ mat.title }}</span>
              </template>
              <div>{{ mat.description }}</div>
            </el-card>
          </el-col>
        </el-row>
      </el-main>
    </el-container>

    <el-dialog v-model="showCreateDialog" title="创建教材">
      <el-form :model="form">
        <el-form-item label="标题">
          <el-input v-model="form.title" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" />
        </el-form-item>
        <el-form-item label="内容">
          <el-input v-model="form.content" type="textarea" rows="5" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="createMaterial">创建</el-button>
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
const form = ref({
  title: '',
  description: '',
  content: ''
})

onMounted(async () => {
  materials.value = await api.materials.getAll()
})

async function createMaterial() {
  try {
    await api.materials.create(form.value)
    materials.value = await api.materials.getAll()
    showCreateDialog.value = false
    form.value = { title: '', description: '', content: '' }
    ElMessage.success('创建成功')
  } catch (e) {
    ElMessage.error('创建失败')
  }
}
</script>

<style scoped>
.materials {
  height: 100vh;
}
.el-header {
  background-color: #67C23A;
  color: white;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>