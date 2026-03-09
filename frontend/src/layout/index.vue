<template>
  <div class="app-layout" :class="{ 'sidebar-collapsed': appStore.sidebarCollapsed }">
    <!-- 侧边栏 -->
    <aside class="sidebar" :style="{ width: appStore.sidebarWidth }">
      <div class="sidebar-header">
        <div class="logo" @click="$router.push('/dashboard')">
          <img :src="logo" alt="Logo" class="logo-icon" :style="{ width: '32px', height: '32px' }" />
          <span v-show="!appStore.sidebarCollapsed" class="logo-text">AI数据中台</span>
        </div>
      </div>
      
      <div class="sidebar-content">
        <SidebarMenu />
      </div>
    </aside>
    
    <!-- 主内容区域 -->
    <div class="main-container" :style="appStore.mainContentStyle">
      <!-- 顶部导航栏 -->
  <header class="header">
    <div class="header-left">
          <el-button
            type="text"
            class="sidebar-toggle"
            @click="appStore.toggleSidebar"
          >
            <el-icon :size="20">
              <Fold v-if="!appStore.sidebarCollapsed" />
              <Expand v-else />
            </el-icon>
          </el-button>
          
          <!-- 动态面包屑导航 -->
          <el-breadcrumb separator="/" class="breadcrumb">
            <el-breadcrumb-item
              v-for="(item, index) in breadcrumbList"
              :key="item.path"
              :to="index === breadcrumbList.length - 1 ? undefined : item.path"
            >
              <el-icon v-if="item.icon" class="breadcrumb-icon">
                <component :is="item.icon" />
              </el-icon>
              {{ item.title }}
            </el-breadcrumb-item>
          </el-breadcrumb>
        </div>
        
    <div class="header-right">
      <div class="header-actions">
        <!-- 消息通知 -->
        <el-badge :value="12" :max="99" class="notification-badge">
          <el-button type="text" class="action-btn">
            <el-icon :size="18">
              <Bell />
            </el-icon>
          </el-button>
        </el-badge>

        <!-- 帮助文档入口 -->
        <el-button type="text" class="action-btn" @click="openHelp">
          <el-icon :size="18">
            <QuestionFilled />
          </el-icon>
          <span style="margin-left:4px">帮助文档</span>
        </el-button>
            
            <!-- 用户头像下拉菜单 -->
            <el-dropdown trigger="click" @command="handleUserCommand">
              <div class="user-avatar">
                <el-avatar :size="32" :src="userStore.userAvatar" />
                <span class="username">{{ userStore.userName }}</span>
                <el-icon class="dropdown-icon">
                  <ArrowDown />
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
                    账户设置
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
      </header>
      
      <!-- 主要内容 -->
      <main class="main-content">
        <router-view v-slot="{ Component, route }">
          <transition name="fade" mode="out-in">
            <keep-alive :include="cachedViews">
              <component :is="Component" :key="route.path" />
            </keep-alive>
          </transition>
        </router-view>
      </main>
      
      <!-- 页脚 -->
      <footer class="footer">
        <div class="footer-content">
          <span>© 2024 ACWL AI. All rights reserved.</span>
          <div class="footer-links">
            <a href="#" @click.prevent="openHelp">帮助文档</a>
            <a href="#" @click.prevent>API文档</a>
            <a href="#" @click.prevent>联系我们</a>
          </div>
        </div>
      </footer>
    </div>
    

  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch, provide } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAppStore } from '@/stores/app'
import { useUserStore } from '@/stores/user'
import SidebarMenu from './components/SidebarMenu.vue'
import logo from '@/assets/logo.png'
import { 
  Fold, 
  Expand, 
  Box,
  Bell, 
  User, 
  Setting, 
  SwitchButton, 
  ArrowDown,
  Odometer,
  Monitor,
  FolderOpened,
  Tools,
  List,
  Upload,
  Plus,
  Document,
  Cpu,
  VideoCamera,
  Connection,
  Folder,
  Key,
  UserFilled,
  Grid,
  Shop
} from '@element-plus/icons-vue'
import { QuestionFilled } from '@element-plus/icons-vue'
import RobotIcon from '@/components/RobotIcon.vue'
import { ElMessage, ElMessageBox } from 'element-plus'

// 使用状态管理
const appStore = useAppStore()
const userStore = useUserStore()
const route = useRoute()
const router = useRouter()

// 图标映射
const iconMap: Record<string, any> = {
  Dashboard: Odometer,
  Box,
  Monitor,
  FolderOpened,
  Setting,
  Tools,
  List,
  Upload,
  Plus,
  User,
  UserFilled,
  Key,
  Document,
  Cpu,
  VideoCamera,
  Connection,
  Folder,
  Robot: RobotIcon,
  App: Grid,
  Shop
}

// 缓存的视图组件
const cachedViews = ref<string[]>([
  'Dashboard',
  'ModelList',
  'DeploymentList'
])

// 面包屑导航
const breadcrumbList = ref<Array<{ title: string; path: string; icon?: string }>>([])

// 生成面包屑导航
const generateBreadcrumb = () => {
  const matched = route.matched.filter(item => item.meta && item.meta.title)
  const breadcrumbs: Array<{ title: string; path: string; icon?: string }> = []
  
  matched.forEach((item, index) => {
    // 跳过根路径
    if (item.path === '/') return
    
    const breadcrumb = {
      title: item.meta?.title as string,
      path: item.path,
      icon: item.meta?.icon as string
    }
    
    breadcrumbs.push(breadcrumb)
  })
  
  breadcrumbList.value = breadcrumbs
}

// 监听路由变化
watch(route, () => {
  generateBreadcrumb()
}, { immediate: true })

// 处理用户下拉菜单命令
const handleUserCommand = async (command: string) => {
  switch (command) {
    case 'profile':
      router.push('/profile')
      break
    case 'settings':
      ElMessage.info('账户设置功能开发中...')
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
        router.push('/login')
      } catch (error) {
        // 用户取消操作
      }
      break
  }
}

// 帮助中心链接：根据当前页面上下文跳转到对应章节
const helpTopicMap: Record<string, string> = {
  Dashboard: 'quick-start',
  DatasourceList: 'datasource-list',
  DatasetList: 'datasource-list',
  ModelList: 'template-list',
  DeploymentList: 'scheduler',
  ResourceServers: 'security-and-permissions',
  ResourceGpus: 'security-and-permissions',
  SystemUsers: 'security-and-permissions',
  SystemRoles: 'security-and-permissions',
  SystemPermissions: 'security-and-permissions',
  SystemSettings: 'security-and-permissions',
  SystemLogs: 'troubleshooting',
  Monitoring: 'troubleshooting',
  InstructionSets: 'template-list',
  InstructionSetDetail: 'template-list',
  InstructionSetTest: 'template-list'
}

const openHelp = () => {
  const currentName = (route.name as string) || ''
  const topic = helpTopicMap[currentName] || ''
  if (topic) {
    router.push({ path: '/help', query: { topic } })
  } else {
    router.push({ path: '/help' })
  }
}

// 提供iconMap给子组件使用
provide('iconMap', iconMap)

// 初始化应用
onMounted(async () => {
  // 初始化应用设置
  appStore.initializeApp()
  
  // 初始化用户认证
  await userStore.initializeAuth()
  
  // 生成初始面包屑
  generateBreadcrumb()
})
</script>

<style lang="scss" scoped>
@use '@/styles/variables' as *;
@use '@/styles/mixins' as *;

.app-layout {
  display: flex;
  height: 100vh;
  overflow: hidden;
}

.sidebar {
  position: fixed;
  top: 0;
  left: 0;
  height: 100vh;
  background: $sidebar-bg;
  transition: width 0.3s ease;
  z-index: 1001;
  box-shadow: 2px 0 8px rgba(0, 0, 0, 0.1);
  
  .sidebar-header {
    height: $header-height;
    @include flex-center;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    
    .logo {
      @include flex-center;
      gap: 12px;
      padding: 0 20px;
      cursor: pointer;
      transition: all 0.3s ease;
      
      &:hover {
        opacity: 0.8;
      }
      
      .logo-icon {
        color: $primary-color;
        flex-shrink: 0;
      }
      
      .logo-text {
        font-size: 20px;
        font-weight: 600;
        color: white;
        white-space: nowrap;
      }
    }
  }
  
  .sidebar-content {
    height: calc(100vh - #{$header-height});
    overflow-y: auto;
    @include scrollbar(6px, transparent, rgba(255, 255, 255, 0.2));
  }
}

.main-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  transition: margin-left 0.3s ease;
}

.header {
  height: $header-height;
  background: $header-bg;
  border-bottom: 1px solid $header-border-color;
  @include flex-between;
  padding: 0 24px;
  position: sticky;
  top: 0;
  z-index: 1000;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
  
  .header-left {
    @include flex-start;
    gap: 16px;
    flex: 1;
    
    .sidebar-toggle {
      padding: 8px;
      border-radius: $border-radius;
      transition: all 0.3s ease;
      
      &:hover {
        background-color: $bg-color-hover;
      }
    }
    
    .breadcrumb {
      margin-left: 8px;
      
      .breadcrumb-icon {
        margin-right: 4px;
        font-size: 14px;
      }
      
      :deep(.el-breadcrumb__item) {
        .el-breadcrumb__inner {
          color: $text-color-regular;
          font-weight: 400;
          
          &:hover {
            color: $primary-color;
          }
        }
        
        &:last-child .el-breadcrumb__inner {
          color: $text-color-primary;
          font-weight: 500;
        }
      }
    }
  }
  
  .header-right {
    @include flex-end;
    
    .header-actions {
      @include flex-center;
      gap: 16px;
      
      .notification-badge {
        .action-btn {
          padding: 8px;
          border-radius: $border-radius;
          transition: all 0.3s ease;
          
          &:hover {
            background-color: $bg-color-hover;
          }
        }
      }
      
      .user-avatar {
        @include flex-center;
        gap: 8px;
        padding: 4px 12px 4px 4px;
        border-radius: 20px;
        cursor: pointer;
        transition: all 0.3s ease;
        
        &:hover {
          background-color: $bg-color-hover;
        }
        
        .username {
          font-size: 14px;
          font-weight: 500;
          color: $text-color-primary;
          max-width: 100px;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }
        
        .dropdown-icon {
          font-size: 12px;
          color: $text-color-secondary;
          transition: transform 0.3s ease;
        }
        
        &:hover .dropdown-icon {
          transform: rotate(180deg);
        }
      }
    }
  }
}

.main-content {
  flex: 1;
  padding: 24px;
  background: $bg-color-page;
  overflow-y: auto;
  @include scrollbar();
}

.footer {
  height: $footer-height;
  background: $header-bg;
  border-top: 1px solid $header-border-color;
  
  .footer-content {
    height: 100%;
    @include flex-between;
    padding: 0 24px;
    color: $text-color-secondary;
    font-size: $font-size-small;
    
    .footer-links {
      @include flex-center;
      gap: 16px;
      
      a {
        color: $text-color-secondary;
        transition: color 0.3s ease;
        
        &:hover {
          color: $primary-color;
        }
      }
    }
  }
}

// 响应式设计
@include respond-to(md) {
  .main-content {
    padding: 16px;
  }
  
  .header {
    padding: 0 16px;
  }
  
  .footer .footer-content {
    padding: 0 16px;
  }
}

@include respond-to(sm) {
  .main-content {
    padding: 12px;
  }
  
  .header {
    padding: 0 12px;
  }
  
  .footer .footer-content {
    padding: 0 12px;
    flex-direction: column;
    gap: 8px;
    text-align: center;
  }
}

// 暗色主题
.dark {
  .sidebar {
    background: #1f1f1f;
    
    .sidebar-header {
      border-bottom-color: rgba(255, 255, 255, 0.05);
    }
  }
  
  .header {
    background: var(--el-bg-color);
    border-bottom-color: var(--el-border-color);
  }
  
  .main-content {
    background: var(--el-bg-color-page);
  }
  
  .footer {
    background: var(--el-bg-color);
    border-top-color: var(--el-border-color);
  }
}

// 侧边栏折叠状态
.sidebar-collapsed {
  .sidebar {
    .sidebar-header .logo {
      padding: 0 16px;
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
    @include flex-start;
    gap: 8px;
    
    .el-icon {
      font-size: 14px;
      color: $text-color-secondary;
    }
    
    &:hover {
      background-color: $bg-color-hover;
      
      .el-icon {
        color: $primary-color;
      }
    }
    
    &.is-divided {
      border-top: 1px solid var(--el-border-color-lighter);
      margin-top: 4px;
      padding-top: 12px;
    }
  }
}

// 通知徽章样式
:deep(.el-badge) {
  .el-badge__content {
    border: 2px solid $header-bg;
  }
}

// 过渡动画
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>