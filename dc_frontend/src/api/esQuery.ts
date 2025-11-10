import request from '@/utils/request'

// ES数据源接口
export interface ESDatasource {
  id: number
  name: string
  host: string
  port: number
  username?: string
  password?: string
  ssl?: boolean
  version?: string
  status?: string
}

// ES索引接口
export interface ESIndex {
  name: string
  docsCount: number
  storeSize: string
  health?: string
  status?: string
  primaryShards?: number
  replicaShards?: number
}

// ES字段映射接口
export interface ESField {
  name: string
  type: string
  comment?: string
  analyzer?: string
  searchAnalyzer?: string
  properties?: Record<string, ESField>
  format?: string
  index?: boolean
}

// ES查询请求接口
export interface ESQueryRequest {
  datasourceId: number
  index: string[]
  query: any
  size?: number
  from?: number
  sort?: any[]
  _source?: string[]
  timeout?: string
  aggs?: any
  // 深分页支持
  search_after?: any[]
  scroll?: string
  scroll_id?: string
}

// ES查询响应接口
export interface ESQueryResponse {
  took: number
  timed_out: boolean
  _shards: {
    total: number
    successful: number
    skipped: number
    failed: number
  }
  hits: {
    total: {
      value: number
      relation: string
    }
    max_score: number
    hits: Array<{
      _index: string
      _type: string
      _id: string
      _score: number
      _source: any
    }>
  }
  aggregations?: any
}

// ES查询统计接口
export interface ESQueryStats {
  totalHits: number
  took: number
  maxScore: number
  shardsInfo: {
    total: number
    successful: number
    failed: number
  }
}

/**
 * 获取ES数据源列表
 * @returns ES数据源列表
 */
export function getESDatasources(): Promise<{ data: ESDatasource[] }> {
  return request({
    url: '/datasources/',
    method: 'get',
    params: {
      datasource_type: 'elasticsearch'
    }
  })
}

/**
 * 获取ES数据源详情
 * @param id 数据源ID
 * @returns ES数据源详情
 */
export function getESDatasource(id: number): Promise<{ data: ESDatasource }> {
  return request({
    url: `/datasources/${id}/`,
    method: 'get'
  })
}

/**
 * 测试ES数据源连接
 * @param datasourceId 数据源ID
 * @returns 连接测试结果
 */
export function testESConnection(datasourceId: number): Promise<{ 
  data: { 
    success: boolean
    message: string
    clusterInfo?: any
    health?: any
  } 
}> {
  return request({
    url: `/datasources/${datasourceId}/test/`,
    method: 'post'
  })
}

/**
 * 获取ES索引列表
 * @param datasourceId 数据源ID
 * @returns ES索引列表
 */
export function getESIndices(datasourceId: number): Promise<{ data: ESIndex[] }> {
  return request({
    url: `/datasources/${datasourceId}/tables/`,
    method: 'get'
  })
}

/**
 * 获取ES索引详情
 * @param datasourceId 数据源ID
 * @param indexName 索引名称
 * @returns ES索引详情
 */
export function getESIndexInfo(datasourceId: number, indexName: string): Promise<{ 
  data: ESIndex & {
    mappings: any
    settings: any
    aliases: any
  }
}> {
  return request({
    url: `/datasources/${datasourceId}/tables/${indexName}/`,
    method: 'get'
  })
}

/**
 * 获取ES字段映射
 * @param datasourceId 数据源ID
 * @param indices 索引名称数组
 * @returns ES字段映射列表
 */
export function getESFieldMapping(datasourceId: number, indices: string[]): Promise<{ data: ESField[] }> {
  return request({
    url: `/es/fields/${datasourceId}`,
    method: 'get',
    params: {
      indices: indices.join(',')
    }
  });
}

/**
 * 执行ES查询
 * @param queryRequest ES查询请求
 * @returns ES查询响应
 */
export function executeESQuery(queryRequest: ESQueryRequest): Promise<{ 
  data: ESQueryResponse
  stats: ESQueryStats
  fieldMappings?: Record<string, { name: string; type: string; comment?: string; display_name: string }>
}> {
  return request({
    url: '/es/query',
    method: 'post',
    data: queryRequest
  })
}

/**
 * 验证ES查询DSL
 * @param datasourceId 数据源ID
 * @param query DSL查询对象
 * @returns 验证结果
 */
export function validateESQuery(datasourceId: number, query: any): Promise<{ 
  data: {
    valid: boolean
    error?: string
    explanation?: any
  }
}> {
  return request({
    url: `/datasources/${datasourceId}/validate/`,
    method: 'post',
    data: { query }
  })
}

/**
 * 解释ES查询执行计划
 * @param datasourceId 数据源ID
 * @param index 索引名称
 * @param query DSL查询对象
 * @returns 查询执行计划
 */
export function explainESQuery(datasourceId: number, index: string, query: any): Promise<{ 
  data: any
}> {
  return request({
    url: `/datasources/${datasourceId}/explain/`,
    method: 'post',
    data: {
      index,
      query
    }
  })
}

/**
 * 获取ES查询建议
 * @param datasourceId 数据源ID
 * @param index 索引名称
 * @param field 字段名称
 * @param text 输入文本
 * @returns 查询建议列表
 */
export function getESQuerySuggestions(datasourceId: number, index: string, field: string, text: string): Promise<{ 
  data: Array<{
    text: string
    score: number
    freq: number
  }>
}> {
  return request({
    url: `/datasources/${datasourceId}/suggest/`,
    method: 'post',
    data: {
      index,
      field,
      text
    }
  })
}

/**
 * 获取ES聚合查询结果
 * @param datasourceId 数据源ID
 * @param indices 索引名称数组
 * @param aggregations 聚合查询配置
 * @returns 聚合查询结果
 */
export function getESAggregations(
  datasourceId: number,
  indices: string[],
  aggregations: any,
  query?: any,
  timeout?: string
): Promise<{ 
  data: {
    aggregations: any
    took: number
    hits: {
      total: {
        value: number
      }
    }
  }
}> {
  return request({
    url: '/es/aggregations',
    method: 'post',
    data: {
      datasourceId,
      indices,
      aggregations,
      query,
      timeout
    }
  })
}

/**
 * 导出ES查询结果
 * @param queryRequest ES查询请求
 * @param format 导出格式 (csv, json, excel)
 * @returns 导出文件流
 */
export function exportESQueryResult(queryRequest: ESQueryRequest, format: 'csv' | 'json' | 'excel' = 'csv'): Promise<Blob> {
  return request({
    url: '/es/export',
    method: 'post',
    data: {
      ...queryRequest,
      format
    },
    responseType: 'blob'
  })
}

/**
 * 保存ES查询模板
 * @param template 查询模板
 * @returns 保存结果
 */
export function saveESQueryTemplate(template: {
  name: string
  description?: string
  datasourceId: number
  dataResourceId?: number
  indices: string[]
  query: any
  tags?: string[]
  conditionLockTypes?: Record<string, string>
  conditionRanges?: Record<string, { min: string; max: string }>
  allowedOperators?: Record<string, string[]>
}): Promise<{ data: { id: number } }> {
  return request({
    url: '/es/templates',
    method: 'post',
    data: template
  })
}

/**
 * 获取ES查询模板列表
 * @param datasourceId 数据源ID（可选）
 * @returns 查询模板列表
 */
export function getESQueryTemplates(datasourceId?: number): Promise<{ 
  data: Array<{
    id: number
    name: string
    description: string
    datasourceId: number
    indices: string[]
    query: any
    tags: string[]
    createdAt: string
    updatedAt: string
    conditionLockTypes?: Record<string, string>
    conditionRanges?: Record<string, { min: string; max: string }>
    allowedOperators?: Record<string, string[]>
  }>
}> {
  return request({
    url: '/es/templates',
    method: 'get',
    params: datasourceId ? { datasourceId } : {}
  })
}

/**
 * 更新ES查询模板
 * @param templateId 模板ID
 * @param template 查询模板数据
 * @returns 更新结果
 */
export function updateESQueryTemplate(templateId: number, template: {
  name: string
  description?: string
  datasourceId: number
  indices: string[]
  query: any
  tags?: string[]
  conditionLockTypes?: Record<string, string>
  conditionRanges?: Record<string, { min: string; max: string }>
  allowedOperators?: Record<string, string[]>
}): Promise<{ data: { id: number; name: string; description: string; isTemplate: boolean } }> {
  return request({
    url: `/es/templates/${templateId}`,
    method: 'put',
    data: template
  })
}

/**
 * 删除ES查询模板
 * @param templateId 模板ID
 * @returns 删除结果
 */
export function deleteESQueryTemplate(templateId: number): Promise<{ data: { success: boolean } }> {
  return request({
    url: `/es/templates/${templateId}`,
    method: 'delete'
  })
}

/**
 * 获取ES集群统计信息
 * @param datasourceId 数据源ID
 * @returns 集群统计信息
 */
export function getESClusterStats(datasourceId: number): Promise<{ 
  data: {
    clusterName: string
    status: string
    nodeCount: number
    dataNodeCount: number
    activeShards: number
    relocatingShards: number
    initializingShards: number
    unassignedShards: number
    indices: {
      count: number
      docsCount: number
      storeSize: string
    }
  }
}> {
  return request({
    url: `/datasources/${datasourceId}/stats/`,
    method: 'get'
  })
}

/**
 * 获取ES索引统计信息
 * @param datasourceId 数据源ID
 * @param indexName 索引名称
 * @returns 索引统计信息
 */
export function getESIndexStats(datasourceId: number, indexName: string): Promise<{ 
  data: {
    health: string
    status: string
    index: string
    uuid: string
    pri: number
    rep: number
    docsCount: number
    docsDeleted: number
    storeSize: string
    priStoreSize: string
  }
}> {
  return request({
    url: `/datasources/${datasourceId}/tables/${indexName}/stats/`,
    method: 'get'
  })
}
