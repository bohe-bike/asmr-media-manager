<template>
  <div class="media-detail" v-loading="loading">
    <div class="page-header">
      <el-button @click="router.back()" :icon="ArrowLeft">返回</el-button>
      <h1>媒体详情</h1>
    </div>

    <template v-if="media">
      <el-row :gutter="20">
        <el-col :span="8">
          <el-card class="cover-card">
            <div class="cover-container">
              <img
                v-if="media.cover_url && !coverError"
                :src="media.cover_url"
                class="cover-image"
                @error="coverError = true"
              />
              <div v-else class="no-cover">
                <el-icon :size="64" color="#c0c4cc">
                  <Headset v-if="media.media_type === 'audio'" />
                  <VideoCamera v-else />
                </el-icon>
                <p>暂无封面</p>
              </div>
            </div>
            <div class="media-type-badge" :class="media.media_type">
              {{ media.media_type === 'audio' ? '音频' : '视频' }}
            </div>
          </el-card>
        </el-col>
        <el-col :span="16">
          <el-card>
            <template #header>
              <div class="card-header">
                <el-icon><InfoFilled /></el-icon>
                <span>基本信息</span>
              </div>
            </template>
            <el-descriptions :column="2" border>
              <el-descriptions-item label="文件名" :span="2">{{ media.file_name }}</el-descriptions-item>
              <el-descriptions-item label="格式">
                <el-tag type="info" effect="plain">{{ media.format.toUpperCase() }}</el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="大小">{{ formatSize(media.file_size) }}</el-descriptions-item>
              <el-descriptions-item v-if="media.duration" label="时长">{{ formatDuration(media.duration) }}</el-descriptions-item>
              <el-descriptions-item v-if="media.bitrate" label="比特率">{{ media.bitrate }} kbps</el-descriptions-item>
              <el-descriptions-item v-if="media.sample_rate" label="采样率">{{ media.sample_rate }} Hz</el-descriptions-item>
              <el-descriptions-item v-if="media.channels" label="声道">{{ media.channels }}</el-descriptions-item>
              <el-descriptions-item v-if="media.width" label="分辨率">{{ media.width }} x {{ media.height }}</el-descriptions-item>
              <el-descriptions-item label="状态">
                <el-tag :type="statusType(media.status)" effect="light">{{ statusLabel(media.status) }}</el-tag>
              </el-descriptions-item>
              <el-descriptions-item v-if="media.metadata_source" label="数据来源">
                <el-tag :type="sourceType(media.metadata_source)" effect="light">{{ sourceLabel(media.metadata_source) }}</el-tag>
              </el-descriptions-item>
            </el-descriptions>
          </el-card>
        </el-col>
      </el-row>

      <el-card class="mt-20">
        <template #header>
          <div class="card-header">
            <el-icon><EditPen /></el-icon>
            <span>元数据编辑</span>
            <div style="margin-left: auto; display: flex; gap: 8px">
              <el-button type="success" size="small" @click="aiAnalyze" :loading="analyzing" :disabled="!settingsStore.settings?.ai_enabled">
                <el-icon><MagicStick /></el-icon> AI 分析
              </el-button>
              <el-button type="warning" size="small" @click="fetchDlsite" :loading="fetchingDlsite" :disabled="!settingsStore.settings?.dlsite_enabled">
                <el-icon><Link /></el-icon> DLsite 补全
              </el-button>
              <el-button type="primary" size="small" @click="saveMetadata" :loading="saving">
                <el-icon><Check /></el-icon> 保存
              </el-button>
            </div>
          </div>
        </template>
        <el-form label-width="100px" label-position="left">
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="标题">
                <el-input v-model="editForm.title" placeholder="作品标题" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="RJ号">
                <el-input v-model="editForm.rj_id" placeholder="RJ123456" />
              </el-form-item>
            </el-col>
          </el-row>
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="CV">
                <el-input v-model="editForm.cv" placeholder="声优名称" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="创作者">
                <el-input v-model="editForm.creator" placeholder="创作者名称" />
              </el-form-item>
            </el-col>
          </el-row>
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="社团">
                <el-input v-model="editForm.circle" placeholder="社团名称" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="平台">
                <el-select v-model="editForm.platform" clearable placeholder="选择平台" style="width: 100%">
                  <el-option label="DLsite" value="dlsite" />
                  <el-option label="Patreon" value="patreon" />
                  <el-option label="YouTube" value="youtube" />
                  <el-option label="其他" value="other" />
                </el-select>
              </el-form-item>
            </el-col>
          </el-row>
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="语言">
                <el-select v-model="editForm.language" clearable placeholder="选择语言" style="width: 100%">
                  <el-option label="日语" value="ja" />
                  <el-option label="中文" value="zh" />
                  <el-option label="英语" value="en" />
                  <el-option label="其他" value="other" />
                </el-select>
              </el-form-item>
            </el-col>
          </el-row>
          <el-form-item label="描述">
            <el-input v-model="editForm.description" type="textarea" :rows="3" placeholder="作品描述（来自 DLsite 或手动填写）" />
          </el-form-item>
        </el-form>
      </el-card>

      <el-card class="mt-20">
        <template #header>
          <div class="card-header">
            <el-icon><PriceTag /></el-icon>
            <span>标签管理</span>
          </div>
        </template>
        <div class="tags-container">
          <el-tag
            v-for="tag in media.tags"
            :key="tag.id"
            closable
            size="large"
            effect="light"
            @close="removeTag(tag.id)"
            class="tag-item"
          >
            {{ tag.name }}
          </el-tag>
          <el-input
            v-if="showTagInput"
            v-model="newTagName"
            size="default"
            style="width: 140px"
            placeholder="标签名称"
            @keyup.enter="addTag"
            @blur="addTag"
          />
          <el-button v-else size="default" @click="showTagInput = true" :icon="Plus">添加标签</el-button>
        </div>
      </el-card>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useMediaStore } from '@/stores/media'
import { useSettingsStore } from '@/stores/settings'
import { tagsApi, metadataApi } from '@/api'
import type { MediaDetail } from '@/types'
import { ElMessage } from 'element-plus'
import { ArrowLeft, Headset, VideoCamera, InfoFilled, EditPen, Check, PriceTag, Plus, MagicStick, Link } from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const mediaStore = useMediaStore()
const settingsStore = useSettingsStore()

const media = ref<MediaDetail | null>(null)
const loading = ref(false)
const saving = ref(false)
const analyzing = ref(false)
const fetchingDlsite = ref(false)
const coverError = ref(false)
const showTagInput = ref(false)
const newTagName = ref('')

const editForm = reactive({
  title: '', rj_id: '', cv: '', creator: '', circle: '', platform: '', language: '', description: '',
})

onMounted(async () => {
  const id = Number(route.params.id)
  loading.value = true
  try {
    const data = await mediaStore.fetchMediaDetail(id)
    media.value = data
    Object.assign(editForm, {
      title: data.title || '', rj_id: data.rj_id || '', cv: data.cv || '',
      creator: data.creator || '', circle: data.circle || '', platform: data.platform || '', language: data.language || '',
      description: data.description || '',
    })
    if (!settingsStore.settings) {
      settingsStore.fetchSettings()
    }
  } finally {
    loading.value = false
  }
})

async function saveMetadata() {
  if (!media.value) return
  saving.value = true
  try {
    await mediaStore.updateMedia(media.value.id, editForm)
    ElMessage.success('保存成功')
  } finally {
    saving.value = false
  }
}

async function aiAnalyze() {
  if (!media.value) return
  analyzing.value = true
  try {
    const res: any = await metadataApi.aiAnalyze({ media_ids: [media.value.id] })
    const result = res.data.results?.[0]
    if (result?.status === 'updated' && result.info) {
      const info = result.info
      if (info.title) editForm.title = info.title
      if (info.cv) editForm.cv = info.cv
      if (info.circle) editForm.circle = info.circle
      if (info.rj_id) editForm.rj_id = info.rj_id
      if (info.language) editForm.language = info.language
      ElMessage.success('AI 分析完成，已自动填充')
    } else if (result?.status === 'no_change') {
      ElMessage.info('AI 分析完成，无需更新')
    } else {
      ElMessage.warning('AI 未能分析出有效信息')
    }
  } catch {
    ElMessage.error('AI 分析失败，请检查设置中的 AI 配置')
  } finally {
    analyzing.value = false
  }
}

async function fetchDlsite() {
  if (!media.value) return
  fetchingDlsite.value = true
  try {
    const res: any = await metadataApi.fetchDlsite({ media_ids: [media.value.id] })
    const result = res.data.results?.[0]
    if (result?.status === 'updated') {
      // 重新加载详情
      const data = await mediaStore.fetchMediaDetail(media.value.id)
      media.value = data
      Object.assign(editForm, {
        title: data.title || '', rj_id: data.rj_id || '', cv: data.cv || '',
        creator: data.creator || '', circle: data.circle || '', platform: data.platform || '', language: data.language || '',
        description: data.description || '',
      })
      ElMessage.success('DLsite 信息补全完成')
    } else if (result?.status === 'no_rj_id') {
      ElMessage.warning('该媒体没有 RJ/DL 号，无法从 DLsite 获取信息')
    } else if (result?.status === 'no_change') {
      ElMessage.info('DLsite 信息已是最新')
    } else {
      ElMessage.warning('DLsite 补全失败，请检查网络或代理设置')
    }
  } catch {
    ElMessage.error('DLsite 补全失败，请检查设置中的 DLsite 配置')
  } finally {
    fetchingDlsite.value = false
  }
}

async function addTag() {
  if (!newTagName.value.trim() || !media.value) return
  try {
    const res: any = await tagsApi.create({ name: newTagName.value.trim() })
    await tagsApi.addToMedia(media.value.id, [res.data.id])
    media.value = await mediaStore.fetchMediaDetail(media.value.id)
    newTagName.value = ''
    showTagInput.value = false
    ElMessage.success('标签已添加')
  } catch {}
}

async function removeTag(tagId: number) {
  if (!media.value) return
  try {
    await tagsApi.removeFromMedia(media.value.id, tagId)
    media.value = await mediaStore.fetchMediaDetail(media.value.id)
    ElMessage.success('标签已移除')
  } catch {}
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  if (bytes < 1024 * 1024 * 1024) return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
  return (bytes / (1024 * 1024 * 1024)).toFixed(2) + ' GB'
}

function formatDuration(seconds: number): string {
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  const s = Math.floor(seconds % 60)
  if (h > 0) return `${h}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
  return `${m}:${String(s).padStart(2, '0')}`
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
  const map: Record<string, string> = { manual: '手动规则', dlsite: 'DLsite', parsed: '文件名解析', metadata: '文件元数据' }
  return map[s] || s
}
</script>

<style scoped>
.media-detail {
  max-width: 1200px;
}

.page-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 24px;
}

.page-header h1 {
  font-size: 24px;
  font-weight: 700;
  color: #1a1a2e;
  margin: 0;
}

.cover-card {
  position: relative;
}

.cover-container {
  border-radius: 10px;
  overflow: hidden;
  background: #f5f7fa;
  min-height: 280px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.cover-image {
  width: 100%;
  display: block;
}

.no-cover {
  text-align: center;
  color: #c0c4cc;
}

.no-cover p {
  margin-top: 12px;
  font-size: 14px;
}

.media-type-badge {
  position: absolute;
  top: 12px;
  right: 12px;
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
  color: #fff;
}

.media-type-badge.audio {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
}

.media-type-badge.video {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 15px;
}

.mt-20 {
  margin-top: 20px;
}

.tags-container {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  align-items: center;
}

.tag-item {
  font-size: 14px;
}
</style>
