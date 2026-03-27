<template>
  <div class="app-header">
    <!-- 左侧区域 -->
    <div class="header-left">
      <!-- 侧边栏切换按钮 -->
      <el-button
        type="text"
        class="sidebar-toggle"
        @click="toggleSidebar"
      >
        <el-icon :size="20">
          <Fold v-if="!appStore.sidebarCollapsed" />
          <Expand v-else />
        </el-icon>
      </el-button>
      
      <!-- 面包屑导航 -->
      <el-breadcrumb separator="/" class="breadcrumb">
        <el-breadcrumb-item
          v-for="item in breadcrumbList"
          :key="item.path"
          :to="item.path === currentRoute.path ? undefined : item.path"
        >
          {{ item.title }}
        </el-breadcrumb-item>
      </el-breadcrumb>
    </div>
    
    <!-- 右侧区域 -->
    <div class="header-right">
      <!-- 全屏切换 -->
      <el-tooltip content="全屏" placement="bottom">
        <el-button
          type="text"
          class="header-action"
          @click="toggleFullscreen"
        >
          <el-icon :size="18">
            <FullScreen v-if="!isFullscreen" />
            <Aim v-else />
          </el-icon>
        </el-button>
      </el-tooltip>
      
      <!-- 主题切换 -->
      <el-tooltip content="主题切换" placement="bottom">
        <el-button
          type="text"
          class="header-action"
          @click="toggleTheme"
        >
          <el-icon :size="18">
            <Sunny v-if="appStore.theme === 'dark'" />
            <Moon v-else />
          </el-icon>
        </el-button>
      </el-tooltip>
      
      <!-- 语言切换 -->
      <el-dropdown trigger="click" @command="handleLanguageChange">
        <el-button type="text" class="header-action">
          <el-icon :size="18">
            <Operation />
          </el-icon>
        </el-button>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item command="zh-CN" :disabled="appStore.language === 'zh-CN'">
              简体中文
            </el-dropdown-item>
            <el-dropdown-item command="en-US" :disabled="appStore.language === 'en-US'">
              English
            </el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
      
      <!-- 消息通知 -->
      <el-badge :value="unreadCount" :hidden="unreadCount === 0" class="notification-badge">
        <el-button type="text" class="header-action" @click="showNotifications">
          <el-icon :size="18">
            <Bell />
          </el-icon>
        </el-button>
      </el-badge>
      
      <!-- 用户菜单 -->
      <el-dropdown trigger="click" @command="handleUserMenuCommand">
        <div class="user-info">
          <el-avatar
            :size="32"
            :src="userStore.userInfo?.avatar"
            class="user-avatar"
          >
            <el-icon><User /></el-icon>
          </el-avatar>
          <span class="username">{{ userStore.displayName }}</span>
          <el-icon class="dropdown-icon"><ArrowDown /></el-icon>
        </div>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item command="profile">
              <el-icon><User /></el-icon>
              个人中心
            </el-dropdown-item>
            <el-dropdown-item command="settings">
              <el-icon><Setting /></el-icon>
              设置
            </el-dropdown-item>
            <el-dropdown-item divided command="logout">
              <el-icon><SwitchButton /></el-icon>
              退出登录
            </el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Fold,
  Expand,
  FullScreen,
  Aim,
  Sunny,
  Moon,
  Operation,
  Bell,
  User,
  ArrowDown,
  Setting,
  SwitchButton
} from '@element-plus/icons-vue'
import { useAppStore } from '@/stores/app'
import { useUserStore } from '@/stores/user'

const route = useRoute()
const router = useRouter()
const appStore = useAppStore()
const userStore = useUserStore()

const currentRoute = computed(() => route)
const isFullscreen = ref(false)
const unreadCount = ref(0)

// 面包屑导航
const breadcrumbList = computed(() => {
  const matched = route.matched.filter(item => item.meta && item.meta.title)
  const breadcrumbs = matched.map(item => ({
    path: item.path,
    title: item.meta?.title || item.name as string
  }))
  
  // 如果不是首页，添加首页到面包屑
  if (breadcrumbs.length > 0 && breadcrumbs[0].path !== '/dashboard') {
    breadcrumbs.unshift({
      path: '/dashboard',
      title: '首页'
    })
  }
  
  return breadcrumbs
})

// 切换侧边栏
const toggleSidebar = () => {
  appStore.toggleSidebar()
}

// 切换主题
const toggleTheme = () => {
  const newTheme = appStore.theme === 'light' ? 'dark' : 'light'
  appStore.setTheme(newTheme)
}

// 切换全屏
const toggleFullscreen = () => {
  if (!document.fullscreenElement) {
    document.documentElement.requestFullscreen()
    isFullscreen.value = true
  } else {
    document.exitFullscreen()
    isFullscreen.value = false
  }
}

// 监听全屏状态变化
const handleFullscreenChange = () => {
  isFullscreen.value = !!document.fullscreenElement
}

// 语言切换
const handleLanguageChange = (language: string) => {
  appStore.setLanguage(language)
  ElMessage.success('语言切换成功')
}

// 显示通知
const showNotifications = () => {
  ElMessage.info('暂无新消息')
}

// 用户菜单操作
const handleUserMenuCommand = async (command: string) => {
  switch (command) {
    case 'profile':
      router.push('/profile')
      break
    case 'settings':
      router.push('/settings')
      break
    case 'logout':
      try {
        await ElMessageBox.confirm(
          '确定要退出登录吗？',
          '提示',
          {
            confirmButtonText: '确定',
            cancelButtonText: '取消',
            type: 'warning'
          }
        )
        await userStore.logout()
        ElMessage.success('退出登录成功')
        router.push('/login')
      } catch {
        // 用户取消
      }
      break
  }
}

onMounted(() => {
  document.addEventListener('fullscreenchange', handleFullscreenChange)
})

onUnmounted(() => {
  document.removeEventListener('fullscreenchange', handleFullscreenChange)
})
</script>

<style lang="scss" scoped>
.app-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 100%;
  padding: 0 20px;
  background: var(--el-bg-color);
  border-bottom: 1px solid var(--el-border-color-light);
  transition: all 0.3s ease;
  
  .header-left {
    display: flex;
    align-items: center;
    flex: 1;
    
    .sidebar-toggle {
      margin-right: 16px;
      color: var(--el-text-color-regular);
      
      &:hover {
        color: var(--el-color-primary);
        background-color: var(--el-color-primary-light-9);
      }
    }
    
    .breadcrumb {
      :deep(.el-breadcrumb__item) {
        .el-breadcrumb__inner {
          color: var(--el-text-color-regular);
          font-weight: normal;
          
          &:hover {
            color: var(--el-color-primary);
          }
        }
        
        &:last-child {
          .el-breadcrumb__inner {
            color: var(--el-text-color-primary);
            font-weight: 500;
          }
        }
      }
    }
  }
  
  .header-right {
    display: flex;
    align-items: center;
    gap: 8px;
    
    .header-action {
      width: 40px;
      height: 40px;
      border-radius: 50%;
      color: var(--el-text-color-regular);
      transition: all 0.3s ease;
      
      &:hover {
        color: var(--el-color-primary);
        background-color: var(--el-color-primary-light-9);
      }
    }
    
    .notification-badge {
      :deep(.el-badge__content) {
        top: 8px;
        right: 8px;
      }
    }
    
    .user-info {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 8px 12px;
      border-radius: 20px;
      cursor: pointer;
      transition: all 0.3s ease;
      
      &:hover {
        background-color: var(--el-color-primary-light-9);
      }
      
      .user-avatar {
        border: 2px solid var(--el-border-color-light);
      }
      
      .username {
        font-size: 14px;
        font-weight: 500;
        color: var(--el-text-color-primary);
        max-width: 100px;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }
      
      .dropdown-icon {
        font-size: 12px;
        color: var(--el-text-color-regular);
        transition: transform 0.3s ease;
      }
    }
  }
}

// 响应式设计
@media (max-width: 768px) {
  .app-header {
    padding: 0 12px;
    
    .header-left {
      .breadcrumb {
        display: none;
      }
    }
    
    .header-right {
      gap: 4px;
      
      .user-info {
        .username {
          display: none;
        }
      }
    }
  }
}

// 暗色主题
.dark {
  .app-header {
    background: var(--el-bg-color);
    border-bottom-color: var(--el-border-color);
  }
}
</style>
