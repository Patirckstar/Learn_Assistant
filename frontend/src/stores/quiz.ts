import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { QuestionOut, ExamResult, ExamHistory, Paper, PaperExamData } from '@/api/quiz'
import * as api from '@/api/quiz'

export const useQuizStore = defineStore('quiz', () => {
  const papers = ref<Paper[]>([])
  const questions = ref<QuestionOut[]>([])
  const currentPaper = ref<PaperExamData | null>(null)
  const result = ref<ExamResult | null>(null)
  const exams = ref<ExamHistory[]>([])
  const loading = ref(false)
  const refreshing = ref(false)

  async function fetchPapers() {
    const res = await api.getPapers()
    papers.value = res.data
    return res.data
  }

  async function refreshPapers(callback?: (progress: number, message: string) => void) {
    refreshing.value = true
    try {
      const response = await api.refreshPapers()
      const reader = response.body?.getReader()
      if (!reader) return

      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const dataStr = line.substring(6).trim()
            try {
              const data = JSON.parse(dataStr)
              if (data.progress !== undefined && callback) {
                callback(data.progress, data.message)
              }
              if (data.status === 'completed') {
                await fetchPapers()
              }
              if (data.status === 'error') {
                throw new Error(data.message || '刷新失败')
              }
            } catch (e) {
              console.error('解析进度数据失败:', e)
            }
          }
        }
      }
    } finally {
      refreshing.value = false
    }
  }

  async function startExam(paperId: number) {
    loading.value = true
    try {
      const res = await api.getPaperExamQuestions(paperId)
      currentPaper.value = res.data
      questions.value = res.data.questions
      result.value = null
      return res.data
    } finally {
      loading.value = false
    }
  }

  async function submit(
    paperId: number,
    answers: { question_id: number; user_answer: string }[],
    timeUsed?: number,
  ) {
    loading.value = true
    try {
      const res = await api.submitPaperExam(paperId, answers, timeUsed)
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
    currentPaper.value = null
    questions.value = []
  }

  return { papers, questions, currentPaper, result, exams, loading, refreshing, fetchPapers, refreshPapers, startExam, submit, fetchExams, fetchExamDetail, clearResult }
})