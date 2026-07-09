import request from '@/api/request'

export interface QuestionOption {
  key: string
  text: string
}

export interface QuestionOut {
  id: number
  chapter_id: number | null
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
  options: QuestionOption[]
  user_answer: string | null
  correct_answer: string
  is_correct: boolean
  explanation: string | null
  score: number
}

export interface ExamResult {
  exam_id: number
  total_score: number
  score: number
  time_used: number | null
  details: ExamDetail[]
  created_at: string
}

export interface ExamHistory {
  id: number
  chapter_id: number | null
  chapter_title: string | null
  total_score: number
  score: number
  time_used: number | null
  created_at: string
}

export function generateQuestions(chapterId: number, count = 5, difficulty = 'medium') {
  return request.post<QuestionOut[]>('/api/quiz/generate', { chapter_id: chapterId, count, difficulty })
}

export function getQuestions(chapterId: number) {
  return request.get<QuestionOut[]>(`/api/quiz/questions/${chapterId}`)
}

export function getExamQuestions(chapterId: number, count = 5) {
  return request.get<QuestionOut[]>(`/api/quiz/questions/${chapterId}/exam`, { params: { count } })
}

export function submitExam(
  chapterId: number,
  questionIds: number[],
  answers: ExamAnswer[],
  timeUsed?: number,
  userId = 1,
) {
  return request.post<ExamResult>('/api/quiz/submit', {
    chapter_id: chapterId,
    question_ids: questionIds,
    answers,
    time_used: timeUsed,
  }, { params: { user_id: userId } })
}

export function getExams(userId = 1, chapterId?: number) {
  return request.get<ExamHistory[]>('/api/quiz/exams', { params: { user_id: userId, chapter_id: chapterId } })
}

export function getExamDetail(examId: number) {
  return request.get<ExamResult>(`/api/quiz/exams/${examId}`)
}
