<template>
  <div class="course-container">
    <div class="page-header">
      <div>
        <h2>课程学习</h2>
        <div class="subtitle">选择章节开始学习</div>
      </div>
      <el-button type="primary" :loading="courseStore.loading" @click="handleGenerate" class="generate-btn">
        <el-icon style="margin-right:4px"><MagicStick /></el-icon>
        生成课程大纲
      </el-button>
    </div>

    <div v-if="!courseStore.outlineTree.length" class="empty-state">
      <div class="icon">📖</div>
      <p>暂无课程大纲</p>
      <p style="font-size:13px;margin-top:4px;">请先上传知识库文档，然后点击「生成课程大纲」</p>
    </div>

    <div v-else class="course-layout">
      <!-- 左侧大纲 -->
      <div class="outline-panel">
        <div class="outline-header">课程目录</div>
        <div
          v-for="ch in courseStore.outlineTree"
          :key="ch.id"
          class="chapter-group"
        >
          <div class="chapter-title">{{ ch.title }}</div>
          <div
            v-for="sec in ch.children"
            :key="sec.id"
            class="section-item"
            :class="{ active: currentChapterId === sec.id }"
            @click="selectChapter(sec.id)"
          >
            <el-icon v-if="getStatusTag(sec.id) === 'success'" class="status-icon success"><CircleCheck /></el-icon>
            <el-icon v-else-if="getStatusTag(sec.id) === 'warning'" class="status-icon warning"><Clock /></el-icon>
            <el-icon v-else class="status-icon default"><Right /></el-icon>
            <span class="section-label">{{ sec.title }}</span>
          </div>
        </div>
      </div>

      <!-- 右侧内容 -->
      <div class="content-panel">
        <div v-if="!courseStore.currentChapter" class="empty-state">
          <div class="icon">📝</div>
          <p>请从左侧选择章节开始学习</p>
        </div>

        <template v-else>
          <div class="content-header">
            <h3>{{ courseStore.currentChapter.title }}</h3>
            <div class="content-actions">
              <el-button
                size="small"
                :type="getChapterStatus(courseStore.currentChapter.id) === 'learning' ? 'warning' : 'primary'"
                plain
                @click="toggleStudy"
              >
                {{ getChapterStatus(courseStore.currentChapter.id) === 'learning' ? '学习中' : '开始学习' }}
              </el-button>
              <el-button
                size="small"
                type="success"
                plain
                :disabled="getChapterStatus(courseStore.currentChapter.id) !== 'learning'"
                @click="markComplete"
              >
                标记完成
              </el-button>
              <el-button
                size="small"
                plain
                @click="handleRegenerate"
                :loading="regenerating"
              >
                重新生成
              </el-button>
            </div>
          </div>
          <div class="content-body" v-html="renderedContent" />
        </template>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onActivated } from 'vue'
import { MagicStick, CircleCheck, Clock, Right } from '@element-plus/icons-vue'
import { marked } from 'marked'
import { useCourseStore } from '@/stores/course'
import { useDashboardStore } from '@/stores/dashboard'

const courseStore = useCourseStore()
const dashboardStore = useDashboardStore()

const currentChapterId = ref<number | null>(null)
const regenerating = ref(false)

const renderedContent = computed(() => {
  if (!courseStore.currentChapter?.content) return ''
  return marked(courseStore.currentChapter.content, { breaks: true }) as string
})

function getStatusTag(chapterId: number) {
  const item = dashboardStore.data.detail.find(d => d.chapter_id === chapterId)
  if (!item) return 'info'
  if (item.status === 'completed') return 'success'
  if (item.status === 'learning') return 'warning'
  return 'info'
}

function getChapterStatus(chapterId: number) {
  const item = dashboardStore.data.detail.find(d => d.chapter_id === chapterId)
  return item?.status || 'not_started'
}

async function selectChapter(id: number) {
  currentChapterId.value = id
  await courseStore.loadChapter(id)
  // 无内容时自动生成
  if (courseStore.currentChapter && !courseStore.currentChapter.content) {
    regenerating.value = true
    try {
      await courseStore.regenerateChapter(id)
    } finally {
      regenerating.value = false
    }
  }
}

async function handleGenerate() {
  try {
    await courseStore.generateOutline()
    await dashboardStore.fetchDashboard()
  } catch (e: any) {
    ElMessage.error(e.message || '生成失败')
  }
}

async function handleRegenerate() {
  if (!currentChapterId.value) return
  regenerating.value = true
  try {
    await courseStore.regenerateChapter(currentChapterId.value)
  } finally {
    regenerating.value = false
  }
}

async function toggleStudy() {
  if (!currentChapterId.value) return
  const current = getChapterStatus(currentChapterId.value)
  const newStatus = current === 'learning' ? 'not_started' : 'learning'
  await dashboardStore.updateProgress(currentChapterId.value, newStatus)
}

async function markComplete() {
  if (!currentChapterId.value) return
  await dashboardStore.updateProgress(currentChapterId.value, 'completed')
}

onActivated(async () => {
  if (!courseStore.outlineTree.length) {
    await Promise.all([
      courseStore.fetchOutline(),
      dashboardStore.fetchDashboard(),
    ])
  }
})
</script>

<style scoped>
.course-layout {
  display: flex;
  gap: 20px;
  align-items: flex-start;
}

.outline-panel {
  width: 260px;
  flex-shrink: 0;
  background: var(--color-surface);
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border);
  padding: 16px;
  position: sticky;
  top: 32px;
  max-height: calc(100vh - 140px);
  overflow-y: auto;
}

.outline-header {
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text-heading);
  padding-bottom: 12px;
  margin-bottom: 8px;
  border-bottom: 1px solid var(--color-border);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.chapter-group {
  margin-bottom: 16px;
}

.chapter-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text-heading);
  padding: 6px 4px;
  margin-bottom: 2px;
}

.section-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 7px 10px;
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: all 0.15s;
  font-size: 13px;
  color: var(--color-text);
}

.section-item:hover {
  background: #f8fafc;
}

.section-item.active {
  background: var(--color-primary-light);
  color: var(--color-primary);
  font-weight: 500;
}

.status-icon {
  font-size: 14px;
  flex-shrink: 0;
}

.status-icon.success { color: var(--color-success); }
.status-icon.warning { color: var(--color-warning); }
.status-icon.default { color: var(--color-text-secondary); }

.section-label {
  line-height: 1.3;
}

/* 内容区 */
.content-panel {
  flex: 1;
  min-width: 0;
  background: var(--color-surface);
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border);
  padding: 24px 28px;
  min-height: 400px;
}

.content-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--color-border);
}

.content-header h3 {
  margin: 0;
  font-size: 18px;
  line-height: 1.4;
}

.content-actions {
  display: flex;
  gap: 6px;
  flex-shrink: 0;
}

.content-body {
  line-height: 1.8;
  font-size: 14px;
  color: var(--color-text);
}

.content-body :deep(h1),
.content-body :deep(h2),
.content-body :deep(h3) {
  margin-top: 24px;
  margin-bottom: 12px;
  font-weight: 600;
}

.content-body :deep(p) {
  margin: 8px 0;
}

.content-body :deep(ul),
.content-body :deep(ol) {
  padding-left: 20px;
  margin: 8px 0;
}

.content-body :deep(li) {
  margin: 4px 0;
}

.content-body :deep(code) {
  background: #f1f5f9;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 13px;
}

.content-body :deep(pre) {
  background: #f8fafc;
  padding: 16px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--color-border);
  overflow-x: auto;
}

.generate-btn {
  flex-shrink: 0;
}
</style>
