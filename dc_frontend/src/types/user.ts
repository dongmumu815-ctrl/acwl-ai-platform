/**
 * 用户相关类型定义
 */

/**
 * 用户基本信息
 */
export interface User {
  id: number
  username: string
  email: string
  full_name?: string
  avatar?: string
  phone?: string
  department?: string
  position?: string
  is_active?: boolean
  is_superuser?: boolean
  role?: string
  permissions?: string[]
  roles?: string[]
  created_at: string
  updated_at?: string
  last_login?: string
}

/**
 * 登录请求数据
 */
export interface LoginRequest {
  email: string
  password: string
  remember?: boolean
}

/**
 * 登录响应数据
 */
export interface LoginResponse {
  access_token: string
  expires_in: number
  token_type: string
  user: User
}

/**
 * 用户权限信息
 */
export interface UserPermission {
  id: number
  name: string
  code: string
  description?: string
  resource_type?: string
  resource_id?: number
}

/**
 * 用户角色信息
 */
export interface UserRole {
  id: number
  name: string
  code: string
  description?: string
  permissions: UserPermission[]
}

/**
 * 用户详细信息（包含权限和角色）
 */
export interface UserDetail extends User {
  permissions: UserPermission[]
  roles: UserRole[]
}

/**
 * 用户更新请求数据
 */
export interface UserUpdateRequest {
  full_name?: string
  email?: string
  phone?: string
  department?: string
  position?: string
  avatar?: string
}

/**
 * 密码修改请求数据
 */
export interface PasswordChangeRequest {
  old_password: string
  new_password: string
  confirm_password: string
}

/**
 * 用户注册请求数据
 */
export interface RegisterRequest {
  username: string
  email: string
  password: string
  confirm_password: string
  full_name: string
  phone?: string
  department?: string
  position?: string
}

/**
 * 忘记密码请求数据
 */
export interface ForgotPasswordRequest {
  email: string
}

/**
 * 重置密码请求数据
 */
export interface ResetPasswordRequest {
  token: string
  password: string
  confirm_password: string
}

/**
 * 用户列表查询参数
 */
export interface UserListQuery {
  page?: number
  page_size?: number
  search?: string
  department?: string
  is_active?: boolean
  sort_by?: string
  sort_order?: 'asc' | 'desc'
}

/**
 * 用户列表响应数据
 */
export interface UserListResponse {
  users: User[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

/**
 * 用户状态枚举
 */
export enum UserStatus {
  ACTIVE = 'active',
  INACTIVE = 'inactive',
  SUSPENDED = 'suspended',
  PENDING = 'pending'
}

/**
 * 权限类型枚举
 */
export enum PermissionType {
  READ = 'read',
  WRITE = 'write',
  DELETE = 'delete',
  ADMIN = 'admin'
}

/**
 * 资源类型枚举
 */
export enum ResourceType {
  DATA_RESOURCE = 'data_resource',
  CATEGORY = 'category',
  TAG = 'tag',
  USER = 'user',
  SYSTEM = 'system'
}

/**
 * API响应基础结构
 */
export interface ApiResponse<T = any> {
  success: boolean
  message: string
  data: T
  code?: number
}

/**
 * 分页响应结构
 */
export interface PaginatedResponse<T = any> {
  items: T[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

/**
 * 用户会话信息
 */
export interface UserSession {
  id: string
  user_id: number
  ip_address: string
  user_agent: string
  created_at: string
  last_activity: string
  is_current: boolean
}

/**
 * 用户活动日志
 */
export interface UserActivity {
  id: number
  user_id: number
  action: string
  resource_type: string
  resource_id?: number
  description: string
  ip_address: string
  user_agent: string
  created_at: string
}

/**
 * 用户偏好设置
 */
export interface UserPreferences {
  theme: 'light' | 'dark' | 'auto'
  language: string
  timezone: string
  date_format: string
  time_format: string
  page_size: number
  notifications: {
    email: boolean
    browser: boolean
    mobile: boolean
  }
}

/**
 * 用户统计信息
 */
export interface UserStats {
  total_logins: number
  last_login: string
  resources_created: number
  resources_accessed: number
  queries_executed: number
  favorites_count: number
}