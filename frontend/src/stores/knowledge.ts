import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Document, SearchResult } from '../api/knowledge'
import { uploadDocument as apiUpload, getDocuments as apiGetDocuments, deleteDocument as apiDeleteDocument, searchKnowledge as apiSearch, askKnowledge as apiAsk } from '../api/knowledge'

export const useKnowledgeStore = defineStore('knowledge', () => {
  const documents = ref<Document[]>([])
  const loading = ref(false)
  const searchResults = ref<SearchResult[]>([])
  const aiAnswer = ref('')
  const aiSources = ref<SearchResult[]>([])
  const aiLoading = ref(false)
  const uploadingProgress = ref<{ filename: string; percent: number } | null>(null)

  async function fetchDocuments() {
    loading.value = true
    try {
      const res = await apiGetDocuments()
      documents.value = res.data
    } finally {
      loading.value = false
    }
  }

  async function upload(file: File) {
    uploadingProgress.value = { filename: file.name, percent: 0 }
    try {
      const res = await apiUpload(file, (p) => {
        if (uploadingProgress.value) uploadingProgress.value.percent = p
      })
      documents.value.unshift(res.data)
      uploadingProgress.value = null
      return res.data
    } catch (e) {
      uploadingProgress.value = null
      throw e
    }
  }

  async function deleteDocument(id: number) {
    await apiDeleteDocument(id)
    documents.value = documents.value.filter((d) => d.id !== id)
  }

  async function search(query: string, k = 5) {
    const res = await apiSearch(query, k)
    searchResults.value = res.data.results
    return res.data
  }

  async function ask(query: string, k = 5) {
    aiLoading.value = true
    try {
      const res = await apiAsk(query, k)
      aiAnswer.value = res.data.answer
      aiSources.value = res.data.sources
      return res.data
    } finally {
      aiLoading.value = false
    }
  }

  function clearAsk() {
    aiAnswer.value = ''
    aiSources.value = []
  }

  return { documents, loading, searchResults, aiAnswer, aiSources, aiLoading, uploadingProgress, fetchDocuments, upload, deleteDocument, search, ask, clearAsk }
})
