import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import * as api from '@/api/course'

export const useDashboardStore = defineStore('dashboard', () => {
  const data = ref({
    total_chapters: 0,
    completed: 0,
    learning: 0,
    not_started: 0,
    percent: 0,
    detail: [] as { chapter_id: number; status: string }[],
  })
  const loading = ref(false)

  const percent = computed(() => data.value.percent)

  async function fetchDashboard(userId = 1) {
    loading.value = true
    try {
      const res = await api.getDashboard(userId)
      data.value = res.data
    } finally {
      loading.value = false
    }
  }

  async function updateProgress(chapterId: number, status: string, userId = 1) {
    await api.updateProgress(chapterId, status, userId)
    await fetchDashboard(userId)
  }

  async function reset(userId = 1) {
    await api.resetProgress(userId)
    await fetchDashboard(userId)
  }

  return { data, loading, percent, fetchDashboard, updateProgress, reset }
})
