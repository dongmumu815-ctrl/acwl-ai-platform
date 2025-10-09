import type { Directive, DirectiveBinding } from 'vue'
import { useUserStore } from '@/stores/user'

/**
 * 权限指令类型定义
 */
interface PermissionBinding {
  value: string | string[] | {
    permission?: string | string[]
    role?: string | string[]
    mode?: 'any' | 'all'
    fallback?: 'hide' | 'disable'
  }
}

/**
 * 权限检查函数
 * @param binding 指令绑定值
 * @returns 是否有权限
 */
function checkPermission(binding: DirectiveBinding<PermissionBinding['value']>): boolean {
  const userStore = useUserStore()
  const { value } = binding

  // 如果没有值，默认允许访问
  if (!value) return true

  // 如果是字符串，检查单个权限
  if (typeof value === 'string') {
    return userStore.hasPermission(value)
  }

  // 如果是数组，检查多个权限（默认为any模式）
  if (Array.isArray(value)) {
    return userStore.hasAnyPermission(value)
  }

  // 如果是对象，根据配置检查权限
  if (typeof value === 'object') {
    const { permission, role, mode = 'any' } = value

    let hasPermission = true
    let hasRole = true

    // 检查权限
    if (permission) {
      if (typeof permission === 'string') {
        hasPermission = userStore.hasPermission(permission)
      } else if (Array.isArray(permission)) {
        hasPermission = mode === 'all' 
          ? userStore.hasAllPermissions(permission)
          : userStore.hasAnyPermission(permission)
      }
    }

    // 检查角色
    if (role) {
      if (typeof role === 'string') {
        hasRole = userStore.hasRole(role)
      } else if (Array.isArray(role)) {
        hasRole = mode === 'all'
          ? role.every(r => userStore.hasRole(r))
          : userStore.hasAnyRole(role)
      }
    }

    // 根据模式返回结果
    return mode === 'all' ? (hasPermission && hasRole) : (hasPermission || hasRole)
  }

  return false
}

/**
 * 处理元素显示/隐藏
 * @param el 元素
 * @param hasPermission 是否有权限
 * @param fallback 降级策略
 */
function handleElement(el: HTMLElement, hasPermission: boolean, fallback: 'hide' | 'disable' = 'hide') {
  if (hasPermission) {
    // 有权限时恢复元素状态
    el.style.display = ''
    el.removeAttribute('disabled')
    el.classList.remove('permission-disabled')
  } else {
    // 无权限时根据策略处理
    if (fallback === 'hide') {
      el.style.display = 'none'
    } else if (fallback === 'disable') {
      el.setAttribute('disabled', 'true')
      el.classList.add('permission-disabled')
    }
  }
}

/**
 * v-permission 权限指令
 * 
 * 使用方式：
 * 1. 简单权限检查：v-permission="'user:read'"
 * 2. 多权限检查（任一）：v-permission="['user:read', 'user:write']"
 * 3. 复杂权限检查：v-permission="{ permission: 'user:read', role: 'admin', mode: 'all', fallback: 'disable' }"
 */
export const permission: Directive<HTMLElement, PermissionBinding['value']> = {
  mounted(el, binding) {
    const hasPermission = checkPermission(binding)
    const fallback = typeof binding.value === 'object' && binding.value.fallback || 'hide'
    handleElement(el, hasPermission, fallback)
  },

  updated(el, binding) {
    const hasPermission = checkPermission(binding)
    const fallback = typeof binding.value === 'object' && binding.value.fallback || 'hide'
    handleElement(el, hasPermission, fallback)
  }
}

/**
 * v-permission-any 权限指令（任一权限）
 * 使用方式：v-permission-any="['user:read', 'user:write']"
 */
export const permissionAny: Directive<HTMLElement, string[]> = {
  mounted(el, binding) {
    const userStore = useUserStore()
    const hasPermission = userStore.hasAnyPermission(binding.value || [])
    handleElement(el, hasPermission)
  },

  updated(el, binding) {
    const userStore = useUserStore()
    const hasPermission = userStore.hasAnyPermission(binding.value || [])
    handleElement(el, hasPermission)
  }
}

/**
 * v-permission-all 权限指令（所有权限）
 * 使用方式：v-permission-all="['user:read', 'user:write']"
 */
export const permissionAll: Directive<HTMLElement, string[]> = {
  mounted(el, binding) {
    const userStore = useUserStore()
    const hasPermission = userStore.hasAllPermissions(binding.value || [])
    handleElement(el, hasPermission)
  },

  updated(el, binding) {
    const userStore = useUserStore()
    const hasPermission = userStore.hasAllPermissions(binding.value || [])
    handleElement(el, hasPermission)
  }
}

/**
 * v-role 角色指令
 * 使用方式：v-role="'admin'" 或 v-role="['admin', 'user']"
 */
export const role: Directive<HTMLElement, string | string[]> = {
  mounted(el, binding) {
    const userStore = useUserStore()
    const hasRole = typeof binding.value === 'string'
      ? userStore.hasRole(binding.value)
      : userStore.hasAnyRole(binding.value || [])
    handleElement(el, hasRole)
  },

  updated(el, binding) {
    const userStore = useUserStore()
    const hasRole = typeof binding.value === 'string'
      ? userStore.hasRole(binding.value)
      : userStore.hasAnyRole(binding.value || [])
    handleElement(el, hasRole)
  }
}

/**
 * 权限指令集合
 */
export default {
  permission,
  permissionAny,
  permissionAll,
  role
}