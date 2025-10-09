import { computed, ref, watch } from 'vue'
import { useUserStore } from '@/stores/user'
import { PERMISSIONS, ROLES, checkPermissionConfig } from '@/utils/permission'
import { usePermissionCache } from '@/utils/permissionCache'
import type { PermissionConfig } from '@/types/router'

/**
 * 权限组合式函数
 * @returns 权限相关的响应式数据和方法
 */
export function usePermission() {
  const userStore = useUserStore()

  /**
   * 检查单个权限
   * @param permission 权限代码
   * @returns 是否有权限
   */
  const hasPermission = (permission: string) => {
    return computed(() => userStore.hasPermission(permission))
  }

  /**
   * 检查多个权限（任一满足）
   * @param permissions 权限代码数组
   * @returns 是否有权限
   */
  const hasAnyPermission = (permissions: string[]) => {
    return computed(() => userStore.hasAnyPermission(permissions))
  }

  /**
   * 检查多个权限（全部满足）
   * @param permissions 权限代码数组
   * @returns 是否有权限
   */
  const hasAllPermissions = (permissions: string[]) => {
    return computed(() => userStore.hasAllPermissions(permissions))
  }

  /**
   * 检查角色
   * @param role 角色代码
   * @returns 是否有角色
   */
  const hasRole = (role: string) => {
    return computed(() => userStore.hasRole(role))
  }

  /**
   * 检查多个角色（任一满足）
   * @param roles 角色代码数组
   * @returns 是否有角色
   */
  const hasAnyRole = (roles: string[]) => {
    return computed(() => userStore.hasAnyRole(roles))
  }

  /**
   * 检查模块权限
   * @param module 模块名
   * @param action 操作名
   * @returns 是否有权限
   */
  const hasModulePermission = (module: string, action: string) => {
    return computed(() => userStore.hasModulePermission(module, action))
  }

  /**
   * 检查权限配置
   * @param config 权限配置
   * @returns 是否有权限
   */
  const checkPermission = (config: PermissionConfig) => {
    return computed(() => {
      if (!config.permission && !config.role) {
        return true
      }
      
      const { getCached, setCached } = usePermissionCache()
      const userId = userStore.user?.id?.toString() || 'anonymous'
      
      // 尝试从缓存获取结果
      const cachedResult = getCached(userId, config)
      if (cachedResult !== null) {
        return cachedResult
      }
      
      // 计算权限结果
      const result = checkPermissionConfig(config, userStore.permissions, userStore.roles)
      
      // 缓存结果
      setCached(userId, config, result)
      
      return result
    })
  }

  /**
   * 是否为管理员
   */
  const isAdmin = computed(() => userStore.isAdmin)

  /**
   * 是否已登录
   */
  const isLoggedIn = computed(() => userStore.isLoggedIn)

  /**
   * 当前用户权限列表
   */
  const permissions = computed(() => userStore.permissions)

  /**
   * 当前用户角色列表
   */
  const roles = computed(() => userStore.roles)

  /**
   * 当前用户权限对象列表
   */
  const permissionObjects = computed(() => userStore.permissionObjects)

  /**
   * 当前用户角色对象列表
   */
  const roleObjects = computed(() => userStore.roleObjects)

  /**
   * 刷新权限
   */
  const refreshPermissions = async () => {
    const { clearUserCache } = usePermissionCache()
    const userId = userStore.user?.id?.toString() || 'anonymous'
    
    // 清除当前用户的权限缓存
    clearUserCache(userId)
    
    // 重新获取用户信息和权限
    await userStore.fetchUserInfo()
  }

  return {
    // 权限检查方法
    hasPermission,
    hasAnyPermission,
    hasAllPermissions,
    hasRole,
    hasAnyRole,
    hasModulePermission,
    checkPermission,
    
    // 状态
    isAdmin,
    isLoggedIn,
    permissions,
    roles,
    permissionObjects,
    roleObjects,
    
    // 方法
    refreshPermissions
  }
}

/**
 * 权限守卫组合式函数
 * @param config 权限配置
 * @returns 权限守卫相关的响应式数据和方法
 */
export function usePermissionGuard(config: PermissionConfig) {
  const { checkPermission } = usePermission()
  
  const hasAccess = checkPermission(config)
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  /**
   * 执行权限检查
   * @param callback 有权限时执行的回调
   * @param fallback 无权限时执行的回调
   */
  const guard = async (
    callback: () => void | Promise<void>,
    fallback?: () => void | Promise<void>
  ) => {
    if (hasAccess.value) {
      try {
        isLoading.value = true
        error.value = null
        await callback()
      } catch (err) {
        error.value = err instanceof Error ? err.message : '操作失败'
        console.error('权限守卫执行失败:', err)
      } finally {
        isLoading.value = false
      }
    } else {
      error.value = '权限不足'
      if (fallback) {
        await fallback()
      }
    }
  }

  return {
    hasAccess,
    isLoading,
    error,
    guard
  }
}

/**
 * 按钮权限组合式函数
 * @param permission 权限代码或权限配置
 * @returns 按钮权限相关的响应式数据
 */
export function useButtonPermission(permission: string | PermissionConfig) {
  const { hasPermission, checkPermission } = usePermission()
  
  const canClick = typeof permission === 'string' 
    ? hasPermission(permission)
    : checkPermission(permission)

  const buttonProps = computed(() => ({
    disabled: !canClick.value,
    style: canClick.value ? {} : { opacity: 0.5, cursor: 'not-allowed' }
  }))

  return {
    canClick,
    buttonProps
  }
}

/**
 * 表格操作权限组合式函数
 * @param permissions 操作权限配置
 * @returns 表格操作权限相关的响应式数据
 */
export function useTablePermission(permissions: {
  create?: string | PermissionConfig
  read?: string | PermissionConfig
  update?: string | PermissionConfig
  delete?: string | PermissionConfig
  [key: string]: string | PermissionConfig | undefined
}) {
  const { hasPermission, checkPermission } = usePermission()

  const actions = computed(() => {
    const result: Record<string, boolean> = {}
    
    for (const [action, permission] of Object.entries(permissions)) {
      if (permission) {
        result[action] = typeof permission === 'string'
          ? hasPermission(permission).value
          : checkPermission(permission).value
      } else {
        result[action] = false
      }
    }
    
    return result
  })

  /**
   * 检查是否可以执行某个操作
   * @param action 操作名
   * @returns 是否可以执行
   */
  const canAction = (action: string) => {
    return computed(() => actions.value[action] || false)
  }

  return {
    actions,
    canAction,
    canCreate: canAction('create'),
    canRead: canAction('read'),
    canUpdate: canAction('update'),
    canDelete: canAction('delete')
  }
}

/**
 * 菜单权限组合式函数
 * @param menuItems 菜单项配置
 * @returns 过滤后的菜单项
 */
export function useMenuPermission<T extends { permission?: string | PermissionConfig; children?: T[] }>(
  menuItems: T[]
) {
  const { hasPermission, checkPermission } = usePermission()

  const filterMenuItems = (items: T[]): T[] => {
    return items.filter(item => {
      // 检查当前菜单项权限
      if (item.permission) {
        const hasAccess = typeof item.permission === 'string'
          ? hasPermission(item.permission).value
          : checkPermission(item.permission).value
        
        if (!hasAccess) {
          return false
        }
      }

      // 递归过滤子菜单
      if (item.children && item.children.length > 0) {
        item.children = filterMenuItems(item.children)
        // 如果所有子菜单都被过滤掉，则隐藏父菜单
        if (item.children.length === 0) {
          return false
        }
      }

      return true
    })
  }

  const filteredMenuItems = computed(() => filterMenuItems([...menuItems]))

  return {
    filteredMenuItems
  }
}

/**
 * 权限监听组合式函数
 * @param callback 权限变化时的回调
 */
export function usePermissionWatcher(callback: (permissions: string[], roles: string[]) => void) {
  const { permissions, roles } = usePermission()

  watch(
    [permissions, roles],
    ([newPermissions, newRoles]) => {
      callback(newPermissions, newRoles)
    },
    { immediate: true, deep: true }
  )
}