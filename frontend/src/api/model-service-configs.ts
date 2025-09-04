import request from '@/utils/request'

// 模型服务配置相关接口
export const modelServiceConfigApi = {
  /**
   * 获取配置列表
   * @param params 查询参数
   */
  getConfigs(params?: {
    page?: number
    size?: number
    search?: string
    provider?: string
    is_active?: boolean
    sort_by?: string
    sort_order?: 'asc' | 'desc'
  }) {
    return request({
      url: '/model-service-configs/',
      method: 'get',
      params
    })
  },

  /**
   * 获取配置详情
   * @param id 配置ID
   */
  getConfig(id: number) {
    return request({
      url: `/model-service-configs/${id}`,
      method: 'get'
    })
  },

  /**
   * 创建配置
   * @param data 配置数据
   */
  createConfig(data: {
    name: string
    display_name: string
    provider: string
    model_type?: string
    model_name: string
    api_endpoint: string
    api_key: string
    max_tokens?: number
    temperature?: number
    timeout?: number
    is_active?: boolean
    is_default?: boolean
    description?: string
    headers?: Array<{ key: string; value: string }>
    extra_params?: Record<string, any>
  }) {
    return request({
      url: '/model-service-configs/',
      method: 'post',
      data
    })
  },

  /**
   * 更新配置
   * @param id 配置ID
   * @param data 更新数据
   */
  updateConfig(id: number, data: {
    name?: string
    display_name?: string
    provider?: string
    model_type?: string
    model_name?: string
    api_endpoint?: string
    api_key?: string
    max_tokens?: number
    temperature?: number
    timeout?: number
    is_active?: boolean
    is_default?: boolean
    description?: string
    headers?: Array<{ key: string; value: string }>
    extra_params?: Record<string, any>
  }) {
    return request({
      url: `/model-service-configs/${id}`,
      method: 'put',
      data
    })
  },

  /**
   * 删除配置
   * @param id 配置ID
   */
  deleteConfig(id: number) {
    return request({
      url: `/model-service-configs/${id}`,
      method: 'delete'
    })
  },

  /**
   * 切换配置状态
   * @param id 配置ID
   * @param is_active 是否激活
   */
  toggleStatus(id: number, is_active: boolean) {
    return request({
      url: `/model-service-configs/${id}/toggle-status`,
      method: 'patch',
      data: { is_active }
    })
  },

  /**
   * 获取Agent可用的模型配置列表
   */
  getAgentConfigs() {
    return request({
      url: '/model-service-configs/available-for-agents',
      method: 'get'
    })
  },

  /**
   * 获取统计信息
   */
  getStats() {
    return request({
      url: '/model-service-configs/stats',
      method: 'get'
    })
  },

  /**
   * 测试配置
   * @param data 测试数据
   */
  testConfig(data: {
    config_id?: number
    provider?: string
    model_name?: string
    api_endpoint?: string
    api_key?: string
    max_tokens?: number
    temperature?: number
    timeout?: number
    headers?: Array<{ key: string; value: string }>
    extra_params?: Record<string, any>
    test_message?: string
  }) {
    return request({
      url: '/model-service-configs/test',
      method: 'post',
      data
    })
  },

  /**
   * 获取支持的服务提供商列表
   */
  getProviders() {
    return request({
      url: '/model-service-configs/providers',
      method: 'get'
    })
  },

  /**
   * 获取Ollama模型列表
   * @param apiEndpoint Ollama API端点
   */
  getOllamaModels(apiEndpoint: string) {
    return request({
      url: '/model-service-configs/ollama-models',
      method: 'get',
      params: {
        api_endpoint: apiEndpoint
      }
    })
  }
}

// 导出类型定义
export interface ModelServiceConfig {
  id: number
  name: string
  display_name: string
  provider: string
  model_type?: string
  model_name: string
  api_endpoint: string
  api_key: string
  max_tokens: number
  temperature: number
  timeout: number
  is_active: boolean
  is_default: boolean
  description?: string
  headers?: Array<{ key: string; value: string }>
  extra_params?: Record<string, any>
  created_at: string
  updated_at: string
}

export interface ModelServiceConfigListResponse {
  items: ModelServiceConfig[]
  total: number
  page: number
  size: number
  pages: number
}

export interface ModelServiceConfigStats {
  total_count: number
  active_count: number
  inactive_count: number
  provider_stats: Record<string, number>
}

export interface ModelServiceConfigTestResult {
  success: boolean
  response_content?: string
  error?: string
  error_details?: string
  response_time?: number
  status_code?: number
  model?: string
  token_usage?: {
    prompt_tokens?: number
    completion_tokens?: number
    total_tokens?: number
  }
  raw_response?: any
  request_info?: {
    url: string
    method: string
    headers?: Record<string, string>
    body?: any
  }
}

export interface ServiceProvider {
  value: string
  label: string
  description?: string
  default_endpoint?: string
  default_model?: string
}