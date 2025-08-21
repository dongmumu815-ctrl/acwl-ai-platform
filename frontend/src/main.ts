import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus, { ElMessage } from 'element-plus'
import 'element-plus/dist/index.css'
import 'element-plus/theme-chalk/dark/css-vars.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'

import App from './App.vue'
import router from './router'
import { useUserStore } from './stores/user'

// 样式文件
import './styles/index.scss'

// 创建应用实例
const app = createApp(App)

// 创建 Pinia 实例
const pinia = createPinia()

// 注册 Element Plus 图标
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

// 使用插件
app.use(pinia)
app.use(router)
app.use(ElementPlus, {
  locale: zhCn,
  size: 'default'
})

// 全局错误处理
app.config.errorHandler = (err, vm, info) => {
  console.error('全局错误:', err)
  console.error('错误信息:', info)
  ElMessage.error('应用发生错误，请刷新页面重试')
}

// 全局警告处理
app.config.warnHandler = (msg, vm, trace) => {
  console.warn('全局警告:', msg)
  console.warn('警告追踪:', trace)
}

// 路由守卫
router.beforeEach(async (to, from, next) => {
  // 显示加载进度
  if (typeof window !== 'undefined' && window.NProgress) {
    window.NProgress.start()
  }
  
  const userStore = useUserStore()
  
  // 检查是否需要认证
  if (to.meta.requiresAuth && !userStore.isLoggedIn) {
    // 尝试从本地存储恢复用户信息
    await userStore.initializeAuth()
    
    if (!userStore.isLoggedIn) {
      next({
        path: '/login',
        query: { redirect: to.fullPath }
      })
      return
    }
  }
  
  // 检查管理员权限
  if (to.meta.requiresAdmin && !userStore.isAdmin) {
    ElMessage.error('需要管理员权限')
    next('/dashboard')
    return
  }
  
  // 如果已登录用户访问登录页，重定向到仪表板
  if (to.path === '/login' && userStore.isLoggedIn) {
    next('/dashboard')
    return
  }
  
  next()
})

router.afterEach(() => {
  // 隐藏加载进度
  if (typeof window !== 'undefined' && window.NProgress) {
    window.NProgress.done()
  }
})

// 挂载应用
app.mount('#app')

// 开发环境下的调试信息
if (import.meta.env.DEV) {
  console.log('🚀 ACWL AI 前端应用启动成功')
  console.log('📦 Vue版本:', app.version)
  console.log('🌍 环境:', import.meta.env.MODE)
}