<template>
  <div class="knowledge-container">
    <div class="page-header">
      <div>
        <h2>知识库</h2>
        <div class="subtitle">上传和管理学习资料文档</div>
      </div>
    </div>

    <!-- 上传区域 -->
    <el-card class="upload-card">
      <el-upload
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
import { onMounted } from 'vue'
import { Delete, UploadFilled } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useKnowledgeStore } from '@/stores/knowledge'

const knowledgeStore = useKnowledgeStore()

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

onMounted(() => {
  knowledgeStore.fetchDocuments()
})
</script>

<style scoped>
.knowledge-container {
  max-width: 800px;
}

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
