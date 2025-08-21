import { request } from '@/utils/request'
import type { LoginForm, RegisterForm, User, ChangePasswordForm } from '@/types/auth'

// 认证API接口
export const authApi = {
  // 用户登录
  login(data: LoginForm) {
    return request.post<{
      access_token: string
      refresh_token?: string
      token_type: string
      user: User
    }>('/auth/login/json', data)
  },

  // 用户注册
  register(data: RegisterForm) {
    return request.post<{
      message: string
      user: User
    }>('/auth/register', data)
  },

  // 用户登出
  logout() {
    return request.post('/auth/logout')
  },

  // 获取当前用户信息
  getCurrentUser() {
    return request.get<User>('/auth/me')
  },

  // 刷新Token
  refreshToken() {
    return request.post<{
      access_token: string
      token_type: string
    }>('/auth/refresh')
  },

  // 更新用户资料
  updateProfile(data: Partial<User>) {
    return request.put<User>('/auth/profile', data)
  },

  // 修改密码
  changePassword(data: ChangePasswordForm) {
    return request.post('/auth/change-password', data)
  },

  // 忘记密码
  forgotPassword(email: string) {
    return request.post('/auth/forgot-password', { email })
  },

  // 重置密码
  resetPassword(data: { token: string; password: string }) {
    return request.post('/auth/reset-password', data)
  },

  // 验证邮箱
  verifyEmail(token: string) {
    return request.post('/auth/verify-email', { token })
  },

  // 重新发送验证邮件
  resendVerificationEmail() {
    return request.post('/auth/resend-verification')
  }
}

// 用户管理API接口（管理员功能）
export const userApi = {
  // 获取用户列表
  getUsers(params?: {
    page?: number
    size?: number
    search?: string
    role?: string
    is_active?: boolean
  }) {
    return request.get('/users/', { params })
  },

  // 获取用户详情
  getUser(userId: number) {
    return request.get<User>(`/users/${userId}`)
  },

  // 创建用户
  createUser(data: RegisterForm) {
    return request.post<User>('/users/', data)
  },

  // 更新用户
  updateUser(userId: number, data: Partial<User>) {
    return request.put<User>(`/users/${userId}`, data)
  },

  // 删除用户
  deleteUser(userId: number) {
    return request.delete(`/users/${userId}`)
  },

  // 批量删除用户
  batchDeleteUsers(userIds: number[]) {
    return request.post('/users/batch-delete', { user_ids: userIds })
  },

  // 启用/禁用用户
  toggleUserStatus(userId: number, isActive: boolean) {
    return request.patch(`/users/${userId}/status`, { is_active: isActive })
  },

  // 重置用户密码
  resetUserPassword(userId: number, newPassword: string) {
    return request.post(`/users/${userId}/reset-password`, { password: newPassword })
  },

  // 获取用户权限
  getUserPermissions(userId: number) {
    return request.get<string[]>(`/users/${userId}/permissions`)
  },

  // 更新用户权限
  updateUserPermissions(userId: number, permissions: string[]) {
    return request.put(`/users/${userId}/permissions`, { permissions })
  },

  // 获取用户操作日志
  getUserLogs(userId: number, params?: {
    page?: number
    size?: number
    start_date?: string
    end_date?: string
  }) {
    return request.get(`/users/${userId}/logs`, { params })
  }
}