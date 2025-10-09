<template>
  <el-button
    v-if="visible"
    v-bind="buttonProps"
    :disabled="!hasAccess || disabled"
    :loading="loading"
    @click="handleClick"
  >
    <slot />
  </el-button>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { ElMessage } from 'element-plus'
import { usePermission } from '@/composables/usePermission'
import type { PermissionConfig } from '@/types/router'
import type { ButtonProps } from 'element-plus'

/**
 * 权限按钮组件
 * 根据权限配置控制按钮的显示和可用性
 */

interface Props extends /* @vue-ignore */ Partial<ButtonProps> {
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
  behavior?: 'hide' | 'disable'
  /** 无权限时的提示信息 */
  noPermissionMessage?: string
  /** 是否显示权限提示 */
  showPermissionTip?: boolean
  /** 额外的禁用条件 */
  disabled?: boolean
  /** 加载状态 */
  loading?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  mode: 'any',
  behavior: 'disable',
  noPermissionMessage: '权限不足，无法执行此操作',
  showPermissionTip: true,
  disabled: false,
  loading: false
})

const emit = defineEmits<{
  click: [event: MouseEvent]
  noPermission: []
}>()

const { checkPermission } = usePermission()

// 构建权限配置
const permissionConfig = computed<PermissionConfig>(() => ({
  permission: props.permission || props.permissions,
  role: props.role || props.roles,
  mode: props.mode
}))

// 检查权限
const hasAccess = checkPermission(permissionConfig)

// 是否可见
const visible = computed(() => {
  if (props.behavior === 'hide' && !hasAccess.value) {
    return false
  }
  return true
})

// 按钮属性
const buttonProps = computed(() => {
  const { permission, permissions, role, roles, mode, behavior, noPermissionMessage, showPermissionTip, disabled, loading, ...restProps } = props
  return restProps
})

// 处理点击事件
const handleClick = (event: MouseEvent) => {
  if (!hasAccess.value) {
    emit('noPermission')
    if (props.showPermissionTip) {
      ElMessage.warning(props.noPermissionMessage)
    }
    return
  }
  
  emit('click', event)
}
</script>

<style scoped>
/* 权限按钮样式可以在这里定义 */
</style>