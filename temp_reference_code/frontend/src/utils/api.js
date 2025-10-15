import axios from 'axios'
import { ElMessage } from 'element-plus'
import router from '@/router'

// 防止并发401请求重复处理
let isHandling401 = false

// 创建axios实例
const api = axios.create({
  baseURL: '/api/v1',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    // 从localStorage获取token
    const token = localStorage.getItem('admin_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
      // 开发环境下添加调试日志
      if (process.env.NODE_ENV === 'development') {
        console.log(`[API Request] ${config.method?.toUpperCase()} ${config.url} - Token: ${token.substring(0, 20)}...`)
      }
    } else {
      // 开发环境下记录无token的请求
      if (process.env.NODE_ENV === 'development') {
        console.warn(`[API Request] ${config.method?.toUpperCase()} ${config.url} - No token found`)
      }
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  (response) => {
    return response
  },
  (error) => {
    const { response } = error
    
    if (response) {
      switch (response.status) {
        case 401:
          // 未授权，清除token并跳转到登录页
          // 防止并发请求重复处理401
          if (!isHandling401) {
            isHandling401 = true
            localStorage.removeItem('admin_token')
            localStorage.removeItem('admin_user')
            router.push('/login')
            ElMessage.error('登录已过期，请重新登录')
            // 重置标志位
            setTimeout(() => {
              isHandling401 = false
            }, 1000)
          }
          break
        case 403:
          ElMessage.error('没有权限访问该资源')
          break
        case 404:
          ElMessage.error('请求的资源不存在')
          break
        case 500:
          ElMessage.error('服务器内部错误')
          break
        default:
          ElMessage.error(response.data?.detail || '请求失败')
      }
    } else {
      ElMessage.error('网络连接失败')
    }
    
    return Promise.reject(error)
  }
)

export default api