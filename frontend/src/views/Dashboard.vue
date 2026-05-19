<template>
  <div class="dashboard">
    <div class="page-header">
      <div>
        <h1>仪表盘</h1>
        <p class="subtitle">ASMR 媒体整理中心概览</p>
      </div>
      <el-button type="primary" :icon="Refresh" @click="refresh">刷新</el-button>
    </div>

    <el-row :gutter="20" class="stats-row">
      <el-col :span="6">
        <div class="stat-card stat-total">
          <div class="stat-icon">
            <el-icon :size="32"><Files /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.totalMedia }}</div>
            <div class="stat-label">媒体总数</div>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card stat-audio">
          <div class="stat-icon">
            <el-icon :size="32"><Headset /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.audioCount }}</div>
            <div class="stat-label">音频文件</div>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card stat-video">
          <div class="stat-icon">
            <el-icon :size="32"><VideoCamera /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.videoCount }}</div>
            <div class="stat-label">视频文件</div>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card stat-classified">
          <div class="stat-icon">
            <el-icon :size="32"><CircleCheck /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.classified }}</div>
            <div class="stat-label">已分类</div>
          </div>
        </div>
      </el-col>
    </el-row>

    <el-row :gutter="20">
      <el-col :span="12">
        <el-card class="scan-card">
          <template #header>
            <div class="card-header">
              <el-icon><Search /></el-icon>
              <span>快速扫描</span>
            </div>
          </template>
          <el-form @submit.prevent="handleScan" label-position="top">
            <el-form-item label="扫描路径">
              <el-input
                v-model="scanPath"
                placeholder="/media/downloads"
                :prefix-icon="FolderOpened"
                size="large"
              />
            </el-form-item>
            <el-form-item label="扫描类型">
              <el-radio-group v-model="scanType" size="large">
                <el-radio-button value="full">全量扫描</el-radio-button>
                <el-radio-button value="incremental">增量扫描</el-radio-button>
              </el-radio-group>
            </el-form-item>
            <el-button
              type="primary"
              size="large"
              @click="handleScan"
              :loading="scanning"
              style="width: 100%"
            >
              <el-icon><Search /></el-icon>
              开始扫描
            </el-button>
          </el-form>
          <div v-if="scanResult" class="scan-result">
            <el-descriptions :column="2" border size="small">
              <el-descriptions-item label="状态">
                <el-tag :type="scanResult.status === 'completed' ? 'success' : 'warning'" size="small">
                  {{ scanResult.status }}
                </el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="总文件">{{ scanResult.total_files }}</el-descriptions-item>
              <el-descriptions-item label="新文件">
                <el-tag type="success" size="small">{{ scanResult.new_files }}</el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="错误">
                <el-tag :type="scanResult.error_files > 0 ? 'danger' : 'info'" size="small">
                  {{ scanResult.error_files }}
                </el-tag>
              </el-descriptions-item>
            </el-descriptions>
          </div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card class="history-card">
          <template #header>
            <div class="card-header">
              <el-icon><Clock /></el-icon>
              <span>最近扫描</span>
            </div>
          </template>
          <div v-if="recentJobs.length === 0" class="empty-state">
            <el-icon :size="48" color="#c0c4cc"><Clock /></el-icon>
            <p>暂无扫描记录</p>
          </div>
          <div v-else class="job-list">
            <div v-for="job in recentJobs" :key="job.id" class="job-item">
              <div class="job-info">
                <div class="job-path">{{ job.scan_path }}</div>
                <div class="job-meta">{{ formatTime(job.created_at) }}</div>
              </div>
              <el-tag
                :type="job.status === 'completed' ? 'success' : job.status === 'running' ? 'warning' : 'info'"
                size="small"
                effect="light"
              >
                {{ job.status === 'completed' ? '完成' : job.status === 'running' ? '运行中' : job.status }}
              </el-tag>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Refresh, FolderOpened, Search, Clock, Files, Headset, VideoCamera, CircleCheck } from '@element-plus/icons-vue'
import { mediaApi, scanApi } from '@/api'
import { useScanStore } from '@/stores/scan'
import type { ScanJob } from '@/types'

const scanStore = useScanStore()
const scanPath = ref('')
const scanType = ref('full')
const scanning = ref(false)
const scanResult = ref<ScanJob | null>(null)
const recentJobs = ref<ScanJob[]>([])

const stats = ref({
  totalMedia: 0,
  audioCount: 0,
  videoCount: 0,
  classified: 0,
})

onMounted(() => {
  refresh()
})

async function refresh() {
  try {
    const res: any = await mediaApi.list({ page_size: 1 })
    stats.value.totalMedia = res.data.total
  } catch {}

  try {
    const res: any = await scanApi.listJobs({ page_size: 5 })
    recentJobs.value = res.data.items
  } catch {}
}

async function handleScan() {
  if (!scanPath.value) return
  scanning.value = true
  try {
    const result = await scanStore.startScan(scanPath.value, scanType.value)
    scanResult.value = result
    refresh()
  } finally {
    scanning.value = false
  }
}

function formatTime(t: string) {
  return new Date(t).toLocaleString()
}
</script>

<style scoped>
.dashboard {
  max-width: 1400px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
}

.page-header h1 {
  font-size: 28px;
  font-weight: 700;
  color: #1a1a2e;
  margin: 0;
}

.subtitle {
  color: #909399;
  margin-top: 4px;
  font-size: 14px;
}

.stats-row {
  margin-bottom: 24px;
}

.stat-card {
  background: #fff;
  border-radius: 16px;
  padding: 24px;
  display: flex;
  align-items: center;
  gap: 16px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
  transition: transform 0.3s, box-shadow 0.3s;
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
}

.stat-icon {
  width: 64px;
  height: 64px;
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
}

.stat-total .stat-icon {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.stat-audio .stat-icon {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
}

.stat-video .stat-icon {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
}

.stat-classified .stat-icon {
  background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
}

.stat-value {
  font-size: 32px;
  font-weight: 700;
  color: #1a1a2e;
  line-height: 1;
}

.stat-label {
  font-size: 14px;
  color: #909399;
  margin-top: 4px;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
}

.scan-result {
  margin-top: 20px;
}

.empty-state {
  text-align: center;
  padding: 40px 0;
  color: #c0c4cc;
}

.empty-state p {
  margin-top: 12px;
  font-size: 14px;
}

.job-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.job-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: #fafbfc;
  border-radius: 10px;
  transition: background 0.2s;
}

.job-item:hover {
  background: #f0f2f5;
}

.job-path {
  font-weight: 500;
  color: #303133;
  font-size: 14px;
}

.job-meta {
  font-size: 12px;
  color: #909399;
  margin-top: 2px;
}
</style>
