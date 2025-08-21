import { api } from './request'

/**
 * 认证API接口
 */
export const authApi = {
  /**
   * 用户登录
   * @param {object} data 登录数据 {username, password}
   */
  login(data) {
    return api.post('/auth/login/json', data)
  },

  /**
   * 用户注册
   * @param {object} data 注册数据
   */
  register(data) {
    return api.post('/auth/register', data)
  },

  /**
   * 用户登出
   */
  logout() {
    return api.post('/auth/logout')
  },

  /**
   * 获取当前用户信息
   */
  getCurrentUser() {
    return api.get('/auth/me')
  },

  /**
   * 刷新Token
   */
  refreshToken() {
    return api.post('/auth/refresh')
  },

  /**
   * 更新用户资料
   * @param {object} data 用户数据
   */
  updateProfile(data) {
    return api.put('/auth/profile', data)
  },

  /**
   * 修改密码
   * @param {object} data 密码数据 {old_password, new_password}
   */
  changePassword(data) {
    return api.post('/auth/change-password', data)
  },

  /**
   * 忘记密码
   * @param {string} email 邮箱地址
   */
  forgotPassword(email) {
    return api.post('/auth/forgot-password', { email })
  },

  /**
   * 重置密码
   * @param {object} data 重置数据 {token, password}
   */
  resetPassword(data) {
    return api.post('/auth/reset-password', data)
  },

  /**
   * 验证邮箱
   * @param {string} token 验证令牌
   */
  verifyEmail(token) {
    return api.post('/auth/verify-email', { token })
  },

  /**
   * 重新发送验证邮件
   */
  resendVerificationEmail() {
    return api.post('/auth/resend-verification')
  }
}

/**
 * 用户管理API接口（管理员功能）
 */
export const userApi = {
  /**
   * 获取用户列表
   * @param {object} params 查询参数
   */
  getUsers(params = {}) {
    return api.get('/users/', params)
  },

  /**
   * 获取用户详情
   * @param {number} userId 用户ID
   */
  getUser(userId) {
    return api.get(`/users/${userId}`)
  },

  /**
   * 创建用户
   * @param {object} data 用户数据
   */
  createUser(data) {
    return api.post('/users/', data)
  },

  /**
   * 更新用户
   * @param {number} userId 用户ID
   * @param {object} data 用户数据
   */
  updateUser(userId, data) {
    return api.put(`/users/${userId}`, data)
  },

  /**
   * 删除用户
   * @param {number} userId 用户ID
   */
  deleteUser(userId) {
    return api.delete(`/users/${userId}`)
  },

  /**
   * 批量删除用户
   * @param {number[]} userIds 用户ID数组
   */
  batchDeleteUsers(userIds) {
    return api.post('/users/batch-delete', { user_ids: userIds })
  },

  /**
   * 启用/禁用用户
   * @param {number} userId 用户ID
   * @param {boolean} isActive 是否激活
   */
  toggleUserStatus(userId, isActive) {
    return api.patch(`/users/${userId}/status`, { is_active: isActive })
  },

  /**
   * 重置用户密码
   * @param {number} userId 用户ID
   * @param {string} newPassword 新密码
   */
  resetUserPassword(userId, newPassword) {
    return api.post(`/users/${userId}/reset-password`, { password: newPassword })
  },

  /**
   * 获取用户权限
   * @param {number} userId 用户ID
   */
  getUserPermissions(userId) {
    return api.get(`/users/${userId}/permissions`)
  },

  /**
   * 更新用户权限
   * @param {number} userId 用户ID
   * @param {string[]} permissions 权限数组
   */
  updateUserPermissions(userId, permissions) {
    return api.put(`/users/${userId}/permissions`, { permissions })
  },

  /**
   * 获取用户操作日志
   * @param {number} userId 用户ID
   * @param {object} params 查询参数
   */
  getUserLogs(userId, params = {}) {
    return api.get(`/users/${userId}/logs`, params)
  }
}