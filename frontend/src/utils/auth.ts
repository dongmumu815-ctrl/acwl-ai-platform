import Cookies from 'js-cookie'

const TOKEN_KEY = 'acwl_token'
const REFRESH_TOKEN_KEY = 'acwl_refresh_token'
const USER_INFO_KEY = 'acwl_user_info'

// Token相关操作
export function getToken(): string | undefined {
  return Cookies.get(TOKEN_KEY) || localStorage.getItem(TOKEN_KEY) || undefined
}

export function setToken(token: string): void {
  Cookies.set(TOKEN_KEY, token, { expires: 7 }) // 7天过期
  localStorage.setItem(TOKEN_KEY, token)
}

export function removeToken(): void {
  Cookies.remove(TOKEN_KEY)
  localStorage.removeItem(TOKEN_KEY)
}

// 刷新Token相关操作
export function getRefreshToken(): string | undefined {
  return Cookies.get(REFRESH_TOKEN_KEY) || localStorage.getItem(REFRESH_TOKEN_KEY) || undefined
}

export function setRefreshToken(refreshToken: string): void {
  Cookies.set(REFRESH_TOKEN_KEY, refreshToken, { expires: 30 }) // 30天过期
  localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken)
}

export function removeRefreshToken(): void {
  Cookies.remove(REFRESH_TOKEN_KEY)
  localStorage.removeItem(REFRESH_TOKEN_KEY)
}

// 用户信息相关操作
export function getUserInfo(): any {
  const userInfo = localStorage.getItem(USER_INFO_KEY)
  return userInfo ? JSON.parse(userInfo) : null
}

export function setUserInfo(userInfo: any): void {
  localStorage.setItem(USER_INFO_KEY, JSON.stringify(userInfo))
}

export function removeUserInfo(): void {
  localStorage.removeItem(USER_INFO_KEY)
}

// 清除所有认证信息
export function clearAuth(): void {
  removeToken()
  removeRefreshToken()
  removeUserInfo()
}

// 检查Token是否过期
export function isTokenExpired(token?: string): boolean {
  if (!token) {
    token = getToken()
  }
  
  if (!token) {
    return true
  }
  
  try {
    // 解析JWT token
    const payload = JSON.parse(atob(token.split('.')[1]))
    const currentTime = Math.floor(Date.now() / 1000)
    
    // 检查是否过期（提前5分钟判断为过期）
    return payload.exp < currentTime + 300
  } catch (error) {
    console.error('Token解析失败:', error)
    return true
  }
}

// 获取Token过期时间
export function getTokenExpiration(token?: string): Date | null {
  if (!token) {
    token = getToken()
  }
  
  if (!token) {
    return null
  }
  
  try {
    const payload = JSON.parse(atob(token.split('.')[1]))
    return new Date(payload.exp * 1000)
  } catch (error) {
    console.error('Token解析失败:', error)
    return null
  }
}

// 获取Token中的用户信息
export function getTokenUserInfo(token?: string): any {
  if (!token) {
    token = getToken()
  }
  
  if (!token) {
    return null
  }
  
  try {
    const payload = JSON.parse(atob(token.split('.')[1]))
    return {
      userId: payload.sub,
      username: payload.username,
      email: payload.email,
      role: payload.role
    }
  } catch (error) {
    console.error('Token解析失败:', error)
    return null
  }
}

// 检查用户权限
export function hasPermission(permission: string, userPermissions?: string[]): boolean {
  if (!userPermissions) {
    const userInfo = getUserInfo()
    userPermissions = userInfo?.permissions || []
  }
  
  return userPermissions.includes(permission)
}

// 检查用户角色
export function hasRole(role: string, userRoles?: string[]): boolean {
  if (!userRoles) {
    const userInfo = getUserInfo()
    userRoles = userInfo?.roles || []
  }
  
  return userRoles.includes(role)
}

// 检查是否为管理员
export function isAdmin(): boolean {
  const userInfo = getUserInfo()
  return userInfo?.role === 'admin'
}

// 格式化权限显示
export function formatPermission(permission: string): string {
  const permissionMap: Record<string, string> = {
    'user:read': '查看用户',
    'user:write': '编辑用户',
    'user:delete': '删除用户',
    'model:read': '查看模型',
    'model:write': '编辑模型',
    'model:delete': '删除模型',
    'deployment:read': '查看部署',
    'deployment:write': '编辑部署',
    'deployment:delete': '删除部署',
    'system:read': '查看系统',
    'system:write': '编辑系统'
  }
  
  return permissionMap[permission] || permission
}

// 格式化角色显示
export function formatRole(role: string): string {
  const roleMap: Record<string, string> = {
    'admin': '管理员',
    'user': '普通用户',
    'viewer': '访客'
  }
  
  return roleMap[role] || role
}