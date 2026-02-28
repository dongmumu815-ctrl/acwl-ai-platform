import { request } from "@/utils/request";
import type { ApiResponse } from "@/types/common";
import type {
  DatabaseConfig,
  DatabaseConfigCreate,
  DatabaseConfigUpdate,
  DatabaseResponse,
  SQLQueryRequest,
  BatchSQLQueryRequest,
  QueryResponse,
  ConnectionTestResult,
  RoutingInfo,
  HealthCheckResponse,
  DatabaseStats,
  QueryHistory,
  TableInfo,
  ColumnInfo,
  DatabasePerformance,
} from "@/types/multiDatabase";

/**
 * 多数据库管理API接口
 */

// ==================== 数据库配置管理 ====================

/**
 * 获取所有数据库配置
 */
export const getAllDatabases = (): Promise<
  ApiResponse<Record<string, DatabaseResponse>>
> => {
  return request({
    url: "/api/v1/multi-db/databases",
    method: "get",
    permission: "data:multi_db:config:view",
  });
};

/**
 * 创建数据库配置
 */
export const createDatabaseConfig = (
  data: DatabaseConfigCreate,
): Promise<ApiResponse<{ message: string }>> => {
  return request({
    url: "/api/v1/multi-db/databases",
    method: "post",
    data,
    permission: "data:multi_db:config:create",
  });
};

/**
 * 更新数据库配置
 */
export const updateDatabaseConfig = (
  dbName: string,
  data: DatabaseConfigUpdate,
): Promise<ApiResponse<{ message: string }>> => {
  return request({
    url: `/api/v1/multi-db/databases/${dbName}`,
    method: "put",
    data,
    permission: "data:multi_db:config:update",
  });
};

/**
 * 删除数据库配置
 */
export const deleteDatabaseConfig = (
  dbName: string,
): Promise<ApiResponse<{ message: string }>> => {
  return request({
    url: `/api/v1/multi-db/databases/${dbName}`,
    method: "delete",
    permission: "data:multi_db:config:delete",
  });
};

// ==================== 数据库连接测试 ====================

/**
 * 测试指定数据库连接
 */
export const testDatabaseConnection = (
  dbName: string,
): Promise<ApiResponse<ConnectionTestResult>> => {
  return request({
    url: `/api/v1/multi-db/databases/${dbName}/test`,
    method: "get",
    permission: "data:multi_db:test",
  });
};

/**
 * 测试所有数据库连接
 */
export const testAllDatabaseConnections = (): Promise<
  ApiResponse<Record<string, boolean>>
> => {
  return request({
    url: "/api/v1/multi-db/databases/test-all",
    method: "get",
    permission: "data:multi_db:test",
  });
};

// ==================== SQL查询执行 ====================

/**
 * 执行SQL查询
 */
export const executeSQLQuery = (
  data: SQLQueryRequest,
): Promise<ApiResponse<QueryResponse>> => {
  return request({
    url: "/api/v1/multi-db/query",
    method: "post",
    data,
    permission: "data:multi_db:query",
  });
};

/**
 * 批量执行SQL查询
 */
export const executeBatchSQLQueries = (
  data: BatchSQLQueryRequest,
): Promise<ApiResponse<QueryResponse[]>> => {
  return request({
    url: "/api/v1/multi-db/query/batch",
    method: "post",
    data,
    permission: "data:multi_db:query",
  });
};

/**
 * 简单SQL查询（GET方式）
 */
export const executeSimpleQuery = (
  sql: string,
  dbName?: string,
  businessTag?: string,
): Promise<ApiResponse<any>> => {
  const params: Record<string, string> = { sql };
  if (dbName) params.db_name = dbName;
  if (businessTag) params.business_tag = businessTag;

  return request({
    url: "/api/v1/multi-db/query/simple",
    method: "get",
    params,
    permission: "data:multi_db:query",
  });
};

// ==================== 路由和监控 ====================

/**
 * 获取路由信息
 */
export const getRoutingInfo = (): Promise<ApiResponse<RoutingInfo>> => {
  return request({
    url: "/api/v1/multi-db/routing/info",
    method: "get",
    permission: "data:multi_db:routing:view",
  });
};

/**
 * 根据标签获取数据库列表
 */
export const getDatabasesByTag = (
  tag: string,
): Promise<ApiResponse<DatabaseResponse[]>> => {
  return request({
    url: `/api/v1/multi-db/databases/by-tag/${tag}`,
    method: "get",
    permission: "data:multi_db:config:view",
  });
};

/**
 * 健康检查
 */
export const getHealthCheck = (): Promise<ApiResponse<HealthCheckResponse>> => {
  return request({
    url: "/api/v1/multi-db/health",
    method: "get",
    permission: "data:multi_db:health:view",
  });
};

// ==================== 扩展功能 ====================

/**
 * 获取数据库统计信息
 */
export const getDatabaseStats = (
  dbName?: string,
): Promise<ApiResponse<DatabaseStats>> => {
  const params = dbName ? { db_name: dbName } : {};
  return request({
    url: "/api/v1/multi-db/stats",
    method: "get",
    params,
    permission: "data:multi_db:stats:view",
  });
};

/**
 * 获取查询历史记录
 */
export const getQueryHistory = (params?: {
  page?: number;
  page_size?: number;
  database?: string;
  start_date?: string;
  end_date?: string;
}): Promise<
  ApiResponse<{
    items: QueryHistory[];
    total: number;
    page: number;
    page_size: number;
  }>
> => {
  return request({
    url: "/api/v1/multi-db/query/history",
    method: "get",
    params,
    permission: "data:multi_db:query_history:view",
  });
};

/**
 * 获取数据库表列表
 */
export const getDatabaseTables = (
  dbName: string,
  schema?: string,
): Promise<ApiResponse<TableInfo[]>> => {
  const params = schema ? { schema } : {};
  return request({
    url: `/api/v1/multi-db/databases/${dbName}/tables`,
    method: "get",
    params,
    permission: "data:multi_db:tables:view",
  });
};

/**
 * 获取表结构信息
 */
export const getTableColumns = (
  dbName: string,
  tableName: string,
  schema?: string,
): Promise<ApiResponse<ColumnInfo[]>> => {
  const params = schema ? { schema } : {};
  return request({
    url: `/api/v1/multi-db/databases/${dbName}/tables/${tableName}/columns`,
    method: "get",
    params,
    permission: "data:multi_db:columns:view",
  });
};

/**
 * 获取数据库性能指标
 */
export const getDatabasePerformance = (
  dbName?: string,
  timeRange?: string,
): Promise<ApiResponse<DatabasePerformance[]>> => {
  const params: Record<string, string> = {};
  if (dbName) params.db_name = dbName;
  if (timeRange) params.time_range = timeRange;

  return request({
    url: "/api/v1/multi-db/performance",
    method: "get",
    params,
    permission: "data:multi_db:performance:view",
  });
};

/**
 * 导出查询结果
 */
export const exportQueryResult = (
  data: SQLQueryRequest & { format?: "csv" | "excel" | "json" },
): Promise<ApiResponse<Blob>> => {
  return request({
    url: "/api/v1/multi-db/query/export",
    method: "post",
    data,
    responseType: "blob",
    permission: "data:multi_db:export",
  });
};

/**
 * 保存查询模板
 */
export const saveQueryTemplate = (data: {
  name: string;
  description?: string;
  query: string;
  database?: string;
  business_tag?: string;
  parameters?: Record<string, any>;
}): Promise<ApiResponse<{ template_id: string }>> => {
  return request({
    url: "/api/v1/multi-db/query/templates",
    method: "post",
    data,
    permission: "data:multi_db:templates:create",
  });
};

/**
 * 获取查询模板列表
 */
export const getQueryTemplates = (params?: {
  page?: number;
  page_size?: number;
  database?: string;
  business_tag?: string;
}): Promise<
  ApiResponse<{
    items: Array<{
      id: string;
      name: string;
      description?: string;
      query: string;
      database?: string;
      business_tag?: string;
      parameters?: Record<string, any>;
      created_at: string;
      updated_at: string;
    }>;
    total: number;
    page: number;
    page_size: number;
  }>
> => {
  return request({
    url: "/api/v1/multi-db/query/templates",
    method: "get",
    params,
    permission: "data:multi_db:templates:view",
  });
};
