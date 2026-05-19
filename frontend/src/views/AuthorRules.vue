<template>
  <div class="author-rules">
    <div class="page-header">
      <div>
        <h1>作者规则管理</h1>
        <p class="subtitle">配置关键词规则，自动匹配创作者信息</p>
      </div>
      <el-button type="primary" @click="showAddDialog = true" :icon="Plus" size="large">添加规则</el-button>
    </div>

    <el-card>
      <el-table :data="rules" v-loading="loading" stripe>
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="keyword" label="关键词" min-width="140">
          <template #default="{ row }">
            <el-tag effect="plain" type="info">{{ row.keyword }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="match_type" label="匹配方式" width="100">
          <template #default="{ row }">
            <el-tag size="small">{{ matchTypeLabel(row.match_type) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="creator" label="创作者" width="130" show-overflow-tooltip />
        <el-table-column prop="circle" label="社团" width="130" show-overflow-tooltip />
        <el-table-column prop="cv" label="CV" width="130" show-overflow-tooltip />
        <el-table-column prop="priority" label="优先级" width="80">
          <template #default="{ row }">
            <el-tag :type="row.priority > 5 ? 'warning' : 'info'" size="small" effect="light">
              {{ row.priority }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="enabled" label="启用" width="80">
          <template #default="{ row }">
            <el-switch v-model="row.enabled" @change="toggleRule(row)" />
          </template>
        </el-table-column>
        <el-table-column prop="hit_count" label="命中" width="70">
          <template #default="{ row }">
            <span :class="{ 'hit-count': row.hit_count > 0 }">{{ row.hit_count }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="140" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="testRule(row)" :icon="Aim">测试</el-button>
            <el-button link type="danger" @click="deleteRule(row)" :icon="Delete">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination">
        <el-pagination
          v-model:current-page="currentPage"
          :page-size="20"
          :total="total"
          layout="total, prev, pager, next"
          @current-change="loadRules"
        />
      </div>
    </el-card>

    <el-dialog v-model="showAddDialog" title="添加作者规则" width="520px" :close-on-click-modal="false">
      <el-form :model="newRule" label-width="90px">
        <el-form-item label="关键词" required>
          <el-input v-model="newRule.keyword" placeholder="输入匹配关键词" />
        </el-form-item>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="匹配方式">
              <el-select v-model="newRule.match_type" style="width: 100%">
                <el-option label="包含" value="contains" />
                <el-option label="精确" value="exact" />
                <el-option label="前缀" value="prefix" />
                <el-option label="后缀" value="suffix" />
                <el-option label="正则" value="regex" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="匹配目标">
              <el-select v-model="newRule.match_target" style="width: 100%">
                <el-option label="文件名" value="filename" />
                <el-option label="全部" value="all" />
                <el-option label="目录名" value="directory" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-divider />
        <el-form-item label="创作者">
          <el-input v-model="newRule.creator" placeholder="匹配后赋值的创作者" />
        </el-form-item>
        <el-form-item label="社团">
          <el-input v-model="newRule.circle" placeholder="匹配后赋值的社团" />
        </el-form-item>
        <el-form-item label="CV">
          <el-input v-model="newRule.cv" placeholder="匹配后赋值的CV" />
        </el-form-item>
        <el-form-item label="优先级">
          <el-slider v-model="newRule.priority" :min="0" :max="100" show-input />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddDialog = false">取消</el-button>
        <el-button type="primary" @click="addRule" :loading="adding">确定</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="showTestDialog" title="规则测试结果" width="650px">
      <template v-if="testResult">
        <el-descriptions :column="2" border class="mb-16">
          <el-descriptions-item label="总媒体数">{{ testResult.total_media }}</el-descriptions-item>
          <el-descriptions-item label="匹配数">
            <el-tag type="success">{{ testResult.matched_media }}</el-tag>
          </el-descriptions-item>
        </el-descriptions>
        <el-table :data="testResult.samples" stripe size="small">
          <el-table-column prop="file_name" label="文件名" min-width="200" show-overflow-tooltip />
          <el-table-column prop="matched_text" label="匹配文本" width="140" />
          <el-table-column prop="match_source" label="匹配来源" width="110" />
        </el-table>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { authorRulesApi } from '@/api'
import type { AuthorRule } from '@/types'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Delete, Aim } from '@element-plus/icons-vue'

const rules = ref<AuthorRule[]>([])
const total = ref(0)
const currentPage = ref(1)
const loading = ref(false)
const adding = ref(false)
const showAddDialog = ref(false)
const showTestDialog = ref(false)
const testResult = ref<any>(null)

const newRule = reactive({
  keyword: '', match_type: 'contains', match_target: 'filename',
  creator: '', circle: '', cv: '', priority: 0,
})

onMounted(() => loadRules())

async function loadRules() {
  loading.value = true
  try {
    const res: any = await authorRulesApi.list({ page: currentPage.value })
    rules.value = res.data.items
    total.value = res.data.total
  } finally {
    loading.value = false
  }
}

async function addRule() {
  if (!newRule.keyword) {
    ElMessage.warning('请输入关键词')
    return
  }
  adding.value = true
  try {
    await authorRulesApi.create(newRule)
    showAddDialog.value = false
    ElMessage.success('规则已添加')
    loadRules()
  } finally {
    adding.value = false
  }
}

async function toggleRule(rule: AuthorRule) {
  try {
    await authorRulesApi.update(rule.id, { enabled: rule.enabled })
    ElMessage.success('已更新')
  } catch {
    rule.enabled = !rule.enabled
  }
}

async function deleteRule(rule: AuthorRule) {
  await ElMessageBox.confirm('确定删除此规则？', '确认删除', { type: 'warning' })
  await authorRulesApi.delete(rule.id)
  ElMessage.success('已删除')
  loadRules()
}

async function testRule(rule: AuthorRule) {
  const res: any = await authorRulesApi.scanTest(rule.id)
  testResult.value = res.data
  showTestDialog.value = true
}

function matchTypeLabel(t: string) {
  const map: Record<string, string> = { contains: '包含', exact: '精确', prefix: '前缀', suffix: '后缀', regex: '正则' }
  return map[t] || t
}
</script>

<style scoped>
.author-rules {
  max-width: 1200px;
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

.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

.hit-count {
  color: #667eea;
  font-weight: 600;
}

.mb-16 {
  margin-bottom: 16px;
}
</style>
