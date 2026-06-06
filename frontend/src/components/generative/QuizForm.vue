<template>
  <div class="quiz-form" v-if="showQuiz">
    <div class="quiz-header">
      <span class="quiz-icon">&#9733;</span>
      <h3>知识点测验：{{ quizData.point_name }}</h3>
    </div>
    <div v-for="(q, qi) in questions" :key="qi" class="quiz-question">
      <p class="question-text">{{ q.question_text }}</p>
      <div v-if="q.question_type === 'choice'" class="question-options">
        <label
          v-for="(opt, oi) in q.options"
          :key="oi"
          class="option-label"
          :class="{ 'option-selected': answers[qi] === opt }"
        >
          <input type="radio" :name="`q-${qi}`" :value="opt" v-model="answers[qi]" />
          {{ opt }}
        </label>
      </div>
      <div v-else class="question-open">
        <textarea v-model="answers[qi]" placeholder="请输入你的答案..." rows="2"></textarea>
      </div>
    </div>
    <button class="btn-submit-quiz" @click="handleSubmit" :disabled="!allAnswered">
      提交答案
    </button>
  </div>

  <div v-else-if="showResult" class="quiz-result" role="region" aria-label="考核结果">
    <div class="result-header" :class="{ 'result-passed': result.passed, 'result-failed': !result.passed }">
      <span class="result-icon">{{ result.passed ? '&#10004;' : '&#10008;' }}</span>
      <h3>{{ result.passed ? '考核通过！' : '继续努力' }}</h3>
    </div>
    <p class="result-feedback">{{ result.feedback }}</p>
    <div class="result-stats">
      <div class="mastery-progress-group">
        <span class="mastery-label">掌握度</span>
        <progress class="mastery-bar" :value="masteryPercent" max="100"></progress>
        <span class="mastery-pct">{{ masteryPercent }}%</span>
      </div>
      <span class="mastery-status">状态: {{ statusLabel }}</span>
    </div>
    <button class="btn-continue-quiz" @click="handleContinue">继续学习</button>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useNarrativeStore } from '@/stores/narrative'

const props = defineProps({
  pointId: { type: String, default: '' },
  questions: { type: Array, default: () => [] },
  pointName: { type: String, default: '' },
  componentId: { type: String, default: '' },
})

const emit = defineEmits(['interact', 'complete', 'continue'])
const narrativeStore = useNarrativeStore()
const answers = ref({})

const quizData = computed(() => narrativeStore.currentAssessment || { point_id: props.pointId, point_name: props.pointName, quiz: { questions: props.questions } })
const resultData = computed(() => narrativeStore.assessmentResult)

const showQuiz = computed(() => !!quizData.value && !resultData.value)
const showResult = computed(() => !!resultData.value)

const questions = computed(() => quizData.value?.quiz?.questions || [])

const allAnswered = computed(() => {
  if (!questions.value.length) return false
  return questions.value.every((q, i) => {
    const answer = answers.value[i]
    return answer && String(answer).trim().length > 0
  })
})

const masteryPercent = computed(() =>
  Math.round(Math.max(0, Math.min(1, resultData.value?.mastery_level || 0)) * 100)
)

const statusLabel = computed(() => {
  const s = resultData.value?.status
  if (s === 'mastered') return '已掌握'
  if (s === 'learning') return '学习中'
  if (s === 'review_needed') return '需要复习'
  return s || ''
})

watch(() => quizData.value, () => {
  answers.value = {}
})

function handleSubmit() {
  const quiz = quizData.value
  if (!quiz) return

  const formattedAnswers = (quiz.quiz?.questions || []).map((q, i) => ({
    question: q,
    answer: answers.value[i] || '',
  }))

  emit('interact', {
    action: 'submit',
    value: { pointId: quiz.point_id || props.pointId, answers: formattedAnswers },
  })
}

function handleContinue() {
  narrativeStore.clearAssessment()
  answers.value = {}
  emit('continue')
}
</script>

<style scoped>
.quiz-form {
  margin: 16px 0;
  padding: 20px;
  background: white;
  border-radius: 12px;
  border: 2px solid var(--color-accent, #8B4513);
  max-width: 100%;
}

.quiz-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 16px;
}

.quiz-icon {
  font-size: 24px;
  color: var(--color-accent, #8B4513);
}

.quiz-header h3 {
  margin: 0;
  font-size: 18px;
  font-family: var(--font-display, serif);
  color: var(--color-ink, #2C2416);
}

.quiz-question {
  margin: 16px 0;
  padding: 12px;
  background: var(--color-bg-warm, #F5F1EB);
  border-radius: 8px;
}

.question-text {
  font-weight: 600;
  margin-bottom: 10px;
  color: var(--color-ink, #2C2416);
}

.question-options {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.option-label {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: var(--color-surface, white);
  border: 2px solid var(--color-border, #E5E0D8);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 14px;
}

.option-label:hover {
  border-color: var(--color-accent, #8B4513);
  background: var(--color-bg-warm, #F5F1EB);
}

.option-selected {
  border-color: var(--color-accent, #8B4513);
  background: var(--color-bg-warm, #F5F1EB);
  font-weight: 600;
}

.option-selected input[type="radio"] {
  accent-color: var(--color-accent, #8B4513);
}

.question-open textarea {
  width: 100%;
  padding: 10px;
  border: 2px solid var(--color-border, #E5E0D8);
  border-radius: 8px;
  font-family: var(--font-body, sans-serif);
  font-size: 14px;
  resize: vertical;
  background: var(--color-surface, white);
  color: var(--color-text, #1A1A1A);
}

.question-open textarea:focus {
  outline: none;
  border-color: var(--color-accent, #8B4513);
}

.btn-submit-quiz {
  display: block;
  width: 100%;
  padding: 12px;
  margin-top: 16px;
  font-family: var(--font-body, sans-serif);
  font-size: 15px;
  font-weight: 600;
  background: var(--color-ink, #2C2416);
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.2s;
}

.btn-submit-quiz:hover:not(:disabled) {
  background: var(--color-accent, #8B4513);
}

.btn-submit-quiz:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.quiz-result {
  margin: 16px 0;
  padding: 20px;
  background: white;
  border-radius: 12px;
  border: 2px solid var(--color-border, #E5E0D8);
}

.result-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 12px;
}

.result-header.result-passed {
  border-bottom: 2px solid #4caf50;
}

.result-header.result-failed {
  border-bottom: 2px solid #ff9800;
}

.result-icon {
  font-size: 24px;
}

.result-passed .result-icon {
  color: #4caf50;
}

.result-failed .result-icon {
  color: #ff9800;
}

.result-header h3 {
  margin: 0;
  font-size: 18px;
  font-family: var(--font-display, serif);
}

.result-feedback {
  margin: 10px 0;
  font-size: 15px;
  line-height: 1.6;
  color: var(--color-text, #1A1A1A);
}

.result-stats {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin: 12px 0;
  font-size: 14px;
  color: var(--color-text-muted, #6B6B6B);
}

.mastery-progress-group {
  display: flex;
  align-items: center;
  gap: 8px;
}

.mastery-label {
  font-weight: 600;
  min-width: 48px;
}

.mastery-bar {
  flex: 1;
  height: 14px;
  border: 1px solid var(--color-border, #E5E0D8);
  border-radius: 7px;
  overflow: hidden;
  background: var(--color-surface, white);
}

.mastery-bar::-webkit-progress-bar {
  background: var(--color-surface, white);
  border-radius: 7px;
}

.mastery-bar::-webkit-progress-value {
  background: linear-gradient(90deg, #6c5ce7, #a29bfe);
  border-radius: 7px;
  transition: width 0.4s ease;
}

.mastery-bar::-moz-progress-bar {
  background: linear-gradient(90deg, #6c5ce7, #a29bfe);
  border-radius: 7px;
}

.mastery-pct {
  font-weight: 700;
  min-width: 36px;
  text-align: right;
  color: #6c5ce7;
}

.mastery-status {
  font-size: 14px;
}

.btn-continue-quiz {
  display: block;
  width: 100%;
  padding: 10px 24px;
  font-family: var(--font-body, sans-serif);
  font-size: 14px;
  font-weight: 600;
  background: var(--color-ink, #2C2416);
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.2s;
  margin-top: 12px;
}

.btn-continue-quiz:hover {
  background: var(--color-accent, #8B4513);
}
</style>