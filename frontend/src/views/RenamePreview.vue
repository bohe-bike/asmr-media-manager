<template>
  <div class="rename-preview">
    <div class="page-header">
      <div>
        <h1>重命名预览</h1>
        <p class="subtitle">预览并执行批量重命名操作</p>
      </div>
    </div>

    <el-card class="mb-20">
      <template #header>
        <div class="card-header">
          <el-icon><Edit /></el-icon>
          <span>重命名配置</span>
        </div>
      </template>
      <el-form label-position="top">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="媒体ID">
              <el-input
                v-model="idsInput"
                placeholder="输入媒体ID，多个用逗号分隔"
                size="large"
                :prefix-icon="Tickets"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="命名模式">
              <el-input v-model="pattern" placeholder="[{cv}] {title} ({rj_id})" size="large" :prefix-icon="Document" />
            </el-form-item>
          </el-col>
        </el-row>
        <div class="pattern-help">
          <span class="help-label">可用变量:</span>
          <el-tag v-for="v in variables" :key="v" size="small" effect="plain" type="info" class="var-tag">{{ v }}</el-tag>
        </div>
        <div class="action-buttons">
          <el-button type="primary" size="large" @click="handlePreview" :loading="loading" :icon="View">
            预览重命名
          </el-button>
          <el-button type="success" size="large" @click="handleExecute" :loading="executing" :disabled="!previewResult" :icon="Check">
            执行重命名
          </el-button>
        </div>
      </el-form>
    </el-card>

    <el-card v-if="previewResult">
      <template #header>
        <div class="card-header">
          <el-icon><List /></el-icon>
          <span>预览结果</span>
          <el-tag type="info" size="small" style="margin-left: 8px">{{ previewResult.total }} 个文件</el-tag>
        </div>
      </template>
      <el-table :data="previewResult.items" stripe>
        <el-table-column prop="media_id" label="ID" width="70" />
        <el-table-column prop="old_path" label="原路径" min-width="220" show-overflow-tooltip>
          <template #default="{ row }">
            <span class="path-old">{{ row.old_path }}</span>
          </template>
        </el-table-column>
        <el-table-column label="" width="40" align="center">
          <template #default>
            <el-icon color="#667eea"><Right /></el-icon>
          </template>
        </el-table-column>
        <el-table-column prop="new_path" label="新路径" min-width="220" show-overflow-tooltip>
          <template #default="{ row }">
            <span class="path-new">{{ row.new_path }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="conflict" label="冲突" width="80" align="center">
          <template #default="{ row }">
            <el-tag :type="row.conflict ? 'danger' : 'success'" size="small" effect="light">
              {{ row.conflict ? '冲突' : '正常' }}
            </el-tag>
          </template>
        </el-table-column>
      </el-table>

      <el-alert
        v-if="previewResult.conflicts.length > 0"
        :title="`存在 ${previewResult.conflicts.length} 个文件名冲突`"
        type="warning"
        show-icon
        :closable="false"
        style="margin-top: 16px"
      />
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { renameApi } from '@/api'
import { ElMessage } from 'element-plus'
import { Edit, View, Check, List, Right, Tickets, Document } from '@element-plus/icons-vue'

const route = useRoute()
const idsInput = ref('')

onMounted(() => {
  // Accept IDs from query parameter (e.g., from batch select in MediaList)
  const queryIds = route.query.ids as string
  if (queryIds) {
    idsInput.value = queryIds
  }
})
const pattern = ref('[{cv}] {title} ({rj_id})')
const loading = ref(false)
const executing = ref(false)
const previewResult = ref<any>(null)
const variables = ['{cv}', '{title}', '{rj_id}', '{creator}', '{circle}', '{dl_id}']

function parseIds(): number[] {
  return idsInput.value.split(/[,，\s]+/).map((s) => parseInt(s.trim())).filter((n) => !isNaN(n))
}

async function handlePreview() {
  const ids = parseIds()
  if (ids.length === 0) {
    ElMessage.warning('请输入有效的媒体ID')
    return
  }
  loading.value = true
  try {
    const res: any = await renameApi.preview({ media_ids: ids, pattern: pattern.value || undefined })
    previewResult.value = res.data
  } finally {
    loading.value = false
  }
}

async function handleExecute() {
  const ids = parseIds()
  if (ids.length === 0) return
  executing.value = true
  try {
    const res: any = await renameApi.execute({ media_ids: ids, pattern: pattern.value || undefined, move_cover: true })
    ElMessage.success(`成功: ${res.data.success}, 失败: ${res.data.failed}`)
    previewResult.value = null
  } finally {
    executing.value = false
  }
}
</script>

<style scoped>
.rename-preview {
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

.pattern-help {
  margin-bottom: 20px;
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.help-label {
  font-size: 13px;
  color: #909399;
}

.var-tag {
  font-family: monospace;
}

.action-buttons {
  display: flex;
  gap: 12px;
}

.path-old {
  color: #909399;
  text-decoration: line-through;
}

.path-new {
  color: #67c23a;
  font-weight: 500;
}
</style>
