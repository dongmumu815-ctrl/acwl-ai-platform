import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { User, LoginRequest, LoginResponse } from '@/types/user'
import { authApi } from '@/api/auth'
import { ElMessage } from 'element-plus'

/**
 * 用户状态管理
 * 处理用户认证、权限管理等功能
 */
export const useUserStore = defineStore('user', () => {
  // 状态
  const user = ref<User | null>(null)
  const token = ref<string>('')
  const permissions = ref<string[]>([])
  const roles = ref<string[]>([])
  const loading = ref(false)
  // 已使用的权限码收集（前端发起API时标注的权限）
  const usedPermissions = ref<string[]>([])

  // 计算属性
  const isLoggedIn = computed(() => {
    return !!token.value && !!user.value
  })

  const userInfo = computed(() => {
    return user.value
  })

  const userPermissions = computed(() => {
    return permissions.value
  })

  const userRoles = computed(() => {
    return roles.value
  })

  /**
   * 是否为管理员
   * - 当 `roles` 包含 `admin` 或 `super_admin`，或权限中包含 `admin` 时视为管理员
   */
  const isAdmin = computed(() => {
    return (
      roles.value.includes('admin') ||
      roles.value.includes('super_admin') ||
      permissions.value.includes('admin')
    )
  })

  /**
   * 用户登录
   * @param loginData 登录数据
   */
  const login = async (loginData: LoginRequest): Promise<void> => {
    try {
      loading.value = true
      const response = await authApi.login(loginData)
      
      if (response.success) {
        // 后端直接返回LoginResponse，前端request会包装到data字段中
        const loginData = response.data as any
        const { access_token, user: userData } = loginData
        
        // 保存用户信息
        user.value = userData
        token.value = access_token
        
        const userRolesArr = userData.role ? [userData.role] : ['user']
        roles.value = userRolesArr
        permissions.value = []
        localStorage.setItem('token', access_token)
        localStorage.setItem('user', JSON.stringify(userData))
        localStorage.setItem('permissions', JSON.stringify([]))
        localStorage.setItem('roles', JSON.stringify(userRolesArr))

        // 登录后拉取真实权限与角色（基于认证信息）
        await loadPermissions()
        
        ElMessage.success('登录成功')
      } else {
        throw new Error(response.message || '登录失败')
      }
    } catch (error: any) {
      ElMessage.error(error.message || '登录失败')
      throw error
    } finally {
      loading.value = false
    }
  }

  /**
   * 用户登出
   */
  const logout = async (): Promise<void> => {
    try {
      loading.value = true
      
      // 尝试调用登出接口，但跳过认证错误处理以防止循环
      try {
        await authApi.logout()
      } catch (error: any) {
        // 如果是认证错误，忽略它，因为我们本来就要登出
        if (error.response?.status === 401 || error.response?.data?.error === 'AUTHENTICATION_ERROR') {
          console.log('登出时遇到认证错误，这是正常的，继续清除本地状态')
        } else {
          console.error('登出接口调用失败:', error)
        }
      }
      
      // 清除状态
      user.value = null
      token.value = ''
      permissions.value = []
      roles.value = []
      
      // 清除本地存储
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      localStorage.removeItem('permissions')
      localStorage.removeItem('roles')
      
      ElMessage.success('已退出登录')
    } catch (error: any) {
      console.error('登出过程失败:', error)
      
      // 即使出错，也要清除本地状态
      user.value = null
      token.value = ''
      permissions.value = []
      roles.value = []
      
      // 清除本地存储
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      localStorage.removeItem('permissions')
      localStorage.removeItem('roles')
      
      // 抛出错误供上层处理
      throw new Error(error.message || '退出登录失败')
    } finally {
      loading.value = false
    }
  }

  /**
   * 获取当前用户信息
   */
  const getCurrentUser = async (): Promise<void> => {
    try {
      loading.value = true
      const response = await authApi.getCurrentUser()
      
      if (response.success) {
        const { user: userData, permissions: userPermissions, roles: userRoles } = response.data
        
        user.value = userData
        permissions.value = userPermissions || []
        roles.value = userRoles || []
        
        // 更新本地存储
        localStorage.setItem('user', JSON.stringify(userData))
        localStorage.setItem('permissions', JSON.stringify(userPermissions || []))
        localStorage.setItem('roles', JSON.stringify(userRoles || []))

        // 进一步同步 /permissions/me 返回的真实权限字段
        await loadPermissions()
      } else {
        throw new Error(response.message || '获取用户信息失败')
      }
    } catch (error: any) {
      console.error('获取用户信息失败:', error)
      // 如果获取用户信息失败，清除本地存储
      await logout()
      throw error
    } finally {
      loading.value = false
    }
  }

  /**
   * 加载当前认证用户的权限与角色
   *
   * - 调用后端接口 `/permissions/me`（基于认证信息解析当前用户）
   * - 使用返回的 `permission_codes` 与 `role_codes` 更新 store
   * - 兼容旧的 `user.role` 字段作为降级
   */
  const loadPermissions = async (): Promise<void> => {
    try {
      const resp = await authApi.getMyPermissions()
      if (!resp.success) {
        throw new Error(resp.message || '获取权限失败')
      }

      const data = resp.data as any
      // 优先使用后端直接提供的权限代码列表
      permissions.value = Array.isArray(data?.permission_codes)
        ? data.permission_codes
        : Array.isArray(data?.permissions)
          ? (data.permissions as any[]).map((p: any) => p?.code).filter(Boolean)
          : []

      // 适配后端返回的多角色：role_codes
      if (Array.isArray(data?.role_codes) && data.role_codes.length > 0) {
        roles.value = data.role_codes
      } else if (user.value?.role) {
        // 兼容旧的 user.role 字段
        roles.value = [user.value.role]
      }

      // 持久化到本地存储
      localStorage.setItem('permissions', JSON.stringify(permissions.value))
      localStorage.setItem('roles', JSON.stringify(roles.value))

      console.log('用户权限加载成功:', permissions.value)
    } catch (error) {
      console.error('加载用户权限失败:', error)
      // 失败时保持现有权限作为降级
    }
  }

  /**
   * 通配符权限匹配
   * - 支持按 `:` 分段的权限码，例如：`data:resource:query`
   * - 当已授予权限为 `data:resource:*` 时，可匹配 `data:resource:query`
   * - 当已授予权限为 `*` 时，匹配任意权限
   * @param granted 已授予的权限码
   * @param required 需要的权限码
   */
  function permissionMatches(granted: string, required: string): boolean {
    if (!granted) return false
    if (granted === '*' || required === '*') return true
    if (granted === required) return true
    const g = granted.split(':')
    const r = required.split(':')
    const len = Math.max(g.length, r.length)
    for (let i = 0; i < len; i++) {
      const gi = g[i] ?? ''
      const ri = r[i] ?? ''
      if (gi === '*' || gi === ri) continue
      return false
    }
    return true
  }

  /**
   * 从本地存储恢复用户状态
   */
  const restoreFromStorage = (): void => {
    try {
      const storedToken = localStorage.getItem('token')
      const storedUser = localStorage.getItem('user')
      const storedPermissions = localStorage.getItem('permissions')
      const storedRoles = localStorage.getItem('roles')
      const storedUsedPerms = localStorage.getItem('used_permissions')
      
      if (storedToken && storedUser) {
        token.value = storedToken
        user.value = JSON.parse(storedUser)
        permissions.value = storedPermissions ? JSON.parse(storedPermissions) : []
        roles.value = storedRoles ? JSON.parse(storedRoles) : []
        usedPermissions.value = storedUsedPerms ? JSON.parse(storedUsedPerms) : []
      }
    } catch (error) {
      console.error('恢复用户状态失败:', error)
      // 如果恢复失败，清除本地存储
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      localStorage.removeItem('permissions')
      localStorage.removeItem('roles')
      localStorage.removeItem('used_permissions')
    }
  }

  /**
   * 检查用户是否有指定权限
   * @param permission 权限标识
   */
  const hasPermission = (permission: string): boolean => {
    if (!permission) return true
    // 管理员放行
    if (isAdmin.value) return true
    // 精确或通配符匹配
    return permissions.value.some(p => permissionMatches(p, permission))
  }

  const hasPermissionStrict = (permission: string): boolean => {
    if (!permission) return true
    return permissions.value.some(p => permissionMatches(p, permission))
  }

  /**
   * 检查用户是否有指定角色
   * @param role 角色标识
   */
  const hasRole = (role: string): boolean => {
    if (!role) return true
    return roles.value.includes(role)
  }

  /**
   * 检查用户是否有任一指定权限
   * @param permissionList 权限列表
   */
  const hasAnyPermission = (permissionList: string[]): boolean => {
    if (!permissionList || permissionList.length === 0) return true
    if (isAdmin.value) return true
    return permissionList.some(required => permissions.value.some(p => permissionMatches(p, required)))
  }

  /**
   * 检查用户是否有所有指定权限
   * @param permissionList 权限列表
   */
  const hasAllPermissions = (permissionList: string[]): boolean => {
    if (!permissionList || permissionList.length === 0) return true
    if (isAdmin.value) return true
    return permissionList.every(required => permissions.value.some(p => permissionMatches(p, required)))
  }

  /**
   * 更新用户信息
   * @param userData 用户数据
   */
  const updateUserInfo = (userData: Partial<User>): void => {
    if (user.value) {
      user.value = { ...user.value, ...userData }
      localStorage.setItem('user', JSON.stringify(user.value))
    }
  }

  /**
   * 刷新用户权限
   */
  const refreshPermissions = async (): Promise<void> => {
    try {
      // 使用 /permissions/me 同步最新权限（优先 permission_codes/role_codes）
      const resp = await authApi.getMyPermissions()
      if (resp.success) {
        const data = resp.data as any
        permissions.value = Array.isArray(data?.permission_codes)
          ? data.permission_codes
          : Array.isArray(data?.permissions)
            ? (data.permissions as any[]).map((p: any) => p?.code).filter(Boolean)
            : []

        roles.value = Array.isArray(data?.role_codes) ? data.role_codes : roles.value

        localStorage.setItem('permissions', JSON.stringify(permissions.value))
        localStorage.setItem('roles', JSON.stringify(roles.value))
      }
    } catch (error) {
      console.error('刷新权限失败:', error)
    }
  }

  /**
   * 重置状态
   */
  const reset = (): void => {
    user.value = null
    token.value = ''
    permissions.value = []
    roles.value = []
    loading.value = false
    usedPermissions.value = []
    localStorage.removeItem('used_permissions')
  }

  /**
   * 记录前端使用到的权限码
   * @param perm 权限码或权限码列表
   */
  const recordUsedPermission = (perm: string | string[]): void => {
    const list = Array.isArray(perm) ? perm : [perm]
    for (const p of list) {
      const code = String(p || '').trim()
      if (!code) continue
      if (!usedPermissions.value.includes(code)) {
        usedPermissions.value.push(code)
      }
    }
    localStorage.setItem('used_permissions', JSON.stringify(usedPermissions.value))
  }

  // 初始化时从本地存储恢复状态
  restoreFromStorage()

  return {
    // 状态
    user,
    token,
    permissions,
    roles,
    loading,
    usedPermissions,
    
    // 计算属性
    isLoggedIn,
    userInfo,
    userPermissions,
    userRoles,
    isAdmin,
    
    // 方法
    login,
    logout,
    getCurrentUser,
    loadPermissions,
    restoreFromStorage,
    hasPermission,
    hasRole,
    hasAnyPermission,
    hasAllPermissions,
    hasPermissionStrict,
    updateUserInfo,
    refreshPermissions,
    reset,
    recordUsedPermission
  }
})

/**
 * 用户状态管理类型定义
 */
export type UserStore = ReturnType<typeof useUserStore>