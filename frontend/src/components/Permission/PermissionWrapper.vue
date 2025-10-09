<template>
  <div v-if="hasAccess" :class="wrapperClass">
    <slot />
  </div>
  <div v-else-if="showFallback" :class="fallbackClass">
    <slot name="fallback">
      <div class="permission-fallback">
        <el-icon><Lock /></el-icon>
        <span>{{ fallbackText }}</span>
      </div>
    </slot>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Lock } from '@element-plus/icons-vue'
import { usePermission } from '@/composables/usePermission'
import type { PermissionConfig } from '@/types/router'

/**
 * 权限包装器组件
 * 根据权限配置显示或隐藏内容
 */

interface Props {
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
  /** 无权限时的行为 */
  fallback?: 'hide' | 'show' | 'disable'
  /** 无权限时显示的文本 */
  fallbackText?: string
  /** 包装器样式类 */
  wrapperClass?: string
  /** 降级显示样式类 */
  fallbackClass?: string
}

const props = withDefaults(defineProps<Props>(), {
  mode: 'any',
  fallback: 'hide',
  fallbackText: '权限不足',
  wrapperClass: '',
  fallbackClass: 'permission-fallback-wrapper'
})

const { checkPermission } = usePermission()

// 构建权限配置
const permissionConfig = computed<PermissionConfig>(() => ({
  permission: props.permission || props.permissions,
  role: props.role || props.roles,
  mode: props.mode
}))

// 检查权限
const hasAccess = checkPermission(permissionConfig)

// 是否显示降级内容
const showFallback = computed(() => {
  return props.fallback === 'show' && !hasAccess.value
})
</script>

<style scoped>
.permission-fallback {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px;
  color: var(--el-text-color-placeholder);
  font-size: 14px;
  gap: 8px;
}

.permission-fallback-wrapper {
  opacity: 0.6;
  background-color: var(--el-fill-color-light);
  border-radius: 4px;
  border: 1px dashed var(--el-border-color);
}
</style>