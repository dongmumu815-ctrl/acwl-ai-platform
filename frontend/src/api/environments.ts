import { request } from '@/utils/request'
import type { PaginatedResponse } from '@/types/common'

export interface Environment {
  id: number
  name: string
  config?: Record<string, any> | null
  description?: string | null
  created_by?: number | null
  created_at: string
  updated_at: string
}

export interface EnvironmentForm {
  name: string
  config?: Record<string, any> | null
  description?: string | null
}

export interface EnvironmentQueryParams {
  page?: number
  size?: number
  search?: string
}

export const environmentApi = {
  getEnvironments(params?: EnvironmentQueryParams): Promise<PaginatedResponse<Environment>> {
    return request.get('/environments/', params)
  },
  getEnvironment(envId: number): Promise<Environment> {
    return request.get(`/environments/${envId}`)
  },
  createEnvironment(data: EnvironmentForm): Promise<{ id: number; message?: string }> {
    return request.post('/environments/', data)
  },
  updateEnvironment(envId: number, data: Partial<EnvironmentForm>): Promise<Environment> {
    return request.put(`/environments/${envId}`, data)
  },
  deleteEnvironment(envId: number): Promise<{ success: boolean; message?: string }> {
    return request.delete(`/environments/${envId}`)
  }
}

export const {
  getEnvironments,
  getEnvironment,
  createEnvironment,
  updateEnvironment,
  deleteEnvironment
} = environmentApi