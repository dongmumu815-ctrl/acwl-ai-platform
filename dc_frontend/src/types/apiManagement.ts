/**
 * API管理相关类型定义
 */

/**
 * 平台信息接口
 */
export interface Customer {
  id: number
  name: string
  email: string
  phone?: string
  company?: string
  app_id: string
  app_secret: string
  rate_limit: number
  max_apis: number
  total_api_calls: number
  last_api_call_at?: string
  is_active: boolean
  created_at: string
  updated_at: string
}

/**
 * 创建平台请求
 */
export interface CustomerCreate {
  name: string
  email: string
  phone?: string
  company?: string
  rate_limit?: number
  max_apis?: number
}

/**
 * 更新平台请求
 */
export interface CustomerUpdate {
  name?: string
  email?: string
  phone?: string
  company?: string
  rate_limit?: number
  max_apis?: number
  is_active?: boolean
}

/**
 * API接口信息
 */
export interface CustomApi {
  id: number
  customer_id: number
  api_name: string
  api_code: string
  description?: string
  endpoint_url: string
  http_method: string
  request_format: 'json' | 'form' | 'xml'
  response_format: 'json' | 'xml' | 'text'
  is_active: boolean
  total_calls: number
  last_called_at?: string
  created_at: string
  updated_at: string
  customer?: Customer
  fields?: ApiField[]
  resource_type_id?: string
  link_read_id?: string | number
}

/**
 * 创建API请求
 */
export interface CustomApiCreate {
  customer_id: number
  api_name: string
  api_code: string
  api_description?: string
  http_method: string
  response_format: 'json' | 'xml' | 'text'
  status?: boolean
  rate_limit?: number
  require_authentication?: boolean
  link_read_id?: string | number
  resource_type_id?: string
}

/**
 * 更新API请求
 */
export interface CustomApiUpdate {
  api_name?: string
  api_description?: string
  http_method?: string
  request_format?: 'json' | 'form' | 'xml'
  response_format?: 'json' | 'xml' | 'text'
  resource_type_id?: string
  link_read_id?: string | number
  mapping_config_id?: number
  is_active?: boolean
}

/**
 * API字段信息
 */
export interface ApiField {
  id: number
  api_id: number
  field_name: string
  field_type: 'string' | 'number' | 'boolean' | 'date' | 'array' | 'object'
  is_required: boolean
  // 是否上传：1 为勾选，0 为不勾选
  is_upload?: number
  default_value?: string
  description?: string
  validation_rules?: string
  sort_order: number
  created_at: string
  updated_at: string
}

/**
 * 创建API字段请求
 */
export interface ApiFieldCreate {
  field_name: string
  field_type: 'string' | 'number' | 'boolean' | 'date' | 'array' | 'object'
  is_required?: boolean
  // 是否上传：1 为勾选，0 为不勾选
  is_upload?: number
  default_value?: string
  description?: string
  validation_rules?: string
  sort_order?: number
}

/**
 * 更新API字段请求
 */
export interface ApiFieldUpdate {
  field_name?: string
  field_type?: 'string' | 'number' | 'boolean' | 'date' | 'array' | 'object'
  is_required?: boolean
  // 是否上传：1 为勾选，0 为不勾选
  is_upload?: number
  default_value?: string
  description?: string
  validation_rules?: string
  sort_order?: number
}

/**
 * 数据批次信息
 */
export interface DataBatch {
  id: number
  customer_id: number
  batch_name: string
  description?: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
  total_records: number
  processed_records: number
  failed_records: number
  file_path?: string
  result_file_path?: string
  error_message?: string
  started_at?: string
  completed_at?: string
  created_at: string
  updated_at: string
  customer?: Customer
}

/**
 * 创建批次请求
 */
export interface DataBatchCreate {
  customer_id: number
  batch_name: string
  description?: string
  file?: File
}

/**
 * 更新批次请求
 */
export interface DataBatchUpdate {
  batch_name?: string
  description?: string
  status?: 'pending' | 'processing' | 'completed' | 'failed'
}

/**
 * API使用日志
 */
export interface ApiUsageLog {
  id: number
  customer_id: number
  api_id: number
  request_data?: string
  response_data?: string
  status_code: number
  response_time: number
  ip_address?: string
  user_agent?: string
  error_message?: string
  created_at: string
  customer?: Customer
  api?: CustomApi
}

/**
 * 数据上传记录
 */
export interface DataUpload {
  id: number
  customer_id: number
  batch_id?: number
  file_name: string
  file_size: number
  file_type: string
  file_path: string
  upload_status: 'uploading' | 'completed' | 'failed'
  error_message?: string
  created_at: string
  updated_at: string
  customer?: Customer
  batch?: DataBatch
}

/**
 * 系统统计信息
 */
export interface SystemStats {
  totalCustomers: number
  totalApis: number
  totalBatches: number
  totalUploads: number
  totalApiCalls: number
  activeCustomers: number
  pendingBatches: number
  processingBatches: number
  completedBatches: number
  failedBatches: number
}

/**
 * 批次状态统计
 */
export interface BatchStatusStats {
  pending: number
  processing: number
  completed: number
  failed: number
}

/**
 * API调用统计
 */
export interface ApiCallStats {
  date: string
  calls: number
  success_calls: number
  failed_calls: number
}

/**
 * 平台活跃度统计
 */
export interface CustomerActivityStats {
  customer_name: string
  api_calls: number
  last_call_date: string
}

/**
 * 分页查询参数
 */
export interface PaginationParams {
  page?: number
  page_size?: number
  search?: string
  customer_id?: number
  status?: string
  start_date?: string
  end_date?: string
}

/**
 * 资源类型信息
 */
export interface ResourceType {
  id: string
  name: string
  describe?: string
  metadata?: any
}

/**
 * 分页响应
 */
export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
  total_pages: number
}