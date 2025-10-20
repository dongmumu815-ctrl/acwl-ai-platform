import axios from 'axios'

const API_BASE_URL = '/dataainsight/api/auth'

// 登录
export const login = async (secretKey) => {
  try {
    const response = await axios.post(`${API_BASE_URL}/login`, {
      secret_key: secretKey
    })
    return response.data
  } catch (error) {
    console.error('登录请求失败:', error)
    throw error
  }
}

// 验证token
export const verifyToken = async (token) => {
  try {
    const response = await axios.post(`${API_BASE_URL}/verify`, {}, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })
    return response.data
  } catch (error) {
    console.error('Token验证失败:', error)
    throw error
  }
}

// 登出
export const logout = () => {
  localStorage.removeItem('auth_token')
}

// 获取token
export const getToken = () => {
  return localStorage.getItem('auth_token')
}

// 检查是否已登录
export const isAuthenticated = () => {
  const token = getToken()
  return !!token
}