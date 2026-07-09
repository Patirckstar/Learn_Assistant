import { defineStore } from 'pinia'
import { ref } from 'vue'
import * as api from '@/api/course'
import type { ChapterTreeNode, ChapterOut, RefreshProgress } from '@/api/course'

export const useCourseStore = defineStore('course', () => {
  const outlineTree = ref<ChapterTreeNode[]>([])
  const currentChapter = ref<ChapterOut | null>(null)
  const loading = ref(false)

  const refreshProgress = ref<RefreshProgress | null>(null)
  const refreshStreaming = ref(false)

  async function refreshOutline() {
    loading.value = true
    try {
      const res = await api.refreshOutline()
      outlineTree.value = res.data
    } catch (e: any) {
      const msg = e?.response?.data?.detail || '刷新失败，请确保知识库已上传文档'
      throw new Error(msg)
    } finally {
      loading.value = false
    }
  }

  async function refreshOutlineWithProgress() {
    refreshStreaming.value = true
    refreshProgress.value = null

    try {
      const result = await api.refreshOutlineStream((progress) => {
        refreshProgress.value = progress
      })

      if (result) {
        outlineTree.value = result
      }
    } catch (e: any) {
      const msg = e?.response?.data?.detail || e.message || '刷新失败'
      if (refreshProgress.value) {
        refreshProgress.value.message = msg
      }
      throw new Error(msg)
    } finally {
      refreshStreaming.value = false
    }
  }

  async function fetchOutline() {
    loading.value = true
    try {
      const res = await api.getOutline()
      outlineTree.value = res.data
    } finally {
      loading.value = false
    }
  }

  async function loadChapter(id: number) {
    const res = await api.getChapter(id)
    currentChapter.value = res.data
  }

  async function regenerateChapter(id: number) {
    const result = await api.regenerateChapter(id)
    if (currentChapter.value && currentChapter.value.id === id) {
      currentChapter.value.content = result.data.content
    }
  }

  return {
    outlineTree,
    currentChapter,
    loading,
    refreshProgress,
    refreshStreaming,
    refreshOutline,
    refreshOutlineWithProgress,
    fetchOutline,
    loadChapter,
    regenerateChapter,
  }
})
