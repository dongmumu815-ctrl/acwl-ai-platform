/**
 * 资源包管理API接口
 */

import { request, post, get, put, del } from '@/utils/request'
import type { ApiResponse } from '@/types/datasource'

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

// 模板接口
export interface Template {
  id: number
  name: string
  description?: string
  type: PackageType
  datasource_id: number
  content: string
  default_params?: Record<string, any>
  is_active: boolean
  created_by: number
  created_at: string
  updated_at: string
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
  template_id: number
  template_type: PackageType
  dynamic_params?: Record<string, any>
  is_active: boolean
  is_lock: string
  created_by: number
  created_at: string
  updated_at: string
  // 新增：生成与下载时间/路径
  download_time?: string
  download_url?: string
  excel_time?: string
  tags: ResourcePackageTag[]
  permissions: ResourcePackagePermission[]
}

// 历史文件接口
export interface ResourcePackageFile {
  id: number
  filename: string
  object_path: string
  generated_at: string
}

// 创建资源包请求接口
export interface ResourcePackageCreateRequest {
  name: string
  description?: string
  type: PackageType
  datasource_id: number
  resource_id?: number
  template_id: number
  template_type: PackageType
  dynamic_params?: Record<string, any>
  is_active: boolean
  is_lock?: string
  tags?: string[]
}

// 更新资源包请求接口
export interface ResourcePackageUpdateRequest {
  name?: string
  description?: string
  template_id?: number
  template_type?: PackageType
  dynamic_params?: Record<string, any>
  is_active?: boolean
  is_lock?: string
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
  is_lock?: string
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



/**
 * 资源包管理API
 */
export const resourcePackageApi = {
  /**
   * 创建资源包
   */
  create(data: ResourcePackageCreateRequest): Promise<ApiResponse<ResourcePackage>> {
    return post('/resource-packages/', data)
  },

  /**
   * 获取资源包详情
   */
  get(id: number): Promise<ApiResponse<ResourcePackage>> {
    return get(`/resource-packages/${id}`)
  },

  /**
   * 更新资源包
   */
  update(id: number, data: ResourcePackageUpdateRequest): Promise<ApiResponse<ResourcePackage>> {
    return put(`/resource-packages/${id}`, data)
  },

  /**
   * 删除资源包
   */
  delete(id: number): Promise<ApiResponse<{ message: string }>> {
    return del(`/resource-packages/${id}`)
  },

  /**
   * 搜索资源包
   */
  search(params: ResourcePackageSearchRequest): Promise<ApiResponse<ResourcePackageListResponse>> {
    return post('/resource-packages/search', params)
  },



  /**
   * 查询资源包数据
   */
  query(id: number, params: ResourcePackageQueryRequest): Promise<ApiResponse<ResourcePackageQueryResponse>> {
    return post(`/resource-packages/${id}/query`, params)
  },

  /**
   * 生成Excel（更新excel_time与download_url）
   */
  generateExcel(id: number, payload: Record<string, any>): Promise<ApiResponse<any>> {
    // 为长耗时任务单独提升超时到180秒
    return post(`/resource-packages/${id}/generate-excel`, payload, { timeout: 180000 })
  },

  /**
   * 下载最新资源包（更新download_time）
   */
  downloadLatest(id: number): Promise<ApiResponse<any>> {
    return post(`/resource-packages/${id}/download-latest`, {})
  },

  /**
   * 安全查询资源包数据 - 增强安全性版本
   * 专为ResourcePackageQueryPage.vue页面设计
   */
  secureQuery(id: number, params: ResourcePackageQueryRequest): Promise<ApiResponse<ResourcePackageQueryResponse>> {
    return post(`/resource-packages/${id}/secure-query`, params)
  },

  /**
   * 获取安全查询历史记录
   */
  getSecureQueryHistory(id: number, page: number = 1, size: number = 20): Promise<ApiResponse<any>> {
    return get(`/resource-packages/${id}/query-history?page=${page}&size=${size}`)
  },

  /**
   * 获取查询历史
   */
  getHistory(id: number, page: number = 1, size: number = 20): Promise<ApiResponse<any>> {
    return get(`/resource-packages/${id}/history`, {
      page, size
    })
  },

  /**
   * 列出历史Excel文件
   */
  listFiles(id: number, page: number = 1, size: number = 20): Promise<ApiResponse<{ items: ResourcePackageFile[]; total: number; page: number; size: number }>> {
    return get(`/resource-packages/${id}/files`, { page, size })
  },

  /**
   * 下载指定历史文件（返回预签名URL）
   */
  downloadFile(id: number, fileId: number): Promise<ApiResponse<{ download_url: string; filename: string; object_path: string }>> {
    return post(`/resource-packages/${id}/files/${fileId}/download`, {})
  }
}

/**
 * 模板管理API
 */
export const templateApi = {
  /**
   * 获取模板列表
   */
  list(params?: { datasource_id?: number; type?: PackageType; data_resource_id?: number; indices?: string[] }): Promise<{ data: Template[] }> {
    const query: any = {}
    if (params?.datasource_id) query.datasource_id = params.datasource_id
    if (params?.data_resource_id) query.data_resource_id = params.data_resource_id
    if (params?.indices && params.indices.length > 0) query.indices = params.indices.join(',')

    if (params?.type === PackageType.ELASTICSEARCH) {
      // ES模板端点
      return get('/es/templates', query)
    }
    // 默认SQL模板端点（并标记为模板）
    query.isTemplate = true
    return get('/sql/templates', query)
  },

  /**
   * 获取模板详情
   */
  get(id: number, type: PackageType): Promise<{ data: Template }> {
    if (type === PackageType.ELASTICSEARCH) {
      return get(`/es/templates/${id}`)
    }
    return get(`/sql/templates/${id}`)
  },

  /**
   * 创建模板
   */
  create(data: Omit<Template, 'id' | 'created_at' | 'updated_at' | 'created_by'>): Promise<Template> {
    return post('/templates/', data)
  },

  /**
   * 更新模板
   */
  update(id: number, data: Partial<Omit<Template, 'id' | 'created_at' | 'updated_at' | 'created_by'>>): Promise<Template> {
    return put(`/templates/${id}`, data)
  },

  /**
   * 删除模板
   */
  delete(id: number): Promise<{ message: string }> {
    return del(`/templates/${id}`)
  }
}

export default resourcePackageApi