/**
 * 多数据库管理相关类型定义
 */

/**
 * 数据库类型枚举
 */
export type DatabaseType = 'mysql' | 'postgresql' | 'sqlite' | 'oracle' | 'sqlserver' | 'mongodb'

/**
 * 数据库配置接口
 */
export interface DatabaseConfig {
  name: string
  type: DatabaseType
  host: string
  port: number
  username: string
  password: string
  database: string
  charset: string
  pool_size: number
  max_overflow: number
  pool_timeout: number
  pool_recycle: number
  extra_params?: Record<string, any>
  business_tags: string[]
  is_primary: boolean
  is_active: boolean
}

/**
 * 创建数据库配置请求
 */
export interface DatabaseConfigCreate {
  name: string
  type: DatabaseType
  host: string
  port: number
  username: string
  password: string
  database: string
  charset?: string
  pool_size?: number
  max_overflow?: number
  business_tags?: string[]
  is_primary?: boolean
}

/**
 * 更新数据库配置请求
 */
export interface DatabaseConfigUpdate {
  host?: string
  port?: number
  username?: string
  password?: string
  database?: string
  charset?: string
  pool_size?: number
  max_overflow?: number
  business_tags?: string[]
  is_active?: boolean
}

/**
 * 数据库信息响应
 */
export interface DatabaseResponse {
  name: string
  type: string
  host: string
  port: number
  database: string
  business_tags: string[]
  is_primary: boolean
  is_active: boolean
}

/**
 * SQL查询请求
 */
export interface SQLQueryRequest {
  query: string
  params?: Record<string, any>
  business_tag?: string
  db_name?: string
}

/**
 * 批量SQL查询请求
 */
export interface BatchSQLQueryRequest {
  queries: Array<{
    query: string
    params?: Record<string, any>
    operation_type?: string
  }>
  business_tag?: string
  db_name?: string
}

/**
 * 查询响应
 */
export interface QueryResponse {
  success: boolean
  data: any
  message?: string
  affected_rows?: number
}

/**
 * 数据库连接测试结果
 */
export interface ConnectionTestResult {
  connected: boolean
}

/**
 * 路由信息
 */
export interface RoutingInfo {
  strategy: string
  rules_count: number
  available_databases: string[]
}

/**
 * 健康检查响应
 */
export interface HealthCheckResponse {
  status: 'healthy' | 'degraded' | 'unhealthy'
  total_databases: number
  healthy_databases: number
  health_percentage: number
  connection_status: Record<string, boolean>
  routing_info: RoutingInfo
  error?: string
}

/**
 * 数据库统计信息
 */
export interface DatabaseStats {
  total_connections: number
  active_connections: number
  idle_connections: number
  total_queries: number
  successful_queries: number
  failed_queries: number
  average_response_time: number
}

/**
 * 查询历史记录
 */
export interface QueryHistory {
  id: string
  query: string
  database: string
  execution_time: number
  status: 'success' | 'error'
  result_count?: number
  error_message?: string
  created_at: string
}

/**
 * 数据库表信息
 */
export interface TableInfo {
  table_name: string
  table_schema: string
  table_type: string
  row_count: number
  data_length: number
  index_length: number
  created_at?: string
  updated_at?: string
}

/**
 * 数据库列信息
 */
export interface ColumnInfo {
  column_name: string
  data_type: string
  is_nullable: boolean
  column_default?: string
  character_maximum_length?: number
  numeric_precision?: number
  numeric_scale?: number
  column_comment?: string
}

/**
 * 数据库性能指标
 */
export interface DatabasePerformance {
  database_name: string
  cpu_usage: number
  memory_usage: number
  disk_usage: number
  connection_count: number
  query_per_second: number
  slow_query_count: number
  lock_wait_time: number
  timestamp: string
}