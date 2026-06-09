<template>
  <el-card class="stat-card" shadow="hover">
    <div class="stat-icon" :class="iconClass">
      <el-icon><component :is="icon" /></el-icon>
    </div>
    <div class="stat-info">
      <div class="stat-value">{{ value }}</div>
      <div class="stat-label">{{ label }}</div>
    </div>
  </el-card>
</template>

<script setup>
import { ElCard, ElIcon } from 'element-plus'

defineProps({
  value: { type: [String, Number], required: true },
  label: { type: String, required: true },
  icon: { type: [Object, Function], required: true },
  iconClass: { type: String, default: '' },
})
</script>

<style scoped>
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
  flex-shrink: 0;
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
</style>
