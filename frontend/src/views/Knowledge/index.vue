<template>
  <div class="knowledge-container">
    <div class="page-header">
      <div>
        <h2>知识库</h2>
        <div class="subtitle">上传和管理学习资料文档</div>
      </div>
    </div>

    <!-- 搜索 & AI 问答 -->
    <el-card class="search-card">
      <el-tabs v-model="searchMode" class="search-tabs">
        <el-tab-pane label="语义搜索" name="search" />
        <el-tab-pane label="AI 问答" name="ask" />
      </el-tabs>

      <div class="search-bar">
        <el-input
          v-model="searchQuery"
          :placeholder="searchMode === 'ask' ? '向 AI 提问，如：Qt 中信号和槽的机制是什么？' : '搜索知识库，如：信号槽怎么用'"
          clearable
          size="large"
          @keyup.enter="searchMode === 'ask' ? handleAsk() : handleSearch()"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        <el-button
          v-if="searchMode === 'search'"
          type="primary"
          size="large"
          @click="handleSearch"
          :loading="searching"
        >
          搜索
        </el-button>
        <el-button
          v-else
          type="primary"
          size="large"
          @click="handleAsk"
          :loading="knowledgeStore.aiLoading"
        >
          提问
        </el-button>
      </div>

      <!-- 搜索结果 -->
      <div v-if="searchMode === 'search' && uniqueSearchResults.length" class="search-results">
        <div class="results-header">
          找到 {{ uniqueSearchResults.length }} 条相关结果（来自 {{ searchFileCount }} 个文件）
        </div>
        <div
          v-for="(item, idx) in uniqueSearchResults"
          :key="idx"
          class="result-item"
        >
          <div class="result-meta">
            <el-tag size="small" type="info" effect="plain">{{ item.filename }}</el-tag>
            <span class="result-score">相关度 {{ (item.score * 100).toFixed(0) }}%</span>
          </div>
          <div class="result-content">{{ item.content }}</div>
        </div>
      </div>

      <!-- AI 回答 -->
      <div v-if="searchMode === 'ask' && knowledgeStore.aiAnswer" class="ai-answer">
        <div class="answer-header">AI 回答</div>
        <div class="answer-content">{{ knowledgeStore.aiAnswer }}</div>
        <div v-if="uniqueAiSources.length" class="answer-sources">
          <div class="sources-title">参考来源（{{ uniqueAiSources.length }} 个文件）：</div>
          <div v-for="(s, idx) in uniqueAiSources" :key="idx" class="source-item">
            <el-tag size="small" type="info" effect="plain">[来源{{ idx + 1 }}] {{ s.filename }}</el-tag>
            <span class="source-score">相关度 {{ (s.score * 100).toFixed(0) }}%</span>
          </div>
        </div>
      </div>
    </el-card>

    <!-- 上传区域 -->
    <el-card class="upload-card">
      <div v-if="knowledgeStore.uploadingProgress" class="upload-progress-wrap">
        <div class="progress-info">
          <el-icon class="upload-icon-sm"><UploadFilled /></el-icon>
          <span class="progress-filename">{{ knowledgeStore.uploadingProgress.filename }}</span>
          <span class="progress-percent">{{ knowledgeStore.uploadingProgress.percent }}%</span>
        </div>
        <el-progress
          :percentage="knowledgeStore.uploadingProgress.percent"
          :stroke-width="10"
          :color="knowledgeStore.uploadingProgress.percent === 100 ? '#67c23a' : '#409eff'"
          striped
          striped-flow
        />
        <div class="progress-hint">上传完成后，后台将自动执行向量化</div>
      </div>
      <el-upload
        v-else
        drag
        multiple
        :auto-upload="false"
        :show-file-list="false"
        :on-change="handleFileSelect"
        accept=".pdf,.docx,.txt,.md,.ppt,.pptx,.json"
        class="upload-area"
      >
        <div class="upload-content">
          <el-icon class="upload-icon"><UploadFilled /></el-icon>
          <div class="upload-title">拖拽文件到此处，或点击选择文件</div>
          <div class="upload-hint">支持 PDF、DOCX、TXT、Markdown、PPT、JSON 格式</div>
        </div>
      </el-upload>
    </el-card>

    <!-- 文档列表 -->
    <el-card class="list-card">
      <template #header>
        <div class="list-header">
          <span>已上传文档</span>
          <el-tag v-if="knowledgeStore.documents.length" type="info" effect="plain" size="small">
            共 {{ knowledgeStore.documents.length }} 个
          </el-tag>
        </div>
      </template>

      <div v-if="!knowledgeStore.documents.length" class="empty-state">
        <div class="icon">📄</div>
        <p>暂无文档，请上传学习资料</p>
      </div>

      <div v-else class="document-grid">
        <div
          v-for="doc in knowledgeStore.documents"
          :key="doc.id"
          class="document-card"
        >
          <div class="doc-icon" :class="getDocIconClass(doc.file_type)">
            {{ getDocIcon(doc.file_type) }}
          </div>
          <div class="doc-info">
            <div class="doc-name">{{ doc.filename }}</div>
            <div class="doc-meta">
              <span>{{ formatFileSize(doc.file_size) }}</span>
              <span class="dot">·</span>
              <span>{{ doc.uploaded_at ? new Date(doc.uploaded_at).toLocaleDateString() : '' }}</span>
            </div>
          </div>
          <el-button
            type="danger"
            :icon="Delete"
            size="small"
            text
            @click="handleDelete(doc.id)"
          />
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { onActivated, ref, watch, computed } from 'vue'
import { Delete, Search, UploadFilled } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useKnowledgeStore } from '@/stores/knowledge'

const knowledgeStore = useKnowledgeStore()
const searchQuery = ref('')
const searching = ref(false)
const searchMode = ref('search')

// 搜索结果去重：同文件名只保留相关度最高的那条
const uniqueSearchResults = computed(() => {
  const seen = new Set<string>()
  return knowledgeStore.searchResults.filter(r => {
    if (!r.filename || seen.has(r.filename)) return false
    seen.add(r.filename)
    return true
  })
})

const searchFileCount = computed(() => uniqueSearchResults.value.length)

const uniqueAiSources = computed(() => {
  const seen = new Set<string>()
  return knowledgeStore.aiSources.filter(s => {
    if (!s.filename || seen.has(s.filename)) return false
    seen.add(s.filename)
    return true
  })
})

// 切换模式时清空结果
watch(searchMode, () => {
  knowledgeStore.searchResults = []
  knowledgeStore.clearAsk()
})

async function handleSearch() {
  if (!searchQuery.value.trim()) return
  searching.value = true
  try {
    await knowledgeStore.search(searchQuery.value.trim())
    if (!knowledgeStore.searchResults.length) {
      ElMessage.info('未找到相关内容')
    }
  } catch {
    ElMessage.error('搜索失败')
  } finally {
    searching.value = false
  }
}

async function handleAsk() {
  if (!searchQuery.value.trim()) return
  try {
    await knowledgeStore.ask(searchQuery.value.trim())
  } catch {
    ElMessage.error('AI 问答失败')
  }
}

function formatFileSize(bytes: number) {
  if (!bytes) return '未知大小'
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

function getDocIcon(type: string) {
  const icons: Record<string, string> = {
    pdf: 'PDF',
    docx: 'DOC',
    txt: 'TXT',
    md: 'MD',
    ppt: 'PPT',
    pptx: 'PPT',
    json: 'JSON',
  }
  return icons[type] || 'FILE'
}

function getDocIconClass(type: string) {
  const classes: Record<string, string> = {
    pdf: 'doc-pdf',
    docx: 'doc-word',
    md: 'doc-md',
    txt: 'doc-txt',
    ppt: 'doc-ppt',
    pptx: 'doc-ppt',
    json: 'doc-json',
  }
  return classes[type] || ''
}

async function handleFileSelect(file: any) {
  try {
    await knowledgeStore.upload(file.raw)
    ElMessage.success(`「${file.name}」上传成功（向量化将在后台执行）`)
  } catch (err: any) {
    ElMessage.error(err?.response?.data?.detail || '上传失败')
  }
}

async function handleDelete(id: number) {
  try {
    await ElMessageBox.confirm('确定要删除该文档吗？', '确认', {
      type: 'warning',
      confirmButtonText: '删除',
      cancelButtonText: '取消',
    })
    await knowledgeStore.deleteDocument(id)
    ElMessage.success('已删除')
  } catch {
    // 取消删除不做操作
  }
}

onActivated(() => {
  if (!knowledgeStore.documents.length) {
    knowledgeStore.fetchDocuments()
  }
})
</script>

<style scoped>
.knowledge-container {
  max-width: 800px;
}

/* 搜索 & AI 问答 */
.search-card {
  margin-bottom: 20px;
}

.search-tabs {
  margin-bottom: 12px;
}

.search-tabs :deep(.el-tabs__header) {
  margin-bottom: 0;
}

.search-bar {
  display: flex;
  gap: 12px;
}

.search-bar .el-input {
  flex: 1;
}

.search-results {
  margin-top: 16px;
  border-top: 1px solid #f0f0f0;
  padding-top: 16px;
}

.results-header {
  font-size: 13px;
  color: var(--color-text-secondary);
  margin-bottom: 12px;
}

.result-item {
  padding: 12px;
  border-radius: var(--radius-sm);
  background: #f8fafc;
  margin-bottom: 8px;
}

.result-item:last-child {
  margin-bottom: 0;
}

.result-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.result-score {
  font-size: 12px;
  color: var(--color-text-secondary);
}

.result-content {
  font-size: 13px;
  color: var(--color-text);
  line-height: 1.6;
}

/* AI 回答 */
.ai-answer {
  margin-top: 16px;
  border-top: 1px solid #f0f0f0;
  padding-top: 16px;
}

.answer-header {
  font-size: 13px;
  font-weight: 500;
  color: var(--color-primary);
  margin-bottom: 12px;
}

.answer-content {
  font-size: 14px;
  color: var(--color-text);
  line-height: 1.8;
  white-space: pre-wrap;
  background: #f8fafc;
  padding: 16px;
  border-radius: var(--radius-sm);
  border-left: 3px solid var(--color-primary);
}

.answer-sources {
  margin-top: 12px;
}

.sources-title {
  font-size: 12px;
  color: var(--color-text-secondary);
  margin-bottom: 8px;
}

.source-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 4px;
}

.source-score {
  font-size: 11px;
  color: var(--color-text-secondary);
}

/* 上传 */
.upload-card {
  margin-bottom: 20px;
}

.upload-area {
  width: 100%;
}

.upload-content {
  padding: 32px 0;
  text-align: center;
}

.upload-icon {
  font-size: 36px;
  color: var(--color-text-secondary);
  margin-bottom: 12px;
}

.upload-title {
  font-size: 15px;
  color: var(--color-text);
  margin-bottom: 8px;
}

.upload-hint {
  font-size: 12px;
  color: var(--color-text-secondary);
}

/* 上传进度 */
.upload-progress-wrap {
  padding: 24px 20px;
}

.progress-info {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
  font-size: 13px;
  color: var(--color-text);
}

.upload-icon-sm {
  font-size: 16px;
  color: var(--color-primary);
}

.progress-filename {
  flex: 1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.progress-percent {
  font-weight: 600;
  color: var(--color-primary);
}

.progress-hint {
  font-size: 12px;
  color: var(--color-text-secondary);
  margin-top: 8px;
}

/* 文档列表 */
.list-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 14px;
  font-weight: 500;
}

.document-grid {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.document-card {
  display: flex;
  align-items: center;
  padding: 12px 12px;
  border-radius: var(--radius-sm);
  transition: background 0.15s;
  gap: 12px;
}

.document-card:hover {
  background: #f8fafc;
}

.doc-icon {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-sm);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.5px;
  flex-shrink: 0;
}

.doc-pdf { background: #fee2e2; color: #dc2626; }
.doc-word { background: #dbeafe; color: #2563eb; }
.doc-md { background: #fef3c7; color: #d97706; }
.doc-txt { background: #f3e8ff; color: #9333ea; }
.doc-ppt { background: #fce7f3; color: #db2777; }
.doc-json { background: #d1fae5; color: #059669; }

.doc-info {
  flex: 1;
  min-width: 0;
}

.doc-name {
  font-size: 13px;
  font-weight: 500;
  color: var(--color-text-heading);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.doc-meta {
  font-size: 11px;
  color: var(--color-text-secondary);
  margin-top: 2px;
}

.dot {
  margin: 0 6px;
}
</style>
