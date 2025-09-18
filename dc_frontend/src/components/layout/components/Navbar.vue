<template>
  <div class="navbar">
    <div class="navbar-left">
      <!-- 折叠按钮 -->
      <div class="hamburger-container" @click="toggleSidebar">
        <el-icon class="hamburger" :class="{ 'is-active': !collapsed }">
          <Fold v-if="!collapsed" />
          <Expand v-else />
        </el-icon>
      </div>
      
      <!-- 面包屑导航 -->
      <Breadcrumb class="breadcrumb-container" />
    </div>
    
    <div class="navbar-right">
      <!-- 全屏按钮 -->
      <div class="right-menu-item hover-effect" @click="toggleFullscreen">
        <el-icon>
          <FullScreen v-if="!isFullscreen" />
          <Aim v-else />
        </el-icon>
      </div>
      
      <!-- 主题切换 -->
      <div class="right-menu-item hover-effect" @click="toggleTheme">
        <el-icon>
          <Sunny v-if="isDark" />
          <Moon v-else />
        </el-icon>
      </div>
      
      <!-- 消息通知 -->
      <el-badge :value="unreadCount" :hidden="unreadCount === 0" class="right-menu-item">
        <el-icon class="hover-effect">
          <Bell />
        </el-icon>
      </el-badge>
      
      <!-- 用户下拉菜单 -->
      <el-dropdown class="avatar-container" trigger="click" @command="handleCommand">
        <div class="avatar-wrapper">
          <el-avatar :size="32" :src="userStore.user?.avatar">
            <el-icon><User /></el-icon>
          </el-avatar>
          <span class="username">{{ userStore.user?.username || '用户' }}</span>
          <el-icon class="caret-down">
            <CaretBottom />
          </el-icon>
        </div>
        
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item command="profile">
              <el-icon><User /></el-icon>
              个人中心
            </el-dropdown-item>
            <el-dropdown-item command="settings">
              <el-icon><Setting /></el-icon>
              系统设置
            </el-dropdown-item>
            <el-dropdown-item divided command="logout" :disabled="userStore.loading">
              <el-icon v-if="!userStore.loading"><SwitchButton /></el-icon>
              <el-icon v-else class="is-loading"><Loading /></el-icon>
              {{ userStore.loading ? '退出中...' : '退出登录' }}
            </el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Fold,
  Expand,
  FullScreen,
  Aim,
  Sunny,
  Moon,
  Bell,
  User,
  CaretBottom,
  Setting,
  SwitchButton,
  Loading
} from '@element-plus/icons-vue'
import { useAppStore } from '@/stores/app'
import { useUserStore } from '@/stores/user'
import Breadcrumb from './Breadcrumb.vue'

/**
 * 顶部导航栏组件
 * 包含侧边栏折叠、面包屑导航、全屏、主题切换、用户菜单等功能
 */

const router = useRouter()
const appStore = useAppStore()
const userStore = useUserStore()

// 响应式数据
const isFullscreen = ref(false)
const unreadCount = ref(0)

// 计算属性
const collapsed = computed(() => appStore.sidebar.collapsed)
const isDark = computed(() => appStore.theme === 'dark')

/**
 * 切换侧边栏折叠状态
 */
function toggleSidebar(): void {
  appStore.toggleSidebar()
}

/**
 * 切换全屏模式
 */
function toggleFullscreen(): void {
  if (!document.fullscreenElement) {
    document.documentElement.requestFullscreen()
    isFullscreen.value = true
  } else {
    if (document.exitFullscreen) {
      document.exitFullscreen()
      isFullscreen.value = false
    }
  }
}

/**
 * 切换主题
 */
function toggleTheme(): void {
  appStore.toggleTheme()
}

/**
 * 处理用户下拉菜单命令
 * @param command 命令类型
 */
function handleCommand(command: string): void {
  switch (command) {
    case 'profile':
      handleProfile()
      break
    case 'settings':
      handleSettings()
      break
    case 'logout':
      handleLogout()
      break
    default:
      break
  }
}

/**
 * 处理个人中心
 */
function handleProfile(): void {
  router.push('/profile')
}

/**
 * 处理系统设置
 */
function handleSettings(): void {
  router.push('/settings')
}

/**
 * 处理退出登录
 */
async function handleLogout(): Promise<void> {
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
    
    // 调用用户store的退出登录方法
    await userStore.logout()
    
    // 跳转到登录页面
    await router.push('/login')
  } catch (error: any) {
    // 如果不是用户取消操作，显示错误信息
    if (error.message && !error.message.includes('cancel')) {
      console.error('退出登录失败:', error)
      ElMessage.error(error.message || '退出登录失败，请重试')
    }
  }
}

// 监听全屏状态变化
document.addEventListener('fullscreenchange', () => {
  isFullscreen.value = !!document.fullscreenElement
})
</script>

<style lang="scss" scoped>
@import '@/styles/variables.scss';

.navbar {
  height: $navbar-height;
  overflow: hidden;
  position: relative;
  background: var(--el-bg-color);
  box-shadow: 0 1px 4px rgba(0, 21, 41, 0.08);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
  transition: all 0.3s ease;
  
  .navbar-left {
    display: flex;
    align-items: center;
    flex: 1;
    
    .hamburger-container {
      line-height: $navbar-height;
      height: $navbar-height;
      cursor: pointer;
      transition: background 0.3s ease;
      padding: 0 8px;
      border-radius: 4px;
      
      &:hover {
        background: var(--el-color-primary-light-9);
      }
      
      .hamburger {
        display: inline-block;
        vertical-align: middle;
        width: 20px;
        height: 20px;
        font-size: 18px;
        color: var(--el-text-color-primary);
        transition: all 0.3s ease;
        
        &.is-active {
          transform: rotate(180deg);
        }
      }
    }
    
    .breadcrumb-container {
      margin-left: 16px;
      flex: 1;
    }
  }
  
  .navbar-right {
    display: flex;
    align-items: center;
    gap: 8px;
    
    .right-menu-item {
      display: inline-block;
      padding: 8px;
      border-radius: 4px;
      cursor: pointer;
      transition: all 0.3s ease;
      
      &.hover-effect:hover {
        background: var(--el-color-primary-light-9);
        color: var(--el-color-primary);
      }
      
      .el-icon {
        font-size: 18px;
        color: var(--el-text-color-primary);
        transition: color 0.3s ease;
        
        &.hover-effect:hover {
          color: var(--el-color-primary);
        }
      }
    }
    
    .avatar-container {
      margin-left: 8px;
      
      .avatar-wrapper {
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 4px 8px;
        border-radius: 20px;
        cursor: pointer;
        transition: all 0.3s ease;
        
        &:hover {
          background: var(--el-color-primary-light-9);
        }
        
        .username {
          font-size: 14px;
          color: var(--el-text-color-primary);
          font-weight: 500;
          max-width: 100px;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }
        
        .caret-down {
          font-size: 12px;
          color: var(--el-text-color-secondary);
          transition: transform 0.3s ease;
        }
        
        &:hover .caret-down {
          transform: rotate(180deg);
        }
      }
    }
  }
}

// 下拉菜单样式
:deep(.el-dropdown-menu) {
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  border: 1px solid var(--el-border-color-light);
  
  .el-dropdown-menu__item {
    padding: 8px 16px;
    display: flex;
    align-items: center;
    gap: 8px;
    transition: all 0.3s ease;
    
    &:hover {
      background: var(--el-color-primary-light-9);
      color: var(--el-color-primary);
    }
    
    .el-icon {
      font-size: 16px;
    }
  }
}

// 暗色主题适配
.dark {
  .navbar {
    background: var(--el-bg-color);
    box-shadow: 0 1px 4px rgba(0, 0, 0, 0.3);
    
    .hamburger-container {
      &:hover {
        background: rgba(255, 255, 255, 0.1);
      }
    }
    
    .right-menu-item {
      &.hover-effect:hover {
        background: rgba(255, 255, 255, 0.1);
      }
    }
    
    .avatar-container {
      .avatar-wrapper {
        &:hover {
          background: rgba(255, 255, 255, 0.1);
        }
      }
    }
  }
}

// 响应式设计
@media (max-width: 768px) {
  .navbar {
    padding: 0 12px;
    
    .navbar-left {
      .breadcrumb-container {
        margin-left: 12px;
      }
    }
    
    .navbar-right {
      gap: 4px;
      
      .avatar-container {
        .avatar-wrapper {
          .username {
            display: none;
          }
        }
      }
    }
  }
}

@media (max-width: 480px) {
  .navbar {
    .navbar-right {
      .right-menu-item {
        padding: 6px;
        
        .el-icon {
          font-size: 16px;
        }
      }
    }
  }
}
</style>