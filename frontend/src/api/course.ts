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

export interface RefreshProgress {
  current: number
  total: number
  percent: number
  message: string
  result?: ChapterTreeNode[]
  error?: string
}

export function refreshOutline() {
  return request.post<ChapterTreeNode[]>('/api/course/outline/refresh')
}

export async function refreshOutlineStream(onProgress: (progress: RefreshProgress) => void): Promise<ChapterTreeNode[] | null> {
  const response = await fetch('http://127.0.0.1:8000/api/course/outline/refresh/stream', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
  })

  if (!response.ok) {
    const text = await response.text()
    throw new Error(text || '请求失败')
  }

  const reader = response.body?.getReader()
  if (!reader) {
    throw new Error('无法读取响应')
  }

  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    buffer += decoder.decode(value, { stream: true })

    const lines = buffer.split('\n\n')
    buffer = lines.pop() || ''

    for (const line of lines) {
      if (!line.startsWith('data: ')) continue

      const jsonStr = line.slice(6)
      try {
        const progress: RefreshProgress = JSON.parse(jsonStr)
        onProgress(progress)

        if (progress.percent === 100) {
          return progress.result || null
        }

        if (progress.error) {
          throw new Error(progress.error)
        }
      } catch (e: any) {
        throw new Error(e.message || '解析进度失败')
      }
    }
  }

  return null
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
