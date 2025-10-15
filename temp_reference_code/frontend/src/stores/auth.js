import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/utils/api'

export const useAuthStore = defineStore('auth', () => {
  // 状态
  const token = ref(localStorage.getItem('admin_token') || '')
  const userInfo = ref((() => {
    const stored = localStorage.getItem('admin_user')
    if (stored && stored !== 'undefined') {
      try {
        return JSON.parse(stored)
      } catch (e) {
        console.warn('Failed to parse stored user info:', e)
        return null
      }
    }
    return null
  })())
  
  // 计算属性
  const isAuthenticated = computed(() => !!token.value)
  
  // 登录
  const login = async (credentials) => {
    try {
      const response = await api.post('/admin/login', credentials)
      const { access_token, user } = response.data
      
      token.value = access_token
      userInfo.value = user
      
      // 保存到本地存储
      localStorage.setItem('admin_token', access_token)
      localStorage.setItem('admin_user', JSON.stringify(user))
      
      // 注意：不在这里设置默认请求头，统一由api.js的请求拦截器处理
      
      return { success: true }
    } catch (error) {
      return {
        success: false,
        message: error.response?.data?.detail || '登录失败'
      }
    }
  }
  
  // 登出
  const logout = () => {
    token.value = ''
    userInfo.value = null
    
    // 清除本地存储
    localStorage.removeItem('admin_token')
    localStorage.removeItem('admin_user')
    
    // 注意：不需要手动清除请求头，api.js的请求拦截器会自动处理
  }
  
  // 注意：不在初始化时设置请求头，统一由api.js的请求拦截器处理
  
  return {
    token,
    userInfo,
    isAuthenticated,
    login,
    logout
  }
})