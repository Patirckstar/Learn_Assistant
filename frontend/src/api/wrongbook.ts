import request from '@/api/request'
import type { QuestionOption } from '@/api/quiz'

export interface WrongQuestion {
  id: number
  question_id: number
  chapter_id: number | null
  chapter_title: string | null
  type: string
  difficulty: string
  stem: string
  options: QuestionOption[]
  answer: string
  explanation: string | null
  wrong_count: number
  correct_count: number
  last_wrong_at: string | null
  last_practiced_at: string | null
}

export interface PracticeQuestion {
  wrongbook_id: number
  question_id: number
  chapter_id: number | null
  type: string
  difficulty: string
  stem: string
  options: QuestionOption[]
}

export interface PracticeResult {
  total: number
  correct: number
  score: number
}

export interface WrongStats {
  total_wrong_questions: number
  total_wrong_times: number
  total_correct_times: number
  total_practice_attempts: number
  correct_rate: number
  by_chapter: { chapter_id: number; chapter_title: string; count: number }[]
}

export function getWrongQuestions(chapterId?: number, userId = 1) {
  return request.get<WrongQuestion[]>('/api/wrongbook', { params: { user_id: userId, chapter_id: chapterId } })
}

export function getPracticeQuestions(count = 10, userId = 1) {
  return request.get<PracticeQuestion[]>('/api/wrongbook/practice', { params: { user_id: userId, count } })
}

export function submitPractice(answers: { wrongbook_id: number; user_answer: string }[], userId = 1) {
  return request.post<PracticeResult>('/api/wrongbook/practice/submit', { answers }, { params: { user_id: userId } })
}

export function getWrongStats(userId = 1) {
  return request.get<WrongStats>('/api/wrongbook/stats', { params: { user_id: userId } })
}
