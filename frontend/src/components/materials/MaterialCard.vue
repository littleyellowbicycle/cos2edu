<template>
  <article
    class="material-card"
    :class="{ 'material-card--failed': material.status === 'failed' }"
    :style="{ animationDelay: `${index * 80}ms` }"
  >
    <div class="material-number">{{ String(index + 1).padStart(2, '0') }}</div>
    <div class="material-content">
      <h3 class="material-title">{{ material.title }}</h3>
      <p class="material-description">{{ material.description || '暂无描述' }}</p>
      <p class="material-excerpt" v-if="material.content">{{ material.content.substring(0, 120) }}...</p>
      <div v-if="material.status" class="material-status">
        <span :class="['status-badge', `status-${material.status}`]">{{ statusLabel(material.status) }}</span>
      </div>
    </div>
    <div class="material-actions">
      <button class="btn-edit" @click="$emit('edit', material)">编辑</button>
      <button class="btn-delete" @click="$emit('delete', material.id)">删除</button>
    </div>
  </article>
</template>

<script setup>
defineProps({
  material: { type: Object, required: true },
  index: { type: Number, default: 0 },
})

defineEmits(['edit', 'delete'])

const statusLabels = {
  uploading: '上传中',
  parsing: '解析中',
  parsed: '已解析',
  indexing: '索引中',
  indexed: '已索引',
  outlining: '生成大纲',
  pending_review: '待审核',
  ready: '就绪',
  failed: '失败',
}

function statusLabel(status) {
  return statusLabels[status] || status
}
</script>

<style scoped>
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

.material-status {
  margin-top: 8px;
}

.status-badge {
  display: inline-block;
  font-size: 12px;
  font-weight: 600;
  padding: 3px 10px;
  border-radius: 12px;
  letter-spacing: 0.03em;
}

.status-badge.status-ready {
  background: #E8F5E9;
  color: #2E7D32;
}

.status-badge.status-failed {
  background: #FEF2F2;
  color: #C75050;
}

.status-badge.status-pending_review {
  background: #FFF8E1;
  color: #E65100;
}

.status-badge.status-parsing,
.status-badge.status-indexing,
.status-badge.status-outlining {
  background: #E3F2FD;
  color: #1565C0;
}

.status-badge.status-indexed,
.status-badge.status-parsed {
  background: #E8F5E9;
  color: #388E3C;
}

.status-badge.status-uploading {
  background: #F3E5F5;
  color: #7B1FA2;
}

.material-card--failed {
  opacity: 0.65;
}

.material-card--failed .material-number {
  color: #C75050;
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
  .material-card {
    grid-template-columns: 1fr;
    gap: 16px;
  }

  .material-number {
    font-size: 32px;
  }
}
</style>
