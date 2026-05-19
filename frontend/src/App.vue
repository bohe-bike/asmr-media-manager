<template>
  <el-container class="app-container">
    <el-aside width="220px" class="app-aside">
      <div class="logo">
        <el-icon :size="28"><Headset /></el-icon>
        <span>ASMR Manager</span>
      </div>
      <el-menu
        :default-active="route.path"
        router
        class="aside-menu"
        background-color="transparent"
        text-color="rgba(255,255,255,0.7)"
        active-text-color="#fff"
      >
        <el-menu-item index="/dashboard">
          <el-icon><Odometer /></el-icon>
          <span>仪表盘</span>
        </el-menu-item>
        <el-menu-item index="/media">
          <el-icon><VideoPlay /></el-icon>
          <span>媒体列表</span>
        </el-menu-item>
        <el-menu-item index="/scan">
          <el-icon><Search /></el-icon>
          <span>扫描管理</span>
        </el-menu-item>
        <el-menu-item index="/rename">
          <el-icon><Edit /></el-icon>
          <span>重命名</span>
        </el-menu-item>
        <el-menu-item index="/author-rules">
          <el-icon><User /></el-icon>
          <span>作者规则</span>
        </el-menu-item>
        <el-menu-item index="/settings">
          <el-icon><Setting /></el-icon>
          <span>设置</span>
        </el-menu-item>
      </el-menu>
      <div class="aside-footer">
        <span>v1.0.0</span>
      </div>
    </el-aside>
    <el-main class="app-main">
      <router-view />
    </el-main>
  </el-container>
</template>

<script setup lang="ts">
import { useRoute } from 'vue-router'
const route = useRoute()
</script>

<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  background: #f0f2f5;
}

.app-container {
  height: 100vh;
}

.app-aside {
  background: linear-gradient(180deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  box-shadow: 4px 0 20px rgba(0, 0, 0, 0.15);
}

.logo {
  height: 70px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  color: #fff;
  font-size: 18px;
  font-weight: 700;
  letter-spacing: 1px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.aside-menu {
  flex: 1;
  border-right: none !important;
  padding: 10px 0;
}

.aside-menu .el-menu-item {
  height: 50px;
  line-height: 50px;
  margin: 4px 12px;
  border-radius: 10px;
  font-weight: 500;
  transition: all 0.3s;
}

.aside-menu .el-menu-item:hover {
  background: rgba(255, 255, 255, 0.1) !important;
  color: #fff !important;
}

.aside-menu .el-menu-item.is-active {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
  color: #fff !important;
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
}

.aside-footer {
  padding: 15px;
  text-align: center;
  color: rgba(255, 255, 255, 0.3);
  font-size: 12px;
  border-top: 1px solid rgba(255, 255, 255, 0.05);
}

.app-main {
  background: #f0f2f5;
  padding: 24px;
  overflow-y: auto;
}

/* Global card styles */
.el-card {
  border-radius: 12px !important;
  border: none !important;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06) !important;
  transition: box-shadow 0.3s !important;
}

.el-card:hover {
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1) !important;
}

.el-card__header {
  font-weight: 600;
  font-size: 15px;
  color: #1a1a2e;
  border-bottom: 1px solid #f0f2f5;
  padding: 16px 20px !important;
}

.el-card__body {
  padding: 20px !important;
}

/* Table styles */
.el-table {
  border-radius: 10px !important;
  overflow: hidden;
}

.el-table th.el-table__cell {
  background: #fafbfc !important;
  font-weight: 600;
  color: #606266;
}

/* Button styles */
.el-button--primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
  border: none !important;
}

.el-button--primary:hover {
  opacity: 0.9;
}

/* Tag styles */
.el-tag {
  border-radius: 6px !important;
}

/* Input styles */
.el-input__wrapper {
  border-radius: 8px !important;
}

.el-select .el-input__wrapper {
  border-radius: 8px !important;
}

/* Pagination */
.el-pagination {
  justify-content: flex-end;
}
</style>
