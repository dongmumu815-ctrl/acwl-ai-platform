/**
 * 用户管理相关的API接口
 */

import { request } from '@/utils/request'
import type {
  User,
  Role,
  Permission,
  UserQuery,
  UserCreateData,
  UserUpdateData,
  RoleQuery,
  RoleCreateData,
  RoleUpdateData,
  PermissionQuery,
  UserProfile,
  UserPreferences,
  UserSession,
  UserLoginLog,
  UserOperationLog,
  UserGroup,
  UserResponse,
  PaginatedUserResponse
} from '@/types/user'

// 用户基础API

/**
 * 获取用户列表
 */
export const getUsers = (params: UserQuery): Promise<PaginatedUserResponse<User>> => {
  return request({
    url: '/api/users',
    method: 'get',
    params
  })
}

/**
 * 获取用户详情
 */
export const getUserById = (id: string): Promise<UserResponse<User>> => {
  return request({
    url: `/api/users/${id}`,
    method: 'get'
  })
}

/**
 * 创建用户
 */
export const createUser = (data: UserCreateData): Promise<UserResponse<User>> => {
  return request({
    url: '/api/users',
    method: 'post',
    data
  })
}

/**
 * 更新用户
 */
export const updateUser = (id: string, data: UserUpdateData): Promise<UserResponse<User>> => {
  return request({
    url: `/api/users/${id}`,
    method: 'put',
    data
  })
}

/**
 * 删除用户
 */
export const deleteUser = (id: string): Promise<UserResponse<void>> => {
  return request({
    url: `/api/users/${id}`,
    method: 'delete'
  })
}

/**
 * 批量删除用户
 */
export const batchDeleteUsers = (ids: string[]): Promise<UserResponse<void>> => {
  return request({
    url: '/api/users/batch-delete',
    method: 'post',
    data: { ids }
  })
}

/**
 * 启用/禁用用户
 */
export const toggleUser = (id: string, enabled: boolean): Promise<UserResponse<void>> => {
  return request({
    url: `/api/users/${id}/toggle`,
    method: 'patch',
    data: { enabled }
  })
}

/**
 * 重置用户密码
 */
export const resetUserPassword = (id: string, newPassword?: string): Promise<UserResponse<{ password?: string }>> => {
  return request({
    url: `/api/users/${id}/reset-password`,
    method: 'post',
    data: { newPassword }
  })
}

/**
 * 强制用户下次登录修改密码
 */
export const forcePasswordChange = (id: string): Promise<UserResponse<void>> => {
  return request({
    url: `/api/users/${id}/force-password-change`,
    method: 'patch'
  })
}

// 用户认证API

/**
 * 用户登录
 */
export const login = (data: {
  username: string
  password: string
  captcha?: string
  rememberMe?: boolean
}): Promise<UserResponse<{ token: string; refreshToken: string; user: User }>> => {
  return request({
    url: '/api/auth/login',
    method: 'post',
    data
  })
}

/**
 * 用户登出
 */
export const logout = (): Promise<UserResponse<void>> => {
  return request({
    url: '/api/auth/logout',
    method: 'post'
  })
}

/**
 * 刷新令牌
 */
export const refreshToken = (refreshToken: string): Promise<UserResponse<{ token: string; refreshToken: string }>> => {
  return request({
    url: '/api/auth/refresh',
    method: 'post',
    data: { refreshToken }
  })
}

/**
 * 获取当前用户信息
 */
export const getCurrentUser = (): Promise<UserResponse<User>> => {
  return request({
    url: '/api/auth/me',
    method: 'get'
  })
}

/**
 * 修改当前用户密码
 */
export const changePassword = (data: {
  oldPassword: string
  newPassword: string
}): Promise<UserResponse<void>> => {
  return request({
    url: '/api/auth/change-password',
    method: 'post',
    data
  })
}

/**
 * 忘记密码
 */
export const forgotPassword = (email: string): Promise<UserResponse<void>> => {
  return request({
    url: '/api/auth/forgot-password',
    method: 'post',
    data: { email }
  })
}

/**
 * 重置密码（通过邮件链接）
 */
export const resetPassword = (data: {
  token: string
  newPassword: string
}): Promise<UserResponse<void>> => {
  return request({
    url: '/api/auth/reset-password',
    method: 'post',
    data
  })
}

/**
 * 验证邮箱
 */
export const verifyEmail = (token: string): Promise<UserResponse<void>> => {
  return request({
    url: '/api/auth/verify-email',
    method: 'post',
    data: { token }
  })
}

/**
 * 发送邮箱验证码
 */
export const sendEmailVerification = (): Promise<UserResponse<void>> => {
  return request({
    url: '/api/auth/send-email-verification',
    method: 'post'
  })
}

// 用户资料API

/**
 * 获取用户资料
 */
export const getUserProfile = (id?: string): Promise<UserResponse<UserProfile>> => {
  const url = id ? `/api/users/${id}/profile` : '/api/auth/profile'
  return request({
    url,
    method: 'get'
  })
}

/**
 * 更新用户资料
 */
export const updateUserProfile = (data: Partial<UserProfile>): Promise<UserResponse<UserProfile>> => {
  return request({
    url: '/api/auth/profile',
    method: 'put',
    data
  })
}

/**
 * 上传用户头像
 */
export const uploadAvatar = (file: File): Promise<UserResponse<{ avatar: string }>> => {
  const formData = new FormData()
  formData.append('avatar', file)
  return request({
    url: '/api/auth/upload-avatar',
    method: 'post',
    data: formData,
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}

/**
 * 获取用户偏好设置
 */
export const getUserPreferences = (): Promise<UserResponse<UserPreferences>> => {
  return request({
    url: '/api/auth/preferences',
    method: 'get'
  })
}

/**
 * 更新用户偏好设置
 */
export const updateUserPreferences = (data: Partial<UserPreferences>): Promise<UserResponse<UserPreferences>> => {
  return request({
    url: '/api/auth/preferences',
    method: 'put',
    data
  })
}

// 用户会话API

/**
 * 获取用户会话列表
 */
export const getUserSessions = (id?: string): Promise<UserResponse<UserSession[]>> => {
  const url = id ? `/api/users/${id}/sessions` : '/api/auth/sessions'
  return request({
    url,
    method: 'get'
  })
}

/**
 * 终止用户会话
 */
export const terminateSession = (sessionId: string): Promise<UserResponse<void>> => {
  return request({
    url: `/api/auth/sessions/${sessionId}/terminate`,
    method: 'post'
  })
}

/**
 * 终止所有其他会话
 */
export const terminateOtherSessions = (): Promise<UserResponse<void>> => {
  return request({
    url: '/api/auth/sessions/terminate-others',
    method: 'post'
  })
}

/**
 * 终止用户所有会话
 */
export const terminateUserSessions = (id: string): Promise<UserResponse<void>> => {
  return request({
    url: `/api/users/${id}/sessions/terminate-all`,
    method: 'post'
  })
}

// 用户日志API

/**
 * 获取用户登录日志
 */
export const getUserLoginLogs = (params: {
  userId?: string
  page?: number
  size?: number
  startDate?: string
  endDate?: string
  ip?: string
  status?: string
}): Promise<PaginatedUserResponse<UserLoginLog>> => {
  return request({
    url: '/api/users/login-logs',
    method: 'get',
    params
  })
}

/**
 * 获取用户操作日志
 */
export const getUserOperationLogs = (params: {
  userId?: string
  page?: number
  size?: number
  startDate?: string
  endDate?: string
  operation?: string
  resource?: string
}): Promise<PaginatedUserResponse<UserOperationLog>> => {
  return request({
    url: '/api/users/operation-logs',
    method: 'get',
    params
  })
}

// 角色管理API

/**
 * 获取角色列表
 */
export const getRoles = (params?: RoleQuery): Promise<PaginatedUserResponse<Role>> => {
  return request({
    url: '/api/roles',
    method: 'get',
    params
  })
}

/**
 * 获取角色详情
 */
export const getRoleById = (id: string): Promise<UserResponse<Role>> => {
  return request({
    url: `/api/roles/${id}`,
    method: 'get'
  })
}

/**
 * 创建角色
 */
export const createRole = (data: RoleCreateData): Promise<UserResponse<Role>> => {
  return request({
    url: '/api/roles',
    method: 'post',
    data
  })
}

/**
 * 更新角色
 */
export const updateRole = (id: string, data: RoleUpdateData): Promise<UserResponse<Role>> => {
  return request({
    url: `/api/roles/${id}`,
    method: 'put',
    data
  })
}

/**
 * 删除角色
 */
export const deleteRole = (id: string): Promise<UserResponse<void>> => {
  return request({
    url: `/api/roles/${id}`,
    method: 'delete'
  })
}

/**
 * 启用/禁用角色
 */
export const toggleRole = (id: string, enabled: boolean): Promise<UserResponse<void>> => {
  return request({
    url: `/api/roles/${id}/toggle`,
    method: 'patch',
    data: { enabled }
  })
}

/**
 * 分配角色给用户
 */
export const assignRoleToUser = (userId: string, roleId: string): Promise<UserResponse<void>> => {
  return request({
    url: `/api/users/${userId}/roles`,
    method: 'post',
    data: { roleId }
  })
}

/**
 * 从用户移除角色
 */
export const removeRoleFromUser = (userId: string, roleId: string): Promise<UserResponse<void>> => {
  return request({
    url: `/api/users/${userId}/roles/${roleId}`,
    method: 'delete'
  })
}

/**
 * 批量分配角色
 */
export const batchAssignRoles = (userIds: string[], roleIds: string[]): Promise<UserResponse<void>> => {
  return request({
    url: '/api/users/batch-assign-roles',
    method: 'post',
    data: { userIds, roleIds }
  })
}

// 权限管理API

/**
 * 获取权限列表
 */
export const getPermissions = (params?: PermissionQuery): Promise<PaginatedUserResponse<Permission>> => {
  return request({
    url: '/api/permissions',
    method: 'get',
    params
  })
}

/**
 * 获取权限详情
 */
export const getPermissionById = (id: string): Promise<UserResponse<Permission>> => {
  return request({
    url: `/api/permissions/${id}`,
    method: 'get'
  })
}

/**
 * 创建权限
 */
export const createPermission = (data: {
  name: string
  code: string
  description?: string
  category?: string
  resource?: string
  action?: string
}): Promise<UserResponse<Permission>> => {
  return request({
    url: '/api/permissions',
    method: 'post',
    data
  })
}

/**
 * 更新权限
 */
export const updatePermission = (id: string, data: {
  name?: string
  description?: string
  category?: string
}): Promise<UserResponse<Permission>> => {
  return request({
    url: `/api/permissions/${id}`,
    method: 'put',
    data
  })
}

/**
 * 删除权限
 */
export const deletePermission = (id: string): Promise<UserResponse<void>> => {
  return request({
    url: `/api/permissions/${id}`,
    method: 'delete'
  })
}

/**
 * 分配权限给角色
 */
export const assignPermissionToRole = (roleId: string, permissionId: string): Promise<UserResponse<void>> => {
  return request({
    url: `/api/roles/${roleId}/permissions`,
    method: 'post',
    data: { permissionId }
  })
}

/**
 * 从角色移除权限
 */
export const removePermissionFromRole = (roleId: string, permissionId: string): Promise<UserResponse<void>> => {
  return request({
    url: `/api/roles/${roleId}/permissions/${permissionId}`,
    method: 'delete'
  })
}

/**
 * 批量分配权限给角色
 */
export const batchAssignPermissions = (roleId: string, permissionIds: string[]): Promise<UserResponse<void>> => {
  return request({
    url: `/api/roles/${roleId}/permissions/batch-assign`,
    method: 'post',
    data: { permissionIds }
  })
}

/**
 * 检查用户权限
 */
export const checkUserPermission = (permission: string, resource?: string): Promise<UserResponse<{ hasPermission: boolean }>> => {
  return request({
    url: '/api/auth/check-permission',
    method: 'get',
    params: { permission, resource }
  })
}

/**
 * 获取用户权限列表
 */
export const getUserPermissions = (id?: string): Promise<UserResponse<Permission[]>> => {
  const url = id ? `/api/users/${id}/permissions` : '/api/auth/permissions'
  return request({
    url,
    method: 'get'
  })
}

// 用户组管理API

/**
 * 获取用户组列表
 */
export const getUserGroups = (params?: {
  page?: number
  size?: number
  keyword?: string
  parentId?: string
}): Promise<PaginatedUserResponse<UserGroup>> => {
  return request({
    url: '/api/user-groups',
    method: 'get',
    params
  })
}

/**
 * 获取用户组详情
 */
export const getUserGroupById = (id: string): Promise<UserResponse<UserGroup>> => {
  return request({
    url: `/api/user-groups/${id}`,
    method: 'get'
  })
}

/**
 * 创建用户组
 */
export const createUserGroup = (data: {
  name: string
  description?: string
  parentId?: string
  type?: string
}): Promise<UserResponse<UserGroup>> => {
  return request({
    url: '/api/user-groups',
    method: 'post',
    data
  })
}

/**
 * 更新用户组
 */
export const updateUserGroup = (id: string, data: {
  name?: string
  description?: string
  parentId?: string
}): Promise<UserResponse<UserGroup>> => {
  return request({
    url: `/api/user-groups/${id}`,
    method: 'put',
    data
  })
}

/**
 * 删除用户组
 */
export const deleteUserGroup = (id: string): Promise<UserResponse<void>> => {
  return request({
    url: `/api/user-groups/${id}`,
    method: 'delete'
  })
}

/**
 * 添加用户到组
 */
export const addUserToGroup = (groupId: string, userId: string): Promise<UserResponse<void>> => {
  return request({
    url: `/api/user-groups/${groupId}/users`,
    method: 'post',
    data: { userId }
  })
}

/**
 * 从组移除用户
 */
export const removeUserFromGroup = (groupId: string, userId: string): Promise<UserResponse<void>> => {
  return request({
    url: `/api/user-groups/${groupId}/users/${userId}`,
    method: 'delete'
  })
}

/**
 * 批量添加用户到组
 */
export const batchAddUsersToGroup = (groupId: string, userIds: string[]): Promise<UserResponse<void>> => {
  return request({
    url: `/api/user-groups/${groupId}/users/batch-add`,
    method: 'post',
    data: { userIds }
  })
}

/**
 * 获取组成员列表
 */
export const getGroupMembers = (groupId: string, params?: {
  page?: number
  size?: number
  keyword?: string
}): Promise<PaginatedUserResponse<User>> => {
  return request({
    url: `/api/user-groups/${groupId}/members`,
    method: 'get',
    params
  })
}

// 搜索API

/**
 * 搜索用户
 */
export const searchUsers = (params: {
  keyword: string
  page?: number
  size?: number
  filters?: Record<string, any>
}): Promise<PaginatedUserResponse<User>> => {
  return request({
    url: '/api/users/search',
    method: 'get',
    params
  })
}

/**
 * 搜索角色
 */
export const searchRoles = (params: {
  keyword: string
  page?: number
  size?: number
}): Promise<PaginatedUserResponse<Role>> => {
  return request({
    url: '/api/roles/search',
    method: 'get',
    params
  })
}

/**
 * 搜索权限
 */
export const searchPermissions = (params: {
  keyword: string
  category?: string
  page?: number
  size?: number
}): Promise<PaginatedUserResponse<Permission>> => {
  return request({
    url: '/api/permissions/search',
    method: 'get',
    params
  })
}

// 导入导出API

/**
 * 导出用户列表
 */
export const exportUsers = (params: {
  format: 'excel' | 'csv'
  filters?: Record<string, any>
}): Promise<Blob> => {
  return request({
    url: '/api/users/export',
    method: 'post',
    data: params,
    responseType: 'blob'
  })
}

/**
 * 导入用户
 */
export const importUsers = (file: File): Promise<UserResponse<{ success: number; failed: number; errors: any[] }>> => {
  const formData = new FormData()
  formData.append('file', file)
  return request({
    url: '/api/users/import',
    method: 'post',
    data: formData,
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}

/**
 * 下载用户导入模板
 */
export const downloadUserTemplate = (): Promise<Blob> => {
  return request({
    url: '/api/users/import-template',
    method: 'get',
    responseType: 'blob'
  })
}

// 统计API

/**
 * 获取用户统计信息
 */
export const getUserStatistics = (): Promise<UserResponse<{
  totalUsers: number
  activeUsers: number
  newUsersThisMonth: number
  onlineUsers: number
  usersByRole: Record<string, number>
  usersByStatus: Record<string, number>
  loginTrend: { date: string; count: number }[]
}>> => {
  return request({
    url: '/api/users/statistics',
    method: 'get'
  })
}

/**
 * 获取角色统计信息
 */
export const getRoleStatistics = (): Promise<UserResponse<{
  totalRoles: number
  activeRoles: number
  roleUsage: { roleId: string; roleName: string; userCount: number }[]
}>> => {
  return request({
    url: '/api/roles/statistics',
    method: 'get'
  })
}

/**
 * 获取权限统计信息
 */
export const getPermissionStatistics = (): Promise<UserResponse<{
  totalPermissions: number
  permissionsByCategory: Record<string, number>
  permissionUsage: { permissionId: string; permissionName: string; roleCount: number }[]
}>> => {
  return request({
    url: '/api/permissions/statistics',
    method: 'get'
  })
}