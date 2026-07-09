import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Document, SearchResult } from '../api/knowledge'
import { uploadDocument as apiUpload, getDocuments as apiGetDocuments, deleteDocument as apiDeleteDocument, searchKnowledge as apiSearch } from '../api/knowledge'

export const useKnowledgeStore = defineStore('knowledge', () => {
  const documents = ref<Document[]>([])
  const loading = ref(false)
  const searchResults = ref<SearchResult[]>([])

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
    const res = await apiUpload(file)
    documents.value.unshift(res.data)
    return res.data
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

  return { documents, loading, searchResults, fetchDocuments, upload, deleteDocument, search }
})
