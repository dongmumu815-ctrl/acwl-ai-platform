/**
 * 工具函数集合
 */

/**
 * 防抖函数
 * @param {Function} func 要防抖的函数
 * @param {number} wait 等待时间
 * @param {boolean} immediate 是否立即执行
 * @returns {Function} 防抖后的函数
 */
export function debounce(func, wait, immediate = false) {
  let timeout
  return function executedFunction(...args) {
    const later = () => {
      timeout = null
      if (!immediate) func(...args)
    }
    const callNow = immediate && !timeout
    clearTimeout(timeout)
    timeout = setTimeout(later, wait)
    if (callNow) func(...args)
  }
}

/**
 * 节流函数
 * @param {Function} func 要节流的函数
 * @param {number} limit 时间间隔
 * @returns {Function} 节流后的函数
 */
export function throttle(func, limit) {
  let inThrottle
  return function(...args) {
    if (!inThrottle) {
      func.apply(this, args)
      inThrottle = true
      setTimeout(() => inThrottle = false, limit)
    }
  }
}

/**
 * 深拷贝对象
 * @param {any} obj 要拷贝的对象
 * @returns {any} 拷贝后的对象
 */
export function deepClone(obj) {
  if (obj === null || typeof obj !== 'object') {
    return obj
  }
  
  if (obj instanceof Date) {
    return new Date(obj.getTime())
  }
  
  if (obj instanceof Array) {
    return obj.map(item => deepClone(item))
  }
  
  if (typeof obj === 'object') {
    const clonedObj = {}
    for (const key in obj) {
      if (obj.hasOwnProperty(key)) {
        clonedObj[key] = deepClone(obj[key])
      }
    }
    return clonedObj
  }
}

/**
 * 格式化文件大小
 * @param {number} bytes 字节数
 * @param {number} decimals 小数位数
 * @returns {string} 格式化后的文件大小
 */
export function formatFileSize(bytes, decimals = 2) {
  if (bytes === 0) return '0 Bytes'
  
  const k = 1024
  const dm = decimals < 0 ? 0 : decimals
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB']
  
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i]
}

/**
 * 格式化数字
 * @param {number} num 数字
 * @param {number} decimals 小数位数
 * @returns {string} 格式化后的数字
 */
export function formatNumber(num, decimals = 0) {
  if (isNaN(num)) return '0'
  
  return num.toLocaleString('zh-CN', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals
  })
}

/**
 * 生成随机字符串
 * @param {number} length 字符串长度
 * @returns {string} 随机字符串
 */
export function generateRandomString(length = 8) {
  const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
  let result = ''
  for (let i = 0; i < length; i++) {
    result += chars.charAt(Math.floor(Math.random() * chars.length))
  }
  return result
}

/**
 * 生成UUID
 * @returns {string} UUID字符串
 */
export function generateUUID() {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
    const r = Math.random() * 16 | 0
    const v = c === 'x' ? r : (r & 0x3 | 0x8)
    return v.toString(16)
  })
}

/**
 * 验证邮箱格式
 * @param {string} email 邮箱地址
 * @returns {boolean} 是否有效
 */
export function validateEmail(email) {
  const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  return re.test(email)
}

/**
 * 验证手机号格式
 * @param {string} phone 手机号
 * @returns {boolean} 是否有效
 */
export function validatePhone(phone) {
  const re = /^1[3-9]\d{9}$/
  return re.test(phone)
}

/**
 * 验证身份证号格式
 * @param {string} idCard 身份证号
 * @returns {boolean} 是否有效
 */
export function validateIdCard(idCard) {
  const re = /(^\d{15}$)|(^\d{18}$)|(^\d{17}(\d|X|x)$)/
  return re.test(idCard)
}

/**
 * 获取URL参数
 * @param {string} name 参数名
 * @param {string} url URL地址
 * @returns {string|null} 参数值
 */
export function getUrlParam(name, url = window.location.href) {
  const regex = new RegExp('[?&]' + name + '(=([^&#]*)|&|#|$)')
  const results = regex.exec(url)
  if (!results) return null
  if (!results[2]) return ''
  return decodeURIComponent(results[2].replace(/\+/g, ' '))
}

/**
 * 设置URL参数
 * @param {string} name 参数名
 * @param {string} value 参数值
 * @param {string} url URL地址
 * @returns {string} 新的URL
 */
export function setUrlParam(name, value, url = window.location.href) {
  const regex = new RegExp('([?&])' + name + '=.*?(&|$)', 'i')
  const separator = url.indexOf('?') !== -1 ? '&' : '?'
  
  if (url.match(regex)) {
    return url.replace(regex, '$1' + name + '=' + value + '$2')
  } else {
    return url + separator + name + '=' + value
  }
}

/**
 * 移除URL参数
 * @param {string} name 参数名
 * @param {string} url URL地址
 * @returns {string} 新的URL
 */
export function removeUrlParam(name, url = window.location.href) {
  const regex = new RegExp('[?&]' + name + '(=([^&#]*)|&|#|$)')
  return url.replace(regex, function(match, p1, p2, p3) {
    return p1 === '?' && p3 ? '?' : ''
  })
}

/**
 * 下载文件
 * @param {string} url 文件URL
 * @param {string} filename 文件名
 */
export function downloadFile(url, filename) {
  const link = document.createElement('a')
  link.href = url
  link.download = filename || 'download'
  link.style.display = 'none'
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}

/**
 * 下载Blob数据
 * @param {Blob} blob Blob数据
 * @param {string} filename 文件名
 */
export function downloadBlob(blob, filename) {
  const url = window.URL.createObjectURL(blob)
  downloadFile(url, filename)
  window.URL.revokeObjectURL(url)
}

/**
 * 复制文本到剪贴板
 * @param {string} text 要复制的文本
 * @returns {Promise<boolean>} 是否成功
 */
export async function copyToClipboard(text) {
  try {
    if (navigator.clipboard && window.isSecureContext) {
      await navigator.clipboard.writeText(text)
      return true
    } else {
      // 降级方案
      const textArea = document.createElement('textarea')
      textArea.value = text
      textArea.style.position = 'fixed'
      textArea.style.left = '-999999px'
      textArea.style.top = '-999999px'
      document.body.appendChild(textArea)
      textArea.focus()
      textArea.select()
      const result = document.execCommand('copy')
      document.body.removeChild(textArea)
      return result
    }
  } catch (error) {
    console.error('复制失败:', error)
    return false
  }
}

/**
 * 获取浏览器信息
 * @returns {object} 浏览器信息
 */
export function getBrowserInfo() {
  const ua = navigator.userAgent
  const isOpera = !!window.opr && !!opr.addons || !!window.opera || navigator.userAgent.indexOf(' OPR/') >= 0
  const isFirefox = typeof InstallTrigger !== 'undefined'
  const isSafari = /constructor/i.test(window.HTMLElement) || (function (p) { return p.toString() === '[object SafariRemoteNotification]' })(!window['safari'] || (typeof safari !== 'undefined' && safari.pushNotification))
  const isIE = /*@cc_on!@*/false || !!document.documentMode
  const isEdge = !isIE && !!window.StyleMedia
  const isChrome = !!window.chrome && (!!window.chrome.webstore || !!window.chrome.runtime)
  const isBlink = (isChrome || isOpera) && !!window.CSS
  
  return {
    isOpera,
    isFirefox,
    isSafari,
    isIE,
    isEdge,
    isChrome,
    isBlink,
    userAgent: ua
  }
}

/**
 * 获取设备信息
 * @returns {object} 设备信息
 */
export function getDeviceInfo() {
  const ua = navigator.userAgent
  const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(ua)
  const isTablet = /iPad|Android(?!.*Mobile)/i.test(ua)
  const isDesktop = !isMobile && !isTablet
  
  return {
    isMobile,
    isTablet,
    isDesktop,
    userAgent: ua,
    platform: navigator.platform,
    language: navigator.language
  }
}

/**
 * 存储管理
 */
export const storage = {
  /**
   * 设置localStorage
   * @param {string} key 键名
   * @param {any} value 值
   */
  set(key, value) {
    try {
      localStorage.setItem(key, JSON.stringify(value))
    } catch (error) {
      console.error('localStorage设置失败:', error)
    }
  },
  
  /**
   * 获取localStorage
   * @param {string} key 键名
   * @param {any} defaultValue 默认值
   * @returns {any} 值
   */
  get(key, defaultValue = null) {
    try {
      const value = localStorage.getItem(key)
      return value ? JSON.parse(value) : defaultValue
    } catch (error) {
      console.error('localStorage获取失败:', error)
      return defaultValue
    }
  },
  
  /**
   * 移除localStorage
   * @param {string} key 键名
   */
  remove(key) {
    try {
      localStorage.removeItem(key)
    } catch (error) {
      console.error('localStorage移除失败:', error)
    }
  },
  
  /**
   * 清空localStorage
   */
  clear() {
    try {
      localStorage.clear()
    } catch (error) {
      console.error('localStorage清空失败:', error)
    }
  }
}

/**
 * 会话存储管理
 */
export const sessionStorage = {
  /**
   * 设置sessionStorage
   * @param {string} key 键名
   * @param {any} value 值
   */
  set(key, value) {
    try {
      window.sessionStorage.setItem(key, JSON.stringify(value))
    } catch (error) {
      console.error('sessionStorage设置失败:', error)
    }
  },
  
  /**
   * 获取sessionStorage
   * @param {string} key 键名
   * @param {any} defaultValue 默认值
   * @returns {any} 值
   */
  get(key, defaultValue = null) {
    try {
      const value = window.sessionStorage.getItem(key)
      return value ? JSON.parse(value) : defaultValue
    } catch (error) {
      console.error('sessionStorage获取失败:', error)
      return defaultValue
    }
  },
  
  /**
   * 移除sessionStorage
   * @param {string} key 键名
   */
  remove(key) {
    try {
      window.sessionStorage.removeItem(key)
    } catch (error) {
      console.error('sessionStorage移除失败:', error)
    }
  },
  
  /**
   * 清空sessionStorage
   */
  clear() {
    try {
      window.sessionStorage.clear()
    } catch (error) {
      console.error('sessionStorage清空失败:', error)
    }
  }
}

/**
 * 日期时间工具
 */
export const dateUtils = {
  /**
   * 格式化日期
   * @param {Date|string|number} date 日期
   * @param {string} format 格式
   * @returns {string} 格式化后的日期
   */
  format(date, format = 'YYYY-MM-DD HH:mm:ss') {
    const d = new Date(date)
    if (isNaN(d.getTime())) return ''
    
    const year = d.getFullYear()
    const month = String(d.getMonth() + 1).padStart(2, '0')
    const day = String(d.getDate()).padStart(2, '0')
    const hours = String(d.getHours()).padStart(2, '0')
    const minutes = String(d.getMinutes()).padStart(2, '0')
    const seconds = String(d.getSeconds()).padStart(2, '0')
    
    return format
      .replace('YYYY', year)
      .replace('MM', month)
      .replace('DD', day)
      .replace('HH', hours)
      .replace('mm', minutes)
      .replace('ss', seconds)
  },
  
  /**
   * 获取相对时间
   * @param {Date|string|number} date 日期
   * @returns {string} 相对时间
   */
  relative(date) {
    const d = new Date(date)
    const now = new Date()
    const diff = now.getTime() - d.getTime()
    
    const minute = 60 * 1000
    const hour = 60 * minute
    const day = 24 * hour
    const week = 7 * day
    const month = 30 * day
    const year = 365 * day
    
    if (diff < minute) {
      return '刚刚'
    } else if (diff < hour) {
      return Math.floor(diff / minute) + '分钟前'
    } else if (diff < day) {
      return Math.floor(diff / hour) + '小时前'
    } else if (diff < week) {
      return Math.floor(diff / day) + '天前'
    } else if (diff < month) {
      return Math.floor(diff / week) + '周前'
    } else if (diff < year) {
      return Math.floor(diff / month) + '个月前'
    } else {
      return Math.floor(diff / year) + '年前'
    }
  }
}

/**
 * 颜色工具
 */
export const colorUtils = {
  /**
   * 十六进制转RGB
   * @param {string} hex 十六进制颜色
   * @returns {object} RGB对象
   */
  hexToRgb(hex) {
    const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex)
    return result ? {
      r: parseInt(result[1], 16),
      g: parseInt(result[2], 16),
      b: parseInt(result[3], 16)
    } : null
  },
  
  /**
   * RGB转十六进制
   * @param {number} r 红色值
   * @param {number} g 绿色值
   * @param {number} b 蓝色值
   * @returns {string} 十六进制颜色
   */
  rgbToHex(r, g, b) {
    return '#' + [r, g, b].map(x => {
      const hex = x.toString(16)
      return hex.length === 1 ? '0' + hex : hex
    }).join('')
  },
  
  /**
   * 生成随机颜色
   * @returns {string} 十六进制颜色
   */
  random() {
    return '#' + Math.floor(Math.random() * 16777215).toString(16)
  }
}

/**
 * 格式化时间
 * @param {Date|string|number} date 日期
 * @param {string} format 格式
 * @returns {string} 格式化后的时间
 */
export function formatTime(date, format = 'YYYY-MM-DD HH:mm:ss') {
  return dateUtils.format(date, format)
}

/**
 * 格式化日期时间
 * @param {Date|string|number} date 日期
 * @param {string} format 格式
 * @returns {string} 格式化后的日期时间
 */
export function formatDateTime(date, format = 'YYYY-MM-DD HH:mm:ss') {
  return dateUtils.format(date, format)
}

/**
 * 格式化持续时间
 * @param {number} duration 持续时间（毫秒）
 * @returns {string} 格式化后的持续时间
 */
export function formatDuration(duration) {
  if (!duration || duration < 0) return '0秒'
  
  const seconds = Math.floor(duration / 1000)
  const minutes = Math.floor(seconds / 60)
  const hours = Math.floor(minutes / 60)
  const days = Math.floor(hours / 24)
  
  if (days > 0) {
    return `${days}天${hours % 24}小时${minutes % 60}分钟`
  } else if (hours > 0) {
    return `${hours}小时${minutes % 60}分钟`
  } else if (minutes > 0) {
    return `${minutes}分钟${seconds % 60}秒`
  } else {
    return `${seconds}秒`
  }
}

export default {
  debounce,
  throttle,
  deepClone,
  formatFileSize,
  formatNumber,
  generateRandomString,
  generateUUID,
  validateEmail,
  validatePhone,
  validateIdCard,
  getUrlParam,
  setUrlParam,
  removeUrlParam,
  downloadFile,
  downloadBlob,
  copyToClipboard,
  getBrowserInfo,
  getDeviceInfo,
  storage,
  sessionStorage,
  dateUtils,
  colorUtils,
  formatTime,
  formatDateTime,
  formatDuration
}