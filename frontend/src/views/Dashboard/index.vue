<template>
  <div class="dashboard-container">
    <div class="page-header">
      <div>
        <h2>学习进度</h2>
        <div class="subtitle">跟踪课程完成情况</div>
      </div>
      <el-button type="danger" plain size="small" @click="handleReset">
        重置进度
      </el-button>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-value">{{ store.data.total_chapters }}</div>
        <div class="stat-label">总章节</div>
      </div>
      <div class="stat-card success">
        <div class="stat-value">{{ store.data.completed }}</div>
        <div class="stat-label">已完成</div>
      </div>
      <div class="stat-card warning">
        <div class="stat-value">{{ store.data.learning }}</div>
        <div class="stat-label">学习中</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ store.data.not_started }}</div>
        <div class="stat-label">未开始</div>
      </div>
    </div>

    <!-- 进度条 -->
    <div class="progress-section">
      <div class="progress-header">
        <span class="progress-title">完课率</span>
        <span class="progress-percent">{{ store.data.percent }}%</span>
      </div>
      <el-progress
        :percentage="store.data.percent"
        :stroke-width="12"
        :color="store.data.percent === 100 ? '#22c55e' : '#3b82f6'"
        :trail-color="'#e8eaed'"
      />
    </div>

    <!-- 章节列表 -->
    <div class="chapter-list">
      <div class="chapter-table-header">
        <span class="col-index">#</span>
        <span class="col-name">章节</span>
        <span class="col-status">状态</span>
        <span class="col-action">操作</span>
      </div>

      <div
        v-for="(item, index) in chapterProgress"
        :key="item.chapter_id"
        class="chapter-row"
      >
        <span class="col-index">{{ index + 1 }}</span>
        <span class="col-name">{{ item.title }}</span>
        <span class="col-status">
          <el-tag
            :type="item.status === 'completed' ? 'success' : item.status === 'learning' ? 'warning' : 'info'"
            effect="plain"
            size="small"
          >
            {{ item.status === 'completed' ? '已完成' : item.status === 'learning' ? '学习中' : '未开始' }}
          </el-tag>
        </span>
        <span class="col-action">
          <el-button
            v-if="item.status === 'not_started'"
            size="small"
            type="primary"
            text
            @click="updateChapter(item.chapter_id, 'learning')"
          >
            开始学习
          </el-button>
          <el-button
            v-if="item.status !== 'completed'"
            size="small"
            type="success"
            text
            @click="updateChapter(item.chapter_id, 'completed')"
          >
            标记完成
          </el-button>
        </span>
      </div>

      <div v-if="!chapterProgress.length" class="empty-state">
        <div class="icon">📊</div>
        <p>暂无进度数据</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onActivated } from 'vue'
import { ElMessageBox, ElMessage } from 'element-plus'
import { useDashboardStore } from '@/stores/dashboard'
import { useCourseStore } from '@/stores/course'

const store = useDashboardStore()
const courseStore = useCourseStore()

const chapterProgress = computed(() => {
  const chapters: { chapter_id: number; title: string; status: string }[] = []
  for (const ch of courseStore.outlineTree) {
    for (const sec of ch.children) {
      const p = store.data.detail.find(d => d.chapter_id === sec.id)
      chapters.push({
        chapter_id: sec.id,
        title: `${ch.title} — ${sec.title}`,
        status: p?.status || 'not_started',
      })
    }
  }
  return chapters
})

function updateChapter(chapterId: number, status: string) {
  store.updateProgress(chapterId, status)
}

function handleReset() {
  ElMessageBox.confirm('确定要重置所有学习进度吗？', '确认', {
    type: 'warning',
    confirmButtonText: '重置',
    cancelButtonText: '取消',
  }).then(() => {
    store.reset()
    ElMessage.success('已重置所有进度')
  }).catch(() => {})
}

onActivated(() => {
  Promise.all([
    store.fetchDashboard(),
    courseStore.fetchOutline(),
  ])
})
</script>

<style scoped>
.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 20px;
}

.stat-card {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: 20px;
  text-align: center;
  transition: box-shadow 0.2s;
}

.stat-card:hover {
  box-shadow: var(--shadow-md);
}

.stat-value {
  font-size: 32px;
  font-weight: 700;
  line-height: 1;
  margin-bottom: 6px;
  color: var(--color-text-heading);
}

.stat-card.success .stat-value { color: var(--color-success); }
.stat-card.warning .stat-value { color: var(--color-warning); }

.stat-label {
  font-size: 13px;
  color: var(--color-text-secondary);
}

/* 进度条 */
.progress-section {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: 20px;
  margin-bottom: 20px;
}

.progress-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.progress-title {
  font-size: 14px;
  font-weight: 500;
  color: var(--color-text);
}

.progress-percent {
  font-size: 20px;
  font-weight: 700;
  color: var(--color-primary);
}

/* 章节列表 */
.chapter-list {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  overflow: hidden;
}

.chapter-table-header {
  display: flex;
  align-items: center;
  padding: 12px 20px;
  background: #f8fafc;
  font-size: 12px;
  font-weight: 600;
  color: var(--color-text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  border-bottom: 1px solid var(--color-border);
}

.chapter-row {
  display: flex;
  align-items: center;
  padding: 14px 20px;
  border-bottom: 1px solid #f1f5f9;
  transition: background 0.15s;
  font-size: 13px;
}

.chapter-row:last-child {
  border-bottom: none;
}

.chapter-row:hover {
  background: #fafbfc;
}

.col-index {
  width: 40px;
  color: var(--color-text-secondary);
}

.col-name {
  flex: 1;
  color: var(--color-text-heading);
  font-weight: 500;
}

.col-status {
  width: 80px;
}

.col-action {
  width: 120px;
  text-align: right;
}

@media (max-width: 768px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
