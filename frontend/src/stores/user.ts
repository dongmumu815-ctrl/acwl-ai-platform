import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { authApi } from '@/api/auth'
import { roleApi } from '@/api/roles'
import { getToken, setToken, removeToken } from '@/utils/auth'
import type { User, LoginForm, RegisterForm } from '@/types/auth'
import type { Permission } from '@/api/roles'

export const useUserStore = defineStore('user', () => {
  // 状态
  const user = ref<User | null>(null)
  const token = ref<string>('')
  const permissions = ref<string[]>([])
  const permissionObjects = ref<Permission[]>([])
  const roles = ref<string[]>([])
  const roleObjects = ref<any[]>([])
  
  // 计算属性
  const isLoggedIn = computed(() => {
    return !!token.value && !!user.value
  })
  
  const isAdmin = computed(() => {
    return user.value?.role === 'admin'
  })
  
  const userName = computed(() => {
    return user.value?.username || ''
  })
  
  const userEmail = computed(() => {
    return user.value?.email || ''
  })
  
  const userAvatar = computed(() => {
    // 如果用户有头像，返回头像URL，否则返回默认头像
    if (user.value?.avatar) {
      return user.value.avatar
    }
    // 使用用户名首字母作为默认头像
    const firstLetter = userName.value.charAt(0).toUpperCase()
    return `https://ui-avatars.com/api/?name=${firstLetter}&background=409eff&color=fff&size=40`
  })
  
  // 动作
  const login = async (loginForm: LoginForm) => {
    try {
      const response = await authApi.login(loginForm)
      const { access_token, user: userData } = response
      
      // 保存token和用户信息
      token.value = access_token
      user.value = userData
      setToken(access_token)
      
      // 尝试获取用户权限，但不影响登录成功
      try {
        await loadUserPermissions()
      } catch (error) {
        console.warn('获取用户权限失败，使用默认权限:', error)
        // 设置默认权限
        setDefaultPermissions()
      }
      
      return response
    } catch (error) {
      console.error('登录失败:', error)
      throw error
    }
  }
  
  const register = async (registerForm: RegisterForm) => {
    try {
      const response = await authApi.register(registerForm)
      return response
    } catch (error) {
      console.error('注册失败:', error)
      throw error
    }
  }
  
  const logout = async () => {
    try {
      // 清除本地状态
      user.value = null
      token.value = ''
      permissions.value = []
      permissionObjects.value = []
      roles.value = []
      roleObjects.value = []
      removeToken()
      
      // 可以调用后端登出接口
      // await authApi.logout()
      
      ElMessage.success('退出登录成功')
    } catch (error) {
      console.error('退出登录失败:', error)
      // 即使后端接口失败，也要清除本地状态
      user.value = null
      token.value = ''
      permissions.value = []
      permissionObjects.value = []
      roles.value = []
      roleObjects.value = []
      removeToken()
    }
  }
  
  const getUserInfo = async () => {
    try {
      const response = await authApi.getCurrentUser()
      user.value = response
      
      // 获取用户权限
      await loadUserPermissions()
      
      return response
    } catch (error) {
      console.error('获取用户信息失败:', error)
      throw error
    }
  }

  /**
   * 加载用户权限信息
   */
  const loadUserPermissions = async () => {
    if (!user.value?.id) {
      console.warn('用户信息不存在，无法加载权限')
      return
    }

    try {
      // 获取用户权限
      const permissionsResponse = await roleApi.getUserPermissions(user.value.id)
      permissionObjects.value = permissionsResponse.data || []
      permissions.value = permissionObjects.value.map(p => p.code)

      // 获取用户角色（如果有相关API）
      // 暂时使用用户的role字段
      if (user.value?.role) {
        roles.value = [user.value.role]
      }

      console.log('用户权限加载成功:', permissions.value)
    } catch (error) {
      console.error('加载用户权限失败:', error)
      // 设置默认权限作为降级方案
      setDefaultPermissions()
    }
  }

  /**
   * 设置默认权限（降级方案）
   */
  const setDefaultPermissions = () => {
    if (user.value?.role === 'admin') {
      roles.value = ['admin']
      permissions.value = [
        'user:read', 'user:write', 'user:delete',
        'role:read', 'role:write', 'role:delete',
        'permission:read', 'permission:write', 'permission:delete',
        'model:read', 'model:write', 'model:delete',
        'deployment:read', 'deployment:write', 'deployment:delete',
        'system:read', 'system:write'
      ]
    } else {
      roles.value = ['user']
      permissions.value = [
        'model:read',
        'deployment:read', 'deployment:write'
      ]
    }
  }
  
  const updateProfile = async (profileData: Partial<User>) => {
    try {
      const response = await authApi.updateProfile(profileData)
      user.value = { ...user.value, ...response }
      ElMessage.success('个人信息更新成功')
      return response
    } catch (error) {
      console.error('更新个人信息失败:', error)
      throw error
    }
  }
  
  const changePassword = async (passwordData: { old_password: string; new_password: string }) => {
    try {
      const response = await authApi.changePassword(passwordData)
      ElMessage.success('密码修改成功')
      return response
    } catch (error) {
      console.error('修改密码失败:', error)
      throw error
    }
  }
  
  const refreshToken = async () => {
    try {
      const response = await authApi.refreshToken()
      const { access_token } = response
      token.value = access_token
      setToken(access_token)
      return response
    } catch (error) {
      console.error('刷新token失败:', error)
      // token刷新失败，清除登录状态
      await logout()
      throw error
    }
  }
  
  const initializeAuth = async () => {
    const savedToken = getToken()
    if (savedToken) {
      token.value = savedToken
      try {
        await getUserInfo()
      } catch (error) {
        console.error('初始化认证失败:', error)
        // 如果获取用户信息失败，清除token
        removeToken()
        token.value = ''
      }
    }
  }
  
  /**
   * 检查用户是否拥有指定权限
   * @param permission 权限代码
   * @returns 是否拥有权限
   */
  const hasPermission = (permission: string) => {
    if (!permission) return true
    return permissions.value.includes(permission)
  }
  
  /**
   * 检查用户是否拥有指定角色
   * @param role 角色名称
   * @returns 是否拥有角色
   */
  const hasRole = (role: string) => {
    if (!role) return true
    return roles.value.includes(role)
  }
  
  /**
   * 检查用户是否拥有任一指定权限
   * @param perms 权限代码数组
   * @returns 是否拥有任一权限
   */
  const hasAnyPermission = (perms: string[]) => {
    if (!perms || perms.length === 0) return true
    return perms.some(permission => permissions.value.includes(permission))
  }
  
  /**
   * 检查用户是否拥有所有指定权限
   * @param perms 权限代码数组
   * @returns 是否拥有所有权限
   */
  const hasAllPermissions = (perms: string[]) => {
    if (!perms || perms.length === 0) return true
    return perms.every(permission => permissions.value.includes(permission))
  }
  
  /**
   * 检查用户是否拥有任一指定角色
   * @param roleList 角色名称数组
   * @returns 是否拥有任一角色
   */
  const hasAnyRole = (roleList: string[]) => {
    if (!roleList || roleList.length === 0) return true
    return roleList.some(role => roles.value.includes(role))
  }

  /**
   * 检查用户是否拥有模块权限
   * @param module 模块名称
   * @param action 操作类型 (read, write, delete)
   * @returns 是否拥有权限
   */
  const hasModulePermission = (module: string, action: string = 'read') => {
    const permissionCode = `${module}:${action}`
    return hasPermission(permissionCode)
  }

  /**
   * 刷新用户权限
   */
  const refreshPermissions = async () => {
    if (user.value?.id) {
      await loadUserPermissions()
    }
  }
  
  return {
    // 状态
    user,
    token,
    permissions,
    permissionObjects,
    roles,
    roleObjects,
    
    // 计算属性
    isLoggedIn,
    isAdmin,
    userName,
    userEmail,
    userAvatar,
    
    // 动作
    login,
    register,
    logout,
    getUserInfo,
    updateProfile,
    changePassword,
    refreshToken,
    initializeAuth,
    loadUserPermissions,
    refreshPermissions,
    
    // 权限检查方法
    hasPermission,
    hasRole,
    hasAnyPermission,
    hasAllPermissions,
    hasAnyRole,
    hasModulePermission
  }
})