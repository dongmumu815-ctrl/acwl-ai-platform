import { request } from '@/utils/request'

// 角色相关类型定义
export interface Role {
  id: number
  name: string
  code: string
  description?: string
  is_active: boolean
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
  is_active?: boolean
}

export interface RoleUpdate {
  name?: string
  code?: string
  description?: string
  is_active?: boolean
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
  resource: string
  action: string
  is_active: boolean
  created_at: string
  updated_at: string
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
    is_active?: boolean
    is_system?: boolean
  }) {
    return request.get<{
      items: Role[]
      total: number
      page: number
      size: number
      pages: number
    }>('/roles/', { params })
  },

  /**
   * 获取角色详情
   */
  getRole(roleId: number) {
    return request.get<Role>(`/roles/${roleId}`)
  },

  /**
   * 创建角色
   */
  createRole(data: RoleCreate) {
    return request.post<Role>('/roles/', data)
  },

  /**
   * 更新角色
   */
  updateRole(roleId: number, data: RoleUpdate) {
    return request.put<Role>(`/roles/${roleId}`, data)
  },

  /**
   * 删除角色
   */
  deleteRole(roleId: number) {
    return request.delete(`/roles/${roleId}`)
  },

  /**
   * 获取角色权限
   */
  getRolePermissions(roleId: number) {
    return request.get<Permission[]>(`/roles/${roleId}/permissions`)
  },

  /**
   * 为角色分配权限
   */
  assignPermissions(roleId: number, permissionIds: number[]) {
    return request.post(`/roles/${roleId}/permissions`, {
      permission_ids: permissionIds
    })
  },

  /**
   * 移除角色权限
   */
  removePermission(roleId: number, permissionId: number) {
    return request.delete(`/roles/${roleId}/permissions/${permissionId}`)
  },

  /**
   * 批量移除角色权限
   */
  removePermissions(roleId: number, permissionIds: number[]) {
    return request.delete(`/roles/${roleId}/permissions/batch`, {
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
    return request.get<{
      items: UserWithRoles[]
      total: number
      page: number
      size: number
      pages: number
    }>(`/roles/${roleId}/users`, { params })
  },

  /**
   * 为用户分配角色
   */
  assignRole(data: UserRoleCreate) {
    return request.post<UserRole>('/roles/assign', data)
  },

  /**
   * 移除用户角色
   */
  removeRole(userId: number, roleId: number) {
    return request.delete(`/roles/remove/${userId}/${roleId}`)
  },

  /**
   * 获取用户角色列表
   */
  getUserRoles(userId: number) {
    return request.get<Role[]>(`/users/${userId}/roles`)
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
   */
  getPermissions(params?: {
    page?: number
    size?: number
    search?: string
    module?: string
    resource?: string
    action?: string
    is_active?: boolean
  }) {
    return request.get<{
      items: Permission[]
      total: number
      page: number
      size: number
      pages: number
    }>('/permissions/', { params })
  },

  /**
   * 获取权限详情
   */
  getPermission(permissionId: number) {
    return request.get<Permission>(`/permissions/${permissionId}`)
  },

  /**
   * 创建权限
   */
  createPermission(data: {
    name: string
    code: string
    description?: string
    module: string
    resource: string
    action: string
    is_active?: boolean
  }) {
    return request.post<Permission>('/permissions/', data)
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
    is_active?: boolean
  }) {
    return request.put<Permission>(`/permissions/${permissionId}`, data)
  },

  /**
   * 删除权限
   */
  deletePermission(permissionId: number) {
    return request.delete(`/permissions/${permissionId}`)
  },

  /**
   * 获取权限树结构
   */
  getPermissionTree() {
    // 后端返回 ResponseModel[PermissionTreeListResponse]
    return request.get<any>('/permissions/tree')
  },

  /**
   * 根据模块获取权限
   */
  getPermissionsByModule(module: string) {
    // 后端路由为 /permissions/modules/{module}
    return request.get<any>(`/permissions/modules/${module}`)
  },

  /**
   * 批量创建权限
   */
  batchCreatePermissions(permissions: Array<{
    name: string
    code: string
    description?: string
    module: string
    resource: string
    action: string
    is_active?: boolean
  }>) {
    return request.post('/permissions/batch', { permissions })
  },

  /**
   * 检查用户权限
   */
  checkUserPermission(userId: number, permissionCode: string) {
    return request.get<{ has_permission: boolean }>(`/permissions/check/${userId}/${permissionCode}`)
  },

  /**
   * 获取用户所有权限
   */
  getUserPermissions(userId: number) {
    // 后端路由为 /permissions/user/{user_id}，返回 ResponseModel[UserPermissionResponse]
    return request.get<any>(`/permissions/user/${userId}`)
  }
}