<template>
  <div class="dashboard-page">
    <div class="dashboard-header">
      <h1>学习中心</h1>
      <p class="welcome-text">{{ greeting }}，欢迎回来</p>
    </div>

    <div v-if="loading" class="loading-container">
      <el-skeleton :rows="5" animated />
    </div>

    <template v-else>
      <div class="stats-grid">
        <el-card class="stat-card" shadow="hover">
          <div class="stat-icon mastered"><el-icon><CircleCheck /></el-icon></div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.mastered }}</div>
            <div class="stat-label">已掌握</div>
          </div>
        </el-card>
        <el-card class="stat-card" shadow="hover">
          <div class="stat-icon learning"><el-icon><Loading /></el-icon></div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.learning }}</div>
            <div class="stat-label">学习中</div>
          </div>
        </el-card>
        <el-card class="stat-card" shadow="hover">
          <div class="stat-icon locked"><el-icon><Lock /></el-icon></div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.locked }}</div>
            <div class="stat-label">未解锁</div>
          </div>
        </el-card>
        <el-card class="stat-card" shadow="hover">
          <div class="stat-icon rate"><el-icon><TrendCharts /></el-icon></div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.completion_rate }}%</div>
            <div class="stat-label">完成率</div>
          </div>
        </el-card>
      </div>

      <div class="progress-section">
        <el-card shadow="never">
          <template #header>
            <div class="section-header">
              <span>整体掌握度</span>
              <span class="mastery-score">{{ stats.avg_mastery }}%</span>
            </div>
          </template>
          <el-progress :percentage="stats.avg_mastery" :stroke-width="20" :color="progressColor" />
        </el-card>
      </div>

      <div class="points-section">
        <el-card shadow="never">
          <template #header>
            <span>知识点详情</span>
          </template>
          <el-table :data="pointDetails" stripe style="width: 100%">
            <el-table-column prop="point_id" label="知识点" min-width="180" />
            <el-table-column prop="status" label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="statusType(row.status)" size="small">{{ statusLabel(row.status) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="mastery_level" label="掌握度" width="160">
              <template #default="{ row }">
                <el-progress :percentage="Math.round(row.mastery_level * 100)" :stroke-width="12" :show-text="false" />
              </template>
            </el-table-column>
            <el-table-column prop="attempts" label="尝试次数" width="100" />
            <el-table-column label="薄弱环节" min-width="200">
              <template #default="{ row }">
                <el-tag v-for="area in (row.weak_areas || []).slice(0, 3)" :key="area" size="small" type="warning" style="margin-right:4px">{{ area }}</el-tag>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </div>

      <div class="actions-section">
        <el-button type="primary" size="large" @click="$router.push('/curriculum')">
          查看课程大纲
        </el-button>
        <el-button size="large" @click="$router.push('/timeline')">
          学习时间线
        </el-button>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { CircleCheck, Loading, Lock, TrendCharts } from '@element-plus/icons-vue'
import { apiClient } from '@/api'

const loading = ref(true)
const dashboardData = ref(null)

const greeting = computed(() => {
  const h = new Date().getHours()
  if (h < 6) return '夜深了'
  if (h < 12) return '早上好'
  if (h < 18) return '下午好'
  return '晚上好'
})

const stats = computed(() => dashboardData.value?.progress_summary || {
  total_points: 0, mastered: 0, learning: 0, locked: 0, avg_mastery: 0, completion_rate: 0,
})

const pointDetails = computed(() => dashboardData.value?.point_details || [])

const progressColor = computed(() => {
  const m = stats.value.avg_mastery
  if (m >= 70) return '#67c23a'
  if (m >= 40) return '#e6a23c'
  return '#f56c6c'
})

function statusType(status) {
  const map = { mastered: 'success', learning: '', locked: 'info' }
  return map[status] || 'info'
}

function statusLabel(status) {
  const map = { mastered: '已掌握', learning: '学习中', unlocked: '学习中', locked: '未解锁' }
  return map[status] || status
}

onMounted(async () => {
  try {
    dashboardData.value = await apiClient.get('/curriculum/progress-summary')
  } catch (e) {
    console.error('Failed to load dashboard:', e)
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.dashboard-page {
  max-width: 960px;
  margin: 0 auto;
  padding: 24px;
}

.dashboard-header h1 {
  font-size: 28px;
  font-weight: 700;
  color: var(--color-ink);
  margin: 0 0 4px;
}

.welcome-text {
  color: var(--color-text-muted);
  font-size: 15px;
  margin: 0 0 24px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

@media (max-width: 768px) {
  .stats-grid { grid-template-columns: repeat(2, 1fr); }
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 16px;
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
}

.stat-icon.mastered { background: #e8f5e9; color: #67c23a; }
.stat-icon.learning { background: #e3f2fd; color: #409eff; }
.stat-icon.locked { background: #f5f5f5; color: #909399; }
.stat-icon.rate { background: #fff3e0; color: #e6a23c; }

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: var(--color-ink);
}

.stat-label {
  font-size: 13px;
  color: var(--color-text-muted);
}

.progress-section, .points-section {
  margin-bottom: 24px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 600;
}

.mastery-score {
  font-size: 20px;
  color: var(--color-accent);
}

.actions-section {
  display: flex;
  gap: 12px;
}
</style>