<template>
  <div class="dashboard-page">
    <div class="dashboard-header">
      <h1>教师管理面板</h1>
      <p class="overview-text">共 {{ totalStudents }} 名学生 / {{ totalKnowledgePoints }} 个知识点</p>
    </div>

    <div v-if="loading" class="loading-container">
      <el-skeleton :rows="5" animated />
    </div>

    <template v-else>
      <div class="students-section">
        <el-card shadow="never">
          <template #header>
            <span>学生进度概览</span>
          </template>
          <el-table :data="students" stripe style="width: 100%">
            <el-table-column prop="username" label="用户名" width="140" />
            <el-table-column prop="display_name" label="显示名" width="120" />
            <el-table-column label="掌握/总数" width="120">
              <template #default="{ row }">
                {{ row.mastered }} / {{ row.total_points }}
              </template>
            </el-table-column>
            <el-table-column label="平均掌握度" width="160">
              <template #default="{ row }">
                <el-progress :percentage="Math.round(row.avg_mastery * 100)" :stroke-width="12" :show-text="true" />
              </template>
            </el-table-column>
            <el-table-column prop="completion_rate" label="完成率" width="100">
              <template #default="{ row }">
                {{ row.completion_rate }}%
              </template>
            </el-table-column>
            <el-table-column label="最后登录" min-width="160">
              <template #default="{ row }">
                {{ row.last_login ? new Date(row.last_login).toLocaleString() : '从未登录' }}
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '@/api'

const loading = ref(true)
const dashboardData = ref(null)

const students = computed(() => dashboardData.value?.students || [])
const totalStudents = computed(() => dashboardData.value?.total_students || 0)
const totalKnowledgePoints = computed(() => dashboardData.value?.total_knowledge_points || 0)

onMounted(async () => {
  try {
    dashboardData.value = await api.get('/auth/dashboard/teacher')
  } catch (e) {
    console.error('Failed to load teacher dashboard:', e)
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.dashboard-page {
  max-width: 1100px;
  margin: 0 auto;
  padding: 24px;
}

.dashboard-header h1 {
  font-size: 28px;
  font-weight: 700;
  color: var(--color-ink);
  margin: 0 0 4px;
}

.overview-text {
  color: var(--color-text-muted);
  font-size: 15px;
  margin: 0 0 24px;
}

.students-section {
  margin-bottom: 24px;
}
</style>