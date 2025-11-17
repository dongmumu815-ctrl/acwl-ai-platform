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
      return get('/es/templates', params, { permission: 'data:es:templates:view' })
    } else if (type === 'sql') {
      // SQL模板使用 /sql/templates 端点
      const params: any = {}
      if (data_resource_id) params.data_resource_id = data_resource_id
      if (datasource_id) params.datasource_id = datasource_id
      params.isTemplate = true
      return get('/sql/templates', params, { permission: 'data:sql:templates:view' })
    } else {
      // 默认使用通用模板端点
      const params: any = {}
      if (datasource_id) params.datasource_id = datasource_id
      if (type) params.type = type
      return get('/templates/', params, { permission: 'data:templates:view' })
    }
  },

  /**
   * 获取模板详情
   */
  get(id: number): Promise<Template> {
    return get(`/templates/${id}`, undefined, { permission: 'data:templates:view' })
  },

  /**
   * 根据类型获取模板详情
   * @param id 模板ID
   * @param type 模板类型 ('sql' | 'es')
   */
  getByType(id: number, type: 'sql' | 'es'): Promise<Template> {
    if (type === 'sql') {
      return get(`/sql/templates/${id}`, undefined, { permission: 'data:sql:templates:view' })
    } else if (type === 'es') {
      return get(`/es/templates/${id}`, undefined, { permission: 'data:es:templates:view' })
    } else {
      return get(`/templates/${id}`, undefined, { permission: 'data:templates:view' })
    }
  },

  /**
   * 创建模板
   */
  create(data: Omit<Template, 'id' | 'created_at' | 'updated_at' | 'created_by'>): Promise<Template> {
    return post('/templates/', data, { permission: 'data:templates:create' })
  },

  /**
   * 更新模板
   */
  update(id: number, data: Partial<Omit<Template, 'id' | 'created_at' | 'updated_at' | 'created_by'>>): Promise<Template> {
    return put(`/templates/${id}`, data, { permission: 'data:templates:edit' })
  },

  /**
   * 删除模板
   */
  delete(id: number): Promise<void> {
    return del(`/templates/${id}`, { permission: 'data:templates:delete' })
  }
}