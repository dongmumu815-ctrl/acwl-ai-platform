/**
 * 日期时间工具函数
 */

/**
 * 格式化日期时间
 * @param date - 日期对象、时间戳或日期字符串
 * @param format - 格式化模式，默认为 'YYYY-MM-DD HH:mm:ss'
 * @returns 格式化后的日期字符串
 */
export function formatDateTime(date: Date | string | number, format: string = 'YYYY-MM-DD HH:mm:ss'): string {
  if (!date) return '-'
  
  const d = new Date(date)
  if (isNaN(d.getTime())) return '-'
  
  const year = d.getFullYear()
  const month = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  const hours = String(d.getHours()).padStart(2, '0')
  const minutes = String(d.getMinutes()).padStart(2, '0')
  const seconds = String(d.getSeconds()).padStart(2, '0')
  
  return format
    .replace('YYYY', String(year))
    .replace('MM', month)
    .replace('DD', day)
    .replace('HH', hours)
    .replace('mm', minutes)
    .replace('ss', seconds)
}

/**
 * 格式化日期
 * @param date - 日期对象、时间戳或日期字符串
 * @returns 格式化后的日期字符串 (YYYY-MM-DD)
 */
export function formatDate(date: Date | string | number): string {
  return formatDateTime(date, 'YYYY-MM-DD')
}

/**
 * 格式化时间
 * @param date - 日期对象、时间戳或日期字符串
 * @returns 格式化后的时间字符串 (HH:mm:ss)
 */
export function formatTime(date: Date | string | number): string {
  return formatDateTime(date, 'HH:mm:ss')
}

/**
 * 获取相对时间描述
 * @param date - 日期对象、时间戳或日期字符串
 * @returns 相对时间描述，如 "刚刚"、"5分钟前"、"2小时前" 等
 */
export function getRelativeTime(date: Date | string | number): string {
  if (!date) return '-'
  
  const d = new Date(date)
  if (isNaN(d.getTime())) return '-'
  
  const now = new Date()
  const diff = now.getTime() - d.getTime()
  
  // 小于1分钟
  if (diff < 60 * 1000) {
    return '刚刚'
  }
  
  // 小于1小时
  if (diff < 60 * 60 * 1000) {
    const minutes = Math.floor(diff / (60 * 1000))
    return `${minutes}分钟前`
  }
  
  // 小于1天
  if (diff < 24 * 60 * 60 * 1000) {
    const hours = Math.floor(diff / (60 * 60 * 1000))
    return `${hours}小时前`
  }
  
  // 小于7天
  if (diff < 7 * 24 * 60 * 60 * 1000) {
    const days = Math.floor(diff / (24 * 60 * 60 * 1000))
    return `${days}天前`
  }
  
  // 超过7天，显示具体日期
  return formatDate(d)
}

/**
 * 判断是否为今天
 * @param date - 日期对象、时间戳或日期字符串
 * @returns 是否为今天
 */
export function isToday(date: Date | string | number): boolean {
  if (!date) return false
  
  const d = new Date(date)
  if (isNaN(d.getTime())) return false
  
  const today = new Date()
  return d.toDateString() === today.toDateString()
}

/**
 * 判断是否为昨天
 * @param date - 日期对象、时间戳或日期字符串
 * @returns 是否为昨天
 */
export function isYesterday(date: Date | string | number): boolean {
  if (!date) return false
  
  const d = new Date(date)
  if (isNaN(d.getTime())) return false
  
  const yesterday = new Date()
  yesterday.setDate(yesterday.getDate() - 1)
  return d.toDateString() === yesterday.toDateString()
}

/**
 * 获取时间段描述
 * @param startDate - 开始时间
 * @param endDate - 结束时间
 * @returns 时间段描述
 */
export function getTimeRange(startDate: Date | string | number, endDate: Date | string | number): string {
  if (!startDate || !endDate) return '-'
  
  const start = new Date(startDate)
  const end = new Date(endDate)
  
  if (isNaN(start.getTime()) || isNaN(end.getTime())) return '-'
  
  const startStr = formatDateTime(start)
  const endStr = formatDateTime(end)
  
  return `${startStr} ~ ${endStr}`
}

/**
 * 计算持续时间
 * @param startDate - 开始时间
 * @param endDate - 结束时间（可选，默认为当前时间）
 * @returns 持续时间描述
 */
export function getDuration(startDate: Date | string | number, endDate?: Date | string | number): string {
  if (!startDate) return '-'
  
  const start = new Date(startDate)
  if (isNaN(start.getTime())) return '-'
  
  const end = endDate ? new Date(endDate) : new Date()
  if (isNaN(end.getTime())) return '-'
  
  const diff = end.getTime() - start.getTime()
  
  if (diff < 0) return '-'
  
  const seconds = Math.floor(diff / 1000)
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

/**
 * 获取当前时间戳
 * @returns 当前时间戳（毫秒）
 */
export function getCurrentTimestamp(): number {
  return Date.now()
}

/**
 * 获取今天的开始时间
 * @returns 今天的开始时间（00:00:00）
 */
export function getTodayStart(): Date {
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  return today
}

/**
 * 获取今天的结束时间
 * @returns 今天的结束时间（23:59:59）
 */
export function getTodayEnd(): Date {
  const today = new Date()
  today.setHours(23, 59, 59, 999)
  return today
}

/**
 * 获取本周的开始时间
 * @returns 本周的开始时间（周一 00:00:00）
 */
export function getWeekStart(): Date {
  const today = new Date()
  const day = today.getDay()
  const diff = today.getDate() - day + (day === 0 ? -6 : 1) // 调整为周一开始
  const monday = new Date(today.setDate(diff))
  monday.setHours(0, 0, 0, 0)
  return monday
}

/**
 * 获取本月的开始时间
 * @returns 本月的开始时间（1号 00:00:00）
 */
export function getMonthStart(): Date {
  const today = new Date()
  return new Date(today.getFullYear(), today.getMonth(), 1, 0, 0, 0, 0)
}

/**
 * 获取本年的开始时间
 * @returns 本年的开始时间（1月1日 00:00:00）
 */
export function getYearStart(): Date {
  const today = new Date()
  return new Date(today.getFullYear(), 0, 1, 0, 0, 0, 0)
}

/**
 * 解析ISO日期字符串
 * @param isoString - ISO格式的日期字符串
 * @returns Date对象
 */
export function parseISOString(isoString: string): Date | null {
  if (!isoString) return null
  
  try {
    const date = new Date(isoString)
    return isNaN(date.getTime()) ? null : date
  } catch {
    return null
  }
}

/**
 * 将Date对象转换为ISO字符串
 * @param date - Date对象
 * @returns ISO格式的日期字符串
 */
export function toISOString(date: Date): string {
  if (!date || isNaN(date.getTime())) return ''
  return date.toISOString()
}

/**
 * 格式化文件大小的时间戳
 * @param timestamp - 时间戳
 * @returns 格式化后的时间字符串
 */
export function formatTimestamp(timestamp: number): string {
  if (!timestamp) return '-'
  return formatDateTime(new Date(timestamp * 1000))
}