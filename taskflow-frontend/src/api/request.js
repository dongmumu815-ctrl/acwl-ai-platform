import axios from 'axios'
import { ElMessage, ElLoading } from 'element-plus'
import Cookies from 'js-cookie'

// 创建axios实例
const request = axios.create({
  baseURL: '/api/v1',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
request.interceptors.request.use(
  config => {
    // 添加认证token
    const token = Cookies.get('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    
    // 显示加载状态
    if (config.loading !== false) {
      config.loadingInstance = ElLoading.service({
        text: '加载中...',
        background: 'rgba(0, 0, 0, 0.7)'
      })
    }
    
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

// 响应拦截器
request.interceptors.response.use(
  response => {
    // 关闭加载状态
    if (response.config.loadingInstance) {
      response.config.loadingInstance.close()
    }
    
    const { data } = response
    
    // 处理业务错误
    if (data.code && data.code !== 200) {
      ElMessage.error(data.message || '请求失败')
      return Promise.reject(new Error(data.message || '请求失败'))
    }
    
    return data
  },
  error => {
    // 关闭加载状态
    if (error.config && error.config.loadingInstance) {
      error.config.loadingInstance.close()
    }
    
    let message = '请求失败'
    
    if (error.response) {
      const { status, data } = error.response
      
      switch (status) {
        case 401:
          message = '未授权，请重新登录'
          // 清除token并跳转到登录页
          Cookies.remove('token')
          // 检查是否禁用自动跳转
          if (!error.config?.skipAutoRedirect) {
            window.location.href = '/taskflow/login'
          }
          break
        case 403:
          message = '拒绝访问'
          break
        case 404:
          message = '请求地址不存在'
          break
        case 500:
          message = '服务器内部错误'
          break
        default:
          message = data?.message || `请求失败 (${status})`
      }
    } else if (error.code === 'ECONNABORTED') {
      message = '请求超时'
    } else {
      message = '网络错误'
    }
    
    ElMessage.error(message)
    return Promise.reject(error)
  }
)

export default request

/**
 * 封装常用的请求方法
 */
export const api = {
  /**
   * GET请求
   * @param {string} url 请求地址
   * @param {object} params 请求参数
   * @param {object} config 请求配置
   */
  get(url, params = {}, config = {}) {
    return request({
      method: 'GET',
      url,
      params,
      ...config
    })
  },
  
  /**
   * POST请求
   * @param {string} url 请求地址
   * @param {object} data 请求数据
   * @param {object} config 请求配置
   */
  post(url, data = {}, config = {}) {
    return request({
      method: 'POST',
      url,
      data,
      ...config
    })
  },
  
  /**
   * PUT请求
   * @param {string} url 请求地址
   * @param {object} data 请求数据
   * @param {object} config 请求配置
   */
  put(url, data = {}, config = {}) {
    return request({
      method: 'PUT',
      url,
      data,
      ...config
    })
  },
  
  /**
   * DELETE请求
   * @param {string} url 请求地址
   * @param {object} config 请求配置
   */
  delete(url, config = {}) {
    return request({
      method: 'DELETE',
      url,
      ...config
    })
  },
  
  /**
   * 文件上传
   * @param {string} url 上传地址
   * @param {FormData} formData 文件数据
   * @param {object} config 请求配置
   */
  upload(url, formData, config = {}) {
    return request({
      method: 'POST',
      url,
      data: formData,
      headers: {
        'Content-Type': 'multipart/form-data'
      },
      ...config
    })
  },
  
  /**
   * 文件下载
   * @param {string} url 下载地址
   * @param {object} params 请求参数
   * @param {string} filename 文件名
   */
  download(url, params = {}, filename = 'download') {
    return request({
      method: 'GET',
      url,
      params,
      responseType: 'blob',
      loading: false
    }).then(response => {
      const blob = new Blob([response])
      const downloadUrl = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = downloadUrl
      link.download = filename
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(downloadUrl)
    })
  }
}