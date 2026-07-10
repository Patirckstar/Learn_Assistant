import request from '@/api/request'

export interface QuestionOption {
  key: string
  text: string
}

export interface QuestionOut {
  id: number
  chapter_id: number | null
  parent_chapter_id: number | null
  type: string
  difficulty: string
  stem: string
  options: QuestionOption[]
  answer?: string
  explanation?: string
  created_at: string
}

export interface ExamAnswer {
  question_id: number
  user_answer: string
}

export interface ExamDetail {
  question_id: number
  stem: string
  type: string
  difficulty: string
  options: QuestionOption[]
  user_answer: string | null
  correct_answer: string
  is_correct: boolean
  explanation: string | null
  score: number
}

export interface ExamResult {
  exam_id: number
  paper_id: number
  paper_title: string
  total_score: number
  score: number
  time_limit: number
  time_used: number | null
  feedback: string
  details: ExamDetail[]
  created_at: string
}

export interface ExamHistory {
  id: number
  chapter_id: number | null
  chapter_title: string | null
  total_score: number
  score: number
  time_limit: number
  time_used: number | null
  created_at: string
}

export interface Paper {
  id: number
  chapter_id: number
  chapter_title: string
  title: string
  description: string
  question_count: number
  time_limit: number
  is_ready: boolean
  created_at: string
  updated_at: string
}

export interface PaperExamData {
  paper_id: number
  paper_title: string
  time_limit: number
  question_count: number
  questions: QuestionOut[]
}

export function getPapers() {
  return request.get<Paper[]>('/api/quiz/papers')
}

export function getPaper(paperId: number) {
  return request.get<Paper>(`/api/quiz/papers/${paperId}`)
}

export function refreshPapers() {
  return fetch('/api/quiz/papers/refresh', { method: 'POST' })
}

export function getPaperExamQuestions(paperId: number) {
  return request.get<PaperExamData>(`/api/quiz/papers/${paperId}/exam`)
}

export function submitPaperExam(
  paperId: number,
  answers: ExamAnswer[],
  timeUsed?: number,
) {
  return request.post<ExamResult>(`/api/quiz/papers/${paperId}/submit`, answers, {
    params: { time_used: timeUsed },
  })
}

export function getExams(chapterId?: number) {
  return request.get<ExamHistory[]>('/api/quiz/exams', { params: { chapter_id: chapterId } })
}

export function getExamDetail(examId: number) {
  return request.get<ExamResult>(`/api/quiz/exams/${examId}`)
}
