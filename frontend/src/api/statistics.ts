/**
 * 统计分析相关的API接口
 */

import { request } from '@/utils/request'
import type {
  StatisticsData,
  AccessRecord,
  PopularResource,
  AccessTrendData,
  ResourceTypeDistribution,
  UserActivityData,
  StatisticsQuery,
  AccessTrendQuery,
  PopularResourceQuery,
  UserActivityQuery,
  AccessRecordQuery,
  ExportQuery,
  RealTimeStats,
  AlertRule,
  AlertRecord,
  PerformanceMetrics,
  ResourceUsageStats,
  UserBehaviorStats,
  SystemHealth,
  DataQualityStats,
  CostAnalysis,
  CapacityPlanning,
  ComplianceStats,
  StatisticsResponse,
  PaginatedStatisticsResponse
} from '@/types/statistics'

/**
 * 获取统计概览数据
 */
export const getStatistics = (params?: StatisticsQuery): Promise<StatisticsResponse<StatisticsData>> => {
  return request({
    url: '/api/statistics/overview',
    method: 'get',
    params
  })
}

/**
 * 获取访问趋势数据
 */
export const getAccessTrend = (params: AccessTrendQuery): Promise<StatisticsResponse<AccessTrendData>> => {
  return request({
    url: '/api/statistics/access-trend',
    method: 'get',
    params
  })
}

/**
 * 获取资源类型分布
 */
export const getResourceTypeDistribution = (): Promise<StatisticsResponse<ResourceTypeDistribution[]>> => {
  return request({
    url: '/api/statistics/resource-type-distribution',
    method: 'get'
  })
}

/**
 * 获取热门资源排行
 */
export const getPopularResources = (params: PopularResourceQuery): Promise<StatisticsResponse<PopularResource[]>> => {
  return request({
    url: '/api/statistics/popular-resources',
    method: 'get',
    params
  })
}

/**
 * 获取用户活跃度数据
 */
export const getUserActivity = (params: UserActivityQuery): Promise<StatisticsResponse<UserActivityData>> => {
  return request({
    url: '/api/statistics/user-activity',
    method: 'get',
    params
  })
}

/**
 * 获取访问记录列表
 */
export const getAccessRecords = (params: AccessRecordQuery): Promise<PaginatedStatisticsResponse<AccessRecord>> => {
  return request({
    url: '/api/statistics/access-records',
    method: 'get',
    params
  })
}

/**
 * 获取访问记录详情
 */
export const getAccessRecordById = (id: string): Promise<StatisticsResponse<AccessRecord>> => {
  return request({
    url: `/api/statistics/access-records/${id}`,
    method: 'get'
  })
}

/**
 * 导出统计数据
 */
export const exportStatistics = (params: ExportQuery): Promise<Blob> => {
  return request({
    url: '/api/statistics/export',
    method: 'post',
    data: params,
    responseType: 'blob'
  })
}

/**
 * 获取实时统计数据
 */
export const getRealTimeStats = (): Promise<StatisticsResponse<RealTimeStats>> => {
  return request({
    url: '/api/statistics/realtime',
    method: 'get'
  })
}

/**
 * 获取性能指标
 */
export const getPerformanceMetrics = (params?: StatisticsQuery): Promise<StatisticsResponse<PerformanceMetrics>> => {
  return request({
    url: '/api/statistics/performance',
    method: 'get',
    params
  })
}

/**
 * 获取资源使用统计
 */
export const getResourceUsageStats = (params?: StatisticsQuery): Promise<StatisticsResponse<ResourceUsageStats[]>> => {
  return request({
    url: '/api/statistics/resource-usage',
    method: 'get',
    params
  })
}

/**
 * 获取用户行为统计
 */
export const getUserBehaviorStats = (params?: StatisticsQuery): Promise<StatisticsResponse<UserBehaviorStats[]>> => {
  return request({
    url: '/api/statistics/user-behavior',
    method: 'get',
    params
  })
}

/**
 * 获取系统健康状态
 */
export const getSystemHealth = (): Promise<StatisticsResponse<SystemHealth>> => {
  return request({
    url: '/api/statistics/system-health',
    method: 'get'
  })
}

/**
 * 获取数据质量统计
 */
export const getDataQualityStats = (params?: StatisticsQuery): Promise<StatisticsResponse<DataQualityStats[]>> => {
  return request({
    url: '/api/statistics/data-quality',
    method: 'get',
    params
  })
}

/**
 * 获取成本分析
 */
export const getCostAnalysis = (params?: StatisticsQuery): Promise<StatisticsResponse<CostAnalysis>> => {
  return request({
    url: '/api/statistics/cost-analysis',
    method: 'get',
    params
  })
}

/**
 * 获取容量规划
 */
export const getCapacityPlanning = (): Promise<StatisticsResponse<CapacityPlanning>> => {
  return request({
    url: '/api/statistics/capacity-planning',
    method: 'get'
  })
}

/**
 * 获取合规性统计
 */
export const getComplianceStats = (): Promise<StatisticsResponse<ComplianceStats>> => {
  return request({
    url: '/api/statistics/compliance',
    method: 'get'
  })
}

// 告警相关API

/**
 * 获取告警规则列表
 */
export const getAlertRules = (): Promise<StatisticsResponse<AlertRule[]>> => {
  return request({
    url: '/api/statistics/alert-rules',
    method: 'get'
  })
}

/**
 * 创建告警规则
 */
export const createAlertRule = (data: Partial<AlertRule>): Promise<StatisticsResponse<AlertRule>> => {
  return request({
    url: '/api/statistics/alert-rules',
    method: 'post',
    data
  })
}

/**
 * 更新告警规则
 */
export const updateAlertRule = (id: string, data: Partial<AlertRule>): Promise<StatisticsResponse<AlertRule>> => {
  return request({
    url: `/api/statistics/alert-rules/${id}`,
    method: 'put',
    data
  })
}

/**
 * 删除告警规则
 */
export const deleteAlertRule = (id: string): Promise<StatisticsResponse<void>> => {
  return request({
    url: `/api/statistics/alert-rules/${id}`,
    method: 'delete'
  })
}

/**
 * 启用/禁用告警规则
 */
export const toggleAlertRule = (id: string, enabled: boolean): Promise<StatisticsResponse<void>> => {
  return request({
    url: `/api/statistics/alert-rules/${id}/toggle`,
    method: 'patch',
    data: { enabled }
  })
}

/**
 * 获取告警记录列表
 */
export const getAlertRecords = (params?: {
  page?: number
  size?: number
  level?: string
  status?: string
  startDate?: string
  endDate?: string
}): Promise<PaginatedStatisticsResponse<AlertRecord>> => {
  return request({
    url: '/api/statistics/alert-records',
    method: 'get',
    params
  })
}

/**
 * 获取告警记录详情
 */
export const getAlertRecordById = (id: string): Promise<StatisticsResponse<AlertRecord>> => {
  return request({
    url: `/api/statistics/alert-records/${id}`,
    method: 'get'
  })
}

/**
 * 确认告警
 */
export const acknowledgeAlert = (id: string): Promise<StatisticsResponse<void>> => {
  return request({
    url: `/api/statistics/alert-records/${id}/acknowledge`,
    method: 'patch'
  })
}

/**
 * 解决告警
 */
export const resolveAlert = (id: string, comment?: string): Promise<StatisticsResponse<void>> => {
  return request({
    url: `/api/statistics/alert-records/${id}/resolve`,
    method: 'patch',
    data: { comment }
  })
}

// 报表相关API

/**
 * 生成报表
 */
export const generateReport = (params: {
  type: 'daily' | 'weekly' | 'monthly' | 'custom'
  startDate?: string
  endDate?: string
  format: 'pdf' | 'excel' | 'html'
  includeCharts?: boolean
}): Promise<Blob> => {
  return request({
    url: '/api/statistics/reports/generate',
    method: 'post',
    data: params,
    responseType: 'blob'
  })
}

/**
 * 获取报表模板列表
 */
export const getReportTemplates = (): Promise<StatisticsResponse<any[]>> => {
  return request({
    url: '/api/statistics/report-templates',
    method: 'get'
  })
}

/**
 * 创建报表模板
 */
export const createReportTemplate = (data: any): Promise<StatisticsResponse<any>> => {
  return request({
    url: '/api/statistics/report-templates',
    method: 'post',
    data
  })
}

/**
 * 更新报表模板
 */
export const updateReportTemplate = (id: string, data: any): Promise<StatisticsResponse<any>> => {
  return request({
    url: `/api/statistics/report-templates/${id}`,
    method: 'put',
    data
  })
}

/**
 * 删除报表模板
 */
export const deleteReportTemplate = (id: string): Promise<StatisticsResponse<void>> => {
  return request({
    url: `/api/statistics/report-templates/${id}`,
    method: 'delete'
  })
}

// 数据分析相关API

/**
 * 获取数据洞察
 */
export const getDataInsights = (params?: {
  dimension: string
  metric: string
  startDate?: string
  endDate?: string
}): Promise<StatisticsResponse<any>> => {
  return request({
    url: '/api/statistics/insights',
    method: 'get',
    params
  })
}

/**
 * 获取异常检测结果
 */
export const getAnomalyDetection = (params?: {
  metric: string
  sensitivity?: number
  startDate?: string
  endDate?: string
}): Promise<StatisticsResponse<any>> => {
  return request({
    url: '/api/statistics/anomaly-detection',
    method: 'get',
    params
  })
}

/**
 * 获取预测分析结果
 */
export const getForecastAnalysis = (params: {
  metric: string
  period: number
  unit: 'day' | 'week' | 'month'
}): Promise<StatisticsResponse<any>> => {
  return request({
    url: '/api/statistics/forecast',
    method: 'get',
    params
  })
}

/**
 * 获取相关性分析
 */
export const getCorrelationAnalysis = (params: {
  metrics: string[]
  startDate?: string
  endDate?: string
}): Promise<StatisticsResponse<any>> => {
  return request({
    url: '/api/statistics/correlation',
    method: 'get',
    params
  })
}

// 自定义查询API

/**
 * 执行自定义查询
 */
export const executeCustomQuery = (query: {
  sql?: string
  dimensions: string[]
  metrics: string[]
  filters?: Record<string, any>
  groupBy?: string[]
  orderBy?: string[]
  limit?: number
}): Promise<StatisticsResponse<any>> => {
  return request({
    url: '/api/statistics/custom-query',
    method: 'post',
    data: query
  })
}

/**
 * 验证查询语法
 */
export const validateQuery = (query: string): Promise<StatisticsResponse<{ valid: boolean; error?: string }>> => {
  return request({
    url: '/api/statistics/validate-query',
    method: 'post',
    data: { query }
  })
}

/**
 * 获取查询历史
 */
export const getQueryHistory = (params?: {
  page?: number
  size?: number
  userId?: string
}): Promise<PaginatedStatisticsResponse<any>> => {
  return request({
    url: '/api/statistics/query-history',
    method: 'get',
    params
  })
}

/**
 * 保存查询
 */
export const saveQuery = (data: {
  name: string
  description?: string
  query: any
  isPublic?: boolean
}): Promise<StatisticsResponse<any>> => {
  return request({
    url: '/api/statistics/saved-queries',
    method: 'post',
    data
  })
}

/**
 * 获取已保存的查询
 */
export const getSavedQueries = (): Promise<StatisticsResponse<any[]>> => {
  return request({
    url: '/api/statistics/saved-queries',
    method: 'get'
  })
}

/**
 * 删除已保存的查询
 */
export const deleteSavedQuery = (id: string): Promise<StatisticsResponse<void>> => {
  return request({
    url: `/api/statistics/saved-queries/${id}`,
    method: 'delete'
  })
}