/**
 * 数据源相关类型定义
 */

// 基础响应类型
export interface ApiResponse<T = any> {
  code: number;
  message: string;
  data: T;
  success: boolean;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

// 数据源类型
export interface DataSource {
  id: number;
  name: string;
  type: string;
  description?: string;
  host: string;
  port: number;
  database?: string;
  username: string;
  password?: string;
  connection_params?: Record<string, any>;
  is_active: boolean;
  is_default: boolean;
  created_at: string;
  updated_at: string;
  created_by: number;
  last_test_at?: string;
  last_test_status?: "success" | "failed";
  last_test_message?: string;
  tags?: string[];
  metadata?: Record<string, any>;
}

// 数据源创建请求
export interface DataSourceCreateRequest {
  name: string;
  type: string;
  description?: string;
  host: string;
  port: number;
  database?: string;
  username: string;
  password: string;
  connection_params?: Record<string, any>;
  is_active?: boolean;
  is_default?: boolean;
  tags?: string[];
}

// 数据源更新请求
export interface DataSourceUpdateRequest {
  name?: string;
  description?: string;
  host?: string;
  port?: number;
  database?: string;
  username?: string;
  password?: string;
  connection_params?: Record<string, any>;
  is_active?: boolean;
  is_default?: boolean;
  tags?: string[];
}

// 数据源测试连接请求
export interface DataSourceTestRequest {
  type: string;
  host: string;
  port: number;
  database?: string;
  username: string;
  password: string;
  connection_params?: Record<string, any>;
}

// 数据源列表查询参数
export interface DataSourceListQuery {
  page?: number;
  page_size?: number;
  search?: string;
  type?: string;
  is_active?: boolean;
  created_by?: number;
  tags?: string[];
  sort_by?: string;
  sort_order?: "asc" | "desc";
}

// 数据源连接状态
export interface DataSourceConnectionStatus {
  status: "success" | "failed";
  message: string;
  response_time?: number;
  tested_at: string;
  error_details?: Record<string, any>;
}

// 数据源统计信息
export interface DataSourceStats {
  total_count: number;
  active_count: number;
  inactive_count: number;
  by_type: Record<string, number>;
  recent_tests: {
    success_count: number;
    failed_count: number;
    last_24h: number;
  };
  health_status: {
    healthy: number;
    unhealthy: number;
    unknown: number;
  };
}

// 数据源配置表单
export interface DataSourceFormData {
  name: string;
  type: string;
  description: string;
  host: string;
  port: number | string;
  database: string;
  username: string;
  password: string;
  connection_params: Record<string, any>;
  is_active: boolean;
  is_default: boolean;
  tags: string[];
}

// 数据源类型配置
export interface DataSourceTypeConfig {
  type: string;
  name: string;
  description: string;
  default_port: number;
  required_fields: string[];
  optional_fields: string[];
  connection_params_schema?: Record<string, any>;
  icon?: string;
  color?: string;
}

// 数据源连接配置
export interface DataSourceConnectionConfig {
  host: string;
  port: number;
  database?: string;
  username: string;
  password: string;
  ssl?: boolean;
  timeout?: number;
  pool_size?: number;
  max_overflow?: number;
  pool_timeout?: number;
  pool_recycle?: number;
  echo?: boolean;
  [key: string]: any;
}

// 数据源健康检查结果
export interface DataSourceHealthCheck {
  datasource_id: number;
  status: "healthy" | "unhealthy" | "unknown";
  last_check_at: string;
  response_time?: number;
  error_message?: string;
  checks: {
    connectivity: boolean;
    authentication: boolean;
    permissions: boolean;
    [key: string]: boolean;
  };
}

// 数据源监控信息
export interface DataSourceMonitor {
  datasource_id: number;
  cpu_usage?: number;
  memory_usage?: number;
  disk_usage?: number;
  connection_count?: number;
  query_count?: number;
  error_count?: number;
  avg_response_time?: number;
  timestamp: string;
}
