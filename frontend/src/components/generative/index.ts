import { registerComponent } from './registry'

registerComponent({
  name: 'EmotionCard',
  version: '1.0',
  description: '角色情绪状态卡片',
  propsSchema: {
    mood: { type: 'number', required: true, min: 0, max: 1 },
    trust: { type: 'number', required: true, min: 0, max: 1 },
    characterName: { type: 'string', required: true },
    reason: { type: 'string', required: false },
    moodDirection: { type: 'string', required: false, enum: ['up', 'down', 'stable', ''] },
  },
  slot: 'inline',
  defaultLifecycle: 'persistent',
  loader: () => import('./EmotionCard.vue'),
})

registerComponent({
  name: 'QuizForm',
  version: '1.0',
  description: '知识点测验表单，支持选择题和简答题',
  propsSchema: {
    pointId: { type: 'string', required: true },
    pointName: { type: 'string', required: true },
    questions: { type: 'array', required: false },
  },
  slot: 'inline',
  defaultLifecycle: 'ephemeral',
  loader: () => import('./QuizForm.vue'),
})

registerComponent({
  name: 'Timeline',
  version: '1.0',
  description: '历史事件时间线，展示时间序列',
  propsSchema: {
    title: { type: 'string', required: false },
    events: { type: 'array', required: true },
    activeIndex: { type: 'number', required: false, min: -1 },
  },
  slot: 'sidebar',
  defaultLifecycle: 'sticky',
  loader: () => import('./Timeline.vue'),
})

registerComponent({
  name: 'KnowledgeGraph',
  version: '1.0',
  description: '知识点依赖关系图谱',
  propsSchema: {
    title: { type: 'string', required: false },
    highlight: { type: 'string', required: true },
    depth: { type: 'number', required: false, min: 1, max: 5 },
    prerequisites: { type: 'array', required: false },
    dependencies: { type: 'array', required: false },
    masteryLevel: { type: 'number', required: false, min: 0, max: 1 },
  },
  slot: 'panel',
  defaultLifecycle: 'sticky',
  loader: () => import('./KnowledgeGraph.vue'),
})

registerComponent({
  name: 'SceneCard',
  version: '1.0',
  description: '叙事场景切换卡片',
  propsSchema: {
    sceneId: { type: 'string', required: true },
    sceneName: { type: 'string', required: false },
    description: { type: 'string', required: false },
    transition: { type: 'string', required: false, enum: ['fade', 'slide', 'instant'] },
    phase: { type: 'string', required: false },
    allowedActions: { type: 'array', required: false },
  },
  slot: 'overlay',
  defaultLifecycle: 'ephemeral',
  loader: () => import('./SceneCard.vue'),
})