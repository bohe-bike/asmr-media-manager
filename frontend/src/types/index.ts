export interface Tag {
  id: number
  name: string
  source?: string
}

export interface MediaItem {
  id: number
  file_name: string
  media_type: 'audio' | 'video'
  title?: string
  rj_id?: string
  cv?: string
  circle?: string
  creator?: string
  platform?: string
  duration?: number
  format: string
  file_size: number
  status: string
  tags: Tag[]
  cover_url?: string
  created_at: string
}

export interface MediaDetail extends MediaItem {
  file_path: string
  file_hash: string
  bitrate?: number
  sample_rate?: number
  channels?: number
  width?: number
  height?: number
  dl_id?: string
  language?: string
  cover_path?: string
  plex_ready: boolean
  error_message?: string
  updated_at: string
  scanned_at?: string
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}

export interface ApiResponse<T> {
  code: number
  message: string
  data: T
}

export interface ScanJob {
  id: number
  scan_path: string
  status: string
  scan_type: string
  total_files: number
  processed_files: number
  new_files: number
  error_files: number
  started_at?: string
  finished_at?: string
  created_at: string
  progress_percent: number
}

export interface AuthorRule {
  id: number
  keyword: string
  match_type: string
  match_target: string
  creator?: string
  circle?: string
  cv?: string
  priority: number
  enabled: boolean
  hit_count: number
  last_hit_at?: string
  created_at: string
  updated_at: string
}

export interface RenamePreviewItem {
  media_id: number
  old_path: string
  new_path: string
  new_dir?: string
  conflict: boolean
}
