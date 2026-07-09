<template>
  <div class="quiz-container">
    <div class="page-header">
      <div>
        <h2>在线测验</h2>
        <div class="subtitle">选择章节，生成题目开始测验</div>
      </div>
    </div>

    <!-- 步骤 1: 选择章节 & 生成题目 -->
    <div class="setup-card">
      <div class="setup-row">
        <div class="form-group">
          <label>选择章节</label>
          <el-select v-model="selectedChapterId" placeholder="请选择要测验的章节" class="chapter-select" :disabled="isExamMode">
            <el-option-group
              v-for="ch in courseStore.outlineTree"
              :key="ch.id"
              :label="ch.title"
            >
              <el-option
                v-for="sec in ch.children"
                :key="sec.id"
                :label="`${sec.title}`"
                :value="sec.id"
              />
            </el-option-group>
          </el-select>
        </div>
        <div class="form-group">
          <label>题目数量</label>
          <el-input-number v-model="questionCount" :min="1" :max="20" :disabled="isExamMode" />
        </div>
        <div class="form-group">
          <label>难度</label>
          <el-select v-model="difficulty" class="diff-select" :disabled="isExamMode">
            <el-option label="简单" value="easy" />
            <el-option label="中等" value="medium" />
            <el-option label="困难" value="hard" />
            <el-option label="混合" value="mixed" />
          </el-select>
        </div>
        <div class="form-group">
          <label>时间限制</label>
          <el-select v-model="timeLimit" class="time-select" :disabled="isExamMode">
            <el-option label="不限时" :value="0" />
            <el-option label="5 分钟" :value="300" />
            <el-option label="10 分钟" :value="600" />
            <el-option label="15 分钟" :value="900" />
            <el-option label="30 分钟" :value="1800" />
          </el-select>
        </div>
        <div class="form-group action-group">
          <label>&nbsp;</label>
          <el-button
            v-if="!isExamMode"
            type="primary"
            :loading="quizStore.generating"
            :disabled="!selectedChapterId"
            @click="handleGenerate"
          >
            <el-icon style="margin-right:4px"><MagicStick /></el-icon>
            生成题目
          </el-button>
          <el-button
            v-if="!isExamMode && questions.length > 0"
            type="success"
            @click="startExam"
          >
            开始考试
          </el-button>
          <el-button v-if="isExamMode" type="warning" @click="cancelExam">
            退出考试
          </el-button>
        </div>
      </div>
    </div>

    <!-- 已有题目预览（未进入考试模式） -->
    <template v-if="!isExamMode && questions.length > 0 && !quizStore.result">
      <div class="questions-preview">
        <div class="section-title">
          已生成题目（{{ questions.length }} 题）
          <el-button size="small" text type="danger" @click="clearQuestions" style="margin-left:12px">
            清除
          </el-button>
        </div>
        <div v-for="(q, idx) in questions" :key="q.id" class="q-preview-item">
          <span class="q-num">{{ idx + 1 }}.</span>
          <span class="q-stem">{{ q.stem }}</span>
          <el-tag size="small" effect="plain" :type="q.type === 'single_choice' ? '' : 'info'">
            {{ q.type === 'single_choice' ? '单选' : '判断' }}
          </el-tag>
          <el-tag size="small" effect="plain" :type="q.difficulty === 'easy' ? 'success' : q.difficulty === 'hard' ? 'danger' : 'warning'">
            {{ q.difficulty === 'easy' ? '简单' : q.difficulty === 'hard' ? '困难' : '中等' }}
          </el-tag>
        </div>
      </div>
    </template>

    <!-- 步骤 2: 考试模式 - 答题 -->
    <template v-if="isExamMode && !quizStore.result">
      <div class="exam-header">
        <div class="exam-info">
          共 {{ questions.length }} 题 · 已答 {{ answeredCount }} 题
        </div>
        <div v-if="timeLimit > 0" class="exam-timer" :class="{ 'timer-warning': remainingTime <= 60 }">
          ⏱ {{ formatTime(remainingTime) }}
        </div>
        <el-button type="primary" size="default" @click="handleSubmit" :loading="quizStore.loading">
          提交答卷
        </el-button>
      </div>

      <div class="exam-questions">
        <div v-for="(q, idx) in questions" :key="q.id" class="exam-question-card" :class="{ answered: userAnswers[q.id] }">
          <div class="eq-header">
            <span class="eq-num">{{ idx + 1 }}.</span>
            <span class="eq-stem">{{ q.stem }}</span>
            <el-tag size="small" effect="plain">{{ q.type === 'single_choice' ? '单选' : '判断' }}</el-tag>
          </div>

          <!-- 单选题 -->
          <div v-if="q.type === 'single_choice'" class="eq-options">
            <label
              v-for="opt in q.options"
              :key="opt.key"
              class="option-item"
              :class="{ selected: userAnswers[q.id] === opt.key }"
            >
              <el-radio
                :model-value="userAnswers[q.id]"
                :value="opt.key"
                @change="selectAnswer(q.id, opt.key)"
                size="large"
              >
                <span class="option-key">{{ opt.key }}.</span>
                {{ opt.text }}
              </el-radio>
            </label>
          </div>

          <!-- 判断题 -->
          <div v-if="q.type === 'true_false'" class="eq-options">
            <label class="option-item" :class="{ selected: userAnswers[q.id] === '对' }">
              <el-radio :model-value="userAnswers[q.id]" value="对" @change="selectAnswer(q.id, '对')" size="large">
                对
              </el-radio>
            </label>
            <label class="option-item" :class="{ selected: userAnswers[q.id] === '错' }">
              <el-radio :model-value="userAnswers[q.id]" value="错" @change="selectAnswer(q.id, '错')" size="large">
                错
              </el-radio>
            </label>
          </div>
        </div>
      </div>

      <div class="exam-footer">
        <el-button type="primary" size="default" @click="handleSubmit" :loading="quizStore.loading">
          提交答卷
        </el-button>
      </div>
    </template>

    <!-- 步骤 3: 考试结果 -->
    <template v-if="quizStore.result">
      <div class="result-card">
        <div class="result-header">
          <div class="result-score-box">
            <div class="score-number" :class="scoreColor">{{ quizStore.result.score }}</div>
            <div class="score-label">得分</div>
          </div>
          <div class="result-summary">
            <div class="summary-item">
              正确: <strong>{{ correctCount }}</strong> / {{ quizStore.result.details.length }}
            </div>
            <div class="summary-item" v-if="quizStore.result.time_used">
              用时: {{ formatTime(quizStore.result.time_used) }}
              <template v-if="quizStore.result.time_limit">
                / {{ formatTime(quizStore.result.time_limit) }}
              </template>
            </div>
          </div>
          <div class="result-actions">
            <el-button @click="cancelExam">返回章节列表</el-button>
            <el-button type="primary" @click="viewHistory">查看历史</el-button>
          </div>
        </div>

        <!-- 逐题解析 -->
        <div class="result-detail-list">
          <div
            v-for="(d, idx) in quizStore.result.details"
            :key="d.question_id"
            class="result-detail-item"
            :class="{ correct: d.is_correct, wrong: !d.is_correct }"
          >
            <div class="rd-header">
              <span class="rd-num">{{ idx + 1 }}.</span>
              <span class="rd-stem">{{ d.stem }}</span>
              <el-tag :type="d.is_correct ? 'success' : 'danger'" size="small" effect="plain">
                {{ d.is_correct ? '正确' : '错误' }}
              </el-tag>
            </div>

            <div class="rd-options">
              <div v-for="opt in d.options" :key="opt.key" class="rd-option"
                :class="{
                  'correct-answer': opt.key === d.correct_answer,
                  'wrong-answer': opt.key === d.user_answer && !d.is_correct,
                }"
              >
                <span class="option-badge">{{ opt.key }}</span>
                {{ opt.text }}
                <span v-if="opt.key === d.correct_answer" class="answer-mark correct-mark">✓</span>
                <span v-if="opt.key === d.user_answer && !d.is_correct" class="answer-mark wrong-mark">✗</span>
              </div>
            </div>

            <div v-if="d.explanation" class="rd-explanation">
              <strong>解析：</strong>{{ d.explanation }}
            </div>
          </div>
        </div>
      </div>
    </template>

    <!-- 步骤 4: 考试历史 -->
    <template v-if="!isExamMode && !quizStore.result && showHistory">
      <div class="history-card" v-loading="historyLoading">
        <div class="section-title">
          考试历史
          <el-button size="small" text @click="showHistory = false" style="margin-left:12px">收起</el-button>
        </div>

        <div v-if="!historyList.length" class="empty-state">
          <div class="icon">📝</div>
          <p>暂无考试记录</p>
        </div>

        <div v-else class="history-table">
          <div class="ht-row ht-header">
            <span class="ht-chapter">章节</span>
            <span class="ht-score">得分</span>
            <span class="ht-time">用时</span>
            <span class="ht-date">时间</span>
            <span class="ht-action">操作</span>
          </div>
          <div
            v-for="h in historyList"
            :key="h.id"
            class="ht-row"
            @click="viewExamDetail(h.id)"
            style="cursor:pointer"
          >
            <span class="ht-chapter">{{ h.chapter_title || `章节 #${h.chapter_id}` }}</span>
            <span class="ht-score">
              <strong :style="{ color: h.score >= 80 ? '#22c55e' : h.score >= 60 ? '#f59e0b' : '#ef4444' }">
                {{ h.score }}
              </strong>
              / {{ h.total_score }}
            </span>
            <span class="ht-time">{{ h.time_used ? formatTime(h.time_used) : '-' }}{{ h.time_limit ? ' / ' + formatTime(h.time_limit) : '' }}</span>
            <span class="ht-date">{{ formatDate(h.created_at) }}</span>
            <span class="ht-action">
              <el-button size="small" text type="primary">查看</el-button>
            </span>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onActivated, reactive } from 'vue'
import { MagicStick } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useQuizStore } from '@/stores/quiz'
import { useCourseStore } from '@/stores/course'
import type { QuestionOut, ExamHistory } from '@/api/quiz'

const quizStore = useQuizStore()
const courseStore = useCourseStore()

const selectedChapterId = ref<number | null>(null)
const questionCount = ref(5)
const difficulty = ref('medium')
const timeLimit = ref(0)
const isExamMode = ref(false)
const userAnswers = reactive<Record<number, string>>({})
const showHistory = ref(false)
const historyList = ref<ExamHistory[]>([])
const historyLoading = ref(false)
const remainingTime = ref(0)
let timerInterval: ReturnType<typeof setInterval> | null = null

const questions = computed(() => quizStore.questions)

const answeredCount = computed(() => Object.keys(userAnswers).length)

const correctCount = computed(() => {
  if (!quizStore.result) return 0
  return quizStore.result.details.filter(d => d.is_correct).length
})

const scoreColor = computed(() => {
  if (!quizStore.result) return ''
  const s = quizStore.result.score
  if (s >= 80) return 'score-high'
  if (s >= 60) return 'score-mid'
  return 'score-low'
})

function selectAnswer(qid: number, answer: string) {
  userAnswers[qid] = answer
}

async function handleGenerate() {
  if (!selectedChapterId.value) return
  userAnswersClean()
  quizStore.clearResult()
  try {
    await quizStore.generate(selectedChapterId.value, questionCount.value, difficulty.value)
    ElMessage.success(`成功生成 ${quizStore.questions.length} 道题目`)
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '生成题目失败')
  }
}

function startExam() {
  isExamMode.value = true
  userAnswersClean()
  quizStore.clearResult()
  // 初始化倒计时
  if (timeLimit.value > 0) {
    remainingTime.value = timeLimit.value
    timerInterval = setInterval(() => {
      remainingTime.value--
      if (remainingTime.value <= 0) {
        clearInterval(timerInterval!)
        timerInterval = null
        ElMessage.warning('答题时间已到，自动提交')
        handleSubmit()
      }
    }, 1000)
  }
}

function cancelExam() {
  isExamMode.value = false
  userAnswersClean()
  quizStore.clearResult()
  clearTimer()
}

function clearTimer() {
  if (timerInterval) {
    clearInterval(timerInterval)
    timerInterval = null
  }
}

function clearQuestions() {
  quizStore.questions = [] as any
  userAnswersClean()
}

function userAnswersClean() {
  Object.keys(userAnswers).forEach(k => delete userAnswers[Number(k)])
}

async function handleSubmit() {
  if (!selectedChapterId.value || !questions.value.length) return
  clearTimer()
  const qids = questions.value.map(q => q.id)
  const answers = qids.map(id => ({
    question_id: id,
    user_answer: userAnswers[id] || '',
  }))

  // 计算实际用时
  const used = timeLimit.value > 0 ? timeLimit.value - remainingTime.value : undefined

  try {
    await quizStore.submit(selectedChapterId.value, qids, answers, timeLimit.value, used)
    isExamMode.value = false
    ElMessage.success(`考试完成，得分 ${quizStore.result?.score}`)
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '提交失败')
  }
}

async function viewHistory() {
  showHistory.value = true
  historyLoading.value = true
  try {
    historyList.value = await quizStore.fetchExams()
  } finally {
    historyLoading.value = false
  }
}

async function viewExamDetail(examId: number) {
  try {
    await quizStore.fetchExamDetail(examId)
  } catch (e: any) {
    ElMessage.error('加载考试详情失败')
  }
}

function formatTime(seconds: number) {
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  return m > 0 ? `${m}分${s}秒` : `${s}秒`
}

function formatDate(dateStr: string) {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

onActivated(async () => {
  if (!courseStore.outlineTree.length) {
    await courseStore.fetchOutline()
  }
})
</script>

<style scoped>
.quiz-container {
  max-width: 900px;
}

/* 设置区 */
.setup-card {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: 20px;
  margin-bottom: 20px;
}

.setup-row {
  display: flex;
  gap: 16px;
  align-items: flex-end;
  flex-wrap: wrap;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.form-group label {
  font-size: 12px;
  font-weight: 600;
  color: var(--color-text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.chapter-select {
  width: 220px;
}

.diff-select {
  width: 100px;
}

.time-select {
  width: 120px;
}

.action-group {
  margin-left: auto;
}

/* 题目预览 */
.questions-preview {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: 20px;
  margin-bottom: 20px;
}

.section-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text-heading);
  margin-bottom: 16px;
}

.q-preview-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  border-radius: var(--radius-sm);
  font-size: 13px;
}

.q-preview-item:hover {
  background: #f8fafc;
}

.q-num {
  font-weight: 600;
  color: var(--color-text-secondary);
  min-width: 24px;
}

.q-stem {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* 考试区 */
.exam-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  margin-bottom: 16px;
  position: sticky;
  top: 12px;
  z-index: 10;
}

.exam-info {
  font-size: 14px;
  color: var(--color-text-secondary);
}

.exam-timer {
  font-size: 20px;
  font-weight: 700;
  color: var(--color-primary);
  font-variant-numeric: tabular-nums;
}

.exam-timer.timer-warning {
  color: #ef4444;
  animation: pulse 1s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.exam-questions {
  display: flex;
  flex-direction: column;
  gap: 16px;
  margin-bottom: 20px;
}

.exam-question-card {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: 20px;
  transition: border-color 0.2s;
}

.exam-question-card.answered {
  border-color: #93c5fd;
}

.eq-header {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  margin-bottom: 16px;
}

.eq-num {
  font-weight: 700;
  color: var(--color-primary);
  min-width: 24px;
  font-size: 15px;
}

.eq-stem {
  flex: 1;
  font-size: 15px;
  font-weight: 500;
  color: var(--color-text-heading);
  line-height: 1.6;
}

.eq-options {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding-left: 32px;
}

.option-item {
  padding: 10px 14px;
  border-radius: var(--radius-sm);
  border: 1px solid #e8eaed;
  cursor: pointer;
  transition: all 0.15s;
}

.option-item:hover {
  border-color: #93c5fd;
  background: #f0f7ff;
}

.option-item.selected {
  border-color: var(--color-primary);
  background: #eff6ff;
}

.option-key {
  font-weight: 700;
  margin-right: 4px;
  color: var(--color-text-secondary);
}

.exam-footer {
  display: flex;
  justify-content: center;
  padding: 20px 0;
}

/* 结果区 */
.result-card {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  margin-bottom: 20px;
}

.result-header {
  display: flex;
  align-items: center;
  gap: 24px;
  padding: 24px;
  border-bottom: 1px solid var(--color-border);
  flex-wrap: wrap;
}

.result-score-box {
  text-align: center;
  min-width: 80px;
}

.score-number {
  font-size: 48px;
  font-weight: 800;
  line-height: 1;
}

.score-number.score-high { color: #22c55e; }
.score-number.score-mid { color: #f59e0b; }
.score-number.score-low { color: #ef4444; }

.score-label {
  font-size: 12px;
  color: var(--color-text-secondary);
  margin-top: 4px;
}

.result-summary {
  flex: 1;
}

.summary-item {
  font-size: 13px;
  color: var(--color-text-secondary);
  margin-bottom: 4px;
}

.summary-item strong {
  font-size: 18px;
  color: var(--color-text-heading);
}

.result-actions {
  display: flex;
  gap: 8px;
}

/* 逐题解析 */
.result-detail-list {
  padding: 0 20px 20px;
}

.result-detail-item {
  padding: 16px 0;
  border-bottom: 1px solid #f1f5f9;
}

.result-detail-item:last-child {
  border-bottom: none;
}

.rd-header {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  margin-bottom: 12px;
}

.rd-num {
  font-weight: 700;
  color: var(--color-text-secondary);
  min-width: 24px;
}

.rd-stem {
  flex: 1;
  font-size: 14px;
  font-weight: 500;
  color: var(--color-text-heading);
}

.rd-options {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding-left: 32px;
}

.rd-option {
  padding: 8px 12px;
  border-radius: var(--radius-sm);
  font-size: 13px;
  border: 1px solid transparent;
  display: flex;
  align-items: center;
  gap: 6px;
}

.rd-option.correct-answer {
  background: #f0fdf4;
  border-color: #bbf7d0;
}

.rd-option.wrong-answer {
  background: #fef2f2;
  border-color: #fecaca;
}

.option-badge {
  font-weight: 700;
  color: var(--color-text-secondary);
  min-width: 20px;
}

.answer-mark {
  margin-left: auto;
  font-weight: 700;
  font-size: 16px;
}

.correct-mark { color: #22c55e; }
.wrong-mark { color: #ef4444; }

.rd-explanation {
  margin-top: 10px;
  padding: 10px 12px;
  background: #f8fafc;
  border-radius: var(--radius-sm);
  font-size: 13px;
  color: var(--color-text-secondary);
  line-height: 1.7;
  margin-left: 32px;
}

.rd-explanation strong {
  color: var(--color-text-heading);
}

/* 历史 */
.history-card {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: 20px;
}

.history-table {
  font-size: 13px;
}

.ht-row {
  display: flex;
  align-items: center;
  padding: 12px 12px;
  border-radius: var(--radius-sm);
  transition: background 0.15s;
}

.ht-row:hover {
  background: #f8fafc;
}

.ht-row.ht-header {
  font-size: 11px;
  font-weight: 700;
  color: var(--color-text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  border-bottom: 1px solid var(--color-border);
  margin-bottom: 4px;
}

.ht-chapter { flex: 1; }
.ht-score { width: 100px; }
.ht-time { width: 80px; }
.ht-date { width: 100px; }
.ht-action { width: 60px; text-align: right; }
</style>
