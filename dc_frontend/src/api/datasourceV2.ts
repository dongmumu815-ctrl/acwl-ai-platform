import { get, post, put, del } from '@/utils/request'

// 简化的分页响应类型
export interface PaginatedResponse<T> {
  items: T[]
  total: number
}

// 数据源类型枚举
export enum DatasourceType {
  MYSQL = 'mysql',
  DORIS = 'doris',
  ORACLE = 'oracle',
  POSTGRESQL = 'postgresql',
  SQLSERVER = 'sqlserver',
  CLICKHOUSE = 'clickhouse',
  MONGODB = 'mongodb',
  REDIS = 'redis',
  ELASTICSEARCH = 'elasticsearch'
}

// 数据源状态枚举
export enum DatasourceStatus {
  CONNECTED = 'connected',
  DISCONNECTED = 'disconnected',
  ERROR = 'error',
  UNKNOWN = 'unknown'
}

// 数据源接口类型定义
export interface Datasource {
  id: number
  name: string
  datasource_type: DatasourceType
  host: string
  port: number
  database_name: string
  username: string
  description?: string
  connection_params?: Record<string, any>
  pool_config?: Record<string, any>
  is_enabled: boolean
  status: DatasourceStatus
  last_test_time?: string
  created_at: string
  updated_at: string
}

// 数据源创建/更新表单类型
export interface DatasourceForm {
  name: string
  datasource_type: DatasourceType
  host: string
  port: number
  database: string
  username: string
  password: string
  description?: string
  connection_params?: Record<string, any>
  pool_config?: Record<string, any>
  is_enabled?: boolean
}

// 数据源查询参数类型
export interface DatasourceQueryParams {
  page?: number
  size?: number
  search?: string
  name?: string
  datasource_type?: DatasourceType
  status?: DatasourceStatus
  is_enabled?: boolean
}

// 数据源查询接口
export interface DatasourceQuery {
  query: string
  limit?: number
}

// 批量操作接口
export interface BatchOperationData {
  ids: number[]
  action: 'enable' | 'disable' | 'delete'
}

// 测试连接参数接口
export interface TestConnectionParams {
  timeout?: number
}

// 统计信息接口
export interface DatasourceStats {
  total_count: number
  active_count: number
  inactive_count?: number
  error_count: number
  recent_test_success_rate: number
  type_distribution?: Record<string, number>
}

// 数据源API接口（兼容 frontend 视图的调用方式）
export const datasourceApi = {
  /** 获取数据源列表 */
  getDatasources(params?: DatasourceQueryParams) {
    return get<PaginatedResponse<Datasource>>('/datasources/', params, { permission: 'data:datasource:view' }).then(res => {
      // 保留 ApiResponse 结构，确保视图能读取 response.data.items
      const total = res?.data?.total ?? 0
      return { ...res, total }
    })
  },

  /** 获取数据源详情 */
  getDatasource(datasourceId: number) {
    return get<Datasource>(`/datasources/${datasourceId}`, undefined, { permission: 'data:datasource:view' })
  },

  /** 创建数据源（字段转换以匹配后端） */
  createDatasource(data: DatasourceForm) {
    const { database, ...rest } = data
    const backendData = { ...rest, database_name: database }
    return post<Datasource>('/datasources/', backendData, { permission: 'data:datasource:create' })
  },

  /** 更新数据源（字段转换以匹配后端） */
  updateDatasource(datasourceId: number, data: Partial<DatasourceForm>) {
    const { database, ...rest } = data
    const backendData = database !== undefined ? { ...rest, database_name: database } : rest
    return put<{ message: string }>(`/datasources/${datasourceId}`, backendData, { permission: 'data:datasource:update' })
  },

  /** 删除数据源 */
  deleteDatasource(datasourceId: number) {
    return del<{ message: string }>(`/datasources/${datasourceId}`, { permission: 'data:datasource:delete' })
  },

  /** 临时测试数据源连接（不保存） */
  testTempDatasourceConnection(datasourceData: DatasourceForm, params?: TestConnectionParams) {
    const { database, ...rest } = datasourceData
    const backendData = { ...rest, database_name: database }
    return post<{ success: boolean; message: string; response_time?: number; test_time?: string; connection_info?: any; error_details?: string }>(
      '/datasources/test-temp',
      { datasource_data: backendData, ...params },
      { permission: 'data:datasource:test' }
    ).then(res => res.data)
  },

  /** 测试数据源连接 */
  testDatasourceConnection(datasourceId: number, params?: TestConnectionParams) {
    return post<{ success: boolean; message: string; response_time?: number; test_time?: string; connection_info?: any; error_details?: string }>(
      `/datasources/${datasourceId}/test`,
      params,
      { permission: 'data:datasource:test' }
    ).then(res => res.data)
  },

  /** 启用数据源 */
  enableDatasource(datasourceId: number) {
    return post<{ message: string }>(`/datasources/${datasourceId}/enable`, undefined, { permission: 'data:datasource:update' })
  },

  /** 停用数据源 */
  disableDatasource(datasourceId: number) {
    return post<{ message: string }>(`/datasources/${datasourceId}/disable`, undefined, { permission: 'data:datasource:update' })
  },

  /** 获取数据源统计信息 */
  getDatasourceStats() {
    return get<DatasourceStats>('/datasources/stats/overview', undefined, { permission: 'data:datasource:stats:view' }).then(res => res.data?.data ?? res.data)
  },

  /** 获取数据源测试日志 */
  getDatasourceTestLogs(datasourceId: number, params?: { page?: number; size?: number }) {
    return get<PaginatedResponse<any>>(`/datasources/${datasourceId}/test-logs`, params, { permission: 'data:datasource:logs:view' })
  },

  /** 获取数据源配置模板 */
  getDatasourceTemplates(datasourceType?: DatasourceType) {
    const params = datasourceType ? { datasource_type: datasourceType } : {}
    return get<Record<string, any>>('/datasources/templates/', params, { permission: 'data:datasource:templates:view' }).then(res => res.data?.data ?? res.data)
  },

  /** 获取数据源连接信息 */
  getDatasourceConnectionInfo(datasourceId: number) {
    return get<Record<string, any>>(`/datasources/${datasourceId}/connection-info`, undefined, { permission: 'data:datasource:connection:view' }).then(res => res.data?.data ?? res.data)
  },

  /** 执行数据源查询 */
  executeDatasourceQuery(datasourceId: number, data: DatasourceQuery) {
    return post<{ columns: string[]; rows: any[][]; total: number }>(`/datasources/${datasourceId}/query`, data, { permission: 'data:datasource:query' }).then(res => res.data?.data ?? res.data)
  }
}

// 便捷导出
export const getDatasources = datasourceApi.getDatasources
export const getDatasource = datasourceApi.getDatasource
export const createDatasource = datasourceApi.createDatasource
export const updateDatasource = datasourceApi.updateDatasource
export const deleteDatasource = datasourceApi.deleteDatasource
export const testTempDatasourceConnection = datasourceApi.testTempDatasourceConnection
export const testDatasourceConnection = datasourceApi.testDatasourceConnection
export const enableDatasource = datasourceApi.enableDatasource
export const disableDatasource = datasourceApi.disableDatasource
export const getDatasourceStats = datasourceApi.getDatasourceStats
export const getDatasourceTestLogs = datasourceApi.getDatasourceTestLogs
export const getDatasourceTemplates = datasourceApi.getDatasourceTemplates
export const getDatasourceConnectionInfo = datasourceApi.getDatasourceConnectionInfo
export const executeDatasourceQuery = datasourceApi.executeDatasourceQuery

// 类型选项与工具函数
export interface DatasourceTypeOption {
  value: DatasourceType
  label: string
  icon: string
}

export interface DatasourceStatusOption {
  value: DatasourceStatus
  label: string
  type: 'success' | 'danger' | 'warning' | 'info'
}

export const DATASOURCE_TYPES: DatasourceTypeOption[] = [
  { value: DatasourceType.MYSQL, label: 'MySQL', icon: 'mysql' },
  { value: DatasourceType.DORIS, label: 'Apache Doris', icon: 'doris' },
  { value: DatasourceType.ORACLE, label: 'Oracle', icon: 'oracle' },
  { value: DatasourceType.POSTGRESQL, label: 'PostgreSQL', icon: 'postgresql' },
  { value: DatasourceType.SQLSERVER, label: 'SQL Server', icon: 'sqlserver' },
  { value: DatasourceType.CLICKHOUSE, label: 'ClickHouse', icon: 'clickhouse' },
  { value: DatasourceType.MONGODB, label: 'MongoDB', icon: 'mongodb' },
  { value: DatasourceType.REDIS, label: 'Redis', icon: 'redis' },
  { value: DatasourceType.ELASTICSEARCH, label: 'Elasticsearch', icon: 'elasticsearch' }
]

export const DATASOURCE_STATUS_OPTIONS: DatasourceStatusOption[] = [
  { value: DatasourceStatus.CONNECTED, label: '已连接', type: 'success' },
  { value: DatasourceStatus.DISCONNECTED, label: '未连接', type: 'danger' },
  { value: DatasourceStatus.ERROR, label: '连接错误', type: 'warning' },
  { value: DatasourceStatus.UNKNOWN, label: '未知', type: 'info' }
]

export function getDatasourceTypeLabel(type: DatasourceType): string {
  const found = DATASOURCE_TYPES.find(t => t.value === type)
  return found?.label || String(type)
}

export function getDatasourceStatusConfig(status: DatasourceStatus): DatasourceStatusOption {
  const found = DATASOURCE_STATUS_OPTIONS.find(s => s.value === status)
  return (
    found || { value: DatasourceStatus.UNKNOWN, label: '未知', type: 'info' }
  )
}

export function getDefaultPort(type: DatasourceType): number {
  const map: Record<DatasourceType, number> = {
    [DatasourceType.MYSQL]: 3306,
    [DatasourceType.DORIS]: 9030,
    [DatasourceType.ORACLE]: 1521,
    [DatasourceType.POSTGRESQL]: 5432,
    [DatasourceType.SQLSERVER]: 1433,
    [DatasourceType.CLICKHOUSE]: 9000,
    [DatasourceType.MONGODB]: 27017,
    [DatasourceType.REDIS]: 6379,
    [DatasourceType.ELASTICSEARCH]: 9200
  }
  return map[type] || 3306
}

export function getConnectionParamsTemplate(type: DatasourceType): Record<string, any> {
  const templates: Record<DatasourceType, Record<string, any>> = {
    [DatasourceType.MYSQL]: { charset: 'utf8mb4' },
    [DatasourceType.POSTGRESQL]: { sslmode: 'disable' },
    [DatasourceType.ORACLE]: {},
    [DatasourceType.SQLSERVER]: {},
    [DatasourceType.CLICKHOUSE]: {},
    [DatasourceType.MONGODB]: {},
    [DatasourceType.REDIS]: {},
    [DatasourceType.DORIS]: {},
    [DatasourceType.ELASTICSEARCH]: {}
  }
  return templates[type] || {}
}

export function getPoolConfigTemplate(type: DatasourceType): Record<string, any> {
  return {
    pool_size: 5,
    max_overflow: 10,
    pool_timeout: 30,
    pool_recycle: 3600
  }
}