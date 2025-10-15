import { request } from '@/utils/request'
import type {
  DataResource,
  DataResourceCategory,
  DataResourceTag,
  DataResourcePermission,
  DataResourceAccessLog,
  DataResourceQueryHistory,
  DataResourceCreateRequest,
  DataResourceUpdateRequest,
  DataResourceQueryRequest,
  DataResourceQueryResponse,
  DataResourceListQuery,
  DataResourceStats,
  DataResourcePreview,
  PermissionGrantRequest,
  BatchOperationRequest,
  DataResourceImportRequest,
  DataResourceExportRequest,
  DataResourceSyncStatus,
  DataResourceHealthCheck,
  ApiResponse,
  PaginatedResponse
} from '@/types/dataResource'

/**
 * 数据资源相关API接口
 */
export const dataResourceApi = {
  /**
   * 获取数据资源列表
   * @param params 查询参数
   */
  getResourceList(params?: DataResourceListQuery): Promise<ApiResponse<PaginatedResponse<DataResource>>> {
    // 统一参数名为后端期望的 page_size
    const pageSizeParam = (params as any)?.page_size ?? (params as any)?.pageSize
    const apiParams = params ? {
      ...params,
      page_size: pageSizeParam,
      pageSize: undefined,
      size: undefined
    } : undefined

    return request({
      url: '/data-resources/',
      method: 'GET',
      params: apiParams
    })
  },

  /**
   * 获取数据资源详情
   * @param id 资源ID
   */
  getResourceDetail(id: number): Promise<ApiResponse<DataResource>> {
    return request({
      url: `/data-resources/${id}`,
      method: 'GET'
    })
  },

  /**
   * 创建数据资源
   * @param data 创建数据
   */
  createResource(data: DataResourceCreateRequest): Promise<ApiResponse<DataResource>> {
    return request({
      url: '/data-resources/',
      method: 'POST',
      data
    })
  },

  /**
   * 更新数据资源
   * @param id 资源ID
   * @param data 更新数据
   */
  updateResource(id: number, data: DataResourceUpdateRequest): Promise<ApiResponse<DataResource>> {
    return request({
      url: `/data-resources/${id}`,
      method: 'PUT',
      data
    })
  },

  /**
   * 删除数据资源
   * @param id 资源ID
   */
  deleteResource(id: number): Promise<ApiResponse<void>> {
    return request({
      url: `/data-resources/${id}`,
      method: 'DELETE'
    })
  },

  /**
   * 搜索数据资源
   * @param params 搜索参数
   */
  searchResources(params: {
    q: string
    page?: number
    page_size?: number
    filters?: Record<string, any>
  }): Promise<ApiResponse<PaginatedResponse<DataResource>>> {
    return request({
      url: '/data-resources/search',
      method: 'GET',
      params
    })
  },

  /**
   * 获取资源结构信息
   * @param id 资源ID
   */
  getResourceSchema(id: number): Promise<ApiResponse<{
    fields: any[]
    indexes: any[]
    constraints: any[]
  }>> {
    return request({
      url: `/data-resources/${id}/schema`,
      method: 'GET'
    })
  },

  /**
   * 获取资源预览数据
   * @param id 资源ID
   * @param params 预览参数
   */
  getResourcePreview(id: number, params?: {
    limit?: number
    offset?: number
  }): Promise<ApiResponse<DataResourcePreview>> {
    return request({
      url: `/data-resources/${id}/preview`,
      method: 'GET',
      params
    })
  },

  /**
   * 执行数据查询
   * @param id 资源ID
   * @param data 查询数据
   */
  queryResource(id: number, data: DataResourceQueryRequest): Promise<ApiResponse<DataResourceQueryResponse>> {
    return request({
      url: `/data-resources/${id}/query`,
      method: 'POST',
      data
    })
  },

  /**
   * 获取查询历史
   * @param id 资源ID
   * @param params 查询参数
   */
  getQueryHistory(id: number, params?: {
    page?: number
    page_size?: number
  }): Promise<ApiResponse<PaginatedResponse<DataResourceQueryHistory>>> {
    return request({
      url: `/data-resources/${id}/query-history`,
      method: 'GET',
      params
    })
  },

  /**
   * 切换收藏状态
   * @param id 资源ID
   */
  toggleFavorite(id: number): Promise<ApiResponse<{ is_favorited: boolean }>> {
    return request({
      url: `/data-resources/${id}/favorite`,
      method: 'POST'
    })
  },

  /**
   * 获取收藏列表
   * @param params 查询参数
   */
  getFavorites(params?: {
    page?: number
    page_size?: number
  }): Promise<ApiResponse<PaginatedResponse<DataResource>>> {
    return request({
      url: '/data-resources/favorites',
      method: 'GET',
      params
    })
  },

  /**
   * 同步资源结构
   * @param id 资源ID
   */
  syncResourceSchema(id: number): Promise<ApiResponse<DataResourceSyncStatus>> {
    return request({
      url: `/data-resources/${id}/sync`,
      method: 'POST'
    })
  },

  /**
   * 检查资源健康状态
   * @param id 资源ID
   */
  checkResourceHealth(id: number): Promise<ApiResponse<DataResourceHealthCheck>> {
    return request({
      url: `/data-resources/${id}/health`,
      method: 'GET'
    })
  },

  /**
   * 批量操作
   * @param data 批量操作数据
   */
  batchOperation(data: BatchOperationRequest): Promise<ApiResponse<{
    success_count: number
    failed_count: number
    errors: string[]
  }>> {
    return request({
      url: '/data-resources/batch',
      method: 'POST',
      data
    })
  },

  /**
   * 导入资源
   * @param data 导入数据
   */
  importResources(data: DataResourceImportRequest): Promise<ApiResponse<{
    imported_count: number
    failed_count: number
    errors: string[]
  }>> {
    const formData = new FormData()
    formData.append('file', data.file)
    formData.append('category_id', data.category_id.toString())
    if (data.tag_ids) {
      formData.append('tag_ids', JSON.stringify(data.tag_ids))
    }
    if (data.is_public !== undefined) {
      formData.append('is_public', data.is_public.toString())
    }

    return request({
      url: '/data-resources/import',
      method: 'POST',
      data: formData,
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },

  /**
   * 导出资源
   * @param data 导出数据
   */
  exportResources(data: DataResourceExportRequest): Promise<Blob> {
    return request({
      url: '/data-resources/export',
      method: 'POST',
      data,
      responseType: 'blob'
    })
  }
}

/**
 * 数据资源分类相关API
 */
export const categoryApi = {
  /**
   * 获取分类列表
   * @param params 查询参数
   */
  getCategoryList(params?: {
    parent_id?: number
    include_children?: boolean
  }): Promise<ApiResponse<DataResourceCategory[]>> {
    return request({
      url: '/categories',
      method: 'GET',
      params
    })
  },

  /**
   * 获取分类树
   */
  getCategoryTree(): Promise<ApiResponse<DataResourceCategory[]>> {
    return request({
      url: '/categories/tree',
      method: 'GET'
    })
  },

  /**
   * 获取分类详情
   * @param id 分类ID
   */
  getCategoryDetail(id: number): Promise<ApiResponse<DataResourceCategory>> {
    return request({
      url: `/categories/${id}`,
      method: 'GET'
    })
  },

  /**
   * 创建分类
   * @param data 分类数据
   */
  createCategory(data: {
    name: string
    description?: string
    parent_id?: number
    sort_order?: number
  }): Promise<ApiResponse<DataResourceCategory>> {
    return request({
      url: '/categories',
      method: 'POST',
      data
    })
  },

  /**
   * 更新分类
   * @param id 分类ID
   * @param data 更新数据
   */
  updateCategory(id: number, data: {
    name?: string
    description?: string
    parent_id?: number
    sort_order?: number
    is_active?: boolean
  }): Promise<ApiResponse<DataResourceCategory>> {
    return request({
      url: `/categories/${id}`,
      method: 'PUT',
      data
    })
  },

  /**
   * 删除分类
   * @param id 分类ID
   */
  deleteCategory(id: number): Promise<ApiResponse<void>> {
    return request({
      url: `/categories/${id}`,
      method: 'DELETE'
    })
  },

  /**
   * 移动分类
   * @param id 分类ID
   * @param data 移动数据
   */
  moveCategory(id: number, data: {
    parent_id?: number
    sort_order?: number
  }): Promise<ApiResponse<DataResourceCategory>> {
    return request({
      url: `/categories/${id}/move`,
      method: 'POST',
      data
    })
  }
}

/**
 * 数据资源标签相关API
 */
export const tagApi = {
  /**
   * 获取标签列表
   * @param params 查询参数
   */
  getTagList(params?: {
    search?: string
    page?: number
    page_size?: number
    status?: string
  }): Promise<ApiResponse<PaginatedResponse<DataResourceTag>>> {
    return request({
      url: '/data-resources/tags/',
      method: 'GET',
      params
    })
  },

  /**
   * 获取所有标签
   */
  getAllTags(): Promise<ApiResponse<DataResourceTag[]>> {
    return request({
      url: '/data-resources/tags/',
      method: 'GET',
      params: {
        page: 1,
        page_size: 1000 // 设置大的page_size来获取所有标签
      }
    }).then(response => {
      // 转换分页响应为简单数组响应
      if (response.success && response.data && response.data.list) {
        return {
          ...response,
          data: response.data.list
        }
      }
      return response
    })
  },

  /**
   * 获取标签详情
   * @param id 标签ID
   */
  getTagDetail(id: number): Promise<ApiResponse<DataResourceTag>> {
    return request({
      url: `/data-resources/tags/${id}`,
      method: 'GET'
    })
  },

  /**
   * 创建标签
   * @param data 标签数据
   */
  createTag(data: {
    name: string
    color: string
    description?: string
  }): Promise<ApiResponse<DataResourceTag>> {
    return request({
      url: '/data-resources/tags/',
      method: 'POST',
      data
    })
  },

  /**
   * 更新标签
   * @param id 标签ID
   * @param data 更新数据
   */
  updateTag(id: number, data: {
    name?: string
    color?: string
    description?: string
  }): Promise<ApiResponse<DataResourceTag>> {
    return request({
      url: `/data-resources/tags/${id}`,
      method: 'PUT',
      data
    })
  },

  /**
   * 删除标签
   * @param id 标签ID
   */
  deleteTag(id: number): Promise<ApiResponse<void>> {
    return request({
      url: `/data-resources/tags/${id}`,
      method: 'DELETE'
    })
  },

  /**
   * 切换标签状态
   * @param id 标签ID
   */
  toggleTagStatus(id: number): Promise<ApiResponse<DataResourceTag>> {
    return request({
      url: `/data-resources/tags/${id}/toggle-status`,
      method: 'POST'
    })
  },

  /**
   * 批量删除标签
   * @param ids 标签ID数组
   */
  batchDeleteTags(ids: number[]): Promise<ApiResponse<{
    success_count: number
    failed_count: number
    errors: string[]
  }>> {
    return request({
      url: '/data-resources/tags/batch-delete',
      method: 'POST',
      data: { tag_ids: ids }
    })
  },

  /**
   * 获取标签使用统计
   * @param id 标签ID
   */
  getTagUsageStats(id: number): Promise<ApiResponse<{
    tag_id: number
    tag_name: string
    resource_count: number
  }>> {
    return request({
      url: `/data-resources/tags/${id}/usage-stats`,
      method: 'GET'
    })
  }
}

/**
 * 数据资源权限相关API
 */
export const permissionApi = {
  /**
   * 获取资源权限列表
   * @param resourceId 资源ID
   * @param params 查询参数
   */
  getResourcePermissions(resourceId: number, params?: {
    page?: number
    page_size?: number
  }): Promise<ApiResponse<PaginatedResponse<DataResourcePermission>>> {
    return request({
      url: `/data-resources/${resourceId}/permissions`,
      method: 'GET',
      params
    })
  },

  /**
   * 授予权限
   * @param resourceId 资源ID
   * @param data 权限数据
   */
  grantPermission(resourceId: number, data: PermissionGrantRequest): Promise<ApiResponse<DataResourcePermission>> {
    return request({
      url: `/data-resources/${resourceId}/permissions`,
      method: 'POST',
      data
    })
  },

  /**
   * 撤销权限
   * @param resourceId 资源ID
   * @param permissionId 权限ID
   */
  revokePermission(resourceId: number, permissionId: number): Promise<ApiResponse<void>> {
    return request({
      url: `/data-resources/${resourceId}/permissions/${permissionId}`,
      method: 'DELETE'
    })
  },

  /**
   * 更新权限
   * @param resourceId 资源ID
   * @param permissionId 权限ID
   * @param data 更新数据
   */
  updatePermission(resourceId: number, permissionId: number, data: {
    permission_type?: string
    expires_at?: string
    is_active?: boolean
  }): Promise<ApiResponse<DataResourcePermission>> {
    return request({
      url: `/data-resources/${resourceId}/permissions/${permissionId}`,
      method: 'PUT',
      data
    })
  },

  /**
   * 获取用户权限列表
   * @param params 查询参数
   */
  getUserPermissions(params?: {
    page?: number
    page_size?: number
    resource_type?: string
  }): Promise<ApiResponse<PaginatedResponse<DataResourcePermission>>> {
    return request({
      url: '/permissions/my',
      method: 'GET',
      params
    })
  }
}

/**
 * 统计相关API
 */
export const statisticsApi = {
  /**
   * 获取数据资源统计信息
   */
  getResourceStats(): Promise<ApiResponse<DataResourceStats>> {
    return request({
      url: '/statistics/resources',
      method: 'GET'
    })
  },

  /**
   * 获取访问统计
   * @param params 查询参数
   */
  getAccessStats(params?: {
    start_date?: string
    end_date?: string
    resource_id?: number
    group_by?: 'day' | 'week' | 'month'
  }): Promise<ApiResponse<any[]>> {
    return request({
      url: '/statistics/access',
      method: 'GET',
      params
    })
  },

  /**
   * 获取用户活跃度统计
   * @param params 查询参数
   */
  getUserActivityStats(params?: {
    start_date?: string
    end_date?: string
    group_by?: 'day' | 'week' | 'month'
  }): Promise<ApiResponse<any[]>> {
    return request({
      url: '/statistics/user-activity',
      method: 'GET',
      params
    })
  },

  /**
   * 获取热门资源统计
   * @param params 查询参数
   */
  getPopularResources(params?: {
    limit?: number
    period?: 'day' | 'week' | 'month' | 'year'
  }): Promise<ApiResponse<any[]>> {
    return request({
      url: '/statistics/popular-resources',
      method: 'GET',
      params
    })
  }
}

/**
 * 导出所有API
 */
export default {
  dataResource: dataResourceApi,
  category: categoryApi,
  tag: tagApi,
  permission: permissionApi,
  statistics: statisticsApi
}