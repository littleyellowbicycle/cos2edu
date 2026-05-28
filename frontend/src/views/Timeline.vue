<template>
  <div class="timeline-page">
    <div class="timeline-header">
      <h1>📅 学习时间线</h1>
      <p class="subtitle">第 {{ narrative.world.currentDay }} 天 / 共 {{ narrative.world.totalDays }} 天</p>
    </div>

    <div class="progress-bar-container">
      <el-progress
        :percentage="narrative.world.progressPercent || 0"
        :stroke-width="24"
        :text-inside="true"
        status="success"
      />
    </div>

    <div class="current-scene">
      <h2>📍 {{ narrative.world.sceneName }}</h2>
      <p>{{ narrative.world.sceneDescription }}</p>
    </div>

    <div class="current-progress" v-if="narrative.progress.currentPoint">
      <h3>📖 当前学习</h3>
      <div class="progress-detail">
        <span class="point-name">{{ narrative.progress.currentPointName || narrative.progress.currentPoint }}</span>
        <el-progress
          :percentage="Math.round(narrative.progress.mastery * 100)"
          :stroke-width="12"
          style="flex: 1; margin-left: 12px;"
        />
      </div>
    </div>

    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-value">{{ narrative.progress.completedPoints }}</div>
        <div class="stat-label">已完成知识点</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ narrative.progress.totalPoints }}</div>
        <div class="stat-label">总知识点</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ narrative.world.currentDay }}</div>
        <div class="stat-label">学习天数</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ narrative.world.narrativePhase }}</div>
        <div class="stat-label">当前阶段</div>
      </div>
    </div>

    <div class="actions">
      <el-button type="primary" @click="$router.push('/conversations')">
        继续学习
      </el-button>
      <el-button @click="$router.push('/curriculum')">
        查看课程
      </el-button>
    </div>
  </div>
</template>

<script setup>
import { useNarrativeStore } from '@/stores/narrative'

const narrative = useNarrativeStore()
</script>

<style scoped>
.timeline-page {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
}

.timeline-header {
  text-align: center;
  margin-bottom: 24px;
}

.timeline-header h1 {
  font-size: 28px;
  margin-bottom: 8px;
}

.subtitle {
  color: #999;
  font-size: 14px;
}

.progress-bar-container {
  margin-bottom: 24px;
}

.current-scene {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 24px;
}

.current-scene h2 {
  margin: 0 0 8px 0;
  font-size: 18px;
}

.current-scene p {
  color: #999;
  margin: 0;
}

.current-progress {
  background: rgba(64, 158, 255, 0.08);
  border-radius: 12px;
  padding: 16px 20px;
  margin-bottom: 24px;
}

.current-progress h3 {
  margin: 0 0 12px 0;
  font-size: 16px;
}

.progress-detail {
  display: flex;
  align-items: center;
  gap: 8px;
}

.point-name {
  font-weight: 600;
  min-width: 120px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

.stat-card {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 12px;
  padding: 20px;
  text-align: center;
}

.stat-value {
  font-size: 32px;
  font-weight: bold;
  color: var(--el-color-primary);
}

.stat-label {
  color: #999;
  font-size: 14px;
  margin-top: 4px;
}

.actions {
  display: flex;
  justify-content: center;
  gap: 12px;
  margin-top: 24px;
}
</style>