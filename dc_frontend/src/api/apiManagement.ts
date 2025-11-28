import { request } from '@/utils/request'
import type { ApiResponse } from '@/types/common'
import type {
  Customer,
  CustomerCreate,
  CustomerUpdate,
  CustomApi,
  CustomApiCreate,
  CustomApiUpdate,
  ApiField,
  ApiFieldCreate,
  ApiFieldUpdate,
  DataBatch,
  DataBatchCreate,
  DataBatchUpdate,
  ApiUsageLog,
  DataUpload,
  SystemStats,
  BatchStatusStats,
  ApiCallStats,
  CustomerActivityStats,
  PaginationParams,
  PaginatedResponse,
  ResourceType
} from '@/types/apiManagement'

/**
 * API管理相关接口
 */

// ==================== 平台管理 ====================

/**
 * 获取平台列表
 */
export const getCustomers = (params?: PaginationParams): Promise<ApiResponse<PaginatedResponse<Customer>>> => {
  return request({
    url: '/customers',
    method: 'get',
    params,
    permission: 'data:customer:view'
  })
}

/**
 * 获取平台详情
 */
export const getCustomer = (id: number): Promise<ApiResponse<Customer>> => {
  return request({
    url: `/customers/${id}`,
    method: 'get',
    permission: 'data:customer:view'
  })
}

/**
 * 创建平台
 */
export const createCustomer = (data: CustomerCreate): Promise<ApiResponse<Customer>> => {
  const formData = new FormData()
  formData.append('name', data.name)
  formData.append('email', data.email)
  if (data.phone) formData.append('phone', data.phone)
  if (data.company) formData.append('company', data.company)
  if (typeof data.rate_limit !== 'undefined') formData.append('rate_limit', String(data.rate_limit))
  if (typeof data.max_apis !== 'undefined') formData.append('max_apis', String(data.max_apis))

  return request({
    url: '/customers',
    method: 'post',
    data: formData,
    headers: {
      'Content-Type': 'multipart/form-data'
    },
    permission: 'data:customer:create'
  })
}

/**
 * 更新平台
 */
export const updateCustomer = (id: number, data: CustomerUpdate): Promise<ApiResponse<Customer>> => {
  const formData = new FormData()
  if (typeof data.name !== 'undefined') formData.append('name', data.name)
  if (typeof data.email !== 'undefined') formData.append('email', data.email)
  if (typeof data.phone !== 'undefined') formData.append('phone', data.phone)
  if (typeof data.company !== 'undefined') formData.append('company', data.company)
  if (typeof data.rate_limit !== 'undefined') formData.append('rate_limit', String(data.rate_limit))
  if (typeof data.max_apis !== 'undefined') formData.append('max_apis', String(data.max_apis))
  if (typeof data.is_active !== 'undefined') formData.append('is_active', String(data.is_active))

  return request({
    url: `/customers/${id}`,
    method: 'put',
    data: formData,
    headers: {
      'Content-Type': 'multipart/form-data'
    },
    permission: 'data:customer:edit'
  })
}

/**
 * 删除平台
 */
export const deleteCustomer = (id: number): Promise<ApiResponse<void>> => {
  return request({
    url: `/customers/${id}`,
    method: 'delete',
    permission: 'data:customer:delete'
  })
}

/**
 * 重置平台密钥
 */
export const resetCustomerSecret = (id: number): Promise<ApiResponse<{ app_secret: string }>> => {
  return request({
    url: `/customers/${id}/reset-secret`,
    method: 'post',
    permission: 'data:customer:reset_secret'
  })
}

/**
 * 重置平台密码
 * 如果不传入 password，则由服务端生成一次性强密码并返回
 */
export const resetCustomerPassword = (
  id: number,
  password?: string
): Promise<ApiResponse<{ password: string }>> => {
  return request({
    url: `/customers/${id}/reset-password`,
    method: 'post',
    data: password ? { password } : undefined,
    permission: 'data:customer:reset_password'
  })
}

// ==================== API管理 ====================

/**
 * 获取API列表
 */
export const getApis = (params?: PaginationParams): Promise<ApiResponse<PaginatedResponse<CustomApi>>> => {
  return request({
    url: '/apis',
    method: 'get',
    params,
    permission: 'data:api:view'
  })
}

/**
 * 获取API详情
 */
export const getApi = (id: number): Promise<ApiResponse<CustomApi>> => {
  return request({
    url: `/apis/${id}`,
    method: 'get',
    permission: 'data:api:view'
  })
}

/**
 * 创建API
 */
export const createApi = (data: CustomApiCreate): Promise<ApiResponse<CustomApi>> => {
  return request({
    url: '/apis',
    method: 'post',
    data,
    permission: 'data:api:create'
  })
}

/**
 * 更新API
 */
export const updateApi = (id: number, data: CustomApiUpdate): Promise<ApiResponse<CustomApi>> => {
  return request({
    url: `/apis/${id}`,
    method: 'put',
    data,
    permission: 'data:api:edit'
  })
}

/**
 * 删除API
 */
export const deleteApi = (id: number): Promise<ApiResponse<void>> => {
  return request({
    url: `/apis/${id}`,
    method: 'delete',
    permission: 'data:api:delete'
  })
}

/**
 * 复制API
 */
export const copyApi = (id: number, data: { target_customer_id: number; new_api_code: string; new_api_name: string }): Promise<ApiResponse<CustomApi>> => {
  return request({
    url: `/apis/${id}/copy`,
    method: 'post',
    data,
    permission: 'data:api:copy'
  })
}

// ==================== API字段管理 ====================

/**
 * 获取API字段列表
 */
export const getApiFields = (apiId: number): Promise<ApiResponse<ApiField[]>> => {
  return request({
    url: `/apis/${apiId}/fields`,
    method: 'get',
    permission: 'data:api_field:view'
  })
}

/**
 * 创建API字段
 */
export const createApiField = (apiId: number, data: ApiFieldCreate): Promise<ApiResponse<ApiField>> => {
  return request({
    url: `/apis/${apiId}/fields`,
    method: 'post',
    data,
    permission: 'data:api_field:create'
  })
}

/**
 * 更新API字段
 */
export const updateApiField = (apiId: number, fieldId: number, data: ApiFieldUpdate): Promise<ApiResponse<ApiField>> => {
  return request({
    url: `/apis/${apiId}/fields/${fieldId}`,
    method: 'put',
    data,
    permission: 'data:api_field:edit'
  })
}

/**
 * 删除API字段
 */
export const deleteApiField = (apiId: number, fieldId: number): Promise<ApiResponse<void>> => {
  return request({
    url: `/apis/${apiId}/fields/${fieldId}`,
    method: 'delete',
    permission: 'data:api_field:delete'
  })
}

/**
 * 批量更新字段顺序
 */
export const updateFieldsOrder = (apiId: number, fields: Array<{ id: number; field_order: number }>): Promise<ApiResponse<void>> => {
  return request({
    url: `/apis/${apiId}/fields/order`,
    method: 'put',
    data: { fields },
    permission: 'data:api_field:edit'
  })
}

// ==================== 批次管理 ====================

/**
 * 获取批次列表
 */
export const getBatches = (params?: PaginationParams): Promise<ApiResponse<PaginatedResponse<DataBatch>>> => {
  return request({
    url: '/batches',
    method: 'get',
    params,
    permission: 'data:batch:view'
  })
}

/**
 * 获取批次详情
 */
export const getBatch = (id: number): Promise<ApiResponse<DataBatch>> => {
  return request({
    url: `/batches/${id}`,
    method: 'get',
    permission: 'data:batch:view'
  })
}

/**
 * 创建批次
 */
export const createBatch = (data: DataBatchCreate): Promise<ApiResponse<DataBatch>> => {
  const formData = new FormData()
  formData.append('customer_id', data.customer_id.toString())
  formData.append('batch_name', data.batch_name)
  if (data.description) formData.append('description', data.description)
  if (data.file) formData.append('file', data.file)

  return request({
    url: '/batches',
    method: 'post',
    data: formData,
    headers: {
      'Content-Type': 'multipart/form-data'
    },
    permission: 'data:batch:create'
  })
}

/**
 * 更新批次
 */
export const updateBatch = (id: number, data: DataBatchUpdate): Promise<ApiResponse<DataBatch>> => {
  return request({
    url: `/batches/${id}`,
    method: 'put',
    data,
    permission: 'data:batch:edit'
  })
}

/**
 * 删除批次
 */
export const deleteBatch = (id: number): Promise<ApiResponse<void>> => {
  return request({
    url: `/batches/${id}`,
    method: 'delete',
    permission: 'data:batch:delete'
  })
}

/**
 * 开始处理批次
 */
export const startBatchProcessing = (id: number): Promise<ApiResponse<void>> => {
  return request({
    url: `/batches/${id}/start`,
    method: 'post',
    permission: 'data:batch:start'
  })
}

/**
 * 停止批次处理
 */
export const stopBatchProcessing = (id: number): Promise<ApiResponse<void>> => {
  return request({
    url: `/batches/${id}/stop`,
    method: 'post',
    permission: 'data:batch:stop'
  })
}

/**
 * 下载批次结果
 */
export const downloadBatchResult = (id: number): Promise<Blob> => {
  return request({
    url: `/batches/${id}/download`,
    method: 'get',
    responseType: 'blob',
    permission: 'data:batch:download'
  })
}

// ==================== 日志和统计 ====================

/**
 * 获取API使用日志
 */
export const getApiUsageLogs = (params?: PaginationParams & {
  api_id?: number
  status_code?: number
}): Promise<ApiResponse<PaginatedResponse<ApiUsageLog>>> => {
  return request({
    url: '/logs/api-usage',
    method: 'get',
    params,
    permission: 'logs:api_usage:view'
  })
}

/**
 * 获取数据上传记录
 */
export const getDataUploads = (params?: PaginationParams & {
  batch_id?: number
  upload_status?: string
}): Promise<ApiResponse<PaginatedResponse<DataUpload>>> => {
  return request({
    url: '/logs/data-uploads',
    method: 'get',
    params,
    permission: 'logs:data_uploads:view'
  })
}

/**
 * 获取系统统计信息
 */
export const getSystemStats = (): Promise<ApiResponse<SystemStats>> => {
  return request({
    url: '/stats/system',
    method: 'get',
    permission: 'system:stats:view'
  })
}

/**
 * 获取数据增长趋势（acwl_type_count）
 */
export const getTypeCountTrend = (params?: { days?: number; start_date?: string; end_date?: string }): Promise<ApiResponse<{ dates: string[]; series: Record<string, number[]> }>> => {
  return request({
    url: '/stats/type-count-trend',
    method: 'get',
    params,
    permission: 'system:stats:view'
  })
}

/**
 * 获取批次状态统计
 */
export const getBatchStatusStats = (): Promise<ApiResponse<BatchStatusStats>> => {
  return request({
    url: '/stats/batch-status',
    method: 'get',
    permission: 'system:stats:view'
  })
}

/**
 * 获取API调用统计
 */
export const getApiCallStats = (params?: {
  start_date?: string
  end_date?: string
  customer_id?: number
  api_id?: number
}): Promise<ApiResponse<ApiCallStats[]>> => {
  return request({
    url: '/stats/api-calls',
    method: 'get',
    params,
    permission: 'system:stats:view'
  })
}

/**
 * 获取平台活跃度统计
 */
export const getCustomerActivityStats = (params?: {
  limit?: number
  start_date?: string
  end_date?: string
}): Promise<ApiResponse<CustomerActivityStats[]>> => {
  return request({
    url: '/stats/customer-activity',
    method: 'get',
    params,
    permission: 'system:stats:view'
  })
}

// ==================== 系统配置 ====================

/**
 * 获取系统配置
 */
export const getSystemConfig = (): Promise<ApiResponse<Record<string, any>>> => {
  return request({
    url: '/config',
    method: 'get',
    permission: 'system:config:view'
  })
}

/**
 * 更新系统配置
 */
export const updateSystemConfig = (data: Record<string, any>): Promise<ApiResponse<void>> => {
  return request({
    url: '/config',
    method: 'put',
    data,
    permission: 'system:config:update'
  })
}

/**
 * 测试API连接
 */
export const testApiConnection = (apiId: number, testData?: Record<string, any>): Promise<ApiResponse<{
  success: boolean
  response_data: any
  response_time: number
  status_code: number
  error_message?: string
}>> => {
  return request({
    url: `/apis/${apiId}/test`,
    method: 'post',
    data: testData || {},
    permission: 'data:api:test'
  })
}

// ==================== 资源类型管理 ====================

/**
 * 获取资源类型列表
 */
export const getResourceTypes = (): Promise<ApiResponse<{
  resource_types: ResourceType[]
  total: number
}>> => {
  return request({
    url: '/resource-types',
    method: 'get',
    permission: 'data:resource_type:view'
  })
}

/**
 * 获取关联任务类型列表
 */
export const getLinkTypes = (): Promise<ApiResponse<any[]>> => {
  return request({
    url: '/link-types',
    method: 'get'
  })
}
