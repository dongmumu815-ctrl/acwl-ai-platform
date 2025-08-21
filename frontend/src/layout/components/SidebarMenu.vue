<template>
  <el-menu
    :default-active="activeMenu"
    :collapse="appStore.sidebarCollapsed"
    :unique-opened="true"
    router
    class="sidebar-menu"
    background-color="transparent"
    text-color="#bfcbd9"
    active-text-color="#409eff"
  >
    <template v-for="route in menuRoutes" :key="route.path">
      <SidebarMenuItem :route="route" />
    </template>
  </el-menu>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useAppStore } from '@/stores/app'
import { useUserStore } from '@/stores/user'
import { asyncRoutes } from '@/router'
import SidebarMenuItem from './SidebarMenuItem.vue'
import type { RouteRecordRaw } from 'vue-router'

const route = useRoute()
const appStore = useAppStore()
const userStore = useUserStore()

// 当前激活的菜单
const activeMenu = computed(() => {
  const { path } = route
  return path
})

// 过滤菜单路由
const menuRoutes = computed(() => {
  return filterMenuRoutes(asyncRoutes)
})

// 过滤路由，只显示有权限且不隐藏的路由
function filterMenuRoutes(routes: RouteRecordRaw[]): RouteRecordRaw[] {
  return routes.filter(route => {
    // 检查路由是否隐藏
    if (route.meta?.hidden) {
      return false
    }
    
    // 检查权限
    if (route.meta?.requiresAuth && !userStore.isLoggedIn) {
      return false
    }
    
    if (route.meta?.requiresAdmin && !userStore.isAdmin) {
      return false
    }
    
    // 递归过滤子路由
    if (route.children && route.children.length > 0) {
      route.children = filterMenuRoutes(route.children)
    }
    
    return true
  })
}
</script>

<style lang="scss" scoped>
.sidebar-menu {
  border: none;
  width: 100%;
  
  :deep(.el-menu-item) {
    height: 48px;
    line-height: 48px;
    margin: 4px 12px;
    border-radius: 6px;
    transition: all 0.3s ease;
    
    &:hover {
      background-color: rgba(255, 255, 255, 0.1) !important;
    }
    
    &.is-active {
      background-color: $primary-color !important;
      color: white !important;
      
      .el-icon {
        color: white !important;
      }
    }
    
    .el-icon {
      margin-right: 8px;
      font-size: 18px;
    }
  }
  
  :deep(.el-sub-menu) {
    .el-sub-menu__title {
      height: 48px;
      line-height: 48px;
      margin: 4px 12px;
      border-radius: 6px;
      transition: all 0.3s ease;
      
      &:hover {
        background-color: rgba(255, 255, 255, 0.1) !important;
      }
      
      .el-icon {
        margin-right: 8px;
        font-size: 18px;
      }
    }
    
    .el-menu {
      background-color: transparent;
      
      .el-menu-item {
        margin: 2px 24px;
        padding-left: 40px !important;
        
        &.is-active {
          background-color: rgba(64, 158, 255, 0.8) !important;
        }
      }
    }
  }
  
  // 折叠状态样式
  &.el-menu--collapse {
    :deep(.el-menu-item),
    :deep(.el-sub-menu__title) {
      margin: 4px 8px;
      text-align: center;
      
      .el-icon {
        margin-right: 0;
      }
    }
    
    :deep(.el-sub-menu) {
      .el-sub-menu__icon-arrow {
        display: none;
      }
    }
  }
}

// 暗色主题
.dark {
  .sidebar-menu {
    :deep(.el-menu-item) {
      &:hover {
        background-color: rgba(255, 255, 255, 0.05) !important;
      }
    }
    
    :deep(.el-sub-menu__title) {
      &:hover {
        background-color: rgba(255, 255, 255, 0.05) !important;
      }
    }
  }
}
</style>