import { request } from '@/utils/request'
import type { PaginatedResponse } from '@/types/common'

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
  inactive_count: number
  error_count: number
  recent_test_success_rate: number
  type_distribution: Record<string, number>
}

// 数据源API接口
export const datasourceApi = {
  /**
   * 获取数据源列表
   * @param params 查询参数
   * @returns 分页的数据源列表
   */
  getDatasources(params?: DatasourceQueryParams) {
    return request.get<PaginatedResponse<Datasource>>('/datasources/', { params })
  },

  /**
   * 获取数据源详情
   * @param datasourceId 数据源ID
   * @returns 数据源详情
   */
  getDatasource(datasourceId: number) {
    return request.get<Datasource>(`/datasources/${datasourceId}`)
  },

  /**
   * 创建数据源
   * @param data 数据源数据
   * @returns 创建结果
   */
  createDatasource(data: DatasourceForm) {
    // 转换字段名以匹配后端模型
    const { database, ...rest } = data
    const backendData = {
      ...rest,
      database_name: database
    }
    return request.post<Datasource>('/datasources/', backendData)
  },

  /**
   * 更新数据源
   * @param datasourceId 数据源ID
   * @param data 更新数据
   * @returns 更新结果
   */
  updateDatasource(datasourceId: number, data: Partial<DatasourceForm>) {
    // 转换字段名以匹配后端模型
    const { database, ...rest } = data
    const backendData = database !== undefined ? {
      ...rest,
      database_name: database
    } : rest
    return request.put<{ message: string }>(`/datasources/${datasourceId}`, backendData)
  },

  /**
   * 删除数据源
   * @param datasourceId 数据源ID
   * @returns 删除结果
   */
  deleteDatasource(datasourceId: number) {
    return request.delete<{ message: string }>(`/datasources/${datasourceId}`)
  },

  /**
   * 临时测试数据源连接（不保存数据源）
   * @param datasourceData 数据源配置
   * @param params 测试参数
   * @returns 测试结果
   */
  testTempDatasourceConnection(datasourceData: DatasourceForm, params?: TestConnectionParams) {
    // 转换字段名以匹配后端模型
    const { database, ...rest } = datasourceData
    const backendData = {
      ...rest,
      database_name: database
    }
    
    return request.post<{ success: boolean; message: string; response_time?: number; test_time?: string; connection_info?: any; error_details?: string }>('/datasources/test-temp', {
      datasource_data: backendData,
      ...params
    })
  },

  /**
   * 测试数据源连接
   * @param datasourceId 数据源ID
   * @param params 测试参数
   * @returns 测试结果
   */
  testDatasourceConnection(datasourceId: number, params?: TestConnectionParams) {
    return request.post<{ success: boolean; message: string; response_time?: number; test_time?: string; connection_info?: any; error_details?: string }>(`/datasources/${datasourceId}/test`, params)
  },

  /**
   * 启用数据源
   * @param datasourceId 数据源ID
   * @returns 操作结果
   */
  enableDatasource(datasourceId: number) {
    return request.post<{ message: string }>(`/datasources/${datasourceId}/enable`)
  },

  /**
   * 停用数据源
   * @param datasourceId 数据源ID
   * @returns 操作结果
   */
  disableDatasource(datasourceId: number) {
    return request.post<{ message: string }>(`/datasources/${datasourceId}/disable`)
  },

  /**
   * 获取数据源统计信息
   * @returns 统计数据
   */
  getDatasourceStats() {
    return request.get<DatasourceStats>('/datasources/stats/overview')
  },

  /**
   * 获取数据源测试日志
   * @param datasourceId 数据源ID
   * @param params 查询参数
   * @returns 测试日志列表
   */
  getDatasourceTestLogs(datasourceId: number, params?: { page?: number; size?: number }) {
    return request.get<PaginatedResponse<any>>(`/datasources/${datasourceId}/test-logs`, { params })
  },

  /**
   * 获取数据源配置模板
   * @param datasourceType 数据源类型（可选）
   * @returns 配置模板
   */
  getDatasourceTemplates(datasourceType?: DatasourceType) {
    const params = datasourceType ? { datasource_type: datasourceType } : {}
    return request.get<Record<string, any>>('/datasources/templates/', { params })
  },

  /**
   * 获取数据源连接信息
   * @param datasourceId 数据源ID
   * @returns 连接信息
   */
  getDatasourceConnectionInfo(datasourceId: number) {
    return request.get<Record<string, any>>(`/datasources/${datasourceId}/connection-info`)
  },

  /**
   * 执行数据源查询
   * @param datasourceId 数据源ID
   * @param data 查询数据
   * @returns 查询结果
   */
  executeDatasourceQuery(datasourceId: number, data: DatasourceQuery) {
    return request.post<{ columns: string[]; rows: any[][]; total: number }>(`/datasources/${datasourceId}/query`, data)
  },

  /**
   * 批量操作数据源
   * @param data 批量操作数据
   * @returns 操作结果
   */
  batchOperateDatasources(data: BatchOperationData) {
    return request.post<{ message: string; success_count: number; failed_count: number }>('/datasources/batch', data)
  }
}

// 兼容性导出（保持向后兼容）
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

// 数据源类型选项接口
export interface DatasourceTypeOption {
  value: DatasourceType
  label: string
  icon: string
}

// 数据源状态选项接口
export interface DatasourceStatusOption {
  value: DatasourceStatus
  label: string
  type: 'success' | 'danger' | 'warning' | 'info'
}

// 数据源类型选项
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

// 数据源状态选项
export const DATASOURCE_STATUS_OPTIONS: DatasourceStatusOption[] = [
  { value: DatasourceStatus.CONNECTED, label: '已连接', type: 'success' },
  { value: DatasourceStatus.DISCONNECTED, label: '未连接', type: 'danger' },
  { value: DatasourceStatus.ERROR, label: '连接错误', type: 'warning' },
  { value: DatasourceStatus.UNKNOWN, label: '未知', type: 'info' }
]

/**
 * 获取数据源类型标签
 * @param type 数据源类型
 * @returns 类型标签
 */
export function getDatasourceTypeLabel(type: DatasourceType): string {
  const typeOption = DATASOURCE_TYPES.find(item => item.value === type)
  return typeOption ? typeOption.label : type
}

/**
 * 获取数据源状态配置
 * @param status 状态值
 * @returns 状态配置
 */
export function getDatasourceStatusConfig(status: DatasourceStatus): DatasourceStatusOption {
  const statusOption = DATASOURCE_STATUS_OPTIONS.find(item => item.value === status)
  return statusOption || { value: status, label: status, type: 'info' }
}

/**
 * 获取数据源默认端口
 * @param type 数据源类型
 * @returns 默认端口
 */
export function getDefaultPort(type: DatasourceType): number {
  const portMap: Record<DatasourceType, number> = {
    [DatasourceType.MYSQL]: 3306,
    [DatasourceType.DORIS]: 9030,
    [DatasourceType.ORACLE]: 1521,
    [DatasourceType.POSTGRESQL]: 5432,
    [DatasourceType.SQLSERVER]: 1433,
    [DatasourceType.CLICKHOUSE]: 8123,
    [DatasourceType.MONGODB]: 27017,
    [DatasourceType.REDIS]: 6379,
    [DatasourceType.ELASTICSEARCH]: 9200
  }
  return portMap[type] || 3306
}

/**
 * 获取数据源连接参数模板
 * @param type 数据源类型
 * @returns 连接参数模板
 */
export function getConnectionParamsTemplate(type: DatasourceType): Record<string, any> {
  const templates = {
    [DatasourceType.MYSQL]: {
      charset: 'utf8mb4',
      autocommit: true,
      connect_timeout: 10,
      read_timeout: 30,
      write_timeout: 30
    },
    [DatasourceType.DORIS]: {
      charset: 'utf8mb4',
      autocommit: true,
      connect_timeout: 10,
      read_timeout: 30
    },
    [DatasourceType.ORACLE]: {
      encoding: 'UTF-8',
      threaded: true,
      connect_timeout: 10
    },
    [DatasourceType.POSTGRESQL]: {
      sslmode: 'prefer',
      connect_timeout: 10,
      application_name: 'acwl-ai-data'
    },
    [DatasourceType.SQLSERVER]: {
      driver: 'ODBC Driver 17 for SQL Server',
      encrypt: true,
      trust_server_certificate: true,
      connect_timeout: 10
    },
    [DatasourceType.CLICKHOUSE]: {
      secure: false,
      verify: false,
      compress: true,
      connect_timeout: 10
    },
    [DatasourceType.MONGODB]: {
      authSource: 'admin',
      serverSelectionTimeoutMS: 10000,
      connectTimeoutMS: 10000
    },
    [DatasourceType.REDIS]: {
      decode_responses: true,
      socket_timeout: 10,
      socket_connect_timeout: 10
    },
    [DatasourceType.ELASTICSEARCH]: {
      timeout: 10,
      max_retries: 3,
      retry_on_timeout: true
    }
  }
  return templates[type] || {}
}

/**
 * 获取连接池配置模板
 * @param type 数据源类型
 * @returns 连接池配置模板
 */
export function getPoolConfigTemplate(type: DatasourceType): Record<string, any> {
  const templates = {
    [DatasourceType.MYSQL]: {
      pool_size: 10,
      max_overflow: 20,
      pool_timeout: 30,
      pool_recycle: 3600,
      pool_pre_ping: true
    },
    [DatasourceType.DORIS]: {
      pool_size: 10,
      max_overflow: 20,
      pool_timeout: 30,
      pool_recycle: 3600
    },
    [DatasourceType.ORACLE]: {
      pool_size: 5,
      max_overflow: 10,
      pool_timeout: 30,
      pool_recycle: 3600
    },
    [DatasourceType.POSTGRESQL]: {
      pool_size: 10,
      max_overflow: 20,
      pool_timeout: 30,
      pool_recycle: 3600
    },
    [DatasourceType.SQLSERVER]: {
      pool_size: 10,
      max_overflow: 20,
      pool_timeout: 30,
      pool_recycle: 3600
    },
    [DatasourceType.CLICKHOUSE]: {
      pool_size: 10,
      max_overflow: 20,
      pool_timeout: 30
    },
    [DatasourceType.MONGODB]: {
      maxPoolSize: 10,
      minPoolSize: 1,
      maxIdleTimeMS: 30000
    },
    [DatasourceType.REDIS]: {
      max_connections: 10,
      retry_on_timeout: true
    },
    [DatasourceType.ELASTICSEARCH]: {
      maxsize: 10,
      timeout: 30
    }
  }
  return templates[type] || {}
}