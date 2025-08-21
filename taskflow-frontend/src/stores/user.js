import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import Cookies from 'js-cookie'
import { api } from '@/api/request'
import { authApi } from '@/api/auth'

/**
 * 用户状态管理
 */
export const useUserStore = defineStore('user', () => {
  // 状态
  const userInfo = ref(null)
  const token = ref(Cookies.get('token') || '')
  const permissions = ref([])
  const roles = ref([])
  
  // 计算属性
  const isLoggedIn = computed(() => !!token.value)
  const userName = computed(() => userInfo.value?.username || '')
  const userAvatar = computed(() => userInfo.value?.avatar || '')
  const userEmail = computed(() => userInfo.value?.email || '')
  
  /**
   * 设置token
   * @param {string} newToken 新token
   */
  const setToken = (newToken) => {
    token.value = newToken
    if (newToken) {
      Cookies.set('token', newToken, { expires: 7 }) // 7天过期
    } else {
      Cookies.remove('token')
    }
  }
  
  /**
   * 设置用户信息
   * @param {object} info 用户信息
   */
  const setUserInfo = (info) => {
    userInfo.value = info
  }
  
  /**
   * 设置权限
   * @param {array} perms 权限列表
   */
  const setPermissions = (perms) => {
    permissions.value = perms
  }
  
  /**
   * 设置角色
   * @param {array} roleList 角色列表
   */
  const setRoles = (roleList) => {
    roles.value = roleList
  }
  
  /**
   * 登录
   * @param {object} loginData 登录数据
   */
  const login = async (loginData) => {
    try {
      const response = await authApi.login(loginData)
      const { access_token, user } = response.data || response
      
      setToken(access_token)
      setUserInfo(user)
      
      return response
    } catch (error) {
      throw error
    }
  }
  
  /**
   * 获取用户信息
   */
  const getUserInfo = async () => {
    try {
      console.log('正在调用获取用户信息API...')
      const response = await authApi.getCurrentUser()
      console.log('获取用户信息API响应:', response)
      const user = response.data || response
      console.log('解析的用户信息:', user)
      
      setUserInfo(user)
      // 如果响应中包含权限和角色信息，则设置
      if (user.permissions) {
        setPermissions(user.permissions)
      }
      if (user.roles) {
        setRoles(user.roles)
      }
      
      console.log('用户信息设置完成')
      return response
    } catch (error) {
      console.error('getUserInfo方法捕获到错误:', error)
      throw error
    }
  }
  
  /**
   * 登出
   */
  const logout = async () => {
    console.log('开始执行登出操作...')
    try {
      await authApi.logout()
      console.log('登出API调用成功')
    } catch (error) {
      console.error('登出请求失败:', error)
    } finally {
      // 清除本地状态
      console.log('清除本地用户状态...')
      setToken('')
      setUserInfo(null)
      setPermissions([])
      setRoles([])
      
      // 跳转到登录页
      console.log('即将跳转到登录页面')
      window.location.href = '/taskflow/login'
    }
  }
  
  /**
   * 刷新 token
   */
  const refreshToken = async () => {
    try {
      const response = await authApi.refreshToken()
      const { access_token } = response.data || response
      setToken(access_token)
      return response
    } catch (error) {
      // 刷新失败，清除 token
      setToken('')
      throw error
    }
  }
  
  /**
   * 检查权限
   * @param {string} permission 权限标识
   */
  const hasPermission = (permission) => {
    return permissions.value.includes(permission)
  }
  
  /**
   * 检查角色
   * @param {string} role 角色标识
   */
  const hasRole = (role) => {
    return roles.value.includes(role)
  }
  
  /**
   * 更新用户信息
   * @param {object} data 更新数据
   */
  const updateUserInfo = async (data) => {
    try {
      const response = await api.put('/auth/user', data)
      const { user } = response.data
      
      setUserInfo(user)
      
      return response
    } catch (error) {
      throw error
    }
  }
  
  /**
   * 修改密码
   * @param {object} data 密码数据
   */
  const changePassword = async (data) => {
    try {
      const response = await api.put('/auth/password', data)
      return response
    } catch (error) {
      throw error
    }
  }
  
  return {
    // 状态
    userInfo,
    token,
    permissions,
    roles,
    
    // 计算属性
    isLoggedIn,
    userName,
    userAvatar,
    userEmail,
    
    // 方法
    setToken,
    setUserInfo,
    setPermissions,
    setRoles,
    login,
    getUserInfo,
    logout,
    refreshToken,
    hasPermission,
    hasRole,
    updateUserInfo,
    changePassword
  }
})