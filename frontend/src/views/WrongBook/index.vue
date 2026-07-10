<template>
  <div class="wrongbook-page">
    <!-- 顶部介绍 -->
    <div class="wb-hero">
      <div class="wb-hero-left">
        <h2 class="wb-title">错题本</h2>
        <p class="wb-desc">记录每次测验的错题，针对性重练，告别一错再错</p>
      </div>
      <div class="wb-hero-right">
        <div class="quick-stat" v-if="wbStore.stats">
          <span class="qs-num">{{ wbStore.stats.total_wrong_questions }}</span>
          <span class="qs-label">错题总数</span>
        </div>
        <div class="quick-stat" v-if="wbStore.stats">
          <span class="qs-num" :class="wbStore.stats.correct_rate >= 60 ? 'green' : 'red'">
            {{ wbStore.stats.correct_rate }}%
          </span>
          <span class="qs-label">重练正确率</span>
        </div>
      </div>
    </div>

    <!-- Tab 导航 -->
    <div class="wb-nav">
      <button
        v-for="tab in tabs"
        :key="tab.key"
        class="wb-nav-btn"
        :class="{ active: activeTab === tab.key }"
        @click="switchTab(tab.key)"
      >
        <span class="wb-nav-icon">{{ tab.icon }}</span>
        <span>{{ tab.label }}</span>
        <span v-if="tab.key === 'list' && wbStore.wrongQuestions.length" class="wb-nav-badge">
          {{ wbStore.wrongQuestions.length }}
        </span>
      </button>
    </div>

    <!-- Tab: 错题列表 -->
    <div v-show="activeTab === 'list'" class="wb-content">
      <!-- 工具栏 -->
      <div class="wb-toolbar">
        <el-select
          v-model="filterChapterId"
          placeholder="全部章节"
          clearable
          size="default"
          class="chapter-filter"
          @change="onChapterFilter"
        >
          <el-option
            v-for="ch in chapterOptions"
            :key="ch.id"
            :label="ch.title"
            :value="ch.id"
          />
        </el-select>
        <div class="toolbar-spacer" />
        <el-button text @click="refreshList" :loading="wbStore.loading">
          <svg viewBox="0 0 24 24" width="14" height="14" fill="none" style="margin-right:4px;vertical-align:middle">
            <path d="M21 12a9 9 0 11-2.64-6.36" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M21 3v6h-6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          刷新
        </el-button>
        <el-button
          type="primary"
          :disabled="!wbStore.wrongQuestions.length"
          @click="goPractice"
        >
          进入重练
        </el-button>
      </div>

      <!-- 加载中 -->
      <div v-if="wbStore.loading && !wbStore.wrongQuestions.length" class="wb-skeleton">
        <div v-for="i in 3" :key="i" class="skeleton-row">
          <div class="skeleton-line w-60" />
          <div class="skeleton-line w-80" />
          <div class="skeleton-line w-40" />
        </div>
      </div>

      <!-- 空状态 -->
      <div v-else-if="!wbStore.wrongQuestions.length" class="wb-empty">
        <div class="wb-empty-icon">
          <svg viewBox="0 0 80 80" fill="none" width="80" height="80">
            <rect x="20" y="10" width="40" height="55" rx="4" stroke="#cbd5e1" stroke-width="2" fill="#f8fafc"/>
            <line x1="28" y1="22" x2="52" y2="22" stroke="#e2e8f0" stroke-width="2" stroke-linecap="round"/>
            <line x1="28" y1="30" x2="48" y2="30" stroke="#e2e8f0" stroke-width="2" stroke-linecap="round"/>
            <line x1="28" y1="38" x2="44" y2="38" stroke="#e2e8f0" stroke-width="2" stroke-linecap="round"/>
            <circle cx="58" cy="54" r="16" fill="#dbeafe" stroke="#93c5fd" stroke-width="2"/>
            <path d="M53 54h10M58 49v10" stroke="#3b82f6" stroke-width="2.5" stroke-linecap="round"/>
          </svg>
        </div>
        <h3>暂无错题</h3>
        <p>去完成一次测验，错题会自动收录到这里</p>
        <el-button type="primary" @click="$router.push('/quiz')">前往测验</el-button>
      </div>

      <!-- 错题列表 -->
      <div v-else class="wb-list">
        <div
          v-for="(item, idx) in wbStore.wrongQuestions"
          :key="item.id"
          class="wb-card"
          :class="{ expanded: expandedId === item.id }"
        >
          <!-- 卡片头部 -->
          <div class="wb-card-header" @click="toggleExpand(item.id)">
            <span class="wb-card-num">{{ idx + 1 }}</span>
            <div class="wb-card-stem">{{ item.stem }}</div>
            <div class="wb-card-tags">
              <span class="tag-diff" :class="'diff-' + item.difficulty">
                {{ difficultyLabel(item.difficulty) }}
              </span>
              <span class="tag-chapter" v-if="item.chapter_title">{{ item.chapter_title }}</span>
            </div>
            <span class="wb-card-arrow" :class="{ open: expandedId === item.id }">&#9662;</span>
          </div>

          <!-- 展开详情 -->
          <div v-if="expandedId === item.id" class="wb-card-body">
            <!-- 选项区域 -->
            <div v-if="item.options && item.options.length" class="wb-options">
              <div
                v-for="opt in item.options"
                :key="opt.key"
                class="wb-option"
                :class="{
                  'is-correct': opt.key === item.answer,
                }"
              >
                <span class="opt-key">{{ opt.key }}</span>
                <span class="opt-text">{{ opt.text }}</span>
                <span v-if="opt.key === item.answer" class="opt-check">&#10003;</span>
              </div>
            </div>
            <div v-else class="wb-answer-box">
              <span class="answer-label">正确答案</span>
              <span class="answer-value">{{ item.answer }}</span>
            </div>

            <!-- 解析 -->
            <div v-if="item.explanation" class="wb-explanation">
              <div class="exp-label">&#9432; 解析</div>
              <div class="exp-text">{{ item.explanation }}</div>
            </div>

            <!-- 统计脚 -->
            <div class="wb-card-footer">
              <div class="footer-stat">
                <span class="fs-dot red"></span>
                错误 {{ item.wrong_count }} 次
              </div>
              <div class="footer-stat" v-if="item.correct_count">
                <span class="fs-dot green"></span>
                重练正确 {{ item.correct_count }} 次
              </div>
              <div class="footer-stat muted" v-if="item.last_wrong_at">
                {{ formatTime(item.last_wrong_at) }}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Tab: 错题重练 -->
    <div v-show="activeTab === 'practice'" class="wb-content">
      <!-- 准备阶段 -->
      <div v-if="!isPracticing && !wbStore.practiceResult" class="practice-prepare">
        <div class="prepare-card">
          <div class="prepare-icon">
            <svg viewBox="0 0 48 48" fill="none" width="48" height="48">
              <rect x="8" y="6" width="32" height="36" rx="4" stroke="#93c5fd" stroke-width="2" fill="#eff6ff"/>
              <path d="M18 22l4 4 8-8" stroke="#3b82f6" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </div>
          <h3>错题重练</h3>
          <p>
            当前共 <strong>{{ wbStore.wrongQuestions.length }}</strong> 道错题，
            系统将随机抽取题目供你重新作答
          </p>
          <div class="count-picker">
            <label>每次练习</label>
            <el-input-number
              v-model="practiceCount"
              :min="1"
              :max="Math.max(1, wbStore.wrongQuestions.length)"
              size="default"
            />
            <label>题</label>
          </div>
          <el-button
            type="primary"
            size="large"
            @click="startPractice"
            :disabled="!wbStore.wrongQuestions.length"
            class="start-btn"
          >
            开始重练
          </el-button>
          <p class="prepare-hint" v-if="!wbStore.wrongQuestions.length">
            尚无错题，先去<a href="/quiz" @click.prevent="$router.push('/quiz')">参加测验</a>吧
          </p>
        </div>
      </div>

      <!-- 答题阶段 -->
      <div v-if="isPracticing && !wbStore.practiceResult" class="practice-exam">
        <div class="pe-header">
          <div class="pe-info">
            <span>第 {{ answeredCount }} / {{ practiceQuestions.length }} 题已作答</span>
            <div class="pe-progress">
              <div class="pe-progress-fill" :style="{ width: progressPercent + '%' }"></div>
            </div>
          </div>
          <el-button type="primary" @click="handlePracticeSubmit" :loading="wbStore.loading">
            提交 {{ practiceQuestions.length }} 题
          </el-button>
        </div>

        <div class="pe-questions">
          <div
            v-for="(q, idx) in practiceQuestions"
            :key="q.wrongbook_id"
            class="pe-card"
            :class="{ answered: practiceAnswers[q.wrongbook_id] }"
          >
            <div class="pe-q-header">
              <span class="pe-q-num">{{ idx + 1 }}</span>
              <span class="pe-q-stem">{{ q.stem }}</span>
              <span class="pe-q-type">{{ q.type === 'single_choice' ? '单选' : '判断' }}</span>
            </div>

            <!-- 单选选项 -->
            <div v-if="q.type === 'single_choice'" class="pe-options">
              <label
                v-for="opt in q.options"
                :key="opt.key"
                class="pe-opt"
                :class="{ selected: practiceAnswers[q.wrongbook_id] === opt.key }"
                @click="selectAnswer(q.wrongbook_id, opt.key)"
              >
                <span class="pe-opt-key">{{ opt.key }}</span>
                <span class="pe-opt-text">{{ opt.text }}</span>
              </label>
            </div>

            <!-- 判断选项 -->
            <div v-if="q.type === 'true_false'" class="pe-options">
              <label
                class="pe-opt"
                :class="{ selected: practiceAnswers[q.wrongbook_id] === '对' }"
                @click="selectAnswer(q.wrongbook_id, '对')"
              >
                <span class="pe-opt-key">&#10003;</span>
                <span class="pe-opt-text">正确</span>
              </label>
              <label
                class="pe-opt"
                :class="{ selected: practiceAnswers[q.wrongbook_id] === '错' }"
                @click="selectAnswer(q.wrongbook_id, '错')"
              >
                <span class="pe-opt-key">&#10007;</span>
                <span class="pe-opt-text">错误</span>
              </label>
            </div>
          </div>
        </div>
      </div>

      <!-- 结果阶段 -->
      <div v-if="wbStore.practiceResult" class="practice-result">
        <div class="pr-card">
          <div class="pr-ring" :class="ringClass">
            <svg viewBox="0 0 120 120" width="120" height="120">
              <circle cx="60" cy="60" r="52" fill="none" stroke="#e5e7eb" stroke-width="8"/>
              <circle
                cx="60" cy="60" r="52" fill="none"
                :stroke="resultColor"
                stroke-width="8"
                stroke-linecap="round"
                :stroke-dasharray="circumference"
                :stroke-dashoffset="dashOffset"
                transform="rotate(-90 60 60)"
              />
            </svg>
            <div class="pr-ring-inner">
              <span class="pr-ring-num">{{ wbStore.practiceResult.score }}</span>
              <span class="pr-ring-label">分</span>
            </div>
          </div>
          <div class="pr-meta">
            <div class="pr-meta-item">
              <span class="pr-meta-val green">{{ wbStore.practiceResult.correct }}</span>
              <span class="pr-meta-lbl">正确</span>
            </div>
            <div class="pr-meta-divider"></div>
            <div class="pr-meta-item">
              <span class="pr-meta-val red">{{ wbStore.practiceResult.total - wbStore.practiceResult.correct }}</span>
              <span class="pr-meta-lbl">错误</span>
            </div>
            <div class="pr-meta-divider"></div>
            <div class="pr-meta-item">
              <span class="pr-meta-val">{{ wbStore.practiceResult.total }}</span>
              <span class="pr-meta-lbl">总题数</span>
            </div>
          </div>
          <el-button size="large" @click="finishPractice" class="pr-back-btn">
            返回错题列表
          </el-button>
        </div>
      </div>
    </div>

    <!-- Tab: 统计 -->
    <div v-show="activeTab === 'stats'" class="wb-content">
      <div v-if="wbStore.stats" class="stats-section">
        <!-- 顶部概览 -->
        <div class="stats-overview">
          <div class="so-card">
            <div class="so-icon wrong">
              <svg viewBox="0 0 24 24" fill="none" width="20" height="20">
                <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z" fill="#ef4444"/>
              </svg>
            </div>
            <div>
              <div class="so-num">{{ wbStore.stats.total_wrong_questions }}</div>
              <div class="so-label">错题总数</div>
            </div>
          </div>
          <div class="so-card">
            <div class="so-icon warn">
              <svg viewBox="0 0 24 24" fill="none" width="20" height="20">
                <circle cx="12" cy="12" r="10" stroke="#f59e0b" stroke-width="2"/>
                <path d="M12 6v8M12 17v1" stroke="#f59e0b" stroke-width="2" stroke-linecap="round"/>
              </svg>
            </div>
            <div>
              <div class="so-num warn">{{ wbStore.stats.total_wrong_times }}</div>
              <div class="so-label">累计错误</div>
            </div>
          </div>
          <div class="so-card">
            <div class="so-icon ok">
              <svg viewBox="0 0 24 24" fill="none" width="20" height="20">
                <path d="M9 11l3 3L22 4" stroke="#22c55e" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M21 12v7a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h11" stroke="#22c55e" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </div>
            <div>
              <div class="so-num ok">{{ wbStore.stats.total_correct_times }}</div>
              <div class="so-label">重练正确</div>
            </div>
          </div>
          <div class="so-card">
            <div class="so-icon rate">
              <svg viewBox="0 0 24 24" fill="none" width="20" height="20">
                <path d="M22 12h-4l-3 9L9 3l-3 9H2" stroke="#3b82f6" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </div>
            <div>
              <div class="so-num rate" :class="wbStore.stats.correct_rate >= 60 ? 'ok' : 'warn'">
                {{ wbStore.stats.correct_rate }}%
              </div>
              <div class="so-label">重练正确率</div>
            </div>
          </div>
        </div>

        <!-- 章节分布 -->
        <div v-if="wbStore.stats.by_chapter.length" class="stats-chapters">
          <h4 class="section-title">章节分布</h4>
          <div class="sc-list">
            <div v-for="ch in wbStore.stats.by_chapter" :key="ch.chapter_id" class="sc-row">
              <div class="sc-info">
                <span class="sc-name">{{ ch.chapter_title }}</span>
                <div class="sc-bar-wrap">
                  <div
                    class="sc-bar"
                    :style="{ width: (ch.count / maxChapterCount) * 100 + '%' }"
                  />
                </div>
              </div>
              <span class="sc-count">{{ ch.count }} 题</span>
            </div>
          </div>
        </div>
      </div>

      <div v-else-if="wbStore.loading" class="wb-skeleton">
        <div v-for="i in 2" :key="i" class="skeleton-row">
          <div class="skeleton-line w-60" />
          <div class="skeleton-line w-40" />
        </div>
      </div>

      <div v-else class="wb-empty">
        <h3>暂无统计</h3>
        <p>完成测验后即可查看错题统计</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, reactive, onActivated, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { useWrongBookStore } from '@/stores/wrongbook'
import { useCourseStore } from '@/stores/course'
import type { PracticeQuestion } from '@/api/wrongbook'
import type { ChapterTreeNode } from '@/api/course'

const wbStore = useWrongBookStore()
const courseStore = useCourseStore()

// Tab
type Tab = { key: string; label: string; icon: string }
const tabs: Tab[] = [
  { key: 'list', label: '错题列表', icon: '📋' },
  { key: 'practice', label: '错题重练', icon: '🔄' },
  { key: 'stats', label: '统计分析', icon: '📊' },
]
const activeTab = ref('list')

function switchTab(key: string) {
  activeTab.value = key
  if (key === 'list') refreshList()
  if (key === 'stats') wbStore.fetchStats()
}

// 章节筛选
const filterChapterId = ref<number | null>(null)
const chapterOptions = ref<{ id: number; title: string }[]>([])

function flattenTree(nodes: ChapterTreeNode[]): { id: number; title: string }[] {
  const result: { id: number; title: string }[] = []
  for (const node of nodes) {
    result.push({ id: node.id, title: node.title })
    if (node.children) {
      result.push(...flattenTree(node.children))
    }
  }
  return result
}

watch(() => courseStore.outlineTree, (tree) => {
  chapterOptions.value = flattenTree(tree)
}, { immediate: true })

function onChapterFilter(chapterId?: number | null) {
  wbStore.fetchWrongQuestions(chapterId || undefined)
}

// 展开/折叠
const expandedId = ref<number | null>(null)
function toggleExpand(id: number) {
  expandedId.value = expandedId.value === id ? null : id
}

// 列表
async function refreshList() {
  try {
    await wbStore.fetchWrongQuestions(filterChapterId.value || undefined)
    await wbStore.fetchStats()
  } catch (e: any) {
    // 静默失败，保持已有数据
  }
}

// 重练
const isPracticing = ref(false)
const practiceCount = ref(5)
const practiceQuestions = ref<PracticeQuestion[]>([])
const practiceAnswers = reactive<Record<number, string>>({})

const answeredCount = computed(() =>
  practiceQuestions.value.filter(q => practiceAnswers[q.wrongbook_id]).length
)
const progressPercent = computed(() =>
  practiceQuestions.value.length ? (answeredCount.value / practiceQuestions.value.length) * 100 : 0
)

function selectAnswer(wid: number, answer: string) {
  practiceAnswers[wid] = answer
}

async function goPractice() {
  activeTab.value = 'practice'
}

async function startPractice() {
  if (!wbStore.wrongQuestions.length) {
    ElMessage.warning('暂无错题，先去参加测验吧')
    return
  }
  resetPracticeState()
  wbStore.clearResult()
  try {
    practiceQuestions.value = await wbStore.fetchPracticeQuestions(practiceCount.value)
    isPracticing.value = true
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '获取重练题目失败')
  }
}

function resetPracticeState() {
  Object.keys(practiceAnswers).forEach(k => delete practiceAnswers[Number(k)])
}

async function handlePracticeSubmit() {
  const unanswered = practiceQuestions.value.filter(q => !practiceAnswers[q.wrongbook_id])
  if (unanswered.length) {
    ElMessage.warning(`还有 ${unanswered.length} 题未作答`)
    return
  }
  const answers = practiceQuestions.value.map(q => ({
    wrongbook_id: q.wrongbook_id,
    user_answer: practiceAnswers[q.wrongbook_id] || '',
  }))
  try {
    await wbStore.submitPractice(answers)
    isPracticing.value = false
    ElMessage.success(`练习完成，得分 ${wbStore.practiceResult?.score}`)
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '提交失败')
  }
}

async function finishPractice() {
  isPracticing.value = false
  resetPracticeState()
  wbStore.clearResult()
  activeTab.value = 'list'
  await refreshList()
}

// 统计
const maxChapterCount = computed(() => {
  if (!wbStore.stats?.by_chapter.length) return 1
  return Math.max(...wbStore.stats.by_chapter.map(c => c.count))
})

const ringClass = computed(() => {
  const s = wbStore.practiceResult?.score ?? 0
  return s >= 80 ? 'ring-high' : s >= 60 ? 'ring-mid' : 'ring-low'
})
const resultColor = computed(() => {
  const s = wbStore.practiceResult?.score ?? 0
  return s >= 80 ? '#22c55e' : s >= 60 ? '#f59e0b' : '#ef4444'
})
const circumference = 2 * Math.PI * 52  // ≈ 326.73
const dashOffset = computed(() => {
  const s = wbStore.practiceResult?.score ?? 0
  return circumference - (s / 100) * circumference
})

// 工具
function difficultyLabel(d: string) {
  return d === 'hard' ? '困难' : d === 'medium' ? '中等' : '简单'
}

function formatTime(dateStr: string) {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleString('zh-CN', {
    month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit',
  })
}

// 生命周期
onActivated(() => {
  if (!wbStore.wrongQuestions.length) {
    refreshList()
  }
})
</script>

<style scoped>
/* ==================== 页面容器 ==================== */
.wrongbook-page {
  max-width: 880px;
  margin: 0 auto;
  padding-bottom: 40px;
}

/* ==================== 顶部 Hero ==================== */
.wb-hero {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
}

.wb-title {
  margin: 0 0 6px;
  font-size: 22px;
  color: var(--color-text-heading);
}

.wb-desc {
  margin: 0;
  font-size: 14px;
  color: var(--color-text-secondary);
}

.wb-hero-right {
  display: flex;
  gap: 24px;
}

.quick-stat {
  text-align: center;
}

.qs-num {
  display: block;
  font-size: 24px;
  font-weight: 700;
  color: var(--color-text-heading);
}

.qs-num.green { color: var(--color-success); }
.qs-num.red { color: var(--color-danger); }

.qs-label {
  font-size: 11px;
  color: var(--color-text-secondary);
  margin-top: 2px;
  display: block;
}

/* ==================== Tab 导航 ==================== */
.wb-nav {
  display: flex;
  gap: 4px;
  background: var(--color-surface);
  border-radius: var(--radius-md);
  padding: 4px;
  margin-bottom: 20px;
  border: 1px solid var(--color-border);
}

.wb-nav-btn {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 10px 16px;
  border: none;
  background: transparent;
  border-radius: 7px;
  font-size: 13px;
  font-weight: 500;
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all 0.15s;
  font-family: inherit;
}

.wb-nav-btn:hover { color: var(--color-text-heading); background: #f8fafc; }
.wb-nav-btn.active {
  color: var(--color-primary);
  background: var(--color-primary-light);
}

.wb-nav-icon { font-size: 15px; }

.wb-nav-badge {
  background: var(--color-primary);
  color: #fff;
  font-size: 10px;
  font-weight: 600;
  padding: 1px 6px;
  border-radius: 10px;
  min-width: 18px;
  text-align: center;
  line-height: 16px;
}

/* ==================== 内容区 ==================== */
.wb-content {
  min-height: 300px;
}

/* ==================== 工具栏 ==================== */
.wb-toolbar {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
}

.chapter-filter {
  width: 180px;
}

.toolbar-spacer { flex: 1; }

/* ==================== 骨架屏 ==================== */
.wb-skeleton { padding: 20px 0; }
.skeleton-row {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: 20px;
  margin-bottom: 12px;
}
.skeleton-line {
  height: 12px;
  background: #e2e8f0;
  border-radius: 6px;
  margin-bottom: 10px;
}
.skeleton-line:last-child { margin-bottom: 0; }
.w-60 { width: 60%; }
.w-80 { width: 80%; }
.w-40 { width: 40%; }

/* ==================== 空状态 ==================== */
.wb-empty {
  text-align: center;
  padding: 64px 20px;
}

.wb-empty-icon {
  margin-bottom: 16px;
  opacity: 0.6;
}

.wb-empty h3 {
  margin: 0 0 8px;
  font-size: 16px;
  color: var(--color-text-heading);
}

.wb-empty p {
  font-size: 13px;
  color: var(--color-text-secondary);
  margin: 0 0 20px;
}

/* ==================== 错题卡片列表 ==================== */
.wb-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.wb-card {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  overflow: hidden;
  transition: box-shadow 0.15s;
}

.wb-card:hover { box-shadow: var(--shadow-sm); }
.wb-card.expanded { box-shadow: var(--shadow-sm); border-color: #c7d2fe; }

.wb-card-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  cursor: pointer;
  user-select: none;
}

.wb-card-num {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: #f1f5f9;
  font-size: 12px;
  font-weight: 700;
  color: var(--color-text-secondary);
  flex-shrink: 0;
}

.wb-card-stem {
  flex: 1;
  font-size: 14px;
  font-weight: 500;
  color: var(--color-text-heading);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  line-height: 1.4;
}

.wb-card-tags {
  display: flex;
  gap: 6px;
  flex-shrink: 0;
}

.tag-diff {
  font-size: 11px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 4px;
}
.tag-diff.diff-easy { background: #dcfce7; color: #16a34a; }
.tag-diff.diff-medium { background: #fef3c7; color: #d97706; }
.tag-diff.diff-hard { background: #fee2e2; color: #dc2626; }

.tag-chapter {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 4px;
  background: #f1f5f9;
  color: var(--color-text-secondary);
  max-width: 120px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.wb-card-arrow {
  font-size: 12px;
  color: var(--color-text-secondary);
  transition: transform 0.2s;
  flex-shrink: 0;
}
.wb-card-arrow.open { transform: rotate(180deg); }

/* 卡片详情 */
.wb-card-body {
  padding: 0 16px 16px;
  border-top: 1px solid #f1f5f9;
  animation: slideDown 0.15s ease;
}

@keyframes slideDown {
  from { opacity: 0; transform: translateY(-4px); }
  to { opacity: 1; transform: translateY(0); }
}

/* 选项 */
.wb-options {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-top: 12px;
}

.wb-option {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 12px;
  border-radius: 6px;
  background: #f8fafc;
  font-size: 13px;
}

.wb-option.is-correct {
  background: #f0fdf4;
  border: 1px solid #bbf7d0;
}

.opt-key {
  width: 22px;
  height: 22px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: #e2e8f0;
  font-size: 11px;
  font-weight: 700;
  color: var(--color-text-secondary);
  flex-shrink: 0;
}

.is-correct .opt-key {
  background: #22c55e;
  color: #fff;
}

.opt-text { flex: 1; }

.opt-check {
  color: #22c55e;
  font-weight: 700;
  font-size: 14px;
}

/* 无选项时的答案 */
.wb-answer-box {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 12px;
  padding: 10px 14px;
  background: #f0fdf4;
  border-radius: 6px;
}

.answer-label {
  font-size: 11px;
  font-weight: 600;
  color: var(--color-text-secondary);
  text-transform: uppercase;
}

.answer-value {
  font-size: 15px;
  font-weight: 600;
  color: #16a34a;
}

/* 解析 */
.wb-explanation {
  margin-top: 10px;
  padding: 12px;
  background: #f8fafc;
  border-radius: 6px;
  border-left: 3px solid #93c5fd;
}

.exp-label {
  font-size: 11px;
  font-weight: 600;
  color: #3b82f6;
  margin-bottom: 4px;
}

.exp-text {
  font-size: 13px;
  color: var(--color-text-secondary);
  line-height: 1.7;
}

/* 卡片底部统计 */
.wb-card-footer {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-top: 12px;
  font-size: 12px;
  color: var(--color-text-secondary);
}

.footer-stat {
  display: flex;
  align-items: center;
  gap: 4px;
}

.footer-stat.muted { margin-left: auto; }

.fs-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
}
.fs-dot.red { background: #ef4444; }
.fs-dot.green { background: #22c55e; }

/* ==================== 重练 - 准备 ==================== */
.practice-prepare {
  display: flex;
  justify-content: center;
  padding: 40px 0;
}

.prepare-card {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: 48px 40px;
  text-align: center;
  width: 100%;
  max-width: 420px;
}

.prepare-icon { margin-bottom: 16px; }

.prepare-card h3 {
  margin: 0 0 8px;
  font-size: 18px;
  color: var(--color-text-heading);
}

.prepare-card p {
  font-size: 13px;
  color: var(--color-text-secondary);
  margin: 0 0 24px;
  line-height: 1.6;
}

.count-picker {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  margin-bottom: 20px;
  font-size: 13px;
  color: var(--color-text-secondary);
}

.start-btn { width: 100%; }

.prepare-hint {
  margin-top: 12px;
  font-size: 12px;
  color: var(--color-text-secondary);
}

.prepare-hint a { color: var(--color-primary); }

/* ==================== 重练 - 答题 ==================== */
.practice-exam { }

.pe-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: 14px 18px;
  margin-bottom: 16px;
  position: sticky;
  top: 0;
  z-index: 10;
}

.pe-info {
  font-size: 13px;
  color: var(--color-text-secondary);
  flex: 1;
  margin-right: 16px;
}

.pe-progress {
  height: 4px;
  background: #e2e8f0;
  border-radius: 2px;
  margin-top: 8px;
  overflow: hidden;
}

.pe-progress-fill {
  height: 100%;
  background: var(--color-primary);
  border-radius: 2px;
  transition: width 0.3s;
}

.pe-questions {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.pe-card {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: 18px;
  transition: border-color 0.15s;
}

.pe-card.answered { border-color: #93c5fd; }

.pe-q-header {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  margin-bottom: 14px;
}

.pe-q-num {
  width: 26px;
  height: 26px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: #eff6ff;
  font-size: 12px;
  font-weight: 700;
  color: var(--color-primary);
  flex-shrink: 0;
}

.pe-q-stem {
  flex: 1;
  font-size: 15px;
  font-weight: 500;
  color: var(--color-text-heading);
  line-height: 1.6;
}

.pe-q-type {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 4px;
  background: #f1f5f9;
  color: var(--color-text-secondary);
  flex-shrink: 0;
}

.pe-options {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding-left: 36px;
}

.pe-opt {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  border-radius: var(--radius-sm);
  border: 1.5px solid #e2e8f0;
  cursor: pointer;
  transition: all 0.12s;
  font-size: 14px;
}

.pe-opt:hover {
  border-color: #93c5fd;
  background: #f0f7ff;
}

.pe-opt.selected {
  border-color: var(--color-primary);
  background: #eff6ff;
}

.pe-opt-key {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: #f1f5f9;
  font-size: 12px;
  font-weight: 700;
  color: var(--color-text-secondary);
  flex-shrink: 0;
}

.pe-opt.selected .pe-opt-key {
  background: var(--color-primary);
  color: #fff;
}

.pe-opt-text { flex: 1; }

/* ==================== 重练 - 结果 ==================== */
.practice-result {
  display: flex;
  justify-content: center;
  padding: 40px 0;
}

.pr-card {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: 40px;
  text-align: center;
  width: 100%;
  max-width: 360px;
}

.pr-ring {
  position: relative;
  width: 120px;
  height: 120px;
  margin: 0 auto 20px;
}

.pr-ring-inner {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.pr-ring-num {
  font-size: 32px;
  font-weight: 800;
  line-height: 1;
}
.ring-high .pr-ring-num { color: #22c55e; }
.ring-mid .pr-ring-num { color: #f59e0b; }
.ring-low .pr-ring-num { color: #ef4444; }

.pr-ring-label {
  font-size: 13px;
  color: var(--color-text-secondary);
  margin-top: 2px;
}

.pr-meta {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 20px;
  margin-bottom: 24px;
}

.pr-meta-item {
  text-align: center;
}

.pr-meta-val {
  display: block;
  font-size: 20px;
  font-weight: 700;
  color: var(--color-text-heading);
}

.pr-meta-val.green { color: #22c55e; }
.pr-meta-val.red { color: #ef4444; }

.pr-meta-lbl {
  font-size: 11px;
  color: var(--color-text-secondary);
}

.pr-meta-divider {
  width: 1px;
  height: 32px;
  background: var(--color-border);
}

.pr-back-btn { margin-top: 8px; }

/* ==================== 统计 ==================== */
.stats-section {}

.stats-overview {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  margin-bottom: 24px;
}

.so-card {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: 18px;
  display: flex;
  align-items: center;
  gap: 12px;
}

.so-icon {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.so-icon.wrong { background: #fef2f2; }
.so-icon.warn { background: #fffbeb; }
.so-icon.ok { background: #f0fdf4; }
.so-icon.rate { background: #eff6ff; }

.so-num {
  font-size: 24px;
  font-weight: 700;
  color: var(--color-text-heading);
  line-height: 1.2;
}
.so-num.warn { color: #d97706; }
.so-num.ok { color: #16a34a; }
.so-num.rate { color: var(--color-primary); }

.so-label {
  font-size: 11px;
  color: var(--color-text-secondary);
}

.section-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text-heading);
  margin: 0 0 12px;
}

.stats-chapters {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: 20px;
}

.sc-list {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.sc-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 0;
}

.sc-row:not(:last-child) {
  border-bottom: 1px solid #f8fafc;
}

.sc-info { flex: 1; margin-right: 16px; }

.sc-name {
  font-size: 13px;
  font-weight: 500;
  color: var(--color-text-heading);
  display: block;
  margin-bottom: 6px;
}

.sc-bar-wrap {
  height: 6px;
  background: #f1f5f9;
  border-radius: 3px;
  overflow: hidden;
}

.sc-bar {
  height: 100%;
  background: var(--color-primary);
  border-radius: 3px;
  transition: width 0.4s ease;
}

.sc-count {
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text-secondary);
  flex-shrink: 0;
}

/* ==================== 响应式 ==================== */
@media (max-width: 768px) {
  .wb-hero { flex-direction: column; gap: 16px; }
  .wb-hero-right { gap: 16px; }
  .stats-overview { grid-template-columns: repeat(2, 1fr); }
  .wb-card-tags { display: none; }
  .pe-header { flex-direction: column; gap: 10px; }
  .pe-options { padding-left: 0; }
}
</style>
