<script setup>
import { onMounted } from 'vue'
import { useAppStore, useUserStore } from '@/stores'
import { ElConfigProvider } from 'element-plus'
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'

/**
 * 应用主组件
 */
const appStore = useAppStore()
const userStore = useUserStore()

/**
 * 组件挂载时初始化应用
 */
onMounted(() => {
  appStore.initializeApp()
  
  // 检查是否有之前保存的错误信息
  const savedError = localStorage.getItem('login_error_debug')
  if (savedError) {
    console.error('上次登录错误信息:', JSON.parse(savedError))
    alert('登录错误详情已保存在控制台，请查看console')
    localStorage.removeItem('login_error_debug')
  }
  
  // 如果有token，获取用户信息
  if (userStore.isLoggedIn) {
    console.log('检测到用户已登录，正在获取用户信息...')
    userStore.getUserInfo().catch((error) => {
      // 获取用户信息失败，记录详细错误信息
      const errorInfo = {
        timestamp: new Date().toISOString(),
        message: error.message,
        status: error.response?.status,
        statusText: error.response?.statusText,
        data: error.response?.data,
        url: error.response?.config?.url,
        method: error.response?.config?.method,
        headers: error.response?.config?.headers
      }
      
      // 保存错误信息到localStorage
      localStorage.setItem('login_error_debug', JSON.stringify(errorInfo))
      
      console.error('获取用户信息失败，详细错误:', error)
      console.error('错误响应:', error.response)
      console.error('错误状态码:', error.response?.status)
      console.error('错误数据:', error.response?.data)
      console.log('即将执行登出操作...')
      userStore.logout()
    })
  } else {
    console.log('用户未登录，跳过获取用户信息')
  }
})
</script>

<template>
  <el-config-provider :locale="zhCn">
    <div id="app" class="app-container">
      <!-- 全局加载遮罩 -->
      <div v-if="appStore.globalLoading" class="global-loading">
        <el-loading
          :visible="true"
          text="加载中..."
          background="rgba(0, 0, 0, 0.8)"
        />
      </div>
      
      <!-- 路由视图 -->
      <router-view v-slot="{ Component }">
        <transition name="fade" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </div>
  </el-config-provider>
</template>

<style>
/* 全局样式 */
.app-container {
  height: 100vh;
  overflow: hidden;
}

.global-loading {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 9999;
}

/* 页面切换动画 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* Element Plus 样式覆盖 */
.el-menu {
  border-right: none;
}

.el-menu--horizontal {
  border-bottom: none;
}

.el-table {
  --el-table-border-color: var(--el-border-color-lighter);
}

.el-card {
  --el-card-border-color: var(--el-border-color-lighter);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .app-container {
    overflow-y: auto;
  }
}
</style>
