import { defineStore } from 'pinia'
import { ref, reactive } from 'vue'

export const useNarrativeStore = defineStore('narrative', () => {
  const world = reactive({
    currentDay: 1,
    totalDays: 90,
    currentScene: 'classroom',
    sceneName: '教室',
    sceneDescription: '明亮的教室，窗外是数据流构成的城市天际线',
    sceneBgColor: '#1a1a2e',
    allowedActions: ['teach', 'question', 'discuss', 'practice'],
    narrativePhase: 'prologue',
    progressPercent: 0,
  })

  const characters = reactive({})

  const progress = reactive({
    currentPoint: null,
    currentPointName: '',
    status: 'idle',
    mastery: 0,
    completedPoints: 0,
    totalPoints: 0,
    masteredPoints: [],
    weakAreas: [],
    nextMilestone: null,
  })

  const activeEvents = ref([])

  const narrativeChoices = ref(null)

  const currentAssessment = ref(null)

  const assessmentResult = ref(null)

  const connectionState = ref('disconnected')

  const lastSyncAt = ref(null)

  function overwriteState(snapshot) {
    if (snapshot.world) {
      Object.assign(world, snapshot.world)
      if (snapshot.world.scene_info) {
        world.sceneName = snapshot.world.scene_info.name
        world.sceneDescription = snapshot.world.scene_info.description
        world.allowedActions = snapshot.world.scene_info.allowed_actions
        world.sceneBgColor = snapshot.world.scene_info.bg_color
      }
    }
    if (snapshot.characters) {
      for (const [cid, cdata] of Object.entries(snapshot.characters)) {
        characters[cid] = {
          ...characters[cid],
          ...cdata,
          moodTrend: cdata.mood > (characters[cid]?.mood || 0.5) ? 'up' : cdata.mood < (characters[cid]?.mood || 0.5) ? 'down' : 'stable',
          lastExpression: cdata.last_expression || characters[cid]?.lastExpression || '',
        }
      }
    }
    if (snapshot.progress) {
      Object.assign(progress, snapshot.progress)
    }
    if (snapshot.active_events) {
      activeEvents.value = snapshot.active_events
    }
    if (snapshot.narrative_choices) {
      narrativeChoices.value = snapshot.narrative_choices
    }
    lastSyncAt.value = new Date()
  }

  function updateEmotion(payload) {
    const cid = payload.character_id
    if (characters[cid]) {
      const prevMood = characters[cid].mood
      characters[cid].mood = payload.mood
      characters[cid].moodTrend = payload.mood > prevMood ? 'up' : payload.mood < prevMood ? 'down' : 'stable'
      characters[cid].lastExpression = payload.expression || ''
    } else {
      characters[cid] = {
        mood: payload.mood,
        moodTrend: 'stable',
        lastExpression: payload.expression || '',
        ...payload,
      }
    }
  }

  function updateProgress(payload) {
    progress.currentPoint = payload.knowledge_point_id
    progress.currentPointName = payload.knowledge_point_id
    progress.status = payload.status
    progress.mastery = payload.mastery
    if (payload.next_point) {
      progress.nextMilestone = { point: payload.next_point }
    }
  }

  function advanceTime(payload) {
    world.currentDay = payload.current_day || world.currentDay + 1
    world.progressPercent = payload.progress_percent || Math.round(world.currentDay / world.totalDays * 100)
    if (payload.narrative_phase) {
      world.narrativePhase = payload.narrative_phase
    }
  }

  function updateSceneChange(payload) {
    world.currentScene = payload.scene_id
    world.sceneName = payload.scene_name
    world.sceneDescription = payload.description
    world.allowedActions = payload.allowed_actions
  }

  function setAssessment(quizData) {
    currentAssessment.value = quizData
    assessmentResult.value = null
  }

  function setAssessmentResult(result) {
    assessmentResult.value = result
    if (result.passed && progress.currentPoint === result.point_id) {
      progress.completedPoints += 1
      progress.masteredPoints.push(result.point_id)
      progress.status = 'mastered'
      progress.mastery = result.mastery_level
    } else {
      progress.mastery = result.mastery_level
      progress.status = result.status
    }
  }

  function clearAssessment() {
    currentAssessment.value = null
    assessmentResult.value = null
  }

  function setConnectionState(state) {
    connectionState.value = state
  }

  function applyTimeAdvance(payload) {
    world.currentDay = payload.current_day || world.currentDay + 1
    world.progressPercent = payload.progress_percent || Math.round(world.currentDay / world.totalDays * 100)
    if (payload.narrative_phase) {
      world.narrativePhase = payload.narrative_phase
    }
    if (payload.scene_info) {
      world.sceneName = payload.scene_info.name
      world.sceneDescription = payload.scene_info.description
      world.currentScene = payload.current_scene || world.currentScene
    }
  }

  function reset() {
    world.currentDay = 1
    world.currentScene = 'classroom'
    world.narrativePhase = 'prologue'
    world.progressPercent = 0
    progress.currentPoint = null
    progress.mastery = 0
    progress.completedPoints = 0
    activeEvents.value = []
    narrativeChoices.value = null
  }

  return {
    world,
    characters,
    progress,
    activeEvents,
    narrativeChoices,
    currentAssessment,
    assessmentResult,
    connectionState,
    lastSyncAt,
    overwriteState,
    updateEmotion,
    updateProgress,
    advanceTime,
    updateSceneChange,
    setAssessment,
    setAssessmentResult,
    clearAssessment,
    applyTimeAdvance,
    setConnectionState,
    reset,
  }
})