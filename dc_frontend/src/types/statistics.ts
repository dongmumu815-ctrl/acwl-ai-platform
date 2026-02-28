/**
 * 统计分析相关的类型定义
 */

// 统计数据接口
export interface StatisticsData {
  totalResources: number;
  totalAccess: number;
  activeUsers: number;
  totalStorage: number;
  resourcesChange: number;
  accessChange: number;
  usersChange: number;
  storageChange: number;
}

// 访问记录接口
export interface AccessRecord {
  id: string;
  resourceId: string;
  resourceName: string;
  resourceType: string;
  userId: string;
  userName: string;
  accessTime: string;
  accessType: "view" | "download" | "query" | "edit";
  duration: number;
  status: "success" | "failed";
  ipAddress?: string;
  userAgent?: string;
}

// 热门资源接口
export interface PopularResource {
  id: string;
  name: string;
  type: string;
  accessCount: number;
  uniqueUsers: number;
  avgDuration: number;
}

// 访问趋势数据接口
export interface AccessTrendData {
  dates: string[];
  accessCounts: number[];
  userCounts: number[];
}

// 资源类型分布接口
export interface ResourceTypeDistribution {
  type: string;
  count: number;
  percentage: number;
}

// 用户活跃度数据接口
export interface UserActivityData {
  hours: string[];
  counts: number[];
}

// 统计查询参数接口
export interface StatisticsQuery {
  startDate?: string;
  endDate?: string;
  resourceType?: string;
  userId?: string;
  page?: number;
  size?: number;
  keyword?: string;
}

// 访问趋势查询参数接口
export interface AccessTrendQuery {
  startDate: string;
  endDate: string;
  type: "day" | "week" | "month";
}

// 热门资源查询参数接口
export interface PopularResourceQuery {
  startDate: string;
  endDate: string;
  limit?: number;
  resourceType?: string;
}

// 用户活跃度查询参数接口
export interface UserActivityQuery {
  startDate: string;
  endDate: string;
  type?: "hour" | "day" | "week";
}

// 访问记录查询参数接口
export interface AccessRecordQuery {
  page: number;
  size: number;
  keyword?: string;
  startDate?: string;
  endDate?: string;
  resourceType?: string;
  accessType?: string;
  status?: string;
  userId?: string;
}

// 导出参数接口
export interface ExportQuery {
  startDate?: string;
  endDate?: string;
  keyword?: string;
  resourceType?: string;
  accessType?: string;
  status?: string;
  format?: "excel" | "csv";
}

// 统计图表数据接口
export interface ChartData {
  labels: string[];
  datasets: ChartDataset[];
}

export interface ChartDataset {
  label: string;
  data: number[];
  backgroundColor?: string | string[];
  borderColor?: string;
  borderWidth?: number;
  fill?: boolean;
}

// 仪表板配置接口
export interface DashboardConfig {
  refreshInterval: number;
  defaultDateRange: number;
  chartTheme: "light" | "dark";
  enableAutoRefresh: boolean;
}

// 统计卡片数据接口
export interface StatCard {
  title: string;
  value: number | string;
  change: number;
  changeType: "positive" | "negative" | "neutral";
  icon: string;
  color: string;
}

// 时间范围枚举
export enum TimeRange {
  TODAY = "today",
  YESTERDAY = "yesterday",
  LAST_7_DAYS = "last_7_days",
  LAST_30_DAYS = "last_30_days",
  LAST_90_DAYS = "last_90_days",
  CUSTOM = "custom",
}

// 图表类型枚举
export enum ChartType {
  LINE = "line",
  BAR = "bar",
  PIE = "pie",
  DOUGHNUT = "doughnut",
  AREA = "area",
}

// 统计维度枚举
export enum StatDimension {
  RESOURCE = "resource",
  USER = "user",
  TIME = "time",
  TYPE = "type",
}

// 聚合类型枚举
export enum AggregationType {
  COUNT = "count",
  SUM = "sum",
  AVG = "avg",
  MAX = "max",
  MIN = "min",
}

// 排序方向枚举
export enum SortDirection {
  ASC = "asc",
  DESC = "desc",
}

// 统计响应接口
export interface StatisticsResponse<T = any> {
  code: number;
  message: string;
  data: T;
  timestamp: string;
}

// 分页统计响应接口
export interface PaginatedStatisticsResponse<T = any> {
  code: number;
  message: string;
  data: {
    records: T[];
    total: number;
    page: number;
    size: number;
    pages: number;
  };
  timestamp: string;
}

// 实时统计数据接口
export interface RealTimeStats {
  onlineUsers: number;
  currentAccess: number;
  systemLoad: number;
  memoryUsage: number;
  diskUsage: number;
  networkTraffic: {
    inbound: number;
    outbound: number;
  };
}

// 告警规则接口
export interface AlertRule {
  id: string;
  name: string;
  metric: string;
  operator: ">" | "<" | ">=" | "<=" | "=" | "!=";
  threshold: number;
  duration: number;
  enabled: boolean;
  notificationChannels: string[];
  createdAt: string;
  updatedAt: string;
}

// 告警记录接口
export interface AlertRecord {
  id: string;
  ruleId: string;
  ruleName: string;
  metric: string;
  value: number;
  threshold: number;
  level: "info" | "warning" | "error" | "critical";
  status: "active" | "resolved";
  triggeredAt: string;
  resolvedAt?: string;
  message: string;
}

// 性能指标接口
export interface PerformanceMetrics {
  responseTime: {
    avg: number;
    p50: number;
    p90: number;
    p95: number;
    p99: number;
  };
  throughput: number;
  errorRate: number;
  availability: number;
}

// 资源使用统计接口
export interface ResourceUsageStats {
  resourceId: string;
  resourceName: string;
  totalAccess: number;
  uniqueUsers: number;
  avgDuration: number;
  peakConcurrency: number;
  dataTransfer: number;
  lastAccessTime: string;
}

// 用户行为统计接口
export interface UserBehaviorStats {
  userId: string;
  userName: string;
  totalSessions: number;
  totalDuration: number;
  avgSessionDuration: number;
  resourcesAccessed: number;
  favoriteResourceTypes: string[];
  lastActiveTime: string;
}

// 系统健康状态接口
export interface SystemHealth {
  status: "healthy" | "warning" | "critical";
  uptime: number;
  version: string;
  services: ServiceHealth[];
  lastCheckTime: string;
}

export interface ServiceHealth {
  name: string;
  status: "up" | "down" | "degraded";
  responseTime: number;
  lastCheckTime: string;
  errorMessage?: string;
}

// 数据质量统计接口
export interface DataQualityStats {
  resourceId: string;
  resourceName: string;
  completeness: number;
  accuracy: number;
  consistency: number;
  timeliness: number;
  validity: number;
  overallScore: number;
  lastUpdated: string;
}

// 成本分析接口
export interface CostAnalysis {
  period: string;
  totalCost: number;
  costByResource: CostByResource[];
  costByUser: CostByUser[];
  costTrend: CostTrend[];
  projectedCost: number;
}

export interface CostByResource {
  resourceId: string;
  resourceName: string;
  cost: number;
  usage: number;
  costPerUnit: number;
}

export interface CostByUser {
  userId: string;
  userName: string;
  cost: number;
  usage: number;
}

export interface CostTrend {
  date: string;
  cost: number;
  usage: number;
}

// 容量规划接口
export interface CapacityPlanning {
  currentCapacity: number;
  usedCapacity: number;
  utilizationRate: number;
  projectedGrowth: number;
  recommendedCapacity: number;
  timeToCapacity: number;
  recommendations: string[];
}

// 合规性统计接口
export interface ComplianceStats {
  totalPolicies: number;
  compliantResources: number;
  nonCompliantResources: number;
  complianceRate: number;
  violations: ComplianceViolation[];
  lastAuditTime: string;
}

export interface ComplianceViolation {
  id: string;
  resourceId: string;
  resourceName: string;
  policyId: string;
  policyName: string;
  severity: "low" | "medium" | "high" | "critical";
  description: string;
  detectedAt: string;
  status: "open" | "resolved" | "ignored";
}
