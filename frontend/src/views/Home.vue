<template>
  <div class="home">
    <HomeHero />

    <section class="features">
      <div class="features-grid">
        <FeatureCard
          v-for="feature in features"
          :key="feature.to"
          v-bind="feature"
        />
      </div>
    </section>

    <footer class="home-footer">
      <p class="quote">"我唯一知道的，就是我一无所知。" — 苏格拉底</p>
    </footer>
  </div>
</template>

<script setup>
import HomeHero from '@/components/home/HomeHero.vue'
import FeatureCard from '@/components/home/FeatureCard.vue'

const features = [
  {
    icon: '◈',
    title: '角色管理',
    description: '创建和管理 AI 教学角色，每个角色都有独特的性格和背景',
    to: '/characters',
  },
  {
    icon: '◇',
    title: '教材中心',
    description: '整理和导入教学材料，让 AI 基于教材进行个性化教学',
    to: '/materials',
  },
  {
    icon: '○',
    title: '对话历史',
    description: '保存和回顾所有对话记录，在历史中汲取智慧',
    to: '/conversations',
  },
  {
    icon: '⚙',
    title: '设置',
    description: '配置 AI 模型和 API Key，确保对话功能正常运行',
    to: '/settings',
  },
  {
    icon: '',
    title: '内容编辑器',
    description: '可视化编辑课程大纲、角色配置和世界观设定 YAML',
    to: '/editor',
  },
  {
    icon: '📊',
    title: '学习中心',
    description: '查看学习进度、掌握度分析和薄弱环节',
    to: '/dashboard',
  },
]
</script>

<style scoped>
.home {
  min-height: 100vh;
  background: var(--color-bg);
}

.features {
  padding: 80px 40px;
  background: var(--color-surface);
}

.features-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 32px;
  max-width: 1200px;
  margin: 0 auto;
}

.home-footer {
  padding: 60px 40px;
  text-align: center;
  background: var(--color-bg);
}

.quote {
  font-family: var(--font-display);
  font-size: 20px;
  font-style: italic;
  color: var(--color-text-muted);
  max-width: 600px;
  margin: 0 auto;
}

@media (max-width: 768px) {
  .features {
    padding: 60px 24px;
  }
}
</style>
