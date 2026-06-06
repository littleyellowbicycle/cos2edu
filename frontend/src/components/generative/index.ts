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
  },
  slot: 'inline',
  defaultLifecycle: 'persistent',
  loader: () => import('./EmotionCard.vue'),
})