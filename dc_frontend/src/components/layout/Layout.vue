<template>
  <div class="app-layout" :class="{ 'is-dark': isDark }">
    <!-- 侧边栏 -->
    <div 
      class="sidebar" 
      :class="{ 'is-collapsed': isCollapsed }"
    >
      <div class="sidebar-header">
        <div class="logo">
          <img 
            v-if="!isCollapsed" 
            src="/logo.svg" 
            alt="数据资源中心" 
            class="logo-img"
          >
          <img 
            v-else 
            src="/logo-mini.svg" 
            alt="DRC" 
            class="logo-img-mini"
          >
          <span v-if="!isCollapsed" class="logo-text">数据资源中心</span>
        </div>
      </div>
      
      <div class="sidebar-content">
        <SidebarMenu :collapsed="isCollapsed" />
      </div>
    </div>
    
    <!-- 主内容区域 -->
    <div class="main-container">
      <!-- 顶部导航栏 -->
      <div class="header">
        <AppHeader 
          :collapsed="isCollapsed" 
          @toggle-sidebar="toggleSidebar"
        />
      </div>
      
      <!-- 面包屑导航 -->
      <div class="breadcrumb-container" v-if="showBreadcrumb">
        <Breadcrumb />
      </div>
      
      <!-- 页面内容 -->
      <div class="content">
        <router-view v-slot="{ Component, route }">
          <transition name="fade-transform" mode="out-in">
            <keep-alive :include="keepAliveComponents">
              <component :is="Component" :key="route.path" />
            </keep-alive>
          </transition>
        </router-view>
      </div>
      
      <!-- 底部 -->
      <div class="footer" v-if="showFooter">
        <AppFooter />
      </div>
    </div>
    
    <!-- 设置面板 -->
    <SettingsPanel v-if="showSettings" @close="showSettings = false" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { useAppStore } from '@/stores/app'
import { useUserStore } from '@/stores/user'
import SidebarMenu from './components/SidebarMenu.vue'
import AppHeader from './components/AppHeader.vue'
import AppFooter from './components/AppFooter.vue'
import Breadcrumb from './components/Breadcrumb.vue'
import SettingsPanel from './components/SettingsPanel.vue'

/**
 * 布局组件
 * 提供应用的整体布局结构
 */

const route = useRoute()
const appStore = useAppStore()
const userStore = useUserStore()

// 响应式状态
const showSettings = ref(false)

// 计算属性
const isCollapsed = computed(() => appStore.sidebar.collapsed)
const isDark = computed(() => appStore.theme === 'dark')
const showBreadcrumb = computed(() => {
  return !route.meta?.hideBreadcrumb && route.name !== 'Dashboard'
})
const showFooter = computed(() => {
  return !route.meta?.hideFooter
})

// 需要缓存的组件
const keepAliveComponents = computed(() => {
  return appStore.cachedViews
})

/**
 * 切换侧边栏折叠状态
 */
const toggleSidebar = (): void => {
  appStore.toggleSidebar()
}

/**
 * 处理窗口大小变化
 */
const handleResize = (): void => {
  const width = window.innerWidth
  
  if (width < 768) {
    // 移动端自动折叠侧边栏
    if (!isCollapsed.value) {
      appStore.toggleSidebar()
    }
  }
}

/**
 * 监听键盘快捷键
 */
const handleKeydown = (event: KeyboardEvent): void => {
  // Ctrl/Cmd + K 打开搜索
  if ((event.ctrlKey || event.metaKey) && event.key === 'k') {
    event.preventDefault()
    // TODO: 打开全局搜索
  }
  
  // Ctrl/Cmd + , 打开设置
  if ((event.ctrlKey || event.metaKey) && event.key === ',') {
    event.preventDefault()
    showSettings.value = true
  }
}

// 生命周期
onMounted(() => {
  window.addEventListener('resize', handleResize)
  window.addEventListener('keydown', handleKeydown)
  
  // 初始化检查窗口大小
  handleResize()
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  window.removeEventListener('keydown', handleKeydown)
})
</script>

<style lang="scss" scoped>
@import '@/styles/variables.scss';

.app-layout {
  display: flex;
  height: 100vh;
  background-color: var(--el-bg-color-page);
  
  &.is-dark {
    background-color: var(--el-bg-color-page);
  }
}

.sidebar {
  width: $sidebar-width;
  background-color: var(--el-bg-color);
  border-right: 1px solid var(--el-border-color-light);
  transition: width 0.3s ease;
  display: flex;
  flex-direction: column;
  position: relative;
  z-index: 1000;
  
  &.is-collapsed {
    width: $sidebar-collapsed-width;
  }
  
  .sidebar-header {
    height: $header-height;
    display: flex;
    align-items: center;
    padding: 0 16px;
    border-bottom: 1px solid var(--el-border-color-lighter);
    
    .logo {
      display: flex;
      align-items: center;
      gap: 8px;
      
      .logo-img,
      .logo-img-mini {
        width: 32px;
        height: 32px;
        object-fit: contain;
      }
      
      .logo-text {
        font-size: 18px;
        font-weight: 600;
        color: var(--el-text-color-primary);
        white-space: nowrap;
      }
    }
  }
  
  .sidebar-content {
    flex: 1;
    overflow-y: auto;
    overflow-x: hidden;
    
    &::-webkit-scrollbar {
      width: 4px;
    }
    
    &::-webkit-scrollbar-track {
      background: transparent;
    }
    
    &::-webkit-scrollbar-thumb {
      background-color: var(--el-border-color);
      border-radius: 2px;
      
      &:hover {
        background-color: var(--el-border-color-dark);
      }
    }
  }
}

.main-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.header {
  height: $header-height;
  background-color: var(--el-bg-color);
  border-bottom: 1px solid var(--el-border-color-light);
  z-index: 999;
}

.breadcrumb-container {
  padding: 12px 16px;
  background-color: var(--el-bg-color);
  border-bottom: 1px solid var(--el-border-color-lighter);
}

.content {
  flex: 1;
  padding: 16px;
  overflow-y: auto;
  background-color: var(--el-bg-color-page);
  
  &::-webkit-scrollbar {
    width: 8px;
  }
  
  &::-webkit-scrollbar-track {
    background: var(--el-bg-color-page);
  }
  
  &::-webkit-scrollbar-thumb {
    background-color: var(--el-border-color);
    border-radius: 4px;
    
    &:hover {
      background-color: var(--el-border-color-dark);
    }
  }
}

.footer {
  padding: 12px 16px;
  background-color: var(--el-bg-color);
  border-top: 1px solid var(--el-border-color-lighter);
  text-align: center;
  color: var(--el-text-color-secondary);
  font-size: 12px;
}

// 页面切换动画
.fade-transform-enter-active,
.fade-transform-leave-active {
  transition: all 0.3s ease;
}

.fade-transform-enter-from {
  opacity: 0;
  transform: translateX(30px);
}

.fade-transform-leave-to {
  opacity: 0;
  transform: translateX(-30px);
}

// 响应式设计
@media (max-width: 768px) {
  .sidebar {
    position: fixed;
    top: 0;
    left: 0;
    height: 100vh;
    z-index: 1001;
    
    &.is-collapsed {
      transform: translateX(-100%);
    }
  }
  
  .main-container {
    margin-left: 0;
  }
  
  .content {
    padding: 12px;
  }
}

@media (max-width: 480px) {
  .content {
    padding: 8px;
  }
  
  .breadcrumb-container {
    padding: 8px 12px;
  }
}
</style>