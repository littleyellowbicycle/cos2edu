<template>
  <div class="yaml-preview">
    <template v-if="data">
      <div class="preview-section" v-for="(value, key) in data" :key="key">
        <div class="preview-key">{{ key }}</div>
        <div class="preview-value">
          <template v-if="typeof value === 'string' || typeof value === 'number' || typeof value === 'boolean'">
            <span :class="['scalar', typeof value]">{{ value }}</span>
          </template>
          <template v-else-if="Array.isArray(value)">
            <div class="array-list">
              <div v-for="(item, idx) in value" :key="idx" class="array-item">
                <template v-if="typeof item === 'object' && item !== null">
                  <yaml-preview :data="item" />
                </template>
                <template v-else>
                  <span class="scalar string">{{ item }}</span>
                </template>
              </div>
            </div>
          </template>
          <template v-else-if="typeof value === 'object' && value !== null">
            <yaml-preview :data="value" />
          </template>
          <template v-else>
            <span class="scalar null">{{ value }}</span>
          </template>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
defineProps({
  data: {
    type: [Object, Array, null],
    default: null,
  },
})
</script>

<style scoped>
.yaml-preview {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.preview-section {
  display: flex;
  gap: 12px;
  padding: 6px 0;
  border-bottom: 1px solid var(--color-border);
}

.preview-section:last-child {
  border-bottom: none;
}

.preview-key {
  min-width: 160px;
  max-width: 200px;
  font-size: 13px;
  font-weight: 600;
  color: var(--color-accent);
  flex-shrink: 0;
  padding-top: 2px;
}

.preview-value {
  flex: 1;
  min-width: 0;
}

.scalar {
  font-size: 13px;
  padding: 1px 4px;
  border-radius: 3px;
}

.scalar.string {
  color: #2E7D32;
  background: #E8F5E9;
}

.scalar.number {
  color: #1565C0;
  background: #E3F2FD;
}

.scalar.boolean {
  color: #E65100;
  background: #FFF3E0;
}

.scalar.null {
  color: #757575;
  font-style: italic;
}

.array-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.array-item {
  padding: 6px 12px;
  background: var(--color-bg);
  border-radius: 4px;
  border-left: 2px solid var(--color-accent);
}
</style>