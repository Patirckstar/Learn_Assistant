import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { WrongQuestion, PracticeQuestion, PracticeResult, WrongStats } from '@/api/wrongbook'
import * as api from '@/api/wrongbook'

export const useWrongBookStore = defineStore('wrongbook', () => {
  const wrongQuestions = ref<WrongQuestion[]>([])
  const practiceQuestions = ref<PracticeQuestion[]>([])
  const practiceResult = ref<PracticeResult | null>(null)
  const stats = ref<WrongStats | null>(null)
  const loading = ref(false)

  async function fetchWrongQuestions(chapterId?: number) {
    loading.value = true
    try {
      const res = await api.getWrongQuestions(chapterId)
      wrongQuestions.value = res.data
      return res.data
    } finally {
      loading.value = false
    }
  }

  async function fetchPracticeQuestions(count = 10) {
    loading.value = true
    try {
      const res = await api.getPracticeQuestions(count)
      practiceQuestions.value = res.data
      return res.data
    } finally {
      loading.value = false
    }
  }

  async function submitPractice(answers: { wrongbook_id: number; user_answer: string }[]) {
    loading.value = true
    try {
      const res = await api.submitPractice(answers)
      practiceResult.value = res.data
      return res.data
    } finally {
      loading.value = false
    }
  }

  async function fetchStats() {
    const res = await api.getWrongStats()
    stats.value = res.data
    return res.data
  }

  function clearResult() {
    practiceResult.value = null
  }

  return { wrongQuestions, practiceQuestions, practiceResult, stats, loading, fetchWrongQuestions, fetchPracticeQuestions, submitPractice, fetchStats, clearResult }
})
