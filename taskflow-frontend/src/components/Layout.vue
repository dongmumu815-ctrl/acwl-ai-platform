<template>
  <div class="layout-container">
    <!-- 侧边栏 -->
    <el-aside
      :width="appStore.sidebarCollapsed ? '64px' : '240px'"
      class="layout-sidebar"
    >
      <div class="sidebar-header">
        <div v-if="!appStore.sidebarCollapsed" class="logo">
          <h2>TaskFlow</h2>
        </div>
        <div v-else class="logo-mini">
          <span>TF</span>
        </div>
      </div>
      
      <el-menu
        :default-active="$route.path"
        :collapse="appStore.sidebarCollapsed"
        :unique-opened="true"
        router
        class="sidebar-menu"
      >
        <el-menu-item index="/dashboard">
          <el-icon><Odometer /></el-icon>
          <template #title>仪表盘</template>
        </el-menu-item>
        
        <el-sub-menu index="/workflows">
          <template #title>
            <el-icon><Operation /></el-icon>
            <span>工作流管理</span>
          </template>
          <el-menu-item index="/workflows">工作流定义</el-menu-item>
          <el-menu-item index="/workflows/create">创建工作流</el-menu-item>
          <el-menu-item index="/workflows/instances">工作流实例</el-menu-item>
          <el-menu-item index="/tasks/instances">任务节点实例</el-menu-item>
        </el-sub-menu>
        
        <el-sub-menu index="/projects">
          <template #title>
            <el-icon><Folder /></el-icon>
            <span>项目管理</span>
          </template>
          <el-menu-item index="/projects">项目列表</el-menu-item>
          <el-menu-item index="/projects/create">创建项目</el-menu-item>
        </el-sub-menu>
        

        
        <el-menu-item index="/monitoring">
          <el-icon><Monitor /></el-icon>
          <template #title>实时监控</template>
        </el-menu-item>
        
        <el-menu-item index="/settings">
          <el-icon><Setting /></el-icon>
          <template #title>系统设置</template>
        </el-menu-item>
      </el-menu>
    </el-aside>
    
    <!-- 主内容区 -->
    <el-container class="layout-main">
      <!-- 头部 -->
      <el-header class="layout-header">
        <div class="header-left">
          <el-button
            type="text"
            @click="appStore.toggleSidebar()"
            class="sidebar-toggle"
          >
            <el-icon><Expand v-if="appStore.sidebarCollapsed" /><Fold v-else /></el-icon>
          </el-button>
          
          <!-- 项目切换下拉菜单 -->
          <el-dropdown 
            trigger="click" 
            class="project-selector"
            @command="handleProjectChange"
          >
            <div class="project-info">
              <el-icon><FolderOpened /></el-icon>
              <span class="project-name">
                {{ projectStore.currentProject?.name || '选择项目' }}
              </span>
              <el-icon class="dropdown-icon"><ArrowDown /></el-icon>
            </div>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item 
                  v-for="project in projectStore.activeProjects" 
                  :key="project.id"
                  :command="project"
                  :class="{ 'is-active': project.id === projectStore.currentProject?.id }"
                >
                  <div class="project-item">
                    <span class="project-title">{{ project.name }}</span>
                    <span class="project-desc">{{ project.description }}</span>
                  </div>
                </el-dropdown-item>
                <el-dropdown-item divided @click="$router.push('/projects')">
                  <el-icon><Setting /></el-icon>
                  管理项目
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
          
          <!-- 面包屑导航 -->
          <el-breadcrumb separator="/" class="breadcrumb">
            <el-breadcrumb-item
              v-for="item in appStore.breadcrumbs"
              :key="item.path"
              :to="item.path"
            >
              {{ item.title }}
            </el-breadcrumb-item>
          </el-breadcrumb>
        </div>
        
        <div class="header-right">
          <!-- 主题切换 -->
          <el-tooltip content="切换主题" placement="bottom">
            <el-button
              type="text"
              @click="toggleTheme"
              class="theme-toggle"
            >
              <el-icon><Sunny v-if="appStore.theme === 'dark'" /><Moon v-else /></el-icon>
            </el-button>
          </el-tooltip>
          
          <!-- 全屏切换 -->
          <el-tooltip content="全屏" placement="bottom">
            <el-button
              type="text"
              @click="toggleFullscreen"
              class="fullscreen-toggle"
            >
              <el-icon><FullScreen /></el-icon>
            </el-button>
          </el-tooltip>
          
          <!-- 用户菜单 -->
          <el-dropdown trigger="click" class="user-dropdown">
            <div class="user-info">
              <el-avatar :size="32" :src="userStore.userInfo?.avatar">
                <el-icon><User /></el-icon>
              </el-avatar>
              <span class="username">{{ userStore.userInfo?.username || '用户' }}</span>
              <el-icon class="dropdown-icon"><ArrowDown /></el-icon>
            </div>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item @click="$router.push('/profile')">
                  <el-icon><User /></el-icon>
                  个人资料
                </el-dropdown-item>
                <el-dropdown-item @click="$router.push('/settings')">
                  <el-icon><Setting /></el-icon>
                  系统设置
                </el-dropdown-item>
                <el-dropdown-item divided @click="handleLogout">
                  <el-icon><SwitchButton /></el-icon>
                  退出登录
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>
      
      <!-- 内容区域 -->
      <el-main class="layout-content">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </el-main>
    </el-container>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAppStore, useUserStore, useProjectStore } from '@/stores'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  FolderOpened,
  ArrowDown,
  Expand,
  Fold,
  Sunny,
  Moon,
  FullScreen,
  User,
  Setting,
  SwitchButton,
  Odometer,
  Operation,
  List,
  Folder,
  Monitor,
  Avatar
} from '@element-plus/icons-vue'

/**
 * 布局组件
 */
const router = useRouter()
const appStore = useAppStore()
const userStore = useUserStore()
const projectStore = useProjectStore()

/**
 * 切换主题
 */
const toggleTheme = () => {
  const newTheme = appStore.theme === 'light' ? 'dark' : 'light'
  appStore.setTheme(newTheme)
}

/**
 * 切换全屏
 */
const toggleFullscreen = () => {
  if (!document.fullscreenElement) {
    document.documentElement.requestFullscreen()
  } else {
    document.exitFullscreen()
  }
}

/**
 * 处理项目切换
 * @param {object} project 项目对象
 */
const handleProjectChange = async (project) => {
  try {
    // 更新当前项目
    projectStore.setCurrentProject(project)
    // 可以在这里添加其他需要刷新的逻辑
    // 比如重新加载工作流列表等
    console.log('已切换到项目:', project.name)
  } catch (error) {
    console.error('切换项目失败:', error)
  }
}

/**
 * 处理退出登录
 */
const handleLogout = async () => {
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
    ElMessage.success('已退出登录')
    router.push('/login')
  } catch (error) {
    // 用户取消操作
  }
}

/**
 * 监听窗口大小变化
 */
const handleResize = () => {
  if (window.innerWidth < 768) {
    appStore.setSidebar({ collapsed: true })
  }
}

/**
 * 组件挂载时添加事件监听
 */
onMounted(async () => {
  window.addEventListener('resize', handleResize)

  handleResize() // 初始检查
  
  // 加载项目列表
  try {
    console.log('开始加载项目列表...')

    // 添加错误处理，防止401错误导致自动跳转
    try {
      // 调用项目列表API，禁用自动跳转
      await projectStore.getProjectList({ skipAutoRedirect: true })
      console.log('项目列表加载完成:', projectStore.projects)
      console.log('活跃项目:', projectStore.activeProjects)
    } catch (apiError) {
      console.error('加载项目列表失败:', apiError)
      // alert('项目列表加载失败，但不会跳转登录页')
      // 不重新抛出错误，避免触发外层catch
      return
    }



    // 如果没有当前项目且有可用项目，设置第一个为当前项目
    if (!projectStore.currentProject && projectStore.activeProjects.length > 0) {
      projectStore.setCurrentProject(projectStore.activeProjects[0])
      console.log('设置当前项目:', projectStore.activeProjects[0])
    } else {
      console.log('当前项目状态:', projectStore.currentProject)
    }
  } catch (error) {
    console.error('加载项目列表失败:', error)
  }
})

/**
 * 组件卸载时移除事件监听
 */
onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
})
</script>

<style scoped>
.layout-container {
  height: 100vh;
  display: flex;
}

.layout-sidebar {
  background: #001529;
  transition: width 0.3s ease;
  overflow: hidden;
}

.sidebar-header {
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-bottom: 1px solid #1f2937;
}

.logo {
  color: white;
  font-weight: 600;
  font-size: 18px;
}

.logo h2 {
  margin: 0;
  color: #1890ff;
}

.logo-mini {
  width: 32px;
  height: 32px;
  background: #1890ff;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: 600;
  font-size: 14px;
}

.sidebar-menu {
  border-right: none;
  background: #001529;
}

/* 修复二级菜单背景色问题 */
.sidebar-menu :deep(.el-sub-menu .el-menu) {
  background-color: #000c17;
}

.sidebar-menu :deep(.el-menu-item),
.sidebar-menu :deep(.el-sub-menu__title) {
  color: rgba(255, 255, 255, 0.65);
}

.sidebar-menu :deep(.el-menu-item:hover),
.sidebar-menu :deep(.el-sub-menu__title:hover) {
  color: #1890ff;
  background: rgba(24, 144, 255, 0.1);
}

.sidebar-menu :deep(.el-menu-item.is-active) {
  color: #1890ff;
  background: rgba(24, 144, 255, 0.1);
}

.layout-main {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.layout-header {
  background: white;
  border-bottom: 1px solid #e8e8e8;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.sidebar-toggle {
  font-size: 18px;
  color: #666;
}

.project-selector {
  margin-left: 16px;
}

.project-info {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border: 1px solid #d9d9d9;
  border-radius: 6px;
  background: white;
  cursor: pointer;
  transition: all 0.3s;
  min-width: 200px;
}

.project-info:hover {
  border-color: #1890ff;
  box-shadow: 0 0 0 2px rgba(24, 144, 255, 0.2);
}

.project-name {
  flex: 1;
  font-size: 14px;
  color: #333;
  font-weight: 500;
}

.project-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.project-title {
  font-size: 14px;
  font-weight: 500;
  color: #333;
}

.project-desc {
  font-size: 12px;
  color: #999;
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.breadcrumb {
  font-size: 14px;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.theme-toggle,
.fullscreen-toggle {
  font-size: 18px;
  color: #666;
}

.user-dropdown {
  cursor: pointer;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 8px;
  border-radius: 6px;
  transition: background-color 0.3s;
}

.user-info:hover {
  background: #f5f5f5;
}

.username {
  font-size: 14px;
  color: #333;
  font-weight: 500;
}

.dropdown-icon {
  font-size: 12px;
  color: #999;
}

.layout-content {
  flex: 1;
  background: #f5f5f5;
  overflow: auto;
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

/* 暗色主题 */
.dark .layout-header {
  background: #1f2937;
  border-bottom-color: #374151;
}

.dark .user-info:hover {
  background: #374151;
}

.dark .username {
  color: #e5e7eb;
}

.dark .sidebar-toggle,
.dark .theme-toggle,
.dark .fullscreen-toggle {
  color: #9ca3af;
}

.dark .layout-content {
  background: #111827;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .layout-header {
    padding: 0 16px;
  }
  
  .header-left {
    gap: 12px;
  }
  
  .header-right {
    gap: 12px;
  }
  
  .username {
    display: none;
  }
  
  .breadcrumb {
    display: none;
  }
}
</style>