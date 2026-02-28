/**
 * 用户管理相关的API接口
 */

import { request } from "@/utils/request";
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
  PaginatedUserResponse,
} from "@/types/user";

// 用户基础API

/**
 * 获取用户列表
 */
export const getUsers = (
  params: UserQuery,
): Promise<PaginatedUserResponse<User>> => {
  return request({
    url: "/api/users",
    method: "get",
    params,
    permission: "system:user:view",
  });
};

/**
 * 获取用户详情
 */
export const getUserById = (id: string): Promise<UserResponse<User>> => {
  return request({
    url: `/api/users/${id}`,
    method: "get",
    permission: "system:user:view",
  });
};

/**
 * 获取用户详细信息（包含扩展信息）
 */
export const getUserDetail = (id: string): Promise<UserResponse<User>> => {
  return request({
    url: `/api/users/${id}/detail`,
    method: "get",
    permission: "system:user:view",
  });
};

/**
 * 获取用户统计信息
 */
export const getUserStats = (
  id: string,
): Promise<
  UserResponse<{
    loginCount: number;
    lastLoginTime: string;
    sessionCount: number;
    operationCount: number;
    resourceCount: number;
    projectCount: number;
  }>
> => {
  return request({
    url: `/api/users/${id}/stats`,
    method: "get",
    permission: "system:user:stats:view",
  });
};

/**
 * 获取用户活动记录
 */
export const getUserActivities = (
  id: string,
  params?: {
    page?: number;
    page_size?: number;
    type?: string;
    startDate?: string;
    endDate?: string;
  },
): Promise<
  PaginatedUserResponse<{
    id: string;
    type: string;
    action: string;
    resource: string;
    description: string;
    ip: string;
    userAgent: string;
    createdAt: string;
  }>
> => {
  return request({
    url: `/api/users/${id}/activities`,
    method: "get",
    params,
    permission: "system:user:activities:view",
  });
};

/**
 * 创建用户
 */
export const createUser = (
  data: UserCreateData,
): Promise<UserResponse<User>> => {
  return request({
    url: "/api/users",
    method: "post",
    data,
    permission: "system:user:create",
  });
};

/**
 * 更新用户
 */
export const updateUser = (
  id: string,
  data: UserUpdateData,
): Promise<UserResponse<User>> => {
  return request({
    url: `/api/users/${id}`,
    method: "put",
    data,
    permission: "system:user:edit",
  });
};

/**
 * 删除用户
 */
export const deleteUser = (id: string): Promise<UserResponse<void>> => {
  return request({
    url: `/api/users/${id}`,
    method: "delete",
    permission: "system:user:delete",
  });
};

/**
 * 批量删除用户
 */
export const batchDeleteUsers = (
  ids: string[],
): Promise<UserResponse<void>> => {
  return request({
    url: "/api/users/batch-delete",
    method: "post",
    data: { ids },
    permission: "system:user:delete",
  });
};

/**
 * 启用/禁用用户
 */
export const toggleUser = (
  id: string,
  enabled: boolean,
): Promise<UserResponse<void>> => {
  return request({
    url: `/api/users/${id}/toggle`,
    method: "patch",
    data: { enabled },
    permission: "system:user:edit",
  });
};

/**
 * 更新用户状态
 */
export const updateUserStatus = (
  id: string,
  status: boolean,
): Promise<UserResponse<void>> => {
  return request({
    url: `/api/users/${id}/status`,
    method: "patch",
    data: { is_active: status },
    permission: "system:user:edit",
  });
};

/**
 * 重置用户密码
 */
export const resetUserPassword = (
  id: string,
  newPassword?: string,
): Promise<UserResponse<{ password?: string }>> => {
  return request({
    url: `/api/users/${id}/reset-password`,
    method: "post",
    data: { newPassword },
    permission: "system:user:password:reset",
  });
};

/**
 * 强制用户下次登录修改密码
 */
export const forcePasswordChange = (
  id: string,
): Promise<UserResponse<void>> => {
  return request({
    url: `/api/users/${id}/force-password-change`,
    method: "patch",
    permission: "system:user:password:force_change",
  });
};

// 用户认证API

/**
 * 用户登录
 */
export const login = (data: {
  username: string;
  password: string;
  captcha?: string;
  rememberMe?: boolean;
}): Promise<
  UserResponse<{ token: string; refreshToken: string; user: User }>
> => {
  return request({
    url: "/api/auth/login",
    method: "post",
    data,
  });
};

/**
 * 用户登出
 */
export const logout = (): Promise<UserResponse<void>> => {
  return request({
    url: "/api/auth/logout",
    method: "post",
  });
};

/**
 * 刷新令牌
 */
export const refreshToken = (
  refreshToken: string,
): Promise<UserResponse<{ token: string; refreshToken: string }>> => {
  return request({
    url: "/api/auth/refresh",
    method: "post",
    data: { refreshToken },
  });
};

/**
 * 获取当前用户信息
 */
export const getCurrentUser = (): Promise<UserResponse<User>> => {
  return request({
    url: "/api/auth/me",
    method: "get",
    permission: "auth:me:view",
  });
};

/**
 * 修改当前用户密码
 */
export const changePassword = (data: {
  oldPassword: string;
  newPassword: string;
}): Promise<UserResponse<void>> => {
  return request({
    url: "/api/auth/change-password",
    method: "post",
    data,
    permission: "auth:password:change",
  });
};

/**
 * 忘记密码
 */
export const forgotPassword = (email: string): Promise<UserResponse<void>> => {
  return request({
    url: "/api/auth/forgot-password",
    method: "post",
    data: { email },
    permission: "auth:password:forgot",
  });
};

/**
 * 重置密码（通过邮件链接）
 */
export const resetPassword = (data: {
  token: string;
  newPassword: string;
}): Promise<UserResponse<void>> => {
  return request({
    url: "/api/auth/reset-password",
    method: "post",
    data,
    permission: "auth:password:reset",
  });
};

/**
 * 验证邮箱
 */
export const verifyEmail = (token: string): Promise<UserResponse<void>> => {
  return request({
    url: "/api/auth/verify-email",
    method: "post",
    data: { token },
    permission: "auth:email:verify",
  });
};

/**
 * 发送邮箱验证码
 */
export const sendEmailVerification = (): Promise<UserResponse<void>> => {
  return request({
    url: "/api/auth/send-email-verification",
    method: "post",
    permission: "auth:email:send_verification",
  });
};

// 用户资料API

/**
 * 获取用户资料
 */
export const getUserProfile = (
  id?: string,
): Promise<UserResponse<UserProfile>> => {
  const url = id ? `/api/users/${id}/profile` : "/api/auth/profile";
  return request({
    url,
    method: "get",
    permission: id ? "system:user:profile:view" : "auth:profile:view",
  });
};

/**
 * 更新用户资料
 */
export const updateUserProfile = (
  data: Partial<UserProfile>,
): Promise<UserResponse<UserProfile>> => {
  return request({
    url: "/api/auth/profile",
    method: "put",
    data,
    permission: "auth:profile:edit",
  });
};

/**
 * 上传用户头像
 */
export const uploadAvatar = (
  file: File,
): Promise<UserResponse<{ avatar: string }>> => {
  const formData = new FormData();
  formData.append("avatar", file);
  return request({
    url: "/api/auth/upload-avatar",
    method: "post",
    data: formData,
    headers: {
      "Content-Type": "multipart/form-data",
    },
    permission: "auth:profile:avatar",
  });
};

/**
 * 获取用户偏好设置
 */
export const getUserPreferences = (): Promise<
  UserResponse<UserPreferences>
> => {
  return request({
    url: "/api/auth/preferences",
    method: "get",
    permission: "auth:preferences:view",
  });
};

/**
 * 更新用户偏好设置
 */
export const updateUserPreferences = (
  data: Partial<UserPreferences>,
): Promise<UserResponse<UserPreferences>> => {
  return request({
    url: "/api/auth/preferences",
    method: "put",
    data,
    permission: "auth:preferences:edit",
  });
};

// 用户会话API

/**
 * 获取用户会话列表
 */
export const getUserSessions = (
  id?: string,
): Promise<UserResponse<UserSession[]>> => {
  const url = id ? `/api/users/${id}/sessions` : "/api/auth/sessions";
  return request({
    url,
    method: "get",
    permission: "auth:sessions:view",
  });
};

/**
 * 终止用户会话
 */
export const terminateSession = (
  sessionId: string,
): Promise<UserResponse<void>> => {
  return request({
    url: `/api/auth/sessions/${sessionId}/terminate`,
    method: "post",
    permission: "auth:sessions:terminate",
  });
};

/**
 * 终止所有其他会话
 */
export const terminateOtherSessions = (): Promise<UserResponse<void>> => {
  return request({
    url: "/api/auth/sessions/terminate-others",
    method: "post",
    permission: "auth:sessions:terminate_others",
  });
};

/**
 * 终止用户所有会话
 */
export const terminateUserSessions = (
  id: string,
): Promise<UserResponse<void>> => {
  return request({
    url: `/api/users/${id}/sessions/terminate-all`,
    method: "post",
    permission: "system:user:sessions:terminate_all",
  });
};

/**
 * 终止用户会话（别名）
 */
export const terminateUserSession = (
  sessionId: string,
): Promise<UserResponse<void>> => {
  return terminateSession(sessionId);
};

// 用户日志API

/**
 * 获取用户登录日志
 */
export const getUserLoginLogs = (params: {
  userId?: string;
  page?: number;
  size?: number;
  startDate?: string;
  endDate?: string;
  ip?: string;
  status?: string;
}): Promise<PaginatedUserResponse<UserLoginLog>> => {
  return request({
    url: "/api/users/login-logs",
    method: "get",
    params,
    permission: "system:user:login_logs:view",
  });
};

/**
 * 获取用户操作日志
 */
export const getUserOperationLogs = (params: {
  userId?: string;
  page?: number;
  size?: number;
  startDate?: string;
  endDate?: string;
  operation?: string;
  resource?: string;
}): Promise<PaginatedUserResponse<UserOperationLog>> => {
  return request({
    url: "/api/users/operation-logs",
    method: "get",
    params,
    permission: "system:user:operation_logs:view",
  });
};

// 角色管理API

/**
 * 获取角色列表
 */
export const getRoles = (
  params?: RoleQuery,
): Promise<PaginatedUserResponse<Role>> => {
  return request({
    url: "/api/roles",
    method: "get",
    params,
    permission: "system:role:view",
  });
};

/**
 * 获取角色详情
 */
export const getRoleById = (id: string): Promise<UserResponse<Role>> => {
  return request({
    url: `/api/roles/${id}`,
    method: "get",
    permission: "system:role:view",
  });
};

/**
 * 创建角色
 */
export const createRole = (
  data: RoleCreateData,
): Promise<UserResponse<Role>> => {
  return request({
    url: "/api/roles",
    method: "post",
    data,
    permission: "system:role:create",
  });
};

/**
 * 更新角色
 */
export const updateRole = (
  id: string,
  data: RoleUpdateData,
): Promise<UserResponse<Role>> => {
  return request({
    url: `/api/roles/${id}`,
    method: "put",
    data,
    permission: "system:role:edit",
  });
};

/**
 * 删除角色
 */
export const deleteRole = (id: string): Promise<UserResponse<void>> => {
  return request({
    url: `/api/roles/${id}`,
    method: "delete",
    permission: "system:role:delete",
  });
};

/**
 * 启用/禁用角色
 */
export const toggleRole = (
  id: string,
  enabled: boolean,
): Promise<UserResponse<void>> => {
  return request({
    url: `/api/roles/${id}/toggle`,
    method: "patch",
    data: { enabled },
    permission: "system:role:edit",
  });
};

/**
 * 分配角色给用户
 */
export const assignRoleToUser = (
  userId: string,
  roleId: string,
): Promise<UserResponse<void>> => {
  return request({
    url: `/api/users/${userId}/roles`,
    method: "post",
    data: { roleId },
    permission: "system:role:assign",
  });
};

/**
 * 从用户移除角色
 */
export const removeRoleFromUser = (
  userId: string,
  roleId: string,
): Promise<UserResponse<void>> => {
  return request({
    url: `/api/users/${userId}/roles/${roleId}`,
    method: "delete",
    permission: "system:role:remove",
  });
};

/**
 * 批量分配角色
 */
export const batchAssignRoles = (
  userIds: string[],
  roleIds: string[],
): Promise<UserResponse<void>> => {
  return request({
    url: "/api/users/batch-assign-roles",
    method: "post",
    data: { userIds, roleIds },
    permission: "system:role:assign",
  });
};

// 权限管理API

/**
 * 获取权限列表
 */
export const getPermissions = (
  params?: PermissionQuery,
): Promise<PaginatedUserResponse<Permission>> => {
  return request({
    url: "/api/permissions",
    method: "get",
    params,
    permission: "system:permission:view",
  });
};

/**
 * 获取权限详情
 */
export const getPermissionById = (
  id: string,
): Promise<UserResponse<Permission>> => {
  return request({
    url: `/api/permissions/${id}`,
    method: "get",
    permission: "system:permission:view",
  });
};

/**
 * 创建权限
 */
export const createPermission = (data: {
  name: string;
  code: string;
  description?: string;
  category?: string;
  resource?: string;
  action?: string;
}): Promise<UserResponse<Permission>> => {
  return request({
    url: "/api/permissions",
    method: "post",
    data,
    permission: "system:permission:create",
  });
};

/**
 * 更新权限
 */
export const updatePermission = (
  id: string,
  data: {
    name?: string;
    description?: string;
    category?: string;
  },
): Promise<UserResponse<Permission>> => {
  return request({
    url: `/api/permissions/${id}`,
    method: "put",
    data,
    permission: "system:permission:edit",
  });
};

/**
 * 删除权限
 */
export const deletePermission = (id: string): Promise<UserResponse<void>> => {
  return request({
    url: `/api/permissions/${id}`,
    method: "delete",
    permission: "system:permission:delete",
  });
};

/**
 * 分配权限给角色
 */
export const assignPermissionToRole = (
  roleId: string,
  permissionId: string,
): Promise<UserResponse<void>> => {
  return request({
    url: `/api/roles/${roleId}/permissions`,
    method: "post",
    data: { permissionId },
    permission: "system:permission:assign",
  });
};

/**
 * 从角色移除权限
 */
export const removePermissionFromRole = (
  roleId: string,
  permissionId: string,
): Promise<UserResponse<void>> => {
  return request({
    url: `/api/roles/${roleId}/permissions/${permissionId}`,
    method: "delete",
    permission: "system:permission:remove",
  });
};

/**
 * 批量分配权限给角色
 */
export const batchAssignPermissions = (
  roleId: string,
  permissionIds: string[],
): Promise<UserResponse<void>> => {
  return request({
    url: `/api/roles/${roleId}/permissions/batch-assign`,
    method: "post",
    data: { permissionIds },
    permission: "system:permission:assign",
  });
};

/**
 * 检查用户权限
 */
export const checkUserPermission = (
  permission: string,
  resource?: string,
): Promise<UserResponse<{ hasPermission: boolean }>> => {
  return request({
    url: "/api/auth/check-permission",
    method: "get",
    params: { permission, resource },
    permission: "system:permission:check",
  });
};

/**
 * 获取用户权限列表
 */
export const getUserPermissions = (
  id?: string,
): Promise<UserResponse<Permission[]>> => {
  const url = id ? `/api/users/${id}/permissions` : "/api/auth/permissions";
  return request({
    url,
    method: "get",
    permission: id ? "system:user:permissions:view" : "auth:permissions:view",
  });
};

// 用户组管理API

/**
 * 获取用户组列表
 */
export const getUserGroups = (params?: {
  page?: number;
  size?: number;
  keyword?: string;
  parentId?: string;
}): Promise<PaginatedUserResponse<UserGroup>> => {
  return request({
    url: "/api/user-groups",
    method: "get",
    params,
    permission: "system:user_group:view",
  });
};

/**
 * 获取用户组详情
 */
export const getUserGroupById = (
  id: string,
): Promise<UserResponse<UserGroup>> => {
  return request({
    url: `/api/user-groups/${id}`,
    method: "get",
    permission: "system:user_group:view",
  });
};

/**
 * 创建用户组
 */
export const createUserGroup = (data: {
  name: string;
  description?: string;
  parentId?: string;
  type?: string;
}): Promise<UserResponse<UserGroup>> => {
  return request({
    url: "/api/user-groups",
    method: "post",
    data,
    permission: "system:user_group:create",
  });
};

/**
 * 更新用户组
 */
export const updateUserGroup = (
  id: string,
  data: {
    name?: string;
    description?: string;
    parentId?: string;
  },
): Promise<UserResponse<UserGroup>> => {
  return request({
    url: `/api/user-groups/${id}`,
    method: "put",
    data,
    permission: "system:user_group:edit",
  });
};

/**
 * 删除用户组
 */
export const deleteUserGroup = (id: string): Promise<UserResponse<void>> => {
  return request({
    url: `/api/user-groups/${id}`,
    method: "delete",
    permission: "system:user_group:delete",
  });
};

/**
 * 添加用户到组
 */
export const addUserToGroup = (
  groupId: string,
  userId: string,
): Promise<UserResponse<void>> => {
  return request({
    url: `/api/user-groups/${groupId}/users`,
    method: "post",
    data: { userId },
    permission: "system:user_group:assign",
  });
};

/**
 * 从组移除用户
 */
export const removeUserFromGroup = (
  groupId: string,
  userId: string,
): Promise<UserResponse<void>> => {
  return request({
    url: `/api/user-groups/${groupId}/users/${userId}`,
    method: "delete",
    permission: "system:user_group:remove",
  });
};

/**
 * 批量添加用户到组
 */
export const batchAddUsersToGroup = (
  groupId: string,
  userIds: string[],
): Promise<UserResponse<void>> => {
  return request({
    url: `/api/user-groups/${groupId}/users/batch-add`,
    method: "post",
    data: { userIds },
    permission: "system:user_group:assign",
  });
};

/**
 * 获取组成员列表
 */
export const getGroupMembers = (
  groupId: string,
  params?: {
    page?: number;
    size?: number;
    keyword?: string;
  },
): Promise<PaginatedUserResponse<User>> => {
  return request({
    url: `/api/user-groups/${groupId}/members`,
    method: "get",
    params,
    permission: "system:user_group:view",
  });
};

// 搜索API

/**
 * 搜索用户
 */
export const searchUsers = (params: {
  keyword: string;
  page?: number;
  size?: number;
  filters?: Record<string, any>;
}): Promise<PaginatedUserResponse<User>> => {
  return request({
    url: "/api/users/search",
    method: "get",
    params,
    permission: "system:user:search",
  });
};

/**
 * 搜索角色
 */
export const searchRoles = (params: {
  keyword: string;
  page?: number;
  size?: number;
}): Promise<PaginatedUserResponse<Role>> => {
  return request({
    url: "/api/roles/search",
    method: "get",
    params,
    permission: "system:role:search",
  });
};

/**
 * 搜索权限
 */
export const searchPermissions = (params: {
  keyword: string;
  category?: string;
  page?: number;
  size?: number;
}): Promise<PaginatedUserResponse<Permission>> => {
  return request({
    url: "/api/permissions/search",
    method: "get",
    params,
    permission: "system:permission:search",
  });
};

// 导入导出API

/**
 * 导出用户列表
 */
export const exportUsers = (params: any): Promise<ApiResponse<Blob>> => {
  return request({
    url: "/api/users/export",
    method: "post",
    data: params,
    responseType: "blob",
    permission: "system:user:export",
  });
};

/**
 * 验证用户导入文件
 */
export const validateUserImport = (
  formData: FormData,
): Promise<
  UserResponse<{
    total: number;
    valid: number;
    errors: number;
    warnings: number;
    error_details?: Array<{
      row: number;
      field: string;
      value: string;
      message: string;
      type: "error" | "warning";
    }>;
    preview_data?: Array<{
      username: string;
      email: string;
      name: string;
      department?: string;
      role?: string;
      status: "valid" | "error" | "warning";
      errors?: string[];
    }>;
  }>
> => {
  return request({
    url: "/api/users/import/validate",
    method: "post",
    data: formData,
    headers: {
      "Content-Type": "multipart/form-data",
    },
    permission: "system:user:import",
  });
};

/**
 * 导入用户
 */
export const importUsers = (
  file: File,
): Promise<
  UserResponse<{ success: number; failed: number; errors: any[] }>
> => {
  const formData = new FormData();
  formData.append("file", file);
  return request({
    url: "/api/users/import",
    method: "post",
    data: formData,
    headers: {
      "Content-Type": "multipart/form-data",
    },
    permission: "system:user:import",
  });
};

/**
 * 下载用户导入模板
 */
export const downloadUserTemplate = (): Promise<ApiResponse<Blob>> => {
  return request({
    url: "/api/users/import-template",
    method: "get",
    responseType: "blob",
    permission: "system:user:import_template",
  });
};

// 统计API

/**
 * 获取用户统计信息
 */
export const getUserStatistics = (): Promise<
  UserResponse<{
    totalUsers: number;
    activeUsers: number;
    newUsersThisMonth: number;
    onlineUsers: number;
    usersByRole: Record<string, number>;
    usersByStatus: Record<string, number>;
    loginTrend: { date: string; count: number }[];
  }>
> => {
  return request({
    url: "/api/users/statistics",
    method: "get",
    permission: "system:user:statistics:view",
  });
};

/**
 * 获取角色统计信息
 */
export const getRoleStatistics = (): Promise<
  UserResponse<{
    totalRoles: number;
    activeRoles: number;
    roleUsage: { roleId: string; roleName: string; userCount: number }[];
  }>
> => {
  return request({
    url: "/api/roles/statistics",
    method: "get",
    permission: "system:role:statistics:view",
  });
};

/**
 * 获取权限统计信息
 */
export const getPermissionStatistics = (): Promise<
  UserResponse<{
    totalPermissions: number;
    permissionsByCategory: Record<string, number>;
    permissionUsage: {
      permissionId: string;
      permissionName: string;
      roleCount: number;
    }[];
  }>
> => {
  return request({
    url: "/api/permissions/statistics",
    method: "get",
    permission: "system:permission:statistics:view",
  });
};

/**
 * 获取权限树（按模块分组）
 */
export const getPermissionTree = (): Promise<UserResponse<any>> => {
  return request({
    url: "/api/permissions/tree",
    method: "get",
    permission: "system:permission:view",
  });
};

/**
 * 批量创建权限
 * @param permissions 权限创建数据列表
 */
export const batchCreatePermissions = (
  permissions: Array<{
    name: string;
    code: string;
    description?: string;
    module: string;
    resource?: string;
    action: string;
    status?: boolean;
    sort_order?: number;
  }>,
): Promise<UserResponse<any>> => {
  return request({
    url: "/api/permissions/batch",
    method: "post",
    data: permissions,
    permission: "system:permission:create",
  });
};
