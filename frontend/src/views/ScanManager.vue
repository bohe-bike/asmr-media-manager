<template>
  <div class="scan-manager">
    <div class="page-header">
      <div>
        <h1>扫描管理</h1>
        <p class="subtitle">扫描目录并导入媒体文件</p>
      </div>
    </div>

    <el-card class="mb-20">
      <template #header>
        <div class="card-header">
          <el-icon><Search /></el-icon>
          <span>启动扫描</span>
        </div>
      </template>
      <el-form @submit.prevent="handleScan" label-position="top">
        <el-row :gutter="20">
          <el-col :span="14">
            <el-form-item label="扫描路径">
              <el-input v-model="scanPath" placeholder="/media/downloads" size="large" :prefix-icon="FolderOpened" />
            </el-form-item>
          </el-col>
          <el-col :span="4">
            <el-form-item label="扫描类型">
              <el-radio-group v-model="scanType" size="large">
                <el-radio-button value="full">全量</el-radio-button>
                <el-radio-button value="incremental">增量</el-radio-button>
              </el-radio-group>
            </el-form-item>
          </el-col>
          <el-col :span="4">
            <el-form-item label=" ">
              <el-checkbox v-model="autoOrganize" size="large">扫描后自动整理</el-checkbox>
            </el-form-item>
          </el-col>
          <el-col :span="3">
            <el-form-item label=" ">
              <el-button type="primary" size="large" @click="handleScan" :loading="scanning" style="width: 100%">
                <el-icon><Search /></el-icon> 开始扫描
              </el-button>
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
    </el-card>

    <el-card v-if="currentJob" class="mb-20 progress-card">
      <template #header>
        <div class="card-header">
          <el-icon v-if="currentJob.status === 'running'" class="spinning"><Loading /></el-icon>
          <el-icon v-else><CircleCheck /></el-icon>
          <span>扫描进度</span>
          <el-tag :type="jobStatusType(currentJob.status)" size="small" effect="light" style="margin-left: auto">
            {{ jobStatusLabel(currentJob.status) }}
          </el-tag>
        </div>
      </template>
      <el-row :gutter="20" class="progress-stats">
        <el-col :span="5">
          <div class="progress-stat">
            <div class="progress-stat-value">{{ currentJob.total_files }}</div>
            <div class="progress-stat-label">总文件</div>
          </div>
        </el-col>
        <el-col :span="5">
          <div class="progress-stat">
            <div class="progress-stat-value primary">{{ currentJob.processed_files }}</div>
            <div class="progress-stat-label">已处理</div>
          </div>
        </el-col>
        <el-col :span="5">
          <div class="progress-stat">
            <div class="progress-stat-value success">{{ currentJob.new_files }}</div>
            <div class="progress-stat-label">新文件</div>
          </div>
        </el-col>
        <el-col :span="4">
          <div class="progress-stat">
            <div class="progress-stat-value" style="color: #e6a23c">{{ currentJob.organized_files || 0 }}</div>
            <div class="progress-stat-label">已整理</div>
          </div>
        </el-col>
        <el-col :span="5">
          <div class="progress-stat">
            <div class="progress-stat-value danger">{{ currentJob.error_files }}</div>
            <div class="progress-stat-label">错误</div>
          </div>
        </el-col>
      </el-row>
      <el-progress
        :percentage="Math.round(currentJob.progress_percent)"
        :status="currentJob.status === 'completed' ? 'success' : undefined"
        :stroke-width="12"
        style="margin-top: 16px"
      />
    </el-card>

    <el-card>
      <template #header>
        <div class="card-header">
          <el-icon><Clock /></el-icon>
          <span>扫描历史</span>
        </div>
      </template>
      <el-table :data="jobs" v-loading="loading" stripe>
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="scan_path" label="扫描路径" min-width="200" show-overflow-tooltip />
        <el-table-column prop="scan_type" label="类型" width="90">
          <template #default="{ row }">
            <el-tag :type="row.scan_type === 'full' ? 'primary' : 'info'" size="small" effect="plain">
              {{ row.scan_type === 'full' ? '全量' : '增量' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="total_files" label="总文件" width="80" />
        <el-table-column prop="new_files" label="新文件" width="80">
          <template #default="{ row }">
            <el-tag v-if="row.new_files > 0" type="success" size="small">{{ row.new_files }}</el-tag>
            <span v-else>{{ row.new_files }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="jobStatusType(row.status)" size="small" effect="light">{{ jobStatusLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useScanStore } from '@/stores/scan'
import { scanApi } from '@/api'
import type { ScanJob } from '@/types'
import { ElMessage } from 'element-plus'
import { Search, FolderOpened, Loading, Clock, CircleCheck } from '@element-plus/icons-vue'

const scanStore = useScanStore()
const scanPath = ref('')
const scanType = ref('full')
const autoOrganize = ref(false)
const scanning = ref(false)
const loading = ref(false)
const currentJob = ref<ScanJob | null>(null)
const jobs = ref<ScanJob[]>([])
let ws: WebSocket | null = null

onMounted(async () => {
  loading.value = true
  try {
    const res: any = await scanApi.listJobs()
    jobs.value = res.data.items
  } finally {
    loading.value = false
  }
})

onUnmounted(() => {
  disconnectWs()
})

function connectWs(jobId: number) {
  disconnectWs()
  const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:'
  ws = new WebSocket(`${protocol}//${location.host}/api/v1/ws/scan/${jobId}`)

  ws.onmessage = (event) => {
    const msg = JSON.parse(event.data)
    if (msg.type === 'progress' && currentJob.value) {
      currentJob.value.processed_files = msg.data.processed_files
      currentJob.value.total_files = msg.data.total_files
      currentJob.value.new_files = msg.data.new_files
      currentJob.value.error_files = msg.data.error_files
      currentJob.value.organized_files = msg.data.organized_files || 0
      currentJob.value.progress_percent = msg.data.progress_percent
    } else if (msg.type === 'completed' && currentJob.value) {
      currentJob.value.status = msg.data.status
      currentJob.value.new_files = msg.data.new_files
      currentJob.value.error_files = msg.data.error_files
      currentJob.value.organized_files = msg.data.organized_files || 0
      currentJob.value.progress_percent = 100
      disconnectWs()
      refreshJobs()
    }
  }

  ws.onerror = () => {
    disconnectWs()
  }
}

function disconnectWs() {
  if (ws) {
    ws.close()
    ws = null
  }
}

async function handleScan() {
  if (!scanPath.value) {
    ElMessage.warning('请输入扫描路径')
    return
  }
  scanning.value = true
  try {
    const result = await scanStore.startScan(scanPath.value, scanType.value, autoOrganize.value)
    currentJob.value = result
    // Connect WebSocket for real-time updates
    if (result.status === 'running') {
      connectWs(result.id)
    }
    ElMessage.success('扫描任务已启动')
    refreshJobs()
  } finally {
    scanning.value = false
  }
}

async function refreshJobs() {
  const res: any = await scanApi.listJobs()
  jobs.value = res.data.items
}

function jobStatusType(status: string) {
  const map: Record<string, string> = { pending: 'info', running: 'warning', completed: 'success', failed: 'danger' }
  return map[status] || 'info'
}

function jobStatusLabel(status: string) {
  const map: Record<string, string> = { pending: '等待中', running: '运行中', completed: '已完成', failed: '失败' }
  return map[status] || status
}

function formatTime(t: string) {
  return new Date(t).toLocaleString()
}
</script>

<style scoped>
.scan-manager {
  max-width: 1200px;
}

.page-header {
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

.mb-20 {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 15px;
}

.spinning {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.progress-stats {
  margin-bottom: 8px;
}

.progress-stat {
  text-align: center;
  padding: 12px;
  background: #fafbfc;
  border-radius: 10px;
}

.progress-stat-value {
  font-size: 28px;
  font-weight: 700;
  color: #303133;
}

.progress-stat-value.primary {
  color: #667eea;
}

.progress-stat-value.success {
  color: #67c23a;
}

.progress-stat-value.danger {
  color: #f56c6c;
}

.progress-stat-label {
  font-size: 13px;
  color: #909399;
  margin-top: 4px;
}
</style>
