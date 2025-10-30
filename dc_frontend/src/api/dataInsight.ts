import axios from 'axios'
import type { AxiosInstance, AxiosResponse } from 'axios'
import { ElMessage } from 'element-plus'
import { DATA_INSIGHT_CONFIG } from '@/config/external-apis'

// 数据源接口类型定义
export interface DataSource {
  id: number
  name: string
  db_type: string
  host: string
  port: number
  database_name: string
  username: string
  oracle_connection_type?: string
  created_at: string
  updated_at: string
}

// 表信息接口类型定义
export interface TableInfo {
  table_name: string
  table_type: string
  table_comment?: string
}

// 表详情接口类型定义
export interface TableDetail {
  table_name: string
  table_type: string
  table_comment?: string
  row_count?: number
  columns: TableColumn[]
}

// 表列信息接口类型定义
export interface TableColumn {
  column_name: string
  data_type: string
  is_nullable: boolean
  is_primary_key: boolean
  column_default?: string
  column_comment?: string
}

// 字段更新请求类型定义
export interface FieldUpdateRequest {
  datasource_id: number
  table_name: string
  schema?: string
  column_name: string
  column_comment?: string
  column_default?: string
  is_nullable?: boolean
}

// 字段更新响应类型定义
export interface FieldUpdateResponse {
  success: boolean
  message: string
}

// 模式信息接口类型定义
export interface SchemaInfo {
  username: string
}

// 连接测试请求类型定义
export interface ConnectionTestRequest {
  db_type: string
  host: string
  port: number
  database_name: string
  username: string
  password: string
  oracle_connection_type?: string
}

// 连接测试响应类型定义
export interface ConnectionTestResponse {
  success: boolean
  message: string
}

// 表数据请求类型定义
export interface TableDataRequest {
  datasource_id: number
  table_name: string
  schema?: string
  limit?: number
  offset?: number
}

// SQL执行请求类型定义
export interface SQLExecuteRequest {
  datasource_id: number
  sql: string
  schema?: string
}

// SQL执行响应类型定义
export interface SQLExecuteResponse {
  success: boolean
  data: any[]
  columns: string[]
  row_count: number
  execution_time: number
  message?: string
}

class DataInsightAPI {
  private api: AxiosInstance

  constructor() {
    this.api = axios.create({
      baseURL: DATA_INSIGHT_CONFIG.baseURL,
      timeout: DATA_INSIGHT_CONFIG.timeout,
      headers: {
        'Content-Type': 'application/json'
      }
    })

    // 请求拦截器
    this.api.interceptors.request.use(
      (config) => {
        // 这里可以添加认证token等
        return config
      },
      (error) => {
        return Promise.reject(error)
      }
    )

    // 响应拦截器
    this.api.interceptors.response.use(
      (response: AxiosResponse) => {
        return response.data
      },
      (error) => {
        const message = error.response?.data?.detail || error.message || '请求失败'
        ElMessage.error(`DataAInsint API错误: ${message}`)
        return Promise.reject(error)
      }
    )
  }

  // 数据源相关API
  datasource = {
    // 测试连接
    testConnection: (data: ConnectionTestRequest): Promise<ConnectionTestResponse> =>
      this.api.post(DATA_INSIGHT_CONFIG.endpoints.datasource.testConnection, data),

    // 获取所有数据源
    getList: (): Promise<DataSource[]> =>
      this.api.get(DATA_INSIGHT_CONFIG.endpoints.datasource.getList),

    // 获取指定数据源
    getById: (id: number): Promise<DataSource> =>
      this.api.get(DATA_INSIGHT_CONFIG.endpoints.datasource.getById(id)),

    // 创建数据源
    create: (data: Omit<DataSource, 'id' | 'created_at' | 'updated_at'>): Promise<DataSource> =>
      this.api.post(DATA_INSIGHT_CONFIG.endpoints.datasource.create, data),

    // 更新数据源
    update: (id: number, data: Partial<DataSource>): Promise<DataSource> =>
      this.api.put(DATA_INSIGHT_CONFIG.endpoints.datasource.update(id), data),

    // 删除数据源
    delete: (id: number): Promise<void> =>
      this.api.delete(DATA_INSIGHT_CONFIG.endpoints.datasource.delete(id))
  }

  // 数据探索相关API
  explorer = {
    // 获取模式列表
    getSchemas: (datasourceId: number): Promise<SchemaInfo[]> =>
      this.api.get(DATA_INSIGHT_CONFIG.endpoints.explorer.getSchemas(datasourceId)),

    // 获取表列表
    getTables: (datasourceId: number): Promise<TableInfo[]> =>
      this.api.get(DATA_INSIGHT_CONFIG.endpoints.explorer.getTables(datasourceId)),

    // 根据模式获取表列表
    getTablesBySchema: (datasourceId: number, schema: string): Promise<TableInfo[]> =>
      this.api.get(DATA_INSIGHT_CONFIG.endpoints.explorer.getTablesBySchema(datasourceId, schema)),

    // 获取表详情
    getTableDetail: (datasourceId: number, tableName: string, schema?: string): Promise<TableDetail> => {
      const url = DATA_INSIGHT_CONFIG.endpoints.explorer.getTableDetail(datasourceId, tableName)
      const params = schema ? { schema } : {}
      return this.api.get(url, { params })
    },

    // 获取表数据
    getTableData: (params: TableDataRequest): Promise<SQLExecuteResponse> =>
      this.api.post(DATA_INSIGHT_CONFIG.endpoints.explorer.getTableData, params),

    // 执行SQL
    executeSQL: (params: SQLExecuteRequest): Promise<SQLExecuteResponse> =>
      this.api.post(DATA_INSIGHT_CONFIG.endpoints.explorer.executeSQL, params),

    // 更新字段
    updateField: (params: FieldUpdateRequest): Promise<FieldUpdateResponse> =>
      this.api.post(DATA_INSIGHT_CONFIG.endpoints.explorer.updateField, params)
  }
}

// 创建单例实例
export const dataInsightAPI = new DataInsightAPI()

// 导出默认实例
export default dataInsightAPI