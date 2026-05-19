import { defineStore } from 'pinia'
import { ref } from 'vue'
import { mediaApi } from '@/api'
import type { MediaItem, MediaDetail, PaginatedResponse } from '@/types'

export const useMediaStore = defineStore('media', () => {
  const items = ref<MediaItem[]>([])
  const total = ref(0)
  const page = ref(1)
  const pageSize = ref(20)
  const loading = ref(false)
  const currentMedia = ref<MediaDetail | null>(null)

  async function fetchMedia(params: Record<string, any> = {}) {
    loading.value = true
    try {
      const res: any = await mediaApi.list({
        page: page.value,
        page_size: pageSize.value,
        ...params,
      })
      items.value = res.data.items
      total.value = res.data.total
    } finally {
      loading.value = false
    }
  }

  async function fetchMediaDetail(id: number) {
    loading.value = true
    try {
      const res: any = await mediaApi.get(id)
      currentMedia.value = res.data
      return res.data
    } finally {
      loading.value = false
    }
  }

  async function updateMedia(id: number, data: Record<string, any>) {
    const res: any = await mediaApi.update(id, data)
    if (currentMedia.value?.id === id) {
      currentMedia.value = { ...currentMedia.value, ...res.data }
    }
    return res.data
  }

  function setPage(p: number) {
    page.value = p
  }

  return {
    items,
    total,
    page,
    pageSize,
    loading,
    currentMedia,
    fetchMedia,
    fetchMediaDetail,
    updateMedia,
    setPage,
  }
})
