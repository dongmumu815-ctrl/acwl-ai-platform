import { request } from '@/utils/request'
import type { ApiResponse } from '@/utils/request'
import type { PaginationParams, PaginatedResponse } from '@/types/apiManagement'

export interface DataUploadLog {
  id: number
  batch_id: string
  data_source_name: string
  platform_name: string
  target_table_name: string
  target_table_desc?: string
  need_review: number
  resource_type: string
  sync_start_time: string
  sync_end_time?: string
  total_data_count?: number
  success_data_count?: number
  failed_data_count?: number
  sync_status: string
  failure_reason?: string
  retry_upload?: number
  encryption_method?: string
  operator: string
  sync_log?: string
  create_time: string
  update_time?: string
}

export interface DataUploadLogsQuery extends PaginationParams {
  sort_by?: string
  order?: 'asc' | 'desc'
}

export const dataUploadLogsApi = {
  getLogs(params?: DataUploadLogsQuery): Promise<ApiResponse<PaginatedResponse<DataUploadLog>>> {
    return request({
      url: '/data-upload-logs/',
      method: 'get',
      params: {
        page: params?.page ?? 1,
        size: params?.page_size ?? 20,
        sort_by: params?.sort_by ?? 'sync_start_time',
        order: params?.order ?? 'desc'
      }
    })
  }
}