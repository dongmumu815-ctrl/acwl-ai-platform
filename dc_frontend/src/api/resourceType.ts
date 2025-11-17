import { get, post, put, del } from '@/utils/request'
import type { ApiResponse } from '@/utils/request'
import type { ResourceTypeItem, ResourceTypeListResponse } from '@/types/resourceType'

const BASE = '/data-resource-types'

export interface CreatePayload {
  name: string
  describe?: string
  metadata?: Record<string, any>
}

export interface UpdatePayload {
  name?: string
  describe?: string
  metadata?: Record<string, any>
}

export interface ListParams {
  page?: number
  page_size?: number
  name?: string
}

export const listResourceTypes = (
  params: ListParams = {}
): Promise<ApiResponse<ResourceTypeListResponse>> => {
  const { page = 1, page_size = 10, name } = params
  return get<ResourceTypeListResponse>(`${BASE}/list`, { page, page_size, name }, { permission: 'data:resource_type:view' })
}

export const getResourceType = (id: string): Promise<ApiResponse<ResourceTypeItem>> => {
  return get<ResourceTypeItem>(`${BASE}/${id}`, undefined, { permission: 'data:resource_type:view' })
}

export const createResourceType = (data: CreatePayload): Promise<ApiResponse<ResourceTypeItem>> => {
  return post<ResourceTypeItem>(`${BASE}/create`, data, { permission: 'data:resource_type:create' })
}

export const updateResourceType = (id: string, data: UpdatePayload): Promise<ApiResponse<ResourceTypeItem>> => {
  return put<ResourceTypeItem>(`${BASE}/${id}`, data, { permission: 'data:resource_type:edit' })
}

export const deleteResourceType = (id: string): Promise<ApiResponse<void>> => {
  return del<void>(`${BASE}/${id}`, { permission: 'data:resource_type:delete' })
}