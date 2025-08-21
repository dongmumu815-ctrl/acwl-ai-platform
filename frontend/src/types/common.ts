/**
 * 通用类型定义
 */

// 分页响应类型
export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  size: number
  pages: number
}

// API响应基础类型
export interface ApiResponse<T = any> {
  success: boolean
  message: string
  data: T
  timestamp: string
}

// ID响应类型
export interface IDResponse {
  id: number
  message: string
}

// 基础实体类型
export interface BaseEntity {
  id: number
  created_at: string
  updated_at: string
}

// 排序方向
export type SortOrder = 'asc' | 'desc'

// 排序参数
export interface SortParams {
  field: string
  order: SortOrder
}

// 分页参数
export interface PaginationParams {
  page?: number
  size?: number
}

// 搜索参数
export interface SearchParams {
  search?: string
}

// 状态类型
export type Status = 'active' | 'inactive' | 'pending' | 'error'

// 文件上传响应
export interface UploadResponse {
  url: string
  filename: string
  size: number
  type: string
}

// 操作结果
export interface OperationResult {
  success: boolean
  message: string
  data?: any
}