import { defineStore } from 'pinia'
import { ref } from 'vue'
import { settingsApi } from '@/api'

interface Settings {
  download_dir: string
  library_dir: string
  watch_enabled: boolean
  stable_seconds: number
  audio_rename_pattern: string
  video_rename_pattern: string
  supported_audio_formats: string[]
  supported_video_formats: string[]
  ai_enabled: boolean
  ai_api_url: string
  ai_api_key: string
  ai_model: string
  ocr_enabled: boolean
  cover_filenames: string[]
  unclassified_dir: string
}

export const useSettingsStore = defineStore('settings', () => {
  const settings = ref<Settings | null>(null)
  const loading = ref(false)

  async function fetchSettings() {
    loading.value = true
    try {
      const res: any = await settingsApi.get()
      settings.value = res.data
    } finally {
      loading.value = false
    }
  }

  async function updateSettings(data: Partial<Settings>) {
    const res: any = await settingsApi.update(data)
    settings.value = res.data
    return res.data
  }

  return {
    settings,
    loading,
    fetchSettings,
    updateSettings,
  }
})
