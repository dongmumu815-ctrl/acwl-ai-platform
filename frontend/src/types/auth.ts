// 用户相关类型定义
export interface User {
  id: number
  username: string
  email: string
  role: 'admin' | 'user' | 'viewer'
  is_active: boolean
  avatar?: string
  full_name?: string
  phone?: string
  department?: string
  last_login?: string
  created_at: string
  updated_at: string
}

// 登录表单
export interface LoginForm {
  email: string
  password: string
  remember?: boolean
}

// 注册表单
export interface RegisterForm {
  username: string
  email: string
  password: string
  confirm_password: string
  full_name?: string
  phone?: string
  department?: string
}

// 修改密码表单
export interface ChangePasswordForm {
  old_password: string
  new_password: string
  confirm_password: string
}

// 用户更新表单
export interface UserUpdateForm {
  username?: string
  email?: string
  full_name?: string
  phone?: string
  department?: string
  avatar?: string
}

// Token信息
export interface TokenInfo {
  access_token: string
  refresh_token?: string
  token_type: string
  expires_in?: number
}

// 用户权限
export interface UserPermission {
  id: number
  name: string
  code: string
  description?: string
  category: string
}

// 用户角色
export interface UserRole {
  id: number
  name: string
  code: string
  description?: string
  permissions: UserPermission[]
}

// 用户会话信息
export interface UserSession {
  id: string
  user_id: number
  ip_address: string
  user_agent: string
  login_time: string
  last_activity: string
  is_active: boolean
}

// 用户操作日志
export interface UserLog {
  id: number
  user_id: number
  action: string
  resource: string
  resource_id?: number
  ip_address: string
  user_agent: string
  details?: Record<string, any>
  created_at: string
}

// 用户统计信息
export interface UserStats {
  total_users: number
  active_users: number
  new_users_today: number
  new_users_this_week: number
  new_users_this_month: number
  user_growth_rate: number
}

// 分页响应
export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  size: number
  pages: number
}

// API响应基础结构
export interface ApiResponse<T = any> {
  success: boolean
  message: string
  data: T
  timestamp: string
}

// 错误响应
export interface ErrorResponse {
  error: string
  message: string
  detail?: any
  timestamp: string
}