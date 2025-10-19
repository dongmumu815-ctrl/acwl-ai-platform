<template>
  <!-- 单个菜单项 -->
  <el-menu-item
    v-if="!hasChildren"
    :index="resolvePath"
    :class="{ 'is-active': isActive }"
  >
    <el-icon v-if="menuIcon">
      <component :is="menuIcon" />
    </el-icon>
    <template #title>
      <span>{{ menuTitle }}</span>
    </template>
  </el-menu-item>
  
  <!-- 子菜单 -->
  <el-sub-menu
    v-else
    :index="resolvePath"
    :class="{ 'is-active': hasActiveChild }"
  >
    <template #title>
      <el-icon v-if="menuIcon">
        <component :is="menuIcon" />
      </el-icon>
      <span>{{ menuTitle }}</span>
    </template>
    
    <template v-for="child in visibleChildren" :key="child.path">
      <SidebarMenuItem :route="child" :base-path="resolvePath" />
    </template>
  </el-sub-menu>
</template>

<script setup lang="ts">
import { computed, inject } from 'vue'
import { useRoute } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { checkRoutePermission } from '@/utils/permission'
import type { RouteRecordRaw } from 'vue-router'

interface Props {
  route: RouteRecordRaw
  basePath?: string
}

const props = withDefaults(defineProps<Props>(), {
  basePath: ''
})

const currentRoute = useRoute()
const userStore = useUserStore()
const iconMap = inject<Record<string, any>>('iconMap', {})

/**
 * 获取菜单项显示的标题
 * 特殊处理仪表板路由，显示子路由的标题
 */
const menuTitle = computed(() => {
  // 特殊处理：如果是仪表板根路由且有dashboard子路由，显示dashboard的标题
  if (props.route.path === '/' && props.route.children && 
      props.route.children.some(child => child.name === 'Dashboard')) {
    const dashboardChild = props.route.children.find(child => child.name === 'Dashboard')
    return dashboardChild?.meta?.title || dashboardChild?.name || '仪表盘'
  }
  
  return props.route.meta?.title || props.route.name
})

/**
 * 获取菜单项显示的图标
 * 特殊处理仪表板路由，显示子路由的图标
 */
const menuIcon = computed(() => {
  let iconName: string | undefined
  
  // 特殊处理：如果是仪表板根路由且有dashboard子路由，显示dashboard的图标
  if (props.route.path === '/' && props.route.children && 
      props.route.children.some(child => child.name === 'Dashboard')) {
    const dashboardChild = props.route.children.find(child => child.name === 'Dashboard')
    iconName = dashboardChild?.meta?.icon
  } else {
    iconName = props.route.meta?.icon
  }
  
  // 通过iconMap获取实际的图标组件
  return iconName ? iconMap[iconName] : undefined
})

// 解析完整路径
const resolvePath = computed(() => {
  // 特殊处理：如果是仪表板根路由且有dashboard子路由，直接返回/dashboard
  if (props.route.path === '/' && props.route.children && 
      props.route.children.some(child => child.name === 'Dashboard')) {
    return '/dashboard'
  }
  
  if (props.route.path.startsWith('/')) {
    return props.route.path
  }
  return `${props.basePath}/${props.route.path}`.replace(/\/+/g, '/')
})

// 检查是否有子菜单
// 特殊处理：仪表板即使有children也显示为一级菜单
const hasChildren = computed(() => {
  // 如果是仪表板路由，强制显示为一级菜单
  if (props.route.path === '/' || props.route.name === 'Dashboard' || 
      (props.route.children && props.route.children.some(child => child.name === 'Dashboard'))) {
    return false
  }
  return props.route.children && props.route.children.length > 0 && visibleChildren.value.length > 0
})

// 可见的子路由
const visibleChildren = computed(() => {
  if (!props.route.children) return []
  
  return props.route.children.filter(child => {
    // 菜单隐藏标记
    if (child.meta?.hidden || child.meta?.hideInMenu) return false

    // 基础认证检查
    if (child.meta?.requiresAuth && !userStore.isLoggedIn) return false
    if (child.meta?.requiresAdmin && !userStore.isAdmin) return false

    // 统一的权限/角色检查
    const result = checkRoutePermission({ meta: child.meta || {} } as any)
    if (!result.hasPermission) return false

    return true
  })
})

// 检查当前菜单项是否激活
const isActive = computed(() => {
  // 特殊处理：仪表板路由的激活状态判断
  if (props.route.path === '/' && props.route.children && 
      props.route.children.some(child => child.name === 'Dashboard')) {
    return currentRoute.path === '/dashboard' || currentRoute.path === '/'
  }
  
  return currentRoute.path === resolvePath.value
})

// 检查是否有激活的子菜单
const hasActiveChild = computed(() => {
  if (!props.route.children) return false
  
  return props.route.children.some(child => {
    const childPath = child.path.startsWith('/') 
      ? child.path 
      : `${resolvePath.value}/${child.path}`.replace(/\/+/g, '/')
    return currentRoute.path.startsWith(childPath)
  })
})
</script>

<style lang="scss" scoped>
// 样式已在父组件中定义
</style>