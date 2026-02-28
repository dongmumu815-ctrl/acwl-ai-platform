import { request } from "@/utils/request";
import type {
  SystemSettings,
  SystemInfo,
  SystemStatus,
  BackupRecord,
  LogRecord,
  PerformanceMetrics,
  EmailTestRequest,
  BackupCreateRequest,
  LogQueryParams,
  SystemUpdateRequest,
} from "@/types/system";
import type { ApiResponse, PaginatedResponse } from "@/types/common";

/**
 * 获取系统信息
 */
export const getSystemInfo = (): Promise<ApiResponse<SystemInfo>> => {
  return request({
    url: "/api/system/info",
    method: "get",
    permission: "system:info:view",
  });
};

/**
 * 获取系统状态
 */
export const getSystemStatus = (): Promise<ApiResponse<SystemStatus>> => {
  return request({
    url: "/api/system/status",
    method: "get",
    permission: "system:status:view",
  });
};

/**
 * 获取系统设置
 */
export const getSystemSettings = (): Promise<ApiResponse<SystemSettings>> => {
  return request({
    url: "/api/system/settings",
    method: "get",
    permission: "system:settings:view",
  });
};

/**
 * 更新系统设置
 */
export const updateSystemSettings = (
  data: Partial<SystemSettings>,
): Promise<ApiResponse<void>> => {
  return request({
    url: "/api/system/settings",
    method: "put",
    data,
    permission: "system:settings:update",
  });
};

/**
 * 重置系统设置
 */
export const resetSystemSettings = (): Promise<ApiResponse<void>> => {
  return request({
    url: "/api/system/settings/reset",
    method: "post",
    permission: "system:settings:reset",
  });
};

/**
 * 测试邮件连接
 */
export const testEmailConnection = (
  data: EmailTestRequest,
): Promise<ApiResponse<{ success: boolean; message: string }>> => {
  return request({
    url: "/api/system/email/test",
    method: "post",
    data,
    permission: "system:email:test",
  });
};

/**
 * 发送测试邮件
 */
export const sendTestEmail = (data: {
  to: string;
  subject?: string;
  content?: string;
}): Promise<ApiResponse<void>> => {
  return request({
    url: "/api/system/email/send-test",
    method: "post",
    data,
    permission: "system:email:send",
  });
};

/**
 * 获取备份列表
 */
export const getBackupList = (params?: {
  page?: number;
  page_size?: number;
  start_date?: string;
  end_date?: string;
}): Promise<PaginatedResponse<BackupRecord>> => {
  return request({
    url: "/api/system/backups",
    method: "get",
    params,
    permission: "system:backup:view",
  });
};

/**
 * 创建系统备份
 */
export const createSystemBackup = (
  data?: BackupCreateRequest,
): Promise<ApiResponse<{ backup_id: string; file_path: string }>> => {
  return request({
    url: "/api/system/backups",
    method: "post",
    data,
    permission: "system:backup:create",
  });
};

/**
 * 恢复系统备份
 */
export const restoreSystemBackup = (
  backupId: string,
): Promise<ApiResponse<void>> => {
  return request({
    url: `/api/system/backups/${backupId}/restore`,
    method: "post",
    permission: "system:backup:restore",
  });
};

/**
 * 下载备份文件
 */
export const downloadBackup = (
  backupId: string,
): Promise<ApiResponse<Blob>> => {
  return request({
    url: `/api/system/backups/${backupId}/download`,
    method: "get",
    responseType: "blob",
    permission: "system:backup:download",
  });
};

/**
 * 删除备份
 */
export const deleteBackup = (backupId: string): Promise<ApiResponse<void>> => {
  return request({
    url: `/api/system/backups/${backupId}`,
    method: "delete",
    permission: "system:backup:delete",
  });
};

/**
 * 获取系统日志
 */
export const getSystemLogs = (
  params: LogQueryParams,
): Promise<PaginatedResponse<LogRecord>> => {
  return request({
    url: "/api/system/logs",
    method: "get",
    params,
    permission: "system:logs:view",
  });
};

/**
 * 清理系统日志
 */
export const clearSystemLogs = (data: {
  before_date?: string;
  log_level?: string;
  log_type?: string;
}): Promise<ApiResponse<{ deleted_count: number }>> => {
  return request({
    url: "/api/system/logs/clear",
    method: "post",
    data,
    permission: "system:logs:clear",
  });
};

/**
 * 导出系统日志
 */
export const exportSystemLogs = (
  params: LogQueryParams,
): Promise<ApiResponse<Blob>> => {
  return request({
    url: "/api/system/logs/export",
    method: "get",
    params,
    responseType: "blob",
    permission: "system:logs:export",
  });
};

/**
 * 获取性能指标
 */
export const getPerformanceMetrics = (params?: {
  start_time?: string;
  end_time?: string;
  metric_type?: string;
}): Promise<ApiResponse<PerformanceMetrics>> => {
  return request({
    url: "/api/system/performance",
    method: "get",
    params,
    permission: "system:performance:view",
  });
};

/**
 * 获取系统健康检查
 */
export const getSystemHealthCheck = (): Promise<
  ApiResponse<{
    status: "healthy" | "warning" | "error";
    checks: Array<{
      name: string;
      status: "pass" | "fail" | "warn";
      message: string;
      duration: number;
    }>;
    timestamp: string;
  }>
> => {
  return request({
    url: "/api/system/health",
    method: "get",
    permission: "system:health:view",
  });
};

/**
 * 重启系统服务
 */
export const restartSystemService = (
  serviceName: string,
): Promise<ApiResponse<void>> => {
  return request({
    url: `/api/system/services/${serviceName}/restart`,
    method: "post",
    permission: "system:services:restart",
  });
};

/**
 * 获取系统服务状态
 */
export const getSystemServices = (): Promise<
  ApiResponse<
    Array<{
      name: string;
      status: "running" | "stopped" | "error";
      uptime: number;
      memory_usage: number;
      cpu_usage: number;
      last_restart: string;
    }>
  >
> => {
  return request({
    url: "/api/system/services",
    method: "get",
    permission: "system:services:view",
  });
};

/**
 * 更新系统
 */
export const updateSystem = (
  data: SystemUpdateRequest,
): Promise<ApiResponse<{ update_id: string }>> => {
  return request({
    url: "/api/system/update",
    method: "post",
    data,
    permission: "system:update:run",
  });
};

/**
 * 获取系统更新状态
 */
export const getUpdateStatus = (
  updateId: string,
): Promise<
  ApiResponse<{
    status: "pending" | "downloading" | "installing" | "completed" | "failed";
    progress: number;
    message: string;
    started_at: string;
    completed_at?: string;
  }>
> => {
  return request({
    url: `/api/system/update/${updateId}/status`,
    method: "get",
    permission: "system:update:view",
  });
};

/**
 * 检查系统更新
 */
export const checkSystemUpdate = (): Promise<
  ApiResponse<{
    has_update: boolean;
    current_version: string;
    latest_version?: string;
    release_notes?: string;
    update_size?: number;
    release_date?: string;
  }>
> => {
  return request({
    url: "/api/system/update/check",
    method: "get",
    permission: "system:update:view",
  });
};

/**
 * 获取系统配置模板
 */
export const getSystemConfigTemplate = (): Promise<
  ApiResponse<Record<string, any>>
> => {
  return request({
    url: "/api/system/config/template",
    method: "get",
    permission: "system:config:view",
  });
};

/**
 * 导入系统配置
 */
export const importSystemConfig = (
  data: FormData,
): Promise<ApiResponse<{ imported_count: number; errors: string[] }>> => {
  return request({
    url: "/api/system/config/import",
    method: "post",
    data,
    headers: {
      "Content-Type": "multipart/form-data",
    },
    permission: "system:config:import",
  });
};

/**
 * 导出系统配置
 */
export const exportSystemConfig = (): Promise<ApiResponse<Blob>> => {
  return request({
    url: "/api/system/config/export",
    method: "get",
    responseType: "blob",
    permission: "system:config:export",
  });
};

/**
 * 获取系统许可证信息
 */
export const getSystemLicense = (): Promise<
  ApiResponse<{
    license_key: string;
    license_type: string;
    issued_to: string;
    issued_date: string;
    expires_date: string;
    max_users: number;
    features: string[];
    is_valid: boolean;
  }>
> => {
  return request({
    url: "/api/system/license",
    method: "get",
    permission: "system:license:view",
  });
};

/**
 * 更新系统许可证
 */
export const updateSystemLicense = (data: {
  license_key: string;
}): Promise<ApiResponse<void>> => {
  return request({
    url: "/api/system/license",
    method: "put",
    data,
    permission: "system:license:update",
  });
};

/**
 * 获取系统统计信息
 */
export const getSystemStatistics = (): Promise<
  ApiResponse<{
    total_users: number;
    active_users: number;
    total_resources: number;
    total_storage_used: number;
    total_api_calls: number;
    system_uptime: number;
    last_backup: string;
    database_size: number;
  }>
> => {
  return request({
    url: "/api/system/statistics",
    method: "get",
    permission: "system:statistics:view",
  });
};

/**
 * 清理系统缓存
 */
export const clearSystemCache = (
  cacheType?: string,
): Promise<ApiResponse<{ cleared_items: number }>> => {
  return request({
    url: "/api/system/cache/clear",
    method: "post",
    data: { cache_type: cacheType },
    permission: "system:cache:clear",
  });
};

/**
 * 获取缓存统计
 */
export const getCacheStatistics = (): Promise<
  ApiResponse<{
    total_keys: number;
    memory_usage: number;
    hit_rate: number;
    miss_rate: number;
    cache_types: Array<{
      type: string;
      keys: number;
      memory: number;
    }>;
  }>
> => {
  return request({
    url: "/api/system/cache/statistics",
    method: "get",
    permission: "system:cache:view",
  });
};
