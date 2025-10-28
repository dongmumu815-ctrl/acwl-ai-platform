import { request } from '@/utils/request'
import type { ApiResponse } from '@/utils/request'
import type { PaginationParams, PaginatedResponse } from '@/types/apiManagement'

export interface UserOperationLog {
  id: number
  user_id?: number
  username?: string
  method: string
  path: string
  status_code: number
  success: boolean
  ip_address?: string
  duration_ms?: number
  request_id?: string
  created_at: string
}

export interface UserOperationLogDetail extends UserOperationLog {
  request_headers?: Record<string, string>
  query_params?: Record<string, any>
  request_body?: any
  response_body?: any
  error_message?: string
  stack_trace?: string
}

export interface UserOperationLogsQuery extends PaginationParams {
  keyword?: string
  method?: string
  path?: string
  status_code?: number
  result_status?: string  // 'success' or 'failure'
  ip_address?: string
  start_date?: string
  end_date?: string
}

export const userOperationLogsApi = {
  getLogs(params?: UserOperationLogsQuery): Promise<ApiResponse<PaginatedResponse<UserOperationLog>>> {
    return request({
      url: '/user-operation-logs/',
      method: 'get',
      params
    })
  },
  getLogDetail(id: number): Promise<ApiResponse<UserOperationLogDetail>> {
    return request({
      url: `/user-operation-logs/${id}`,
      method: 'get'
    })
  }
}