import { defineStore } from 'pinia'
import { ref } from 'vue'
import * as api from '@/api/course'
import type { ChapterTreeNode, ChapterOut } from '@/api/course'

export const useCourseStore = defineStore('course', () => {
  const outlineTree = ref<ChapterTreeNode[]>([])
  const currentChapter = ref<ChapterOut | null>(null)
  const loading = ref(false)

  async function generateOutline() {
    loading.value = true
    try {
      const res = await api.generateOutline()
      outlineTree.value = res.data
    } catch (e: any) {
      const msg = e?.response?.data?.detail || '生成失败，请确保 Ollama 服务运行中且知识库已上传文档'
      throw new Error(msg)
    } finally {
      loading.value = false
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
    generateOutline,
    fetchOutline,
    loadChapter,
    regenerateChapter,
  }
})
