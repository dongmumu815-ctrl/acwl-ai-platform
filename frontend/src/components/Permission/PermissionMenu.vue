<template>
  <el-menu v-bind="$attrs" v-on="$listeners">
    <template v-for="item in visibleMenuItems" :key="item.key">
      <!-- 子菜单 -->
      <el-sub-menu
        v-if="item.children && item.children.length > 0"
        :index="item.key"
        :disabled="!hasMenuAccess(item)"
      >
        <template #title>
          <el-icon v-if="item.icon">
            <component :is="item.icon" />
          </el-icon>
          <span>{{ item.label }}</span>
        </template>
        
        <PermissionMenu
          :menu-items="item.children"
          @menu-select="handleMenuSelect"
        />
      </el-sub-menu>
      
      <!-- 菜单项 -->
      <el-menu-item
        v-else
        :index="item.key"
        :disabled="!hasMenuAccess(item)"
        @click="handleMenuClick(item)"
      >
        <el-icon v-if="item.icon">
          <component :is="item.icon" />
        </el-icon>
        <template #title>
          <span>{{ item.label }}</span>
        </template>
      </el-menu-item>
    </template>
  </el-menu>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { usePermission } from '@/composables/usePermission'
import type { PermissionConfig } from '@/types/router'

/**
 * 权限菜单组件
 * 根据权限配置过滤和控制菜单项
 */

interface MenuItem {
  /** 菜单唯一标识 */
  key: string
  /** 菜单标签 */
  label: string
  /** 菜单图标 */
  icon?: string | Component
  /** 权限代码 */
  permission?: string
  /** 权限代码数组 */
  permissions?: string[]
  /** 角色代码 */
  role?: string
  /** 角色代码数组 */
  roles?: string[]
  /** 权限检查模式 */
  mode?: 'any' | 'all'
  /** 路由路径 */
  route?: string
  /** 点击处理函数 */
  handler?: () => void
  /** 子菜单 */
  children?: MenuItem[]
  /** 是否禁用 */
  disabled?: boolean
  /** 显示条件函数 */
  show?: () => boolean
}

interface Props {
  /** 菜单项配置 */
  menuItems: MenuItem[]
  /** 无权限时的行为 */
  behavior?: 'hide' | 'disable'
}

const props = withDefaults(defineProps<Props>(), {
  behavior: 'hide'
})

const emit = defineEmits<{
  menuSelect: [item: MenuItem]
  menuClick: [item: MenuItem]
}>()

const { checkPermission } = usePermission()

// 检查菜单项权限
const hasMenuAccess = (item: MenuItem): boolean => {
  if (item.disabled) return false
  
  const permissionConfig: PermissionConfig = {
    permission: item.permission || item.permissions,
    role: item.role || item.roles,
    mode: item.mode || 'any'
  }
  
  return checkPermission(permissionConfig).value
}

// 过滤可见的菜单项
const visibleMenuItems = computed(() => {
  const filterMenuItems = (items: MenuItem[]): MenuItem[] => {
    return items.filter(item => {
      // 检查显示条件
      if (typeof item.show === 'function' && !item.show()) {
        return false
      }
      
      // 检查权限
      if (props.behavior === 'hide' && !hasMenuAccess(item)) {
        return false
      }
      
      // 递归过滤子菜单
      if (item.children && item.children.length > 0) {
        const filteredChildren = filterMenuItems(item.children)
        item.children = filteredChildren
        
        // 如果子菜单全部被过滤掉，则隐藏父菜单
        if (filteredChildren.length === 0 && props.behavior === 'hide') {
          return false
        }
      }
      
      return true
    })
  }
  
  return filterMenuItems(props.menuItems)
})

// 处理菜单选择
const handleMenuSelect = (item: MenuItem) => {
  emit('menuSelect', item)
}

// 处理菜单点击
const handleMenuClick = (item: MenuItem) => {
  if (!hasMenuAccess(item)) {
    return
  }
  
  if (typeof item.handler === 'function') {
    item.handler()
  }
  
  emit('menuClick', item)
}
</script>

<style scoped>
/* 权限菜单样式可以在这里定义 */
</style>