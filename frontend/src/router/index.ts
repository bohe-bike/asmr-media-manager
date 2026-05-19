import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      redirect: '/dashboard',
    },
    {
      path: '/dashboard',
      name: 'Dashboard',
      component: () => import('@/views/Dashboard.vue'),
      meta: { title: '仪表盘' },
    },
    {
      path: '/media',
      name: 'MediaList',
      component: () => import('@/views/MediaList.vue'),
      meta: { title: '媒体列表' },
    },
    {
      path: '/media/:id',
      name: 'MediaDetail',
      component: () => import('@/views/MediaDetail.vue'),
      meta: { title: '媒体详情' },
    },
    {
      path: '/scan',
      name: 'ScanManager',
      component: () => import('@/views/ScanManager.vue'),
      meta: { title: '扫描管理' },
    },
    {
      path: '/rename',
      name: 'RenamePreview',
      component: () => import('@/views/RenamePreview.vue'),
      meta: { title: '重命名预览' },
    },
    {
      path: '/author-rules',
      name: 'AuthorRules',
      component: () => import('@/views/AuthorRules.vue'),
      meta: { title: '作者规则' },
    },
    {
      path: '/settings',
      name: 'Settings',
      component: () => import('@/views/Settings.vue'),
      meta: { title: '设置' },
    },
  ],
})

export default router
