import { get, post, put, del } from '@/utils/request'

/**
 * 模板类型定义
 */
export interface Template {
  id: number
  name: string
  description?: string
  type: 'sql' | 'es'
  datasource_id: number
  query_content: string
  dynamic_params?: Record<string, any>
  created_at: string
  updated_at: string
  created_by: number
  creator?: {
    id: number
    username: string
    nickname?: string
  }
  datasource?: {
    id: number
    name: string
    type: string
  }
}

/**
 * 模板API
 */
export const templateApi = {
  /**
   * 获取模板列表
   * 根据类型调用不同的API端点
   */
  list(datasource_id?: number, type?: 'sql' | 'es', data_resource_id?: number, indices?: string[]): Promise<Template[]> {
    if (type === 'es') {
      // ES模板使用 /es/templates 端点
      const params: any = {}
      if (datasource_id) params.datasource_id = datasource_id
      if (data_resource_id) params.data_resource_id = data_resource_id
      if (indices && indices.length > 0) params.indices = indices.join(',')
      return get('/es/templates', params)
    } else if (type === 'sql') {
      // SQL模板使用 /sql/templates 端点
      const params: any = {}
      if (data_resource_id) params.data_resource_id = data_resource_id
      if (datasource_id) params.datasource_id = datasource_id
      params.isTemplate = true
      return get('/sql/templates', params)
    } else {
      // 默认使用通用模板端点
      const params: any = {}
      if (datasource_id) params.datasource_id = datasource_id
      if (type) params.type = type
      return get('/templates/', params)
    }
  },

  /**
   * 获取模板详情
   */
  get(id: number): Promise<Template> {
    return get(`/templates/${id}`)
  },

  /**
   * 根据类型获取模板详情
   * @param id 模板ID
   * @param type 模板类型 ('sql' | 'es')
   */
  getByType(id: number, type: 'sql' | 'es'): Promise<Template> {
    if (type === 'sql') {
      return get(`/sql/templates/${id}`)
    } else if (type === 'es') {
      return get(`/es/templates/${id}`)
    } else {
      return get(`/templates/${id}`)
    }
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
  delete(id: number): Promise<void> {
    return del(`/templates/${id}`)
  }
}