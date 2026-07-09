<template>
  <div class="wrongbook-container">
    <div class="page-header">
      <div>
        <h2>错题本</h2>
        <div class="subtitle">错题归档、重练与统计分析</div>
      </div>
    </div>

    <!-- Tab 切换 -->
    <el-tabs v-model="activeTab" class="wb-tabs">
      <el-tab-pane label="错题列表" name="list">
        <div class="tab-toolbar">
          <el-button type="primary" :loading="loading" @click="loadList">刷新</el-button>
          <el-button type="success" :disabled="!wrongList.length" @click="startPractice">开始重练</el-button>
        </div>

        <div v-if="!wrongList.length && !loading" class="empty-state">
          <div class="icon">🎉</div>
          <p>暂无错题，继续加油！</p>
        </div>

        <el-collapse v-else v-model="expandedItems" accordion>
          <el-collapse-item
            v-for="(item, idx) in wrongList"
            :key="item.id"
            :name="item.id"
          >
            <template #title>
              <div class="wrong-item-header">
                <span class="wi-num">{{ idx + 1 }}.</span>
                <span class="wi-stem">{{ item.stem }}</span>
                <el-tag size="small" effect="plain" class="wi-chapter" v-if="item.chapter_title">
                  {{ item.chapter_title }}
                </el-tag>
                <el-tag size="small" effect="plain" :type="item.difficulty === 'hard' ? 'danger' : item.difficulty === 'medium' ? 'warning' : 'success'">
                  {{ item.difficulty === 'hard' ? '难' : item.difficulty === 'medium' ? '中' : '易' }}
                </el-tag>
              </div>
            </template>

            <div class="wrong-item-detail">
              <div class="wid-answer-section">
                <div class="wid-label">正确答案</div>
                <div class="wid-correct">{{ item.answer }}</div>
              </div>
              <div v-if="item.explanation" class="wid-explanation">
                <div class="wid-label">解析</div>
                <div>{{ item.explanation }}</div>
              </div>
              <div class="wid-stats">
                <span>错误 {{ item.wrong_count }} 次</span>
                <span class="dot">·</span>
                <span>重练正确 {{ item.correct_count }} 次</span>
                <span class="dot">·</span>
                <span v-if="item.last_wrong_at">最近错误: {{ formatDate(item.last_wrong_at) }}</span>
              </div>
            </div>
          </el-collapse-item>
        </el-collapse>
      </el-tab-pane>

      <el-tab-pane label="错题重练" name="practice">
        <template v-if="!isPracticing && !wbStore.practiceResult">
          <div class="practice-start">
            <p style="color:var(--color-text-secondary);margin-bottom:16px;">
              当前错题数: <strong>{{ wrongList.length }}</strong>
            </p>
            <div class="form-group" style="margin-bottom:20px;">
              <label>重练题数</label>
              <el-input-number v-model="practiceCount" :min="1" :max="wrongList.length" />
            </div>
            <el-button type="primary" @click="startPractice" :disabled="!wrongList.length">
              开始重练
            </el-button>
          </div>
        </template>

        <template v-if="isPracticing && !wbStore.practiceResult">
          <div class="practice-header">
            <span>重练答题 · {{ practiceQuestions.length }} 题</span>
            <el-button type="primary" @click="handlePracticeSubmit" :loading="wbStore.loading">
              提交
            </el-button>
          </div>

          <div class="practice-questions">
            <div v-for="(q, idx) in practiceQuestions" :key="q.wrongbook_id" class="exam-question-card"
              :class="{ answered: practiceAnswers[q.wrongbook_id] }"
            >
              <div class="eq-header">
                <span class="eq-num">{{ idx + 1 }}.</span>
                <span class="eq-stem">{{ q.stem }}</span>
                <el-tag size="small" effect="plain">{{ q.type === 'single_choice' ? '单选' : '判断' }}</el-tag>
              </div>

              <div v-if="q.type === 'single_choice'" class="eq-options">
                <label
                  v-for="opt in q.options"
                  :key="opt.key"
                  class="option-item"
                  :class="{ selected: practiceAnswers[q.wrongbook_id] === opt.key }"
                >
                  <el-radio
                    :model-value="practiceAnswers[q.wrongbook_id]"
                    :value="opt.key"
                    @change="selectPracticeAnswer(q.wrongbook_id, opt.key)"
                    size="large"
                  >
                    <span class="option-key">{{ opt.key }}.</span>
                    {{ opt.text }}
                  </el-radio>
                </label>
              </div>

              <div v-if="q.type === 'true_false'" class="eq-options">
                <label class="option-item" :class="{ selected: practiceAnswers[q.wrongbook_id] === '对' }">
                  <el-radio :model-value="practiceAnswers[q.wrongbook_id]" value="对" @change="selectPracticeAnswer(q.wrongbook_id, '对')" size="large">对</el-radio>
                </label>
                <label class="option-item" :class="{ selected: practiceAnswers[q.wrongbook_id] === '错' }">
                  <el-radio :model-value="practiceAnswers[q.wrongbook_id]" value="错" @change="selectPracticeAnswer(q.wrongbook_id, '错')" size="large">错</el-radio>
                </label>
              </div>
            </div>
          </div>
        </template>

        <template v-if="wbStore.practiceResult">
          <div class="practice-result">
            <div class="pr-score">
              <span class="pr-num" :class="wbStore.practiceResult.score >= 80 ? 'score-high' : wbStore.practiceResult.score >= 60 ? 'score-mid' : 'score-low'">
                {{ wbStore.practiceResult.score }}
              </span>
              <span class="pr-label">分</span>
            </div>
            <div class="pr-detail">
              正确 <strong>{{ wbStore.practiceResult.correct }}</strong> / {{ wbStore.practiceResult.total }} 题
            </div>
            <el-button @click="finishPractice">返回</el-button>
          </div>
        </template>
      </el-tab-pane>

      <el-tab-pane label="统计" name="stats">
        <div v-if="wbStore.stats" class="stats-grid">
          <div class="stat-card">
            <div class="stat-value">{{ wbStore.stats.total_wrong_questions }}</div>
            <div class="stat-label">错题总数</div>
          </div>
          <div class="stat-card warning">
            <div class="stat-value">{{ wbStore.stats.total_wrong_times }}</div>
            <div class="stat-label">累计错误次数</div>
          </div>
          <div class="stat-card success">
            <div class="stat-value">{{ wbStore.stats.total_correct_times }}</div>
            <div class="stat-label">重练正确次数</div>
          </div>
          <div class="stat-card">
            <div class="stat-value">{{ wbStore.stats.correct_rate }}%</div>
            <div class="stat-label">重练正确率</div>
          </div>
        </div>

        <div v-if="wbStore.stats?.by_chapter.length" class="chapter-stats">
          <div class="section-title">章节分布</div>
          <div v-for="ch in wbStore.stats.by_chapter" :key="ch.chapter_id" class="cs-row">
            <span class="cs-name">{{ ch.chapter_title }}</span>
            <el-tag size="small" effect="plain">{{ ch.count }} 题</el-tag>
          </div>
        </div>

        <div v-if="!wbStore.stats" class="empty-state">
          <div class="icon">📊</div>
          <p>暂无统计数据</p>
        </div>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { useWrongBookStore } from '@/stores/wrongbook'
import type { PracticeQuestion } from '@/api/wrongbook'

const wbStore = useWrongBookStore()

const activeTab = ref('list')
const loading = ref(false)
const expandedItems = ref<number[]>([])
const isPracticing = ref(false)
const practiceCount = ref(5)
const practiceQuestions = ref<PracticeQuestion[]>([])
const practiceAnswers = reactive<Record<number, string>>({})

const wrongList = computed(() => wbStore.wrongQuestions)

function selectPracticeAnswer(wid: number, answer: string) {
  practiceAnswers[wid] = answer
}

async function loadList() {
  loading.value = true
  try {
    await wbStore.fetchWrongQuestions()
    await wbStore.fetchStats()
  } finally {
    loading.value = false
  }
}

async function startPractice() {
  if (!wrongList.value.length) {
    ElMessage.warning('暂无错题可练习')
    return
  }
  activeTab.value = 'practice'
  practiceAnswersClean()
  wbStore.clearResult()
  try {
    practiceQuestions.value = await wbStore.fetchPracticeQuestions(practiceCount.value)
    isPracticing.value = true
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '获取重练题目失败')
  }
}

function finishPractice() {
  isPracticing.value = false
  practiceAnswersClean()
  wbStore.clearResult()
  activeTab.value = 'list'
  loadList()
}

function practiceAnswersClean() {
  Object.keys(practiceAnswers).forEach(k => delete practiceAnswers[Number(k)])
}

async function handlePracticeSubmit() {
  const answers = practiceQuestions.value.map(q => ({
    wrongbook_id: q.wrongbook_id,
    user_answer: practiceAnswers[q.wrongbook_id] || '',
  }))
  try {
    await wbStore.submitPractice(answers)
    isPracticing.value = false
    ElMessage.success(`重练完成，得分 ${wbStore.practiceResult?.score}`)
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '提交失败')
  }
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

onMounted(() => {
  loadList()
})
</script>

<style scoped>
.wrongbook-container {
  max-width: 900px;
}

.wb-tabs {
  margin-top: 8px;
}

.tab-toolbar {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
}

/* 错题列表 */
.wrong-item-header {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  overflow: hidden;
}

.wi-num {
  font-weight: 600;
  color: var(--color-text-secondary);
  min-width: 24px;
}

.wi-stem {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 13px;
}

.wi-chapter {
  flex-shrink: 0;
}

/* 详情 */
.wrong-item-detail {
  padding: 8px 16px 16px;
}

.wid-answer-section, .wid-explanation {
  margin-bottom: 12px;
}

.wid-label {
  font-size: 11px;
  font-weight: 600;
  color: var(--color-text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 4px;
}

.wid-correct {
  font-size: 16px;
  font-weight: 600;
  color: #22c55e;
}

.wid-explanation {
  background: #f8fafc;
  padding: 12px;
  border-radius: var(--radius-sm);
  font-size: 13px;
  color: var(--color-text-secondary);
  line-height: 1.7;
}

.wid-stats {
  font-size: 12px;
  color: var(--color-text-secondary);
  margin-top: 8px;
}

.wid-stats .dot {
  margin: 0 8px;
}

/* 重练 */
.practice-start {
  text-align: center;
  padding: 40px 0;
}

.practice-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  margin-bottom: 16px;
  font-size: 14px;
  color: var(--color-text-secondary);
}

.practice-questions {
  display: flex;
  flex-direction: column;
  gap: 16px;
  margin-bottom: 20px;
}

.practice-result {
  text-align: center;
  padding: 60px 0;
}

.pr-score {
  margin-bottom: 12px;
}

.pr-num {
  font-size: 56px;
  font-weight: 800;
}

.pr-num.score-high { color: #22c55e; }
.pr-num.score-mid { color: #f59e0b; }
.pr-num.score-low { color: #ef4444; }

.pr-label {
  font-size: 20px;
  color: var(--color-text-secondary);
  margin-left: 4px;
}

.pr-detail {
  font-size: 14px;
  color: var(--color-text-secondary);
  margin-bottom: 20px;
}

.pr-detail strong {
  font-size: 22px;
  color: var(--color-text-heading);
}

/* 统计 */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

.stat-card {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: 20px;
  text-align: center;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: var(--color-text-heading);
}

.stat-card.success .stat-value { color: var(--color-success); }
.stat-card.warning .stat-value { color: var(--color-warning); }

.stat-label {
  font-size: 12px;
  color: var(--color-text-secondary);
  margin-top: 4px;
}

.section-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text-heading);
  margin-bottom: 12px;
}

.chapter-stats {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: 20px;
}

.cs-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 0;
  border-bottom: 1px solid #f1f5f9;
  font-size: 13px;
}

.cs-row:last-child {
  border-bottom: none;
}

.cs-name {
  color: var(--color-text-heading);
  font-weight: 500;
}

/* 复用 quiz 组件的一些样式 */
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

@media (max-width: 768px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
