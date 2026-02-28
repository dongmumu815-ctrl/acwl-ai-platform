/**
 * 数据资源相关的类型定义
 */

// 基础响应类型
export interface ResourceResponse<T = any> {
  code: number;
  message: string;
  data: T;
  timestamp?: string;
}

export interface PaginatedResourceResponse<T = any> {
  code: number;
  message: string;
  data: {
    items: T[];
    total: number;
    page: number;
    size: number;
    pages: number;
  };
  timestamp?: string;
}

// 数据资源类型枚举
export enum ResourceType {
  MYSQL = "mysql",
  POSTGRESQL = "postgresql",
  ORACLE = "oracle",
  SQLSERVER = "sqlserver",
  MONGODB = "mongodb",
  REDIS = "redis",
  ELASTICSEARCH = "elasticsearch",
  KAFKA = "kafka",
  HIVE = "hive",
  HDFS = "hdfs",
  S3 = "s3",
  FTP = "ftp",
  SFTP = "sftp",
  HTTP = "http",
  WEBSERVICE = "webservice",
  FILE = "file",
  EXCEL = "excel",
  CSV = "csv",
  JSON = "json",
  XML = "xml",
  API = "api",
}

// 资源状态枚举
export enum ResourceStatus {
  ACTIVE = "active",
  INACTIVE = "inactive",
  TESTING = "testing",
  ERROR = "error",
  SYNCING = "syncing",
  MAINTENANCE = "maintenance",
}

// 连接状态枚举
export enum ConnectionStatus {
  CONNECTED = "connected",
  DISCONNECTED = "disconnected",
  CONNECTING = "connecting",
  ERROR = "error",
  TIMEOUT = "timeout",
}

// 权限类型枚举
export enum PermissionType {
  READ = "read",
  WRITE = "write",
  DELETE = "delete",
  ADMIN = "admin",
  EXECUTE = "execute",
  EXPORT = "export",
  IMPORT = "import",
}

// 字段数据类型枚举
export enum FieldDataType {
  STRING = "string",
  INTEGER = "int",
  FLOAT = "float",
  DOUBLE = "double",
  DECIMAL = "decimal",
  BOOLEAN = "boolean",
  DATE = "date",
  DATETIME = "datetime",
  TIMESTAMP = "timestamp",
  TIME = "time",
  TEXT = "text",
  BLOB = "blob",
  JSON = "json",
  ARRAY = "array",
  OBJECT = "object",
}

// 数据资源接口
export interface DataResource {
  id: string;
  name: string;
  description?: string;
  type: ResourceType;
  status: ResourceStatus;
  connectionStatus: ConnectionStatus;
  categoryId?: string;
  category?: ResourceCategory;
  config: ResourceConfig;
  metadata?: ResourceMetadata;
  tags: string[];
  permissions: ResourcePermission[];
  fields?: ResourceField[];
  statistics?: ResourceStatistics;
  createdBy: string;
  createdAt: string;
  updatedBy?: string;
  updatedAt?: string;
  lastAccessAt?: string;
  version: string;
  isPublic: boolean;
  isTemplate: boolean;
  templateId?: string;
}

// 资源配置接口
export interface ResourceConfig {
  // 数据库连接配置
  host?: string;
  port?: number;
  database?: string;
  username?: string;
  password?: string;
  schema?: string;

  // 文件系统配置
  path?: string;
  encoding?: string;
  delimiter?: string;

  // API配置
  url?: string;
  method?: string;
  headers?: Record<string, string>;
  params?: Record<string, any>;
  auth?: {
    type: "basic" | "bearer" | "apikey" | "oauth2";
    credentials: Record<string, string>;
  };

  // 连接池配置
  poolSize?: number;
  maxConnections?: number;
  connectionTimeout?: number;
  queryTimeout?: number;

  // SSL配置
  ssl?: {
    enabled: boolean;
    cert?: string;
    key?: string;
    ca?: string;
    rejectUnauthorized?: boolean;
  };

  // 其他配置
  options?: Record<string, any>;
}

// 资源元数据接口
export interface ResourceMetadata {
  size?: number;
  recordCount?: number;
  tableCount?: number;
  lastSyncAt?: string;
  syncFrequency?: string;
  dataFormat?: string;
  compression?: string;
  checksum?: string;
  location?: string;
  owner?: string;
  department?: string;
  businessDomain?: string;
  dataClassification?: "public" | "internal" | "confidential" | "restricted";
  retentionPeriod?: string;
  backupEnabled?: boolean;
  encryptionEnabled?: boolean;
  customFields?: Record<string, any>;
}

// 资源统计信息接口
export interface ResourceStatistics {
  totalAccess: number;
  dailyAccess: number;
  weeklyAccess: number;
  monthlyAccess: number;
  uniqueUsers: number;
  avgResponseTime: number;
  errorRate: number;
  lastAccessTime?: string;
  popularTables?: string[];
  popularFields?: string[];
}

// 资源分类接口
export interface ResourceCategory {
  id: string;
  name: string;
  description?: string;
  parentId?: string;
  children?: ResourceCategory[];
  icon?: string;
  color?: string;
  sortOrder: number;
  resourceCount: number;
  createdAt: string;
  updatedAt?: string;
}

// 资源字段接口
export interface ResourceField {
  id: string;
  name: string;
  displayName?: string;
  description?: string;
  dataType: FieldDataType;
  length?: number;
  precision?: number;
  scale?: number;
  nullable: boolean;
  primaryKey: boolean;
  foreignKey: boolean;
  unique: boolean;
  indexed: boolean;
  defaultValue?: any;
  comment?: string;
  table?: string;
  schema?: string;
  constraints?: string[];
  statistics?: FieldStatistics;
  tags?: string[];
  businessRules?: string[];
  dataQuality?: FieldDataQuality;
}

// 字段统计信息接口
export interface FieldStatistics {
  distinctCount?: number;
  nullCount?: number;
  minValue?: any;
  maxValue?: any;
  avgValue?: any;
  mostFrequentValue?: any;
  dataDistribution?: Record<string, number>;
}

// 字段数据质量接口
export interface FieldDataQuality {
  completeness: number; // 完整性百分比
  accuracy: number; // 准确性百分比
  consistency: number; // 一致性百分比
  validity: number; // 有效性百分比
  issues?: string[]; // 数据质量问题列表
}

// 资源权限接口
export interface ResourcePermission {
  id: string;
  resourceId: string;
  userId?: string;
  roleId?: string;
  user?: {
    id: string;
    name: string;
    email: string;
  };
  role?: {
    id: string;
    name: string;
    description: string;
  };
  permissions: PermissionType[];
  grantedBy: string;
  grantedAt: string;
  expiresAt?: string;
  conditions?: Record<string, any>;
}

// 资源访问记录接口
export interface ResourceAccessRecord {
  id: string;
  resourceId: string;
  userId: string;
  user?: {
    id: string;
    name: string;
    email: string;
  };
  operation: string;
  details?: any;
  ip: string;
  userAgent: string;
  duration?: number;
  status: "success" | "error" | "timeout";
  errorMessage?: string;
  accessedAt: string;
  sessionId?: string;
  requestId?: string;
}

// 资源标签接口
export interface ResourceTag {
  id: string;
  name: string;
  color?: string;
  description?: string;
  category?: string;
  usageCount: number;
  createdBy: string;
  createdAt: string;
}

// 资源版本接口
export interface ResourceVersion {
  id: string;
  resourceId: string;
  version: string;
  description?: string;
  changes?: string;
  config: ResourceConfig;
  metadata?: ResourceMetadata;
  createdBy: string;
  createdAt: string;
  isActive: boolean;
}

// 资源备份接口
export interface ResourceBackup {
  id: string;
  resourceId: string;
  name: string;
  description?: string;
  type: "full" | "incremental" | "differential";
  size: number;
  location: string;
  includeData: boolean;
  status: "creating" | "completed" | "failed" | "expired";
  createdBy: string;
  createdAt: string;
  completedAt?: string;
  expiresAt?: string;
  errorMessage?: string;
}

// 资源监控指标接口
export interface ResourceMetrics {
  resourceId: string;
  timestamp: string;
  cpu?: number;
  memory?: number;
  disk?: number;
  network?: number;
  connections?: number;
  queries?: number;
  responseTime?: number;
  errorRate?: number;
  throughput?: number;
  availability?: number;
  customMetrics?: Record<string, number>;
}

// 资源验证结果接口
export interface ResourceValidation {
  resourceId: string;
  validatedAt: string;
  overall: {
    score: number;
    status: "excellent" | "good" | "fair" | "poor";
    issues: number;
  };
  dimensions: {
    completeness: ValidationDimension;
    accuracy: ValidationDimension;
    consistency: ValidationDimension;
    validity: ValidationDimension;
    uniqueness: ValidationDimension;
    timeliness: ValidationDimension;
  };
  fieldResults?: FieldValidationResult[];
  recommendations?: string[];
}

// 验证维度接口
export interface ValidationDimension {
  score: number;
  status: "pass" | "warning" | "fail";
  issues: ValidationIssue[];
}

// 验证问题接口
export interface ValidationIssue {
  type: string;
  severity: "low" | "medium" | "high" | "critical";
  message: string;
  field?: string;
  count?: number;
  examples?: any[];
}

// 字段验证结果接口
export interface FieldValidationResult {
  fieldName: string;
  score: number;
  status: "pass" | "warning" | "fail";
  issues: ValidationIssue[];
}

// 资源模板接口
export interface ResourceTemplate {
  id: string;
  name: string;
  description?: string;
  type: ResourceType;
  category?: string;
  config: ResourceConfig;
  metadata?: ResourceMetadata;
  fields?: ResourceField[];
  isPublic: boolean;
  usageCount: number;
  rating?: number;
  tags: string[];
  createdBy: string;
  createdAt: string;
  updatedAt?: string;
  version: string;
}

// 查询参数接口
export interface ResourceQuery {
  page?: number;
  size?: number;
  keyword?: string;
  type?: ResourceType;
  status?: ResourceStatus;
  categoryId?: string;
  tags?: string[];
  createdBy?: string;
  startDate?: string;
  endDate?: string;
  sortBy?: string;
  sortOrder?: "asc" | "desc";
  includeFields?: boolean;
  includeStatistics?: boolean;
  includePermissions?: boolean;
}

// 创建资源数据接口
export interface ResourceCreateData {
  name: string;
  description?: string;
  type: ResourceType;
  categoryId?: string;
  config: ResourceConfig;
  metadata?: Partial<ResourceMetadata>;
  tags?: string[];
  permissions?: Partial<ResourcePermission>[];
  isPublic?: boolean;
  templateId?: string;
}

// 更新资源数据接口
export interface ResourceUpdateData {
  name?: string;
  description?: string;
  categoryId?: string;
  config?: Partial<ResourceConfig>;
  metadata?: Partial<ResourceMetadata>;
  tags?: string[];
  status?: ResourceStatus;
  isPublic?: boolean;
}

// 连接测试数据接口
export interface ResourceTestConnection {
  type: ResourceType;
  config: ResourceConfig;
  timeout?: number;
}

// 同步数据接口
export interface ResourceSyncData {
  force?: boolean;
  tables?: string[];
  includeData?: boolean;
  batchSize?: number;
}

// 预览数据接口
export interface ResourcePreviewData {
  columns: {
    name: string;
    type: string;
    nullable?: boolean;
  }[];
  rows: any[][];
  total: number;
  page: number;
  size: number;
  hasMore: boolean;
  executionTime?: number;
  query?: string;
}

// 导入数据接口
export interface ResourceImportData {
  name: string;
  description?: string;
  type: ResourceType;
  categoryId?: string;
  config: ResourceConfig;
  metadata?: Partial<ResourceMetadata>;
  tags?: string[];
  isPublic?: boolean;
}

// 导出数据接口
export interface ResourceExportData {
  format: "json" | "yaml" | "xml" | "excel";
  includeConfig?: boolean;
  includeMetadata?: boolean;
  includeFields?: boolean;
  includePermissions?: boolean;
}

// 批量操作接口
export interface ResourceBatchOperation {
  id: string;
  operation:
    | "update"
    | "delete"
    | "move"
    | "tag"
    | "untag"
    | "enable"
    | "disable";
  data?: any;
}

// 搜索结果接口
export interface ResourceSearchResult {
  resource: DataResource;
  score: number;
  highlights?: Record<string, string[]>;
  matchedFields?: string[];
}

// 高级搜索查询接口
export interface AdvancedSearchQuery {
  filters: {
    field: string;
    operator:
      | "eq"
      | "ne"
      | "gt"
      | "gte"
      | "lt"
      | "lte"
      | "in"
      | "nin"
      | "like"
      | "regex";
    value: any;
  }[];
  fullText?: string;
  fuzzy?: boolean;
  boost?: Record<string, number>;
  page?: number;
  size?: number;
  sortBy?: string;
  sortOrder?: "asc" | "desc";
}

// 数据血缘接口
export interface DataLineage {
  resourceId: string;
  upstream: LineageNode[];
  downstream: LineageNode[];
  relationships: LineageRelationship[];
}

// 血缘节点接口
export interface LineageNode {
  id: string;
  name: string;
  type: ResourceType;
  level: number;
  metadata?: Record<string, any>;
}

// 血缘关系接口
export interface LineageRelationship {
  id: string;
  sourceId: string;
  targetId: string;
  type: "read" | "write" | "transform" | "derive";
  description?: string;
  metadata?: Record<string, any>;
}

// 数据字典接口
export interface DataDictionary {
  resourceId: string;
  tables: TableDictionary[];
  generatedAt: string;
  version: string;
}

// 表字典接口
export interface TableDictionary {
  name: string;
  comment?: string;
  type: "table" | "view" | "materialized_view";
  schema?: string;
  fields: FieldDictionary[];
  indexes?: IndexDictionary[];
  constraints?: ConstraintDictionary[];
  statistics?: TableStatistics;
}

// 字段字典接口
export interface FieldDictionary {
  name: string;
  type: string;
  length?: number;
  precision?: number;
  scale?: number;
  nullable: boolean;
  defaultValue?: any;
  comment?: string;
  isPrimaryKey: boolean;
  isForeignKey: boolean;
  isUnique: boolean;
  isIndexed: boolean;
  businessName?: string;
  businessDescription?: string;
  dataClassification?: string;
  sensitivityLevel?: string;
}

// 索引字典接口
export interface IndexDictionary {
  name: string;
  type: "primary" | "unique" | "index" | "fulltext";
  fields: string[];
  isUnique: boolean;
}

// 约束字典接口
export interface ConstraintDictionary {
  name: string;
  type: "primary_key" | "foreign_key" | "unique" | "check" | "not_null";
  fields: string[];
  referencedTable?: string;
  referencedFields?: string[];
  checkCondition?: string;
}

// 表统计信息接口
export interface TableStatistics {
  rowCount: number;
  dataSize: number;
  indexSize: number;
  lastAnalyzed?: string;
  avgRowLength?: number;
  autoIncrement?: number;
}

// 资源使用情况接口
export interface ResourceUsage {
  resourceId: string;
  period: string;
  metrics: {
    totalQueries: number;
    uniqueUsers: number;
    dataTransferred: number;
    avgResponseTime: number;
    errorCount: number;
    peakConcurrency: number;
  };
  trends: {
    queriesGrowth: number;
    usersGrowth: number;
    performanceChange: number;
  };
  topUsers: {
    userId: string;
    userName: string;
    queryCount: number;
    dataTransferred: number;
  }[];
  topQueries: {
    query: string;
    count: number;
    avgDuration: number;
  }[];
}

// 资源健康检查接口
export interface ResourceHealthCheck {
  resourceId: string;
  checkedAt: string;
  overall: {
    status: "healthy" | "warning" | "critical" | "unknown";
    score: number;
  };
  checks: {
    connectivity: HealthCheckResult;
    performance: HealthCheckResult;
    availability: HealthCheckResult;
    dataQuality: HealthCheckResult;
    security: HealthCheckResult;
    compliance: HealthCheckResult;
  };
  recommendations: string[];
  nextCheckAt: string;
}

// 健康检查结果接口
export interface HealthCheckResult {
  status: "pass" | "warning" | "fail" | "unknown";
  score: number;
  message: string;
  details?: Record<string, any>;
  checkedAt: string;
}

// 资源配额接口
export interface ResourceQuota {
  resourceId: string;
  quotas: {
    maxConnections?: number;
    maxQueriesPerHour?: number;
    maxDataTransferPerDay?: number;
    maxStorageSize?: number;
    maxCpuUsage?: number;
    maxMemoryUsage?: number;
  };
  usage: {
    currentConnections: number;
    queriesThisHour: number;
    dataTransferToday: number;
    currentStorageSize: number;
    currentCpuUsage: number;
    currentMemoryUsage: number;
  };
  alerts: {
    type: string;
    threshold: number;
    currentValue: number;
    status: "ok" | "warning" | "critical";
  }[];
}
