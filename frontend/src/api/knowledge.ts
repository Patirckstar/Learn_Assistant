import request from './request'

export interface Document {
  id: number
  filename: string
  file_type: string
  file_size: number | null
  chunk_count: number
  uploaded_at: string
}

export interface SearchResult {
  content: string
  score: number
  file_id: number | null
  filename: string | null
  chunk_index: number | null
}

export interface KnowledgeSearchResponse {
  query: string
  results: SearchResult[]
}

export interface KnowledgeAskResponse {
  query: string
  answer: string
  sources: SearchResult[]
}

export function uploadDocument(file: File, onProgress?: (percent: number) => void) {
  const form = new FormData()
  form.append('file', file)
  return request.post<Document>('/api/knowledge/upload', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
    onUploadProgress(e) {
      if (onProgress && e.total) {
        onProgress(Math.round((e.loaded / e.total) * 100))
      }
    },
  })
}

export function getDocuments() {
  return request.get<Document[]>('/api/knowledge/documents')
}

export function deleteDocument(id: number) {
  return request.delete(`/api/knowledge/documents/${id}`)
}

export function searchKnowledge(query: string, k = 5) {
  return request.get<KnowledgeSearchResponse>('/api/knowledge/search', {
    params: { query, k },
  })
}

export function askKnowledge(query: string, k = 5) {
  return request.get<KnowledgeAskResponse>('/api/knowledge/ask', {
    params: { query, k },
  })
}
