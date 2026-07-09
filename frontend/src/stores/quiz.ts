import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { QuestionOut, ExamResult, ExamHistory } from '@/api/quiz'
import * as api from '@/api/quiz'

export const useQuizStore = defineStore('quiz', () => {
  const questions = ref<QuestionOut[]>([])
  const result = ref<ExamResult | null>(null)
  const exams = ref<ExamHistory[]>([])
  const loading = ref(false)
  const generating = ref(false)

  async function generate(chapterId: number, count = 5, difficulty = 'medium') {
    generating.value = true
    try {
      const res = await api.generateQuestions(chapterId, count, difficulty)
      questions.value = res.data
      return res.data
    } finally {
      generating.value = false
    }
  }

  async function fetchQuestions(chapterId: number, count = 5) {
    loading.value = true
    try {
      const res = await api.getExamQuestions(chapterId, count)
      questions.value = res.data
      return res.data
    } finally {
      loading.value = false
    }
  }

  async function submit(
    chapterId: number,
    questionIds: number[],
    answers: { question_id: number; user_answer: string }[],
    timeLimit = 0,
    timeUsed?: number,
  ) {
    loading.value = true
    try {
      const res = await api.submitExam(chapterId, questionIds, answers, timeLimit, timeUsed)
      result.value = res.data
      return res.data
    } finally {
      loading.value = false
    }
  }

  async function fetchExams(chapterId?: number) {
    const res = await api.getExams(1, chapterId)
    exams.value = res.data
    return res.data
  }

  async function fetchExamDetail(examId: number) {
    const res = await api.getExamDetail(examId)
    result.value = res.data
    return res.data
  }

  function clearResult() {
    result.value = null
  }

  return { questions, result, exams, loading, generating, generate, fetchQuestions, submit, fetchExams, fetchExamDetail, clearResult }
})
