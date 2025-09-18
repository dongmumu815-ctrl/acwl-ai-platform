/**
 * 资源包管理API接口
 */

import { request, post, get, put, del } from '@/utils/request'

// 资源包类型枚举
export enum PackageType {
  SQL = 'sql',
  ELASTICSEARCH = 'elasticsearch'
}

// 权限类型枚举
export enum PermissionType {
  READ = 'read',
  WRITE = 'write',
  ADMIN = 'admin'
}

// 条件操作符枚举
export enum ConditionOperator {
  EQ = '=',
  NE = '!=',
  GT = '>',
  GTE = '>=',
  LT = '<',
  LTE = '<=',
  LIKE = 'LIKE',
  IN = 'IN',
  NOT_IN = 'NOT IN',
  IS_NULL = 'IS NULL',
  IS_NOT_NULL = 'IS NOT NULL',
  BETWEEN = 'BETWEEN',
  NOT_BETWEEN = 'NOT BETWEEN'
}

// 逻辑操作符枚举
export enum LogicOperator {
  AND = 'AND',
  OR = 'OR'
}

// 排序方向枚举
export enum SortDirection {
  ASC = 'ASC',
  DESC = 'DESC'
}

// 基础配置接口
export interface BaseConfig {
  schema?: string
  table?: string
  fields: string[]
}

// 条件配置接口
export interface ConditionConfig {
  field: string
  operator: ConditionOperator
  value?: any
  logic: LogicOperator
  description?: string
}

// 动态条件配置接口
export interface DynamicConditionConfig extends ConditionConfig {
  default_value?: any
  required: boolean
  param_name?: string
  param_type?: string
  validation_rules?: Record<string, any>
}

// 排序配置接口
export interface OrderConfig {
  field: string
  direction: SortDirection
}

// 资源包标签接口
export interface ResourcePackageTag {
  id: number
  package_id: number
  tag_name: string
  tag_color: string
  created_at: string
}

// 资源包权限接口
export interface ResourcePackagePermission {
  id: number
  package_id: number
  user_id: number
  permission_type: PermissionType
  granted_by: number
  granted_at: string
  expires_at?: string
  is_active: boolean
}

// 资源包接口
export interface ResourcePackage {
  id: number
  name: string
  description?: string
  type: PackageType
  datasource_id: number
  resource_id?: number
  base_config: BaseConfig
  locked_conditions: ConditionConfig[]
  dynamic_conditions: DynamicConditionConfig[]
  order_config?: OrderConfig
  limit_config: number
  is_active: boolean
  created_by: number
  created_at: string
  updated_at: string
  tags: ResourcePackageTag[]
  permissions: ResourcePackagePermission[]
}

// 创建资源包请求接口
export interface ResourcePackageCreateRequest {
  name: string
  description?: string
  type: PackageType
  datasource_id: number
  resource_id?: number
  base_config: BaseConfig
  locked_conditions: ConditionConfig[]
  dynamic_conditions: DynamicConditionConfig[]
  order_config?: OrderConfig
  limit_config: number
  is_active: boolean
  tags?: string[]
}

// 更新资源包请求接口
export interface ResourcePackageUpdateRequest {
  name?: string
  description?: string
  base_config?: BaseConfig
  locked_conditions?: ConditionConfig[]
  dynamic_conditions?: DynamicConditionConfig[]
  order_config?: OrderConfig
  limit_config?: number
  is_active?: boolean
  tags?: string[]
}

// 搜索请求接口
export interface ResourcePackageSearchRequest {
  keyword?: string
  type?: PackageType
  datasource_id?: number
  created_by?: number
  tags?: string[]
  is_active?: boolean
  page: number
  size: number
  sort_by: string
  sort_order: string
}

// 列表响应接口
export interface ResourcePackageListResponse {
  items: ResourcePackage[]
  total: number
  page: number
  size: number
  pages: number
}

// 查询请求接口
export interface ResourcePackageQueryRequest {
  dynamic_params: Record<string, any>
  limit?: number
  offset: number
  format?: string
}

// 查询响应接口
export interface ResourcePackageQueryResponse {
  success: boolean
  columns: string[]
  data: any[][]
  total_count: number
  execution_time: number
  query_id?: string
  generated_query?: string
  error_message?: string
}

// 参数信息接口
export interface ResourcePackageParamInfo {
  param_name: string
  field: string
  operator: ConditionOperator
  param_type: string
  default_value?: any
  required: boolean
  description?: string
  validation_rules?: Record<string, any>
}

// 参数响应接口
export interface ResourcePackageParamsResponse {
  package_id: number
  package_name: string
  params: ResourcePackageParamInfo[]
  base_config: BaseConfig
  locked_conditions: ConditionConfig[]
}

/**
 * 资源包管理API
 */
export const resourcePackageApi = {
  /**
   * 创建资源包
   */
  create(data: ResourcePackageCreateRequest): Promise<ResourcePackage> {
    return post('/resource-packages', data)
  },

  /**
   * 获取资源包详情
   */
  get(id: number): Promise<ResourcePackage> {
    return get(`/resource-packages/${id}`)
  },

  /**
   * 更新资源包
   */
  update(id: number, data: ResourcePackageUpdateRequest): Promise<ResourcePackage> {
    return put(`/resource-packages/${id}`, data)
  },

  /**
   * 删除资源包
   */
  delete(id: number): Promise<{ message: string }> {
    return del(`/resource-packages/${id}`)
  },

  /**
   * 搜索资源包
   */
  search(params: ResourcePackageSearchRequest): Promise<ResourcePackageListResponse> {
    return post('/resource-packages/search', params)
  },

  /**
   * 获取资源包参数信息
   */
  getParams(id: number): Promise<ResourcePackageParamsResponse> {
    return get(`/resource-packages/${id}/params`)
  },

  /**
   * 查询资源包数据
   */
  query(id: number, params: ResourcePackageQueryRequest): Promise<ResourcePackageQueryResponse> {
    return post(`/resource-packages/${id}/query`, params)
  },

  /**
   * 获取查询历史
   */
  getHistory(id: number, page: number = 1, size: number = 20): Promise<any> {
    return get(`/resource-packages/${id}/history`, {
      page, size
    })
  }
}

export default resourcePackageApi