<template>
  <div class="settings-page">
    <div class="page-header">
      <div>
        <h1>设置</h1>
        <p class="subtitle">配置系统参数和偏好</p>
      </div>
      <el-button type="primary" @click="handleSave" :loading="saving" :icon="Check" size="large">保存设置</el-button>
    </div>

    <el-card v-loading="loading">
      <el-form label-width="130px" label-position="left" v-if="settings">
        <div class="settings-section">
          <h3><el-icon><FolderOpened /></el-icon> 目录设置</h3>
          <el-form-item label="下载目录">
            <el-input v-model="settings.download_dir" placeholder="/media/downloads" />
          </el-form-item>
          <el-form-item label="整理目录">
            <el-input v-model="settings.library_dir" placeholder="/media/library" />
          </el-form-item>
        </div>

        <div class="settings-section">
          <h3><el-icon><Search /></el-icon> 扫描设置</h3>
          <el-form-item label="启用监听">
            <el-switch v-model="settings.watch_enabled" active-text="是" inactive-text="否" />
          </el-form-item>
          <el-form-item label="稳定秒数">
            <el-input-number v-model="settings.stable_seconds" :min="1" :max="60" />
            <span class="form-tip">文件大小稳定多少秒后判定下载完成</span>
          </el-form-item>
        </div>

        <div class="settings-section">
          <h3><el-icon><Edit /></el-icon> 重命名设置</h3>
          <el-form-item label="音频命名模式">
            <el-input v-model="settings.audio_rename_pattern" />
            <span class="form-tip">可用变量: {cv} {title} {rj_id} {creator} {circle}</span>
          </el-form-item>
          <el-form-item label="视频命名模式">
            <el-input v-model="settings.video_rename_pattern" />
          </el-form-item>
        </div>

        <div class="settings-section">
          <h3><el-icon><MagicStick /></el-icon> AI 设置</h3>
          <el-form-item label="启用AI">
            <el-switch v-model="settings.ai_enabled" active-text="开启" inactive-text="关闭" />
          </el-form-item>
          <el-form-item label="API地址">
            <el-input v-model="settings.ai_api_url" :disabled="!settings.ai_enabled" placeholder="https://api.openai.com/v1" />
          </el-form-item>
          <el-form-item label="API密钥">
            <el-input v-model="settings.ai_api_key" :disabled="!settings.ai_enabled" type="password" show-password placeholder="sk-..." />
          </el-form-item>
          <el-form-item label="AI模型">
            <el-input v-model="settings.ai_model" :disabled="!settings.ai_enabled" placeholder="gpt-4o-mini" />
          </el-form-item>
          <el-form-item label="启用OCR">
            <el-switch v-model="settings.ocr_enabled" active-text="开启" inactive-text="关闭" />
          </el-form-item>
        </div>

        <div class="settings-section">
          <h3><el-icon><Document /></el-icon> 支持格式</h3>
          <el-form-item label="音频格式">
            <div class="format-tags">
              <el-tag v-for="f in settings.supported_audio_formats" :key="f" effect="plain" type="info">{{ f }}</el-tag>
            </div>
          </el-form-item>
          <el-form-item label="视频格式">
            <div class="format-tags">
              <el-tag v-for="f in settings.supported_video_formats" :key="f" effect="plain" type="info">{{ f }}</el-tag>
            </div>
          </el-form-item>
        </div>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useSettingsStore } from '@/stores/settings'
import { ElMessage } from 'element-plus'
import { Check, FolderOpened, Search, Edit, MagicStick, Document } from '@element-plus/icons-vue'

const settingsStore = useSettingsStore()
const loading = ref(false)
const saving = ref(false)
const settings = ref<any>(null)

onMounted(async () => {
  loading.value = true
  try {
    await settingsStore.fetchSettings()
    settings.value = { ...settingsStore.settings }
  } finally {
    loading.value = false
  }
})

async function handleSave() {
  saving.value = true
  try {
    await settingsStore.updateSettings(settings.value)
    ElMessage.success('设置已保存')
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.settings-page {
  max-width: 900px;
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

.settings-section {
  margin-bottom: 32px;
}

.settings-section:last-child {
  margin-bottom: 0;
}

.settings-section h3 {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
  color: #1a1a2e;
  margin-bottom: 20px;
  padding-bottom: 12px;
  border-bottom: 2px solid #f0f2f5;
}

.form-tip {
  display: block;
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

.format-tags {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}
</style>
