import { defineStore } from 'pinia'
import { ref } from 'vue'
import { scanApi } from '@/api'
import type { ScanJob } from '@/types'

export const useScanStore = defineStore('scan', () => {
  const jobs = ref<ScanJob[]>([])
  const currentJob = ref<ScanJob | null>(null)
  const loading = ref(false)

  async function startScan(path: string, scanType: string = 'full', organize: boolean = false) {
    loading.value = true
    try {
      const res: any = await scanApi.start({ path, scan_type: scanType, organize })
      currentJob.value = res.data
      return res.data
    } finally {
      loading.value = false
    }
  }

  async function fetchJob(jobId: number) {
    const res: any = await scanApi.getJob(jobId)
    currentJob.value = res.data
    return res.data
  }

  async function fetchJobs() {
    loading.value = true
    try {
      const res: any = await scanApi.listJobs()
      jobs.value = res.data.items
    } finally {
      loading.value = false
    }
  }

  return {
    jobs,
    currentJob,
    loading,
    startScan,
    fetchJob,
    fetchJobs,
  }
})
