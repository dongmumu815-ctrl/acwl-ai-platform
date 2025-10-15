/**
 * 数据资源相关类型定义
 */

/**
 * 资源类型枚举
 */
export enum ResourceType {
  DORIS_TABLE = 'doris_table',
  ELASTICSEARCH_INDEX = 'elasticsearch_index'
}

/**
 * 资源状态枚举
 */
export enum ResourceStatus {
  ACTIVE = 'active',
  INACTIVE = 'inactive',
  ARCHIVED = 'archived',
  ERROR = 'error'
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
 * 数据资源分类
 */
export interface DataResourceCategory {
  id: number
  name: string
  description?: string
  parent_id?: number
  level: number
  sort_order: number
  is_active: boolean
  created_at: string
  updated_at: string
  children?: DataResourceCategory[]
  resource_count?: number
}

/**
 * 标签状态枚举
 */
export enum TagStatus {
  ACTIVE = 'active',
  DISABLED = 'disabled'
}

/**
 * 数据资源标签
 */
export interface DataResourceTag {
  id: number
  name: string
  color: string
  description?: string
  status: TagStatus
  usage_count: number
  created_at: string
  updated_at: string
  created_by?: number
  updated_by?: number
  resource_count?: number
}

/**
 * 标签创建请求
 */
export interface TagCreateRequest {
  name: string
  color: string
  description?: string
  status?: TagStatus
}

/**
 * 标签更新请求
 */
export interface TagUpdateRequest {
  name?: string
  color?: string
  description?: string
  status?: TagStatus
}

/**
 * 标签列表查询参数
 */
export interface TagListQuery {
  page?: number
  page_size?: number
  search?: string
  status?: TagStatus
  sort_by?: 'name' | 'usage_count' | 'created_at'
  sort_order?: 'asc' | 'desc'
}

/**
 * 标签使用详情
 */
export interface TagUsage {
  id: number
  resource_id: number
  resource_name: string
  resource_type: string
  category_name: string
  created_at: string
}

/**
 * 标签使用统计
 */
export interface TagUsageStats {
  tag_id: number
  tag_name: string
  resource_count: number
  usage_list: TagUsage[]
}

/**
 * 批量删除标签请求
 */
export interface TagBatchDeleteRequest {
  tag_ids: number[]
}

/**
 * 下拉菜单命令
 */
export interface DropdownCommand {
  action: 'edit' | 'toggle' | 'delete'
  data: DataResourceTag
}

/**
 * 数据资源字段信息
 */
export interface DataResourceField {
  name: string
  type: string
  description?: string
  is_nullable: boolean
  default_value?: string
  max_length?: number
  precision?: number
  scale?: number
  is_primary_key: boolean
  is_index: boolean
}

/**
 * 数据资源连接配置
 */
export interface DataResourceConnection {
  host: string
  port: number
  database?: string
  username?: string
  password?: string
  ssl?: boolean
  timeout?: number
  pool_size?: number
  additional_params?: Record<string, any>
}

/**
 * 数据资源基本信息
 */
export interface DataResource {
  id: number
  name: string
  display_name: string
  description?: string
  resource_type: ResourceType
  status: ResourceStatus
  category_id: number
  category?: DataResourceCategory
  tags: DataResourceTag[]
  connection_config: DataResourceConnection
  table_name: string
  schema_name?: string
  fields: DataResourceField[]
  row_count?: number
  size_mb?: number
  last_updated?: string
  created_by: number
  created_at: string
  updated_at: string
  is_public: boolean
  access_count: number
  favorite_count: number
  is_favorited?: boolean
  creator?: {
    id: number
    username: string
    full_name: string
  }
}

/**
 * 数据资源权限
 */
export interface DataResourcePermission {
  id: number
  resource_id: number
  user_id: number
  permission_type: PermissionType
  granted_by: number
  granted_at: string
  expires_at?: string
  is_active: boolean
  user?: {
    id: number
    username: string
    full_name: string
  }
  granter?: {
    id: number
    username: string
    full_name: string
  }
}

/**
 * 数据资源访问日志
 */
export interface DataResourceAccessLog {
  id: number
  resource_id: number
  user_id: number
  action: string
  query?: string
  result_count?: number
  execution_time?: number
  ip_address: string
  user_agent: string
  created_at: string
  user?: {
    id: number
    username: string
    full_name: string
  }
}

/**
 * 数据资源收藏
 */
export interface DataResourceFavorite {
  id: number
  resource_id: number
  user_id: number
  created_at: string
}

/**
 * 数据资源查询历史
 */
export interface DataResourceQueryHistory {
  id: number
  resource_id: number
  user_id: number
  query: string
  result_count: number
  execution_time: number
  created_at: string
}

/**
 * 数据资源创建请求
 */
export interface DataResourceCreateRequest {
  name: string
  display_name: string
  description?: string
  resource_type: ResourceType
  category_id: number
  tag_ids?: number[]
  connection_config: DataResourceConnection
  table_name: string
  schema_name?: string
  is_public?: boolean
}

/**
 * 数据资源更新请求
 */
export interface DataResourceUpdateRequest {
  display_name?: string
  description?: string
  category_id?: number
  tag_ids?: number[]
  connection_config?: DataResourceConnection
  is_public?: boolean
  status?: ResourceStatus
}

/**
 * 数据资源查询请求
 */
export interface DataResourceQueryRequest {
  query: string
  limit?: number
  offset?: number
  format?: 'json' | 'csv' | 'excel'
}

/**
 * 数据资源查询响应
 */
export interface DataResourceQueryResponse {
  columns: string[]
  data: any[][]
  total_count: number
  execution_time: number
  query_id: string
}

/**
 * 数据资源列表查询参数
 */
export interface DataResourceListQuery {
  page?: number
  page_size?: number
  search?: string
  category_id?: number
  tag_ids?: number[]
  resource_type?: ResourceType
  status?: ResourceStatus
  is_public?: boolean
  created_by?: number
  sort_by?: string
  sort_order?: 'asc' | 'desc'
  favorites_only?: boolean
}

/**
 * 数据资源统计信息
 */
export interface DataResourceStats {
  total_resources: number
  active_resources: number
  inactive_resources: number
  doris_tables: number
  elasticsearch_indices: number
  total_size_mb: number
  total_access_count: number
  categories_count: number
  tags_count: number
  users_with_access: number
}

/**
 * 数据资源预览数据
 */
export interface DataResourcePreview {
  columns: DataResourceField[]
  sample_data: any[][]
  total_rows: number
  sample_size: number
}

/**
 * 权限授予请求
 */
export interface PermissionGrantRequest {
  user_id: number
  permission_type: PermissionType
  expires_at?: string
}

/**
 * 批量操作请求
 */
export interface BatchOperationRequest {
  resource_ids: number[]
  operation: 'delete' | 'archive' | 'activate' | 'deactivate' | 'change_category' | 'add_tags' | 'remove_tags'
  params?: Record<string, any>
}

/**
 * 数据资源导入请求
 */
export interface DataResourceImportRequest {
  file: File
  category_id: number
  tag_ids?: number[]
  is_public?: boolean
}

/**
 * 数据资源导出请求
 */
export interface DataResourceExportRequest {
  resource_ids: number[]
  format: 'json' | 'csv' | 'excel'
  include_data?: boolean
  include_schema?: boolean
}

/**
 * 数据资源同步状态
 */
export interface DataResourceSyncStatus {
  resource_id: number
  last_sync_at?: string
  sync_status: 'pending' | 'syncing' | 'success' | 'failed'
  sync_message?: string
  fields_added: number
  fields_removed: number
  fields_modified: number
}

/**
 * 数据资源健康检查结果
 */
export interface DataResourceHealthCheck {
  resource_id: number
  is_healthy: boolean
  connection_status: 'connected' | 'disconnected' | 'error'
  table_exists: boolean
  field_count: number
  row_count?: number
  last_check_at: string
  error_message?: string
}