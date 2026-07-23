<template>
  <div class="media-list">
    <div class="page-header">
      <div>
        <h1>媒体列表</h1>
        <p class="subtitle">管理所有音频和视频文件</p>
      </div>
      <div class="header-actions" v-if="selectedIds.length > 0">
        <el-tag type="primary" size="large" effect="dark">已选 {{ selectedIds.length }} 项</el-tag>
        <el-button type="primary" @click="batchOrganize" :icon="FolderOpened">批量整理</el-button>
        <el-button type="warning" @click="batchFetchDlsite" :icon="Link">DLsite 补全</el-button>
        <el-button type="success" @click="batchWriteTags" :icon="PriceTag">写入标签</el-button>
        <el-button @click="clearSelection">取消选择</el-button>
      </div>
    </div>

    <el-card class="filter-card">
      <div class="filters">
        <el-input
          v-model="search"
          placeholder="搜索标题、文件名、CV..."
          clearable
          size="large"
          style="width: 320px"
          :prefix-icon="Search"
          @input="debounceSearch"
        />
        <el-select v-model="mediaType" placeholder="媒体类型" clearable size="large" @change="loadMedia">
          <el-option label="音频" value="audio">
            <el-icon><Headset /></el-icon> 音频
          </el-option>
          <el-option label="视频" value="video">
            <el-icon><VideoCamera /></el-icon> 视频
          </el-option>
        </el-select>
        <el-select v-model="status" placeholder="处理状态" clearable size="large" @change="loadMedia">
          <el-option label="待处理" value="pending" />
          <el-option label="已处理" value="processed" />
          <el-option label="已重命名" value="renamed" />
          <el-option label="错误" value="error" />
        </el-select>
        <el-button-group size="large">
          <el-button :type="showUnclassified ? 'danger' : 'default'" @click="toggleUnclassified">
            <el-icon><Warning /></el-icon> 未分类
          </el-button>
        </el-button-group>
      </div>
    </el-card>

    <el-card class="table-card">
      <el-table
        :data="mediaStore.items"
        v-loading="mediaStore.loading"
        stripe
        style="width: 100%"
        @selection-change="handleSelectionChange"
        ref="tableRef"
      >
        <el-table-column type="selection" width="50" />
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="file_name" label="文件名" min-width="220" show-overflow-tooltip>
          <template #default="{ row }">
            <div class="file-name-cell">
              <el-icon :size="16" :color="row.media_type === 'audio' ? '#f5576c' : '#4facfe'">
                <Headset v-if="row.media_type === 'audio'" />
                <VideoCamera v-else />
              </el-icon>
              <span>{{ row.file_name }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="title" label="标题" min-width="160" show-overflow-tooltip />
        <el-table-column prop="rj_id" label="RJ号" width="120">
          <template #default="{ row }">
            <el-tag v-if="row.rj_id" type="info" size="small" effect="plain">{{ row.rj_id }}</el-tag>
            <span v-else class="text-muted">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="cv" label="CV" width="130" show-overflow-tooltip>
          <template #default="{ row }">
            <span v-if="row.cv" class="cv-name">{{ row.cv }}</span>
            <span v-else class="text-muted">-</span>
          </template>
        </el-table-column>
        <el-table-column label="大小" width="100">
          <template #default="{ row }">
            <span class="file-size">{{ formatSize(row.file_size) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="statusType(row.status)" size="small" effect="light">
              {{ statusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="来源" width="100">
          <template #default="{ row }">
            <el-tag v-if="row.metadata_source" :type="sourceType(row.metadata_source)" size="small" effect="plain">
              {{ sourceLabel(row.metadata_source) }}
            </el-tag>
            <span v-else class="text-muted">-</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="goDetail(row.id)">
              <el-icon><View /></el-icon> 详情
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination">
        <el-pagination
          v-model:current-page="currentPage"
          :page-size="mediaStore.pageSize"
          :total="mediaStore.total"
          layout="total, prev, pager, next, jumper"
          @current-change="handlePageChange"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { Search, Headset, VideoCamera, View, PriceTag, FolderOpened, Link, Warning } from '@element-plus/icons-vue'
import { useMediaStore } from '@/stores/media'
import { mediaApi, metadataApi } from '@/api'
import { ElMessage, ElMessageBox } from 'element-plus'

const router = useRouter()
const route = useRoute()
const mediaStore = useMediaStore()

const search = ref('')
const mediaType = ref('')
const status = ref('')
const showUnclassified = ref(false)
const currentPage = ref(1)
const selectedIds = ref<number[]>([])
const tableRef = ref<any>(null)
let searchTimer: ReturnType<typeof setTimeout> | null = null

onMounted(() => {
  // 从 Dashboard 跳转过来时自动应用未分类筛选
  if (route.query.unclassified === '1') {
    showUnclassified.value = true
  }
  loadMedia()
})

function loadMedia() {
  const params: Record<string, any> = {}
  if (search.value) params.search = search.value
  if (mediaType.value) params.media_type = mediaType.value
  if (status.value) params.status = status.value
  if (showUnclassified.value) params.unclassified = true
  mediaStore.setPage(currentPage.value)
  mediaStore.fetchMedia(params)
}

function toggleUnclassified() {
  showUnclassified.value = !showUnclassified.value
  currentPage.value = 1
  loadMedia()
}

function debounceSearch() {
  if (searchTimer) clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {
    currentPage.value = 1
    loadMedia()
  }, 300)
}

function handlePageChange(page: number) {
  currentPage.value = page
  loadMedia()
}

function handleSelectionChange(rows: any[]) {
  selectedIds.value = rows.map((r) => r.id)
}

function clearSelection() {
  tableRef.value?.clearSelection()
  selectedIds.value = []
}

function goDetail(id: number) {
  router.push(`/media/${id}`)
}

function batchRename() {
  if (selectedIds.value.length === 0) return
  router.push({ path: '/rename', query: { ids: selectedIds.value.join(',') } })
}

async function batchWriteTags() {
  if (selectedIds.value.length === 0) return
  try {
    await metadataApi.writeTags({ media_ids: selectedIds.value })
    ElMessage.success(`已对 ${selectedIds.value.length} 个文件写入标签`)
  } catch {}
}

async function batchOrganize() {
  if (selectedIds.value.length === 0) return
  try {
    await ElMessageBox.confirm(
      `确定要将 ${selectedIds.value.length} 个文件整理到 library 目录吗？`,
      '批量整理',
      { confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning' }
    )
    const res: any = await mediaApi.organizeExecute({ media_ids: selectedIds.value })
    ElMessage.success(`整理完成：成功 ${res.data.success}，失败 ${res.data.failed}`)
    clearSelection()
    loadMedia()
  } catch {}
}

async function batchFetchDlsite() {
  if (selectedIds.value.length === 0) return
  try {
    const res: any = await metadataApi.fetchDlsite({ media_ids: selectedIds.value })
    ElMessage.success(`DLsite 补全完成：更新 ${res.data.updated}，跳过 ${res.data.skipped}，失败 ${res.data.failed}`)
    clearSelection()
    loadMedia()
  } catch {}
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  if (bytes < 1024 * 1024 * 1024) return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
  return (bytes / (1024 * 1024 * 1024)).toFixed(2) + ' GB'
}

function statusType(s: string) {
  const map: Record<string, string> = { pending: 'info', processed: 'success', renamed: 'warning', error: 'danger' }
  return map[s] || 'info'
}

function statusLabel(s: string) {
  const map: Record<string, string> = { pending: '待处理', processed: '已处理', renamed: '已重命名', error: '错误' }
  return map[s] || s
}

function sourceType(s: string) {
  const map: Record<string, string> = { manual: 'danger', dlsite: 'warning', parsed: 'info', metadata: 'success' }
  return map[s] || 'info'
}

function sourceLabel(s: string) {
  const map: Record<string, string> = { manual: '手动', dlsite: 'DLsite', parsed: '解析', metadata: '元数据' }
  return map[s] || s
}
</script>

<style scoped>
.media-list {
  max-width: 1400px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 20px;
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

.header-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.filter-card {
  margin-bottom: 20px;
}

.filters {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.table-card {
  min-height: 400px;
}

.file-name-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.cv-name {
  color: #f5576c;
  font-weight: 500;
}

.file-size {
  color: #909399;
  font-size: 13px;
}

.text-muted {
  color: #c0c4cc;
}

.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
</style>
