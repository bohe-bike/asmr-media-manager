import axios, { type AxiosError, type AxiosRequestConfig, type AxiosResponse } from 'axios'
import { ElMessage } from 'element-plus'
import type { ApiResponse, PaginatedResponse, MediaItem, MediaDetail, ScanJob, AuthorRule } from '@/types'

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 30000,
})

type ApiClient = typeof api & {
  get<T = unknown, R = ApiResponse<T>>(url: string, config?: AxiosRequestConfig): Promise<R>
  post<T = unknown, R = ApiResponse<T>>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<R>
  patch<T = unknown, R = ApiResponse<T>>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<R>
  delete<T = unknown, R = ApiResponse<T>>(url: string, config?: AxiosRequestConfig): Promise<R>
}

api.interceptors.response.use(
  ((response: AxiosResponse<ApiResponse<unknown>>) => {
    const data = response.data
    if (data.code && data.code !== 200) {
      ElMessage.error(data.message || '请求失败')
      return Promise.reject(new Error(data.message))
    }
    return data
  }) as unknown as (response: AxiosResponse) => AxiosResponse,
  (error: AxiosError<{ detail?: string }>) => {
    const message = error.response?.data?.detail || error.message || '网络错误'
    ElMessage.error(message)
    return Promise.reject(error)
  }
)

const client = api as ApiClient

export default client

// Media API
export const mediaApi = {
  list: (params: Record<string, unknown>) =>
    client.get<PaginatedResponse<MediaItem>>('/media', { params }),
  get: (id: number) =>
    client.get<MediaDetail>(`/media/${id}`),
  update: (id: number, data: Record<string, unknown>) =>
    client.patch<MediaDetail>(`/media/${id}`, data),
  getCover: (id: number) => `/api/v1/media/${id}/cover`,
}

// Scan API
export const scanApi = {
  start: (data: { path: string; scan_type?: string; recursive?: boolean }) =>
    client.post<ScanJob>('/scan', data),
  getJob: (jobId: number) =>
    client.get<ScanJob>(`/scan/${jobId}`),
  listJobs: (params?: Record<string, unknown>) =>
    client.get<PaginatedResponse<ScanJob>>('/scan/jobs', { params }),
}

// Tags API
export const tagsApi = {
  list: (params?: Record<string, unknown>) => client.get('/tags', { params }),
  create: (data: { name: string; category?: string }) => client.post('/tags', data),
  addToMedia: (mediaId: number, tagIds: number[]) =>
    client.post(`/media/${mediaId}/tags`, { tag_ids: tagIds, source: 'user' }),
  removeFromMedia: (mediaId: number, tagId: number) =>
    client.delete(`/media/${mediaId}/tags/${tagId}`),
}

// Author Rules API
export const authorRulesApi = {
  list: (params?: Record<string, unknown>) =>
    client.get<PaginatedResponse<AuthorRule>>('/author-rules', { params }),
  create: (data: Record<string, unknown>) =>
    client.post<AuthorRule>('/author-rules', data),
  batchCreate: (rules: Record<string, unknown>[]) =>
    client.post('/author-rules/batch', { rules }),
  update: (id: number, data: Record<string, unknown>) =>
    client.patch(`/author-rules/${id}`, data),
  delete: (id: number) => client.delete(`/author-rules/${id}`),
  scanTest: (ruleId: number) =>
    client.post('/author-rules/scan-test', null, { params: { rule_id: ruleId } }),
  apply: (data: { rule_ids?: number[]; overwrite?: boolean }) =>
    client.post('/author-rules/apply', data),
}

// Rename API
export const renameApi = {
  preview: (data: { media_ids: number[]; pattern?: string }) =>
    client.post('/rename/preview', data),
  execute: (data: { media_ids: number[]; pattern?: string; move_cover?: boolean }) =>
    client.post('/rename/execute', data),
  rollback: (data: { media_ids: number[] }) =>
    client.post('/rename/rollback', data),
}

// Metadata API
export const metadataApi = {
  generate: (data: { media_ids: number[]; generate_nfo?: boolean; generate_covers?: boolean }) =>
    client.post('/metadata/generate', data),
  writeTags: (data: { media_ids: number[]; fields?: string[] }) =>
    client.post('/metadata/write-tags', data),
  aiAnalyze: (data: { media_ids: number[] }) =>
    client.post('/metadata/ai-analyze', data),
  fetchDlsite: (data: { media_ids: number[]; overwrite?: boolean }) =>
    client.post('/metadata/fetch-dlsite', data),
}

// Settings API
export const settingsApi = {
  get: () => client.get('/settings'),
  update: (data: Record<string, unknown>) => client.patch('/settings', data),
}
