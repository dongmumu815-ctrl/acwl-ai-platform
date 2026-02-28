// 基础响应类型
export interface ApiResponse<T = any> {
  code: number;
  message: string;
  data: T;
  timestamp: string;
}

export interface PaginatedResponse<T> extends ApiResponse<T[]> {
  pagination: {
    page: number;
    page_size: number;
    total: number;
    total_pages: number;
  };
}

// 系统信息
export interface SystemInfo {
  system_name: string;
  system_version: string;
  system_description: string;
  build_time: string;
  build_version: string;
  environment: "development" | "testing" | "production";
  database_version: string;
  python_version: string;
  platform: string;
  architecture: string;
  timezone: string;
  uptime: number;
  start_time: string;
}

// 系统状态
export interface SystemStatus {
  status: "healthy" | "warning" | "error";
  cpu_usage: number;
  memory_usage: number;
  disk_usage: number;
  network_status: "connected" | "disconnected";
  database_status: "connected" | "disconnected" | "error";
  cache_status: "connected" | "disconnected" | "error";
  active_users: number;
  active_sessions: number;
  last_check_time: string;
  services: SystemService[];
}

// 系统服务
export interface SystemService {
  name: string;
  status: "running" | "stopped" | "error";
  uptime: number;
  memory_usage: number;
  cpu_usage: number;
  last_restart: string;
  description: string;
}

// 系统设置
export interface SystemSettings {
  basic: BasicSettings;
  security: SecuritySettings;
  email: EmailSettings;
  storage: StorageSettings;
  backup: BackupSettings;
  logs: LogSettings;
  performance: PerformanceSettings;
}

// 基本设置
export interface BasicSettings {
  system_name: string;
  system_description: string;
  system_version: string;
  default_language: string;
  default_timezone: string;
  default_page_size: number;
  maintenance_mode: boolean;
  allow_registration: boolean;
  terms_of_service_url?: string;
  privacy_policy_url?: string;
  support_email?: string;
  support_phone?: string;
}

// 安全设置
export interface SecuritySettings {
  password_policy: PasswordPolicy;
  password_expiry_days: number;
  max_login_attempts: number;
  lockout_duration: number;
  session_timeout: number;
  enable_2fa: boolean;
  ip_whitelist: string;
  allowed_origins: string[];
  csrf_protection: boolean;
  secure_cookies: boolean;
}

// 密码策略
export interface PasswordPolicy {
  min_length: number;
  max_length: number;
  require_uppercase: boolean;
  require_lowercase: boolean;
  require_numbers: boolean;
  require_symbols: boolean;
  forbidden_patterns: string[];
}

// 邮件设置
export interface EmailSettings {
  smtp_host: string;
  smtp_port: number;
  smtp_username: string;
  smtp_password: string;
  smtp_encryption: "none" | "ssl" | "tls";
  from_email: string;
  from_name: string;
  reply_to_email?: string;
  bounce_email?: string;
  max_send_rate: number;
  template_path: string;
}

// 存储设置
export interface StorageSettings {
  storage_type: "local" | "aliyun_oss" | "tencent_cos" | "aws_s3" | "minio";
  storage_path: string;
  max_file_size: number;
  allowed_file_types: string;
  storage_config: string;
  enable_cdn: boolean;
  cdn_domain?: string;
  auto_cleanup: boolean;
  cleanup_days: number;
}

// 备份设置
export interface BackupSettings {
  auto_backup: boolean;
  backup_frequency: "daily" | "weekly" | "monthly";
  backup_time: string;
  retention_days: number;
  backup_path: string;
  compress_backup: boolean;
  include_files: boolean;
  include_database: boolean;
  backup_encryption: boolean;
  encryption_key?: string;
}

// 日志设置
export interface LogSettings {
  log_level: "debug" | "info" | "warning" | "error";
  log_retention_days: number;
  max_log_file_size: number;
  log_user_actions: boolean;
  log_api_calls: boolean;
  log_database_queries: boolean;
  log_file_path: string;
  enable_remote_logging: boolean;
  remote_log_endpoint?: string;
}

// 性能设置
export interface PerformanceSettings {
  enable_cache: boolean;
  cache_type: "memory" | "redis" | "memcached";
  cache_ttl: number;
  cache_max_size: number;
  db_pool_size: number;
  db_pool_timeout: number;
  enable_rate_limit: boolean;
  rate_limit_per_minute: number;
  enable_compression: boolean;
  compression_level: number;
  enable_static_cache: boolean;
  static_cache_ttl: number;
}

// 备份记录
export interface BackupRecord {
  id: string;
  filename: string;
  file_path: string;
  file_size: number;
  backup_type: "manual" | "auto";
  status: "pending" | "running" | "completed" | "failed";
  progress: number;
  error_message?: string;
  created_at: string;
  completed_at?: string;
  created_by: string;
  includes_files: boolean;
  includes_database: boolean;
  is_encrypted: boolean;
}

// 日志记录
export interface LogRecord {
  id: string;
  timestamp: string;
  level: "debug" | "info" | "warning" | "error";
  logger: string;
  message: string;
  module: string;
  function: string;
  line_number: number;
  user_id?: string;
  session_id?: string;
  ip_address?: string;
  user_agent?: string;
  request_id?: string;
  extra_data?: Record<string, any>;
}

// 性能指标
export interface PerformanceMetrics {
  timestamp: string;
  cpu_usage: number;
  memory_usage: number;
  disk_usage: number;
  network_in: number;
  network_out: number;
  active_connections: number;
  database_connections: number;
  cache_hit_rate: number;
  response_time: number;
  requests_per_second: number;
  error_rate: number;
}

// 邮件测试请求
export interface EmailTestRequest {
  smtp_host: string;
  smtp_port: number;
  smtp_username: string;
  smtp_password: string;
  smtp_encryption: "none" | "ssl" | "tls";
  from_email: string;
  test_email?: string;
}

// 备份创建请求
export interface BackupCreateRequest {
  backup_type?: "manual" | "auto";
  include_files?: boolean;
  include_database?: boolean;
  compress?: boolean;
  encrypt?: boolean;
  description?: string;
}

// 日志查询参数
export interface LogQueryParams {
  page?: number;
  page_size?: number;
  level?: "debug" | "info" | "warning" | "error";
  logger?: string;
  module?: string;
  user_id?: string;
  start_time?: string;
  end_time?: string;
  keyword?: string;
  ip_address?: string;
  request_id?: string;
}

// 系统更新请求
export interface SystemUpdateRequest {
  version?: string;
  update_type: "patch" | "minor" | "major";
  force_update?: boolean;
  backup_before_update?: boolean;
  restart_after_update?: boolean;
}

// 系统许可证
export interface SystemLicense {
  license_key: string;
  license_type: "trial" | "standard" | "professional" | "enterprise";
  issued_to: string;
  issued_date: string;
  expires_date: string;
  max_users: number;
  max_storage: number;
  features: string[];
  is_valid: boolean;
  days_remaining: number;
}

// 缓存统计
export interface CacheStatistics {
  total_keys: number;
  memory_usage: number;
  hit_rate: number;
  miss_rate: number;
  evictions: number;
  connections: number;
  cache_types: CacheTypeStats[];
}

export interface CacheTypeStats {
  type: string;
  keys: number;
  memory: number;
  hit_rate: number;
  ttl_average: number;
}

// 系统健康检查
export interface HealthCheck {
  name: string;
  status: "pass" | "fail" | "warn";
  message: string;
  duration: number;
  timestamp: string;
  details?: Record<string, any>;
}

export interface SystemHealth {
  status: "healthy" | "warning" | "error";
  checks: HealthCheck[];
  timestamp: string;
  overall_score: number;
}

// 系统统计
export interface SystemStatistics {
  total_users: number;
  active_users: number;
  total_resources: number;
  total_storage_used: number;
  total_api_calls: number;
  system_uptime: number;
  last_backup: string;
  database_size: number;
  cache_size: number;
  log_size: number;
  error_count_24h: number;
  avg_response_time: number;
}

// 系统配置模板
export interface SystemConfigTemplate {
  basic: Partial<BasicSettings>;
  security: Partial<SecuritySettings>;
  email: Partial<EmailSettings>;
  storage: Partial<StorageSettings>;
  backup: Partial<BackupSettings>;
  logs: Partial<LogSettings>;
  performance: Partial<PerformanceSettings>;
}

// 系统更新状态
export interface SystemUpdateStatus {
  update_id: string;
  status: "pending" | "downloading" | "installing" | "completed" | "failed";
  progress: number;
  message: string;
  started_at: string;
  completed_at?: string;
  error_message?: string;
  rollback_available: boolean;
}

// 系统更新信息
export interface SystemUpdateInfo {
  has_update: boolean;
  current_version: string;
  latest_version?: string;
  release_notes?: string;
  update_size?: number;
  release_date?: string;
  security_update: boolean;
  breaking_changes: boolean;
  minimum_requirements?: Record<string, string>;
}

// 枚举类型
export enum SystemStatus {
  HEALTHY = "healthy",
  WARNING = "warning",
  ERROR = "error",
}

export enum ServiceStatus {
  RUNNING = "running",
  STOPPED = "stopped",
  ERROR = "error",
}

export enum LogLevel {
  DEBUG = "debug",
  INFO = "info",
  WARNING = "warning",
  ERROR = "error",
}

export enum BackupStatus {
  PENDING = "pending",
  RUNNING = "running",
  COMPLETED = "completed",
  FAILED = "failed",
}

export enum BackupType {
  MANUAL = "manual",
  AUTO = "auto",
}

export enum StorageType {
  LOCAL = "local",
  ALIYUN_OSS = "aliyun_oss",
  TENCENT_COS = "tencent_cos",
  AWS_S3 = "aws_s3",
  MINIO = "minio",
}

export enum CacheType {
  MEMORY = "memory",
  REDIS = "redis",
  MEMCACHED = "memcached",
}

export enum UpdateType {
  PATCH = "patch",
  MINOR = "minor",
  MAJOR = "major",
}

export enum LicenseType {
  TRIAL = "trial",
  STANDARD = "standard",
  PROFESSIONAL = "professional",
  ENTERPRISE = "enterprise",
}
