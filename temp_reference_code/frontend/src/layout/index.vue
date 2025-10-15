<template>
  <div class="admin-layout">
    <!-- 顶部导航 -->
    <el-header class="admin-header" height="60px">
      <div style="display: flex; justify-content: space-between; align-items: center; height: 100%; padding: 0 20px;">
        <div style="display: flex; align-items: center;">
          <h2 style="margin: 0; color: #333;">ACWL API 管理后台</h2>
        </div>
        <div style="display: flex; align-items: center; gap: 16px;">
          <span>欢迎，{{ userInfo?.username }}</span>
          <el-button type="primary" @click="handleLogout">退出登录</el-button>
        </div>
      </div>
    </el-header>
    
    <!-- 主体内容 -->
    <el-container class="admin-content">
      <!-- 侧边栏 -->
      <el-aside class="admin-sidebar" width="200px">
        <el-menu
          :default-active="$route.path"
          router
          background-color="#001529"
          text-color="#fff"
          active-text-color="#1890ff"
        >
          <el-menu-item
            v-for="route in menuRoutes"
            :key="route.path"
            :index="route.path"
          >
            <el-icon><component :is="route.meta.icon" /></el-icon>
            <span>{{ route.meta.title }}</span>
          </el-menu-item>
        </el-menu>
      </el-aside>
      
      <!-- 主内容区 -->
      <el-main class="admin-main">
        <router-view />
      </el-main>
    </el-container>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { ElMessageBox } from 'element-plus'

const router = useRouter()
const authStore = useAuthStore()

// 用户信息
const userInfo = computed(() => authStore.userInfo)

// 菜单路由（过滤掉隐藏的路由）
const menuRoutes = computed(() => {
  const routes = router.getRoutes()
  const layoutRoute = routes.find(route => route.path === '/')
  if (layoutRoute && layoutRoute.children) {
    return layoutRoute.children.filter(child => !child.meta?.hidden)
  }
  return []
})

// 退出登录
const handleLogout = async () => {
  try {
    await ElMessageBox.confirm('确定要退出登录吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    authStore.logout()
    router.push('/login')
  } catch {
    // 用户取消
  }
}
</script>

<style scoped>
.admin-layout {
  height: 100vh;
  display: flex;
  flex-direction: column;
}

.admin-header {
  background: #fff;
  box-shadow: 0 1px 4px rgba(0,21,41,.08);
  z-index: 1000;
}

.admin-content {
  flex: 1;
  overflow: hidden;
}

.admin-sidebar {
  background: #001529;
  overflow-y: auto;
}

.admin-main {
  background: #f5f5f5;
  overflow-y: auto;
}

:deep(.el-menu) {
  border-right: none;
}

:deep(.el-menu-item) {
  height: 50px;
  line-height: 50px;
}

:deep(.el-menu-item:hover) {
  background-color: #1890ff !important;
}

:deep(.el-menu-item.is-active) {
  background-color: #1890ff !important;
}
</style>