import request from '@/api/request'

export interface ChapterOut {
  id: number
  parent_id: number | null
  title: string
  level: number
  sort_order: number
  content: string | null
  created_at: string
}

export interface ChapterTreeNode {
  id: number
  title: string
  level: number
  sort_order: number
  children: ChapterTreeNode[]
}

export function generateOutline() {
  return request.post<ChapterTreeNode[]>('/api/course/outline/generate')
}

export function getOutline() {
  return request.get<ChapterTreeNode[]>('/api/course/outline')
}

export function getChapter(id: number) {
  return request.get<ChapterOut>(`/api/course/chapters/${id}`)
}

export function regenerateChapter(id: number) {
  return request.post<{ content: string }>(`/api/course/chapters/${id}/regenerate`)
}

export function getProgress(userId = 1) {
  return request.get('/api/course/progress', { params: { user_id: userId } })
}

export function updateProgress(chapterId: number, status: string, userId = 1) {
  return request.put(`/api/course/progress/${chapterId}`, null, { params: { status, user_id: userId } })
}

export function getDashboard(userId = 1) {
  return request.get('/api/course/dashboard', { params: { user_id: userId } })
}

export function resetProgress(userId = 1) {
  return request.post('/api/course/progress/reset', null, { params: { user_id: userId } })
}
