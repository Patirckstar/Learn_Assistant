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
      outlineTree.value = await api.generateOutline()
    } finally {
      loading.value = false
    }
  }

  async function fetchOutline() {
    loading.value = true
    try {
      outlineTree.value = await api.getOutline()
    } finally {
      loading.value = false
    }
  }

  async function loadChapter(id: number) {
    currentChapter.value = await api.getChapter(id)
  }

  async function regenerateChapter(id: number) {
    const result = await api.regenerateChapter(id)
    if (currentChapter.value && currentChapter.value.id === id) {
      currentChapter.value.content = result.content
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
