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
import { asyncRoutes } from '@/router'
import { filterRoutesByPermission } from '@/utils/permission'
import SidebarMenuItem from './SidebarMenuItem.vue'
import type { RouteRecordRaw } from 'vue-router'

const route = useRoute()
const appStore = useAppStore()

// 当前激活的菜单
const activeMenu = computed(() => {
  const { path } = route
  return path
})

// 过滤菜单路由（按隐藏标记与权限）
const menuRoutes = computed(() => {
  // 先按权限过滤（支持 noPermissionBehavior: 'hide'）
  const permitted = filterRoutesByPermission(asyncRoutes)
  // 再移除在菜单中隐藏的项
  return filterHiddenInMenu(permitted)
})

// 过滤路由，只显示有权限且不隐藏的路由
function filterHiddenInMenu(routes: RouteRecordRaw[]): RouteRecordRaw[] {
  return routes
    .filter(route => !(route.meta?.hidden || route.meta?.hideInMenu))
    .map(route => {
      const r = { ...route }
      if (r.children && r.children.length > 0) {
        r.children = filterHiddenInMenu(r.children)
      }
      return r
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