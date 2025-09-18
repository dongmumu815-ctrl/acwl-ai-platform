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
        
        // 将后端的单个role字段转换为前端期望的roles数组
        const userRoles = userData.role ? [userData.role] : ['user']
        roles.value = userRoles
        
        // 根据角色设置默认权限
        const userPermissions = userData.role === 'admin' 
          ? ['admin', 'user', 'read', 'write', 'delete', 'data:elasticsearch:query'] 
          : ['user', 'read']
        permissions.value = userPermissions
        
        // 保存到本地存储
        localStorage.setItem('token', access_token)
        localStorage.setItem('user', JSON.stringify(userData))
        localStorage.setItem('permissions', JSON.stringify(userPermissions))
        localStorage.setItem('roles', JSON.stringify(userRoles))
        
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
      
      // 调用登出接口
      await authApi.logout()
      
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
      console.error('登出接口调用失败:', error)
      
      // 即使接口调用失败，也要清除本地状态
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
   * 从本地存储恢复用户状态
   */
  const restoreFromStorage = (): void => {
    try {
      const storedToken = localStorage.getItem('token')
      const storedUser = localStorage.getItem('user')
      const storedPermissions = localStorage.getItem('permissions')
      const storedRoles = localStorage.getItem('roles')
      
      if (storedToken && storedUser) {
        token.value = storedToken
        user.value = JSON.parse(storedUser)
        permissions.value = storedPermissions ? JSON.parse(storedPermissions) : []
        roles.value = storedRoles ? JSON.parse(storedRoles) : []
      }
    } catch (error) {
      console.error('恢复用户状态失败:', error)
      // 如果恢复失败，清除本地存储
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      localStorage.removeItem('permissions')
      localStorage.removeItem('roles')
    }
  }

  /**
   * 检查用户是否有指定权限
   * @param permission 权限标识
   */
  const hasPermission = (permission: string): boolean => {
    if (!permission) return true
    return permissions.value.includes(permission)
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
    return permissionList.some(permission => permissions.value.includes(permission))
  }

  /**
   * 检查用户是否有所有指定权限
   * @param permissionList 权限列表
   */
  const hasAllPermissions = (permissionList: string[]): boolean => {
    if (!permissionList || permissionList.length === 0) return true
    return permissionList.every(permission => permissions.value.includes(permission))
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
      const response = await authApi.getUserPermissions()
      if (response.success) {
        permissions.value = response.data.permissions || []
        roles.value = response.data.roles || []
        
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
    
    // 计算属性
    isLoggedIn,
    userInfo,
    userPermissions,
    userRoles,
    
    // 方法
    login,
    logout,
    getCurrentUser,
    restoreFromStorage,
    hasPermission,
    hasRole,
    hasAnyPermission,
    hasAllPermissions,
    updateUserInfo,
    refreshPermissions,
    reset
  }
})

/**
 * 用户状态管理类型定义
 */
export type UserStore = ReturnType<typeof useUserStore>