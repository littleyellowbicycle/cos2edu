<template>
  <div class="exam-page">
    <div v-if="loading" class="exam-loading">
      <el-icon class="is-loading" :size="48"><Loading /></el-icon>
      <p>正在生成考核题目...</p>
    </div>

    <div v-else-if="!quiz && !result" class="exam-intro">
      <div class="intro-card">
        <h2>知识点考核</h2>
        <p class="intro-desc">考核你对当前知识点的掌握程度。</p>
        <p class="intro-point" v-if="narrative.progress.currentPointName">
          知识点: <strong>{{ narrative.progress.currentPointName }}</strong>
        </p>
        <el-button type="primary" size="large" @click="requestQuiz" :disabled="!narrative.progress.currentPoint">
          开始考核
        </el-button>
        <p class="intro-hint" v-if="!narrative.progress.currentPoint">没有正在学习的知识点，请先开始对话学习。</p>
      </div>
    </div>

    <div v-else-if="quiz && !result" class="exam-questions">
      <div class="quiz-header">
        <h2>{{ quiz.knowledge_point_name }}</h2>
        <el-progress
          :percentage="progressPercentage"
          :stroke-width="8"
          :format="() => `${currentIndex + 1} / ${quiz.questions.length}`"
        />
      </div>

      <div class="question-card" v-if="currentQuestion">
        <div class="question-number">第 {{ currentIndex + 1 }} 题</div>
        <h3 class="question-text">{{ currentQuestion.question_text }}</h3>
        <el-radio-group v-model="selectedAnswer" class="options-group">
          <el-radio
            v-for="(option, i) in currentQuestion.options"
            :key="i"
            :value="i"
            class="option-item"
          >
            {{ option }}
          </el-radio>
        </el-radio-group>
      </div>

      <div class="quiz-actions">
        <el-button @click="goBack">返回</el-button>
        <el-button type="primary" @click="nextQuestion" :disabled="selectedAnswer === null">
          {{ isLastQuestion ? '提交答案' : '下一题' }}
        </el-button>
      </div>
    </div>

    <div v-else-if="result" class="exam-results">
      <el-result
        :icon="result.passed ? 'success' : 'warning'"
        :title="result.passed ? '考核通过' : '未通过考核'"
        :sub-title="result.feedback"
      >
        <template #extra>
          <div class="result-details">
            <div class="mastery-bar">
              <span class="mastery-label">掌握度</span>
              <el-progress
                :percentage="Math.round(result.mastery_level * 100)"
                :stroke-width="20"
                :color="masteryColor"
                :text-inside="true"
              />
            </div>
            <p class="result-score">
              正确 {{ result.correct_count }} / {{ result.total_questions }} 题
            </p>
            <div class="result-actions">
              <el-button v-if="!result.passed" type="warning" @click="retryQuiz">重新考核</el-button>
              <el-button type="primary" @click="goToScene">继续学习</el-button>
              <el-button @click="goToChat">返回对话</el-button>
            </div>
          </div>
        </template>
      </el-result>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { Loading } from '@element-plus/icons-vue'
import { useNarrativeStore } from '@/stores/narrative'
import { useWebSocket } from '@/composables/useWebSocket'

const narrative = useNarrativeStore()
const ws = useWebSocket()
const router = useRouter()

const loading = ref(false)
const quiz = ref(null)
const result = ref(null)
const currentIndex = ref(0)
const selectedAnswer = ref(null)
const answers = ref([])

const currentQuestion = computed(() => {
  if (!quiz.value || !quiz.value.questions) return null
  return quiz.value.questions[currentIndex.value]
})

const isLastQuestion = computed(() => {
  if (!quiz.value || !quiz.value.questions) return true
  return currentIndex.value >= quiz.value.questions.length - 1
})

const progressPercentage = computed(() => {
  if (!quiz.value || !quiz.value.questions) return 0
  return Math.round(((currentIndex.value + 1) / quiz.value.questions.length) * 100)
})

const masteryColor = computed(() => {
  if (!result.value) return '#409eff'
  const level = result.value.mastery_level
  if (level >= 0.8) return '#67c23a'
  if (level >= 0.6) return '#e6a23c'
  return '#f56c6c'
})

function requestQuiz() {
  loading.value = true
  ws.startAssessment(narrative.progress.currentPoint)
}

function nextQuestion() {
  if (selectedAnswer.value === null) return

  answers.value.push(selectedAnswer.value)

  if (isLastQuestion.value) {
    loading.value = true
    ws.submitAssessmentAnswer(
      quiz.value.knowledge_point_id,
      answers.value,
    )
  } else {
    currentIndex.value++
    selectedAnswer.value = null
  }
}

function retryQuiz() {
  result.value = null
  quiz.value = null
  answers.value = []
  currentIndex.value = 0
  selectedAnswer.value = null
  requestQuiz()
}

function goToScene() {
  router.push('/scene')
}

function goToChat() {
  router.push('/conversations')
}

function goBack() {
  router.back()
}

function onQuizMessage(msg) {
  loading.value = false
  quiz.value = msg.payload
  answers.value = []
  currentIndex.value = 0
  selectedAnswer.value = null
  narrative.setQuiz(msg.payload)
}

function onResultMessage(msg) {
  loading.value = false
  result.value = msg.payload
  narrative.setAssessmentResult(msg.payload)
}

function onErrorMessage(msg) {
  loading.value = false
  console.error('Assessment error:', msg.content)
}

onMounted(() => {
  ws.on('assessment.quiz', onQuizMessage)
  ws.on('assessment.result', onResultMessage)
  ws.on('error', onErrorMessage)
})

onUnmounted(() => {
  ws.off('assessment.quiz', onQuizMessage)
  ws.off('assessment.result', onResultMessage)
  ws.off('error', onErrorMessage)
})
</script>

<style scoped>
.exam-page {
  max-width: 700px;
  margin: 0 auto;
  padding: 24px;
  min-height: 80vh;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.exam-loading {
  text-align: center;
  padding: 60px 0;
  color: var(--color-text-muted);
}

.intro-card {
  text-align: center;
  padding: 48px 32px;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 12px;
}

.intro-card h2 {
  font-size: 28px;
  font-weight: 600;
  color: var(--color-ink);
  margin-bottom: 12px;
}

.intro-desc {
  color: var(--color-text-muted);
  margin-bottom: 24px;
}

.intro-point {
  color: var(--color-ink);
  margin-bottom: 24px;
}

.intro-hint {
  color: var(--color-text-muted);
  font-size: 13px;
  margin-top: 12px;
}

.quiz-header {
  margin-bottom: 24px;
}

.quiz-header h2 {
  font-size: 22px;
  font-weight: 600;
  color: var(--color-ink);
  margin-bottom: 12px;
}

.question-card {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 8px;
  padding: 24px;
  margin-bottom: 24px;
}

.question-number {
  font-size: 12px;
  color: var(--color-accent);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 12px;
}

.question-text {
  font-size: 18px;
  font-weight: 500;
  color: var(--color-ink);
  margin-bottom: 20px;
  line-height: 1.6;
}

.options-group {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.option-item {
  padding: 12px 16px;
  border: 1px solid var(--color-border);
  border-radius: 6px;
  transition: all 0.2s;
  margin: 0;
}

.option-item:hover {
  border-color: var(--color-accent-light);
}

.quiz-actions {
  display: flex;
  justify-content: space-between;
}

.exam-results {
  padding: 24px;
}

.result-details {
  margin-top: 16px;
}

.mastery-bar {
  margin-bottom: 16px;
}

.mastery-label {
  display: block;
  font-size: 14px;
  color: var(--color-text-muted);
  margin-bottom: 8px;
}

.result-score {
  font-size: 16px;
  color: var(--color-ink);
  margin-bottom: 24px;
}

.result-actions {
  display: flex;
  gap: 12px;
  justify-content: center;
}

@media (max-width: 768px) {
  .exam-page {
    padding: 16px;
  }

  .intro-card {
    padding: 32px 20px;
  }

  .question-card {
    padding: 16px;
  }
}
</style>