import axios, { type AxiosResponse } from 'axios'
import { ElMessage } from 'element-plus'
import type { ApiResponse, PaginatedResponse, MediaItem, MediaDetail, ScanJob, AuthorRule } from '@/types'

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 30000,
})

api.interceptors.response.use(
  (response: AxiosResponse<ApiResponse<unknown>>) => {
    const data = response.data
    if (data.code && data.code !== 200) {
      ElMessage.error(data.message || '请求失败')
      return Promise.reject(new Error(data.message))
    }
    return data
  },
  (error) => {
    const message = error.response?.data?.detail || error.message || '网络错误'
    ElMessage.error(message)
    return Promise.reject(error)
  }
)

export default api

// Media API
export const mediaApi = {
  list: (params: Record<string, unknown>) =>
    api.get<any, ApiResponse<PaginatedResponse<MediaItem>>>('/media', { params }),
  get: (id: number) =>
    api.get<any, ApiResponse<MediaDetail>>(`/media/${id}`),
  update: (id: number, data: Record<string, unknown>) =>
    api.patch<any, ApiResponse<MediaDetail>>(`/media/${id}`, data),
  getCover: (id: number) => `/api/v1/media/${id}/cover`,
}

// Scan API
export const scanApi = {
  start: (data: { path: string; scan_type?: string; recursive?: boolean }) =>
    api.post<any, ApiResponse<ScanJob>>('/scan', data),
  getJob: (jobId: number) =>
    api.get<any, ApiResponse<ScanJob>>(`/scan/${jobId}`),
  listJobs: (params?: Record<string, unknown>) =>
    api.get<any, ApiResponse<PaginatedResponse<ScanJob>>>('/scan/jobs', { params }),
}

// Tags API
export const tagsApi = {
  list: (params?: Record<string, unknown>) => api.get('/tags', { params }),
  create: (data: { name: string; category?: string }) => api.post('/tags', data),
  addToMedia: (mediaId: number, tagIds: number[]) =>
    api.post(`/media/${mediaId}/tags`, { tag_ids: tagIds, source: 'user' }),
  removeFromMedia: (mediaId: number, tagId: number) =>
    api.delete(`/media/${mediaId}/tags/${tagId}`),
}

// Author Rules API
export const authorRulesApi = {
  list: (params?: Record<string, unknown>) =>
    api.get<any, ApiResponse<PaginatedResponse<AuthorRule>>>('/author-rules', { params }),
  create: (data: Record<string, unknown>) =>
    api.post<any, ApiResponse<AuthorRule>>('/author-rules', data),
  batchCreate: (rules: Record<string, unknown>[]) =>
    api.post('/author-rules/batch', { rules }),
  update: (id: number, data: Record<string, unknown>) =>
    api.patch(`/author-rules/${id}`, data),
  delete: (id: number) => api.delete(`/author-rules/${id}`),
  scanTest: (ruleId: number) =>
    api.post('/author-rules/scan-test', null, { params: { rule_id: ruleId } }),
  apply: (data: { rule_ids?: number[]; overwrite?: boolean }) =>
    api.post('/author-rules/apply', data),
}

// Rename API
export const renameApi = {
  preview: (data: { media_ids: number[]; pattern?: string }) =>
    api.post('/rename/preview', data),
  execute: (data: { media_ids: number[]; pattern?: string; move_cover?: boolean }) =>
    api.post('/rename/execute', data),
  rollback: (data: { media_ids: number[] }) =>
    api.post('/rename/rollback', data),
}

// Metadata API
export const metadataApi = {
  generate: (data: { media_ids: number[]; generate_nfo?: boolean; generate_covers?: boolean }) =>
    api.post('/metadata/generate', data),
  writeTags: (data: { media_ids: number[]; fields?: string[] }) =>
    api.post('/metadata/write-tags', data),
  aiAnalyze: (data: { media_ids: number[] }) =>
    api.post('/metadata/ai-analyze', data),
}

// Settings API
export const settingsApi = {
  get: () => api.get('/settings'),
  update: (data: Record<string, unknown>) => api.patch('/settings', data),
}
