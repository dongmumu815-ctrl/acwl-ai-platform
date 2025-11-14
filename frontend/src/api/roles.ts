import { request } from '@/utils/request'
import type { ApiResponse } from '@/types/common'

// 角色相关类型定义
export interface Role {
  id: number
  name: string
  code: string
  description?: string
  status: boolean
  is_system: boolean
  created_at: string
  updated_at: string
  created_by?: number
  updated_by?: number
}

export interface RoleCreate {
  name: string
  code: string
  description?: string
  status?: boolean
}

export interface RoleUpdate {
  name?: string
  code?: string
  description?: string
  status?: boolean
}

export interface UserRole {
  id: number
  user_id: number
  role_id: number
  created_at: string
  created_by?: number
}

export interface UserRoleCreate {
  user_id: number
  role_id: number
}

export interface RolePermission {
  id: number
  role_id: number
  permission_id: number
  created_at: string
  created_by?: number
}

export interface RolePermissionBatchCreate {
  role_id: number
  permission_ids: number[]
}

export interface RoleWithPermissions extends Role {
  permissions: Permission[]
}

export interface UserWithRoles {
  id: number
  username: string
  email: string
  roles: Role[]
}

export interface Permission {
  id: number
  name: string
  code: string
  description?: string
  module: string
  resource: string | null
  action: string
  status: boolean
  sort_order: number
  is_system: boolean
  created_at: string
  updated_at: string
}

// 角色分页数据结构（与后端 RoleListResponse 对齐）
export interface RoleListResponse {
  items: Role[]
  total: number
  page: number
  size: number
  pages: number
}

// 角色管理API接口
export const roleApi = {
  /**
   * 获取角色列表
   */
  getRoles(params?: {
    page?: number
    size?: number
    search?: string
    status?: boolean
    is_system?: boolean
  }) {
    return request.get<ApiResponse<RoleListResponse>>('/roles/', { params })
  },

  /**
   * 获取角色详情
   */
  getRole(roleId: number) {
    return request.get<ApiResponse<Role>>(`/roles/${roleId}`)
  },

  /**
   * 创建角色
   */
  createRole(data: RoleCreate) {
    return request.post<ApiResponse<Role>>('/roles/', data)
  },

  /**
   * 更新角色
   */
  updateRole(roleId: number, data: RoleUpdate) {
    return request.put<ApiResponse<Role>>(`/roles/${roleId}`, data)
  },

  /**
   * 删除角色
   */
  deleteRole(roleId: number) {
    return request.delete<ApiResponse<any>>(`/roles/${roleId}`)
  },

  /**
   * 获取角色权限
   */
  getRolePermissions(roleId: number) {
    return request.get<ApiResponse<RoleWithPermissions>>(`/roles/${roleId}/permissions`)
  },

  /**
   * 为角色分配权限
   */
  assignPermissions(roleId: number, permissionIds: number[]) {
    // 后端要求 Body 同时包含 role_id 与 permission_ids
    return request.post<ApiResponse<any>>(`/roles/${roleId}/permissions`, {
      role_id: roleId,
      permission_ids: permissionIds
    })
  },

  /**
   * 移除角色权限
   */
  removePermission(roleId: number, permissionId: number) {
    return request.delete<ApiResponse<any>>(`/roles/${roleId}/permissions/${permissionId}`)
  },

  /**
   * 批量移除角色权限
   */
  removePermissions(roleId: number, permissionIds: number[]) {
    return request.delete<ApiResponse<any>>(`/roles/${roleId}/permissions/batch`, {
      data: { permission_ids: permissionIds }
    })
  },

  /**
   * 获取角色用户列表
   */
  getRoleUsers(roleId: number, params?: {
    page?: number
    size?: number
  }) {
    return request.get<ApiResponse<UserWithRoles[]>>(`/roles/${roleId}/users`, { params })
  },

  /**
   * 为用户分配角色
   */
  assignRole(data: UserRoleCreate) {
    return request.post<ApiResponse<UserRole>>('/roles/assign-user', data)
  },

  /**
   * 移除用户角色
   */
  removeRole(userId: number, roleId: number) {
    return request.delete<ApiResponse<any>>(`/roles/remove-user/${userId}/${roleId}`)
  },

  /**
   * 获取用户角色列表
   */
  getUserRoles(userId: number) {
    return request.get<ApiResponse<Role[]>>(`/roles/users/${userId}/roles`)
  },

  /**
   * 批量分配角色
   */
  batchAssignRoles(userIds: number[], roleIds: number[]) {
    return request.post('/roles/batch-assign', {
      user_ids: userIds,
      role_ids: roleIds
    })
  },

  /**
   * 批量移除角色
   */
  batchRemoveRoles(userIds: number[], roleIds: number[]) {
    return request.post('/roles/batch-remove', {
      user_ids: userIds,
      role_ids: roleIds
    })
  }
}

// 权限管理API接口
export const permissionApi = {
  /**
   * 获取权限列表
   *
   * 说明：后端参数为 `skip` 与 `limit`，若传入 `page/size`，后端会忽略。
   * 为兼容现有用法，保留 `page/size` 定义，但建议在批量操作或全量拉取时使用 `skip/limit`。
   */
  getPermissions(params?: {
    page?: number
    size?: number
    skip?: number
    limit?: number
    search?: string
    module?: string
    resource?: string
    action?: string
    status?: boolean
  }) {
    return request.get<ApiResponse<{ items: Permission[]; total: number; page: number; size: number; pages: number }>>('/permissions/', { params })
  },

  /**
   * 获取权限详情
   */
  getPermission(permissionId: number) {
    return request.get<ApiResponse<Permission>>(`/permissions/${permissionId}`)
  },

  /**
   * 创建权限
   *
   * 说明：`resource` 可为 `null`，用于表示非特定资源的操作权限。
   */
  createPermission(data: {
    name: string
    code: string
    description?: string
    module: string
    resource: string | null
    action: string
    status?: boolean
    sort_order?: number
  }) {
    return request.post<ApiResponse<Permission>>('/permissions/', data)
  },

  /**
   * 更新权限
   */
  updatePermission(permissionId: number, data: {
    name?: string
    code?: string
    description?: string
    module?: string
    resource?: string
    action?: string
    status?: boolean
    sort_order?: number
  }) {
    return request.put<ApiResponse<Permission>>(`/permissions/${permissionId}`, data)
  },

  /**
   * 删除权限
   */
  deletePermission(permissionId: number) {
    return request.delete<ApiResponse<any>>(`/permissions/${permissionId}`)
  },

  /**
   * 获取权限树结构
   */
  getPermissionTree() {
    // 后端返回 ResponseModel[PermissionTreeListResponse]
    return request.get<ApiResponse<any>>('/permissions/tree')
  },

  /**
   * 根据模块获取权限
   */
  getPermissionsByModule(module: string) {
    // 后端路由为 /permissions/modules/{module}
    return request.get<ApiResponse<Permission[]>>(`/permissions/modules/${module}`)
  },

  /**
   * 批量创建权限
   * 请求体为权限数组（List[PermissionCreate]），不是对象包装
   */
  batchCreatePermissions(permissions: Array<{
    name: string
    code: string
    description?: string
    module: string
    resource: string | null
    action: string
    status?: boolean
    sort_order?: number
  }>) {
    return request.post<ApiResponse<any>>('/permissions/batch', permissions)
  },

  /**
   * 检查用户权限
   */
  checkUserPermission(userId: number, permissionCode: string) {
    return request.get<ApiResponse<{ has_permission: boolean }>>(`/permissions/check/${userId}/${permissionCode}`)
  },

  /**
   * 检查当前认证用户的权限
   * @param permissionCode 权限代码
   * @returns 是否拥有该权限（基于认证信息解析当前用户）
   */
  checkMyPermission(permissionCode: string) {
    return request.get<ApiResponse<boolean>>(`/permissions/check/${permissionCode}`)
  },

  /**
   * 获取用户所有权限
   */
  getUserPermissions(userId: number) {
    // 后端路由为 /permissions/user/{user_id}，返回 ResponseModel[UserPermissionResponse]
    return request.get<ApiResponse<any>>(`/permissions/user/${userId}`)
  },

  /**
   * 获取当前认证用户的所有权限
   * @returns 后端返回 ResponseModel[UserPermissionResponse]
   */
  getMyPermissions() {
    return request.get<ApiResponse<any>>('/permissions/me')
  }
}