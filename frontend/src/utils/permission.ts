import type { RouteLocationNormalized } from 'vue-router'
import type { RoutePermissionResult, PermissionConfig } from '@/types/router'
import { useUserStore } from '@/stores/user'

/**
 * 检查路由权限
 * @param route 路由对象
 * @returns 权限检查结果
 */
export function checkRoutePermission(route: RouteLocationNormalized): RoutePermissionResult {
  const userStore = useUserStore()
  const { meta } = route

  // 如果用户未登录且需要认证，重定向到登录页
  if (meta.requiresAuth && !userStore.isLoggedIn) {
    return {
      hasPermission: false,
      action: 'redirect',
      redirectTo: '/login',
      message: '请先登录'
    }
  }

  // 如果不需要认证，直接允许访问
  if (!meta.requiresAuth) {
    return {
      hasPermission: true,
      action: 'allow'
    }
  }

  // 检查管理员权限
  if (meta.requiresAdmin && !userStore.isAdmin) {
    return {
      hasPermission: false,
      action: 'redirect',
      redirectTo: meta.noPermissionRedirect || '/403',
      message: '需要管理员权限'
    }
  }

  // 检查单个权限
  if (meta.permission) {
    const hasPermission = userStore.hasPermission(meta.permission)
    if (!hasPermission) {
      return {
        hasPermission: false,
        missingPermissions: [meta.permission],
        action: meta.noPermissionBehavior === 'hide' ? 'deny' : 'redirect',
        redirectTo: meta.noPermissionRedirect || '/403',
        message: `缺少权限: ${meta.permission}`
      }
    }
  }

  // 检查多个权限（任一满足）
  if (meta.permissions && meta.permissions.length > 0) {
    const hasAnyPermission = userStore.hasAnyPermission(meta.permissions)
    if (!hasAnyPermission) {
      return {
        hasPermission: false,
        missingPermissions: meta.permissions,
        action: meta.noPermissionBehavior === 'hide' ? 'deny' : 'redirect',
        redirectTo: meta.noPermissionRedirect || '/403',
        message: `缺少以下任一权限: ${meta.permissions.join(', ')}`
      }
    }
  }

  // 检查多个权限（全部满足）
  if (meta.requireAllPermissions && meta.requireAllPermissions.length > 0) {
    const hasAllPermissions = userStore.hasAllPermissions(meta.requireAllPermissions)
    if (!hasAllPermissions) {
      const missingPermissions = meta.requireAllPermissions.filter(
        permission => !userStore.hasPermission(permission)
      )
      return {
        hasPermission: false,
        missingPermissions,
        action: meta.noPermissionBehavior === 'hide' ? 'deny' : 'redirect',
        redirectTo: meta.noPermissionRedirect || '/403',
        message: `缺少以下权限: ${missingPermissions.join(', ')}`
      }
    }
  }

  // 检查单个角色
  if (meta.role) {
    const hasRole = userStore.hasRole(meta.role)
    if (!hasRole) {
      return {
        hasPermission: false,
        missingRoles: [meta.role],
        action: meta.noPermissionBehavior === 'hide' ? 'deny' : 'redirect',
        redirectTo: meta.noPermissionRedirect || '/403',
        message: `缺少角色: ${meta.role}`
      }
    }
  }

  // 检查多个角色（任一满足）
  if (meta.roles && meta.roles.length > 0) {
    const hasAnyRole = userStore.hasAnyRole(meta.roles)
    if (!hasAnyRole) {
      return {
        hasPermission: false,
        missingRoles: meta.roles,
        action: meta.noPermissionBehavior === 'hide' ? 'deny' : 'redirect',
        redirectTo: meta.noPermissionRedirect || '/403',
        message: `缺少以下任一角色: ${meta.roles.join(', ')}`
      }
    }
  }

  // 检查多个角色（全部满足）
  if (meta.requireAllRoles && meta.requireAllRoles.length > 0) {
    const hasAllRoles = meta.requireAllRoles.every(role => userStore.hasRole(role))
    if (!hasAllRoles) {
      const missingRoles = meta.requireAllRoles.filter(role => !userStore.hasRole(role))
      return {
        hasPermission: false,
        missingRoles,
        action: meta.noPermissionBehavior === 'hide' ? 'deny' : 'redirect',
        redirectTo: meta.noPermissionRedirect || '/403',
        message: `缺少以下角色: ${missingRoles.join(', ')}`
      }
    }
  }

  // 所有检查通过
  return {
    hasPermission: true,
    action: 'allow'
  }
}

/**
 * 检查权限配置
 * @param config 权限配置
 * @returns 是否有权限
 */
export function checkPermissionConfig(config: PermissionConfig): boolean {
  const userStore = useUserStore()
  const { permission, role, mode = 'any' } = config

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

/**
 * 获取用户可访问的路由
 * @param routes 路由数组
 * @returns 过滤后的路由数组
 */
export function filterRoutesByPermission(routes: any[]): any[] {
  return routes.filter(route => {
    // 检查当前路由权限
    const mockRoute = { meta: route.meta || {} } as RouteLocationNormalized
    const result = checkRoutePermission(mockRoute)
    
    if (!result.hasPermission && route.meta?.noPermissionBehavior === 'hide') {
      return false
    }

    // 递归检查子路由
    if (route.children && route.children.length > 0) {
      route.children = filterRoutesByPermission(route.children)
      // 如果所有子路由都被过滤掉，且当前路由没有自己的组件，则隐藏当前路由
      if (route.children.length === 0 && !route.component) {
        return false
      }
    }

    return true
  })
}

/**
 * 检查模块权限
 * @param module 模块名
 * @param action 操作名
 * @returns 是否有权限
 */
export function hasModulePermission(module: string, action: string): boolean {
  const userStore = useUserStore()
  return userStore.hasModulePermission(module, action)
}

/**
 * 权限装饰器工厂
 * @param config 权限配置
 * @returns 装饰器函数
 */
export function requirePermission(config: PermissionConfig) {
  return function (target: any, propertyKey: string, descriptor: PropertyDescriptor) {
    const originalMethod = descriptor.value

    descriptor.value = function (...args: any[]) {
      if (checkPermissionConfig(config)) {
        return originalMethod.apply(this, args)
      } else {
        console.warn(`权限不足，无法执行方法: ${propertyKey}`)
        return false
      }
    }

    return descriptor
  }
}

/**
 * 权限常量
 */
export const PERMISSIONS = {
  // 用户管理
  USER_READ: 'user:read',
  USER_CREATE: 'user:create',
  USER_UPDATE: 'user:update',
  USER_DELETE: 'user:delete',
  
  // 角色管理
  ROLE_READ: 'role:read',
  ROLE_CREATE: 'role:create',
  ROLE_UPDATE: 'role:update',
  ROLE_DELETE: 'role:delete',
  
  // 权限管理
  PERMISSION_READ: 'permission:read',
  PERMISSION_CREATE: 'permission:create',
  PERMISSION_UPDATE: 'permission:update',
  PERMISSION_DELETE: 'permission:delete',
  
  // 模型管理
  MODEL_READ: 'model:read',
  MODEL_CREATE: 'model:create',
  MODEL_UPDATE: 'model:update',
  MODEL_DELETE: 'model:delete',
  MODEL_DEPLOY: 'model:deploy',
  
  // 数据集管理
  DATASET_READ: 'dataset:read',
  DATASET_CREATE: 'dataset:create',
  DATASET_UPDATE: 'dataset:update',
  DATASET_DELETE: 'dataset:delete',
  
  // 项目管理
  PROJECT_READ: 'project:read',
  PROJECT_CREATE: 'project:create',
  PROJECT_UPDATE: 'project:update',
  PROJECT_DELETE: 'project:delete',
  
  // 系统管理
  SYSTEM_READ: 'system:read',
  SYSTEM_UPDATE: 'system:update',
  SYSTEM_MONITOR: 'system:monitor',
  
  // 指令集管理
  INSTRUCTION_SET_READ: 'instruction_set:read',
  INSTRUCTION_SET_CREATE: 'instruction_set:create',
  INSTRUCTION_SET_UPDATE: 'instruction_set:update',
  INSTRUCTION_SET_DELETE: 'instruction_set:delete',
  INSTRUCTION_SET_TEST: 'instruction_set:test'
} as const

/**
 * 角色常量
 */
export const ROLES = {
  ADMIN: 'admin',
  USER: 'user',
  GUEST: 'guest',
  DEVELOPER: 'developer',
  OPERATOR: 'operator'
} as const