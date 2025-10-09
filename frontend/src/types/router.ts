import 'vue-router'

/**
 * 扩展路由元信息类型
 */
declare module 'vue-router' {
  interface RouteMeta {
    /** 页面标题 */
    title?: string
    /** 图标名称 */
    icon?: string
    /** 是否隐藏在菜单中 */
    hidden?: boolean
    /** 是否在菜单中隐藏 */
    hideInMenu?: boolean
    /** 是否需要认证 */
    requiresAuth?: boolean
    /** 是否需要管理员权限 */
    requiresAdmin?: boolean
    /** 需要的权限代码（单个权限） */
    permission?: string
    /** 需要的权限代码（多个权限，满足任一即可） */
    permissions?: string[]
    /** 需要的权限代码（多个权限，必须全部满足） */
    requireAllPermissions?: string[]
    /** 需要的角色 */
    role?: string
    /** 需要的角色（多个角色，满足任一即可） */
    roles?: string[]
    /** 需要的角色（多个角色，必须全部满足） */
    requireAllRoles?: string[]
    /** 权限检查模式：'any' | 'all' */
    permissionMode?: 'any' | 'all'
    /** 无权限时的行为：'redirect' | 'hide' */
    noPermissionBehavior?: 'redirect' | 'hide'
    /** 权限不足时重定向的路径 */
    noPermissionRedirect?: string
    /** 是否缓存页面 */
    keepAlive?: boolean
    /** 面包屑导航 */
    breadcrumb?: boolean
    /** 是否固定在标签页 */
    affix?: boolean
    /** 外部链接 */
    externalLink?: string
    /** 是否在新窗口打开 */
    target?: '_blank' | '_self'
  }
}

/**
 * 权限检查配置
 */
export interface PermissionConfig {
  /** 权限代码 */
  permission?: string | string[]
  /** 角色代码 */
  role?: string | string[]
  /** 检查模式 */
  mode?: 'any' | 'all'
  /** 无权限时的行为 */
  fallback?: 'redirect' | 'hide'
  /** 重定向路径 */
  redirectTo?: string
}

/**
 * 路由权限检查结果
 */
export interface RoutePermissionResult {
  /** 是否有权限 */
  hasPermission: boolean
  /** 缺少的权限 */
  missingPermissions?: string[]
  /** 缺少的角色 */
  missingRoles?: string[]
  /** 建议的操作 */
  action: 'allow' | 'redirect' | 'deny'
  /** 重定向路径 */
  redirectTo?: string
  /** 错误信息 */
  message?: string
}