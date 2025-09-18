/**
 * 验证工具函数
 * 提供各种数据验证和格式检查功能
 */

/**
 * 验证是否为外部链接
 * @param path 路径字符串
 * @returns 是否为外部链接
 */
export function isExternal(path: string): boolean {
  return /^(https?:|mailto:|tel:)/.test(path)
}

/**
 * 验证是否为有效的URL
 * @param url URL字符串
 * @returns 是否为有效URL
 */
export function isValidURL(url: string): boolean {
  try {
    new URL(url)
    return true
  } catch {
    return false
  }
}

/**
 * 验证邮箱格式
 * @param email 邮箱字符串
 * @returns 是否为有效邮箱
 */
export function isValidEmail(email: string): boolean {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  return emailRegex.test(email)
}

/**
 * 验证手机号格式（中国大陆）
 * @param phone 手机号字符串
 * @returns 是否为有效手机号
 */
export function isValidPhone(phone: string): boolean {
  const phoneRegex = /^1[3-9]\d{9}$/
  return phoneRegex.test(phone)
}

/**
 * 验证密码强度
 * @param password 密码字符串
 * @returns 密码强度等级 (0-4)
 */
export function getPasswordStrength(password: string): number {
  let strength = 0
  
  // 长度检查
  if (password.length >= 8) strength++
  if (password.length >= 12) strength++
  
  // 包含小写字母
  if (/[a-z]/.test(password)) strength++
  
  // 包含大写字母
  if (/[A-Z]/.test(password)) strength++
  
  // 包含数字
  if (/\d/.test(password)) strength++
  
  // 包含特殊字符
  if (/[^\w\s]/.test(password)) strength++
  
  return Math.min(strength, 4)
}

/**
 * 验证身份证号码（中国大陆）
 * @param idCard 身份证号码
 * @returns 是否为有效身份证号
 */
export function isValidIdCard(idCard: string): boolean {
  const idCardRegex = /^[1-9]\d{5}(18|19|20)\d{2}((0[1-9])|(1[0-2]))(([0-2][1-9])|10|20|30|31)\d{3}[0-9Xx]$/
  
  if (!idCardRegex.test(idCard)) {
    return false
  }
  
  // 校验码验证
  const weights = [7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2]
  const checkCodes = ['1', '0', 'X', '9', '8', '7', '6', '5', '4', '3', '2']
  
  let sum = 0
  for (let i = 0; i < 17; i++) {
    sum += parseInt(idCard[i]) * weights[i]
  }
  
  const checkCode = checkCodes[sum % 11]
  return checkCode === idCard[17].toUpperCase()
}

/**
 * 验证IP地址格式
 * @param ip IP地址字符串
 * @returns 是否为有效IP地址
 */
export function isValidIP(ip: string): boolean {
  const ipRegex = /^((25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(25[0-5]|2[0-4]\d|[01]?\d\d?)$/
  return ipRegex.test(ip)
}

/**
 * 验证端口号
 * @param port 端口号
 * @returns 是否为有效端口号
 */
export function isValidPort(port: number | string): boolean {
  const portNum = typeof port === 'string' ? parseInt(port) : port
  return Number.isInteger(portNum) && portNum >= 1 && portNum <= 65535
}

/**
 * 验证用户名格式
 * @param username 用户名
 * @returns 是否为有效用户名
 */
export function isValidUsername(username: string): boolean {
  // 用户名：3-20位，只能包含字母、数字、下划线，不能以数字开头
  const usernameRegex = /^[a-zA-Z_][a-zA-Z0-9_]{2,19}$/
  return usernameRegex.test(username)
}

/**
 * 验证文件扩展名
 * @param filename 文件名
 * @param allowedExtensions 允许的扩展名数组
 * @returns 是否为允许的文件类型
 */
export function isValidFileExtension(filename: string, allowedExtensions: string[]): boolean {
  const extension = filename.split('.').pop()?.toLowerCase()
  return extension ? allowedExtensions.includes(extension) : false
}

/**
 * 验证文件大小
 * @param fileSize 文件大小（字节）
 * @param maxSize 最大允许大小（字节）
 * @returns 是否在允许范围内
 */
export function isValidFileSize(fileSize: number, maxSize: number): boolean {
  return fileSize > 0 && fileSize <= maxSize
}

/**
 * 验证JSON字符串
 * @param jsonString JSON字符串
 * @returns 是否为有效JSON
 */
export function isValidJSON(jsonString: string): boolean {
  try {
    JSON.parse(jsonString)
    return true
  } catch {
    return false
  }
}

/**
 * 验证SQL表名或字段名
 * @param name 表名或字段名
 * @returns 是否为有效名称
 */
export function isValidSQLName(name: string): boolean {
  // SQL标识符：字母开头，可包含字母、数字、下划线
  const sqlNameRegex = /^[a-zA-Z][a-zA-Z0-9_]*$/
  return sqlNameRegex.test(name) && name.length <= 64
}

/**
 * 验证数据库连接字符串
 * @param connectionString 连接字符串
 * @returns 是否为有效连接字符串
 */
export function isValidConnectionString(connectionString: string): boolean {
  // 简单验证：包含必要的组件
  const hasHost = /host=/.test(connectionString)
  const hasPort = /port=/.test(connectionString)
  const hasDatabase = /database=/.test(connectionString)
  
  return hasHost && hasPort && hasDatabase
}

/**
 * 验证颜色值（十六进制）
 * @param color 颜色值
 * @returns 是否为有效颜色值
 */
export function isValidHexColor(color: string): boolean {
  const hexColorRegex = /^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$/
  return hexColorRegex.test(color)
}

/**
 * 验证版本号格式（语义化版本）
 * @param version 版本号
 * @returns 是否为有效版本号
 */
export function isValidVersion(version: string): boolean {
  const versionRegex = /^\d+\.\d+\.\d+(-[a-zA-Z0-9]+)?$/
  return versionRegex.test(version)
}

/**
 * 验证CRON表达式
 * @param cron CRON表达式
 * @returns 是否为有效CRON表达式
 */
export function isValidCron(cron: string): boolean {
  const cronParts = cron.trim().split(/\s+/)
  
  // 标准CRON表达式应该有5或6个部分
  if (cronParts.length !== 5 && cronParts.length !== 6) {
    return false
  }
  
  // 简单验证每个部分的格式
  const cronRegex = /^(\*|\d+(-\d+)?(,\d+(-\d+)?)*|\*\/\d+)$/
  return cronParts.every(part => cronRegex.test(part))
}

/**
 * 验证MAC地址
 * @param mac MAC地址
 * @returns 是否为有效MAC地址
 */
export function isValidMacAddress(mac: string): boolean {
  const macRegex = /^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$/
  return macRegex.test(mac)
}

/**
 * 验证UUID格式
 * @param uuid UUID字符串
 * @returns 是否为有效UUID
 */
export function isValidUUID(uuid: string): boolean {
  const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i
  return uuidRegex.test(uuid)
}