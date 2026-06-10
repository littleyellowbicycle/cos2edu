import { describe, it, expect, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useNarrativeStore } from '@/stores/narrative'

describe('useNarrativeStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('initializes with default values', () => {
    const store = useNarrativeStore()
    expect(store.world.currentDay).toBe(1)
    expect(store.world.currentScene).toBe('classroom')
    expect(store.progress.status).toBe('idle')
    expect(store.progress.mastery).toBe(0)
    expect(store.connectionState).toBe('disconnected')
  })

  it('overwrites state from snapshot', () => {
    const store = useNarrativeStore()
    store.overwriteState({
      world: { currentDay: 5, totalDays: 30, currentScene: 'lab' },
    })
    expect(store.world.currentDay).toBe(5)
    expect(store.world.totalDays).toBe(30)
    expect(store.world.currentScene).toBe('lab')
  })

  it('updates emotion and character mood', () => {
    const store = useNarrativeStore()
    store.updateEmotion({
      character_id: 'char1',
      mood: 0.9,
      expression: 'happy',
    })
    expect(store.characters.char1.mood).toBe(0.9)
  })

  it('updates progress with knowledge point name', () => {
    const store = useNarrativeStore()
    store.updateProgress({
      knowledge_point_id: 'point_1',
      knowledge_point_name: 'Perceptron',
      status: 'in_progress',
      mastery: 0.5,
    })
    expect(store.progress.currentPoint).toBe('point_1')
    expect(store.progress.currentPointName).toBe('Perceptron')
    expect(store.progress.mastery).toBe(0.5)
  })

  it('updates progress falling back to ID when name missing', () => {
    const store = useNarrativeStore()
    store.updateProgress({
      knowledge_point_id: 'point_2',
      status: 'in_progress',
      mastery: 0.3,
    })
    expect(store.progress.currentPointName).toBe('point_2')
  })

  it('handles scene change', () => {
    const store = useNarrativeStore()
    store.updateSceneChange({
      scene_id: 'library',
      scene_name: '图书馆',
      scene_description: '安静的图书馆',
      allowed_actions: ['read', 'study'],
      bg_color: '#2d2d44',
    })
    expect(store.world.currentScene).toBe('library')
    expect(store.world.sceneName).toBe('图书馆')
  })

  it('sets connection state', () => {
    const store = useNarrativeStore()
    store.setConnectionState('connected')
    expect(store.connectionState).toBe('connected')
  })

  it('manages generative components', () => {
    const store = useNarrativeStore()
    store.addGenerativeComponent({
      id: 'comp1',
      component: 'QuizForm',
      props: {},
      slot: 'inline',
      lifecycle: 'persistent',
    })
    expect(store.generativeComponents).toHaveLength(1)
    expect(store.generativeComponents[0].id).toBe('comp1')

    store.updateGenerativeComponent('comp1', { question: 'What?' })
    expect(store.generativeComponents[0].props.question).toBe('What?')

    store.removeGenerativeComponent('comp1')
    expect(store.generativeComponents).toHaveLength(0)
  })

  it('manages assessment lifecycle', () => {
    const store = useNarrativeStore()
    const quiz = { point_id: 'p1', quiz: { questions: [] } }
    store.setAssessment(quiz)
    expect(store.currentAssessment).toEqual(quiz)

    const result = { passed: true, mastery_level: 0.8, point_id: 'p1' }
    store.setAssessmentResult(result)
    expect(store.assessmentResult).toEqual(result)

    store.clearAssessment()
    expect(store.currentAssessment).toBeNull()
    expect(store.assessmentResult).toBeNull()
  })
})