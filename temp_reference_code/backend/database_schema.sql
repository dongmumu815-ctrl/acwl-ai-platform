-- 自定义接口系统数据库建表语句
-- 数据库: acwl_api_system
-- 字符集: utf8mb4
-- 排序规则: utf8mb4_unicode_ci

CREATE DATABASE IF NOT EXISTS acwl_api_system CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE acwl_api_system;

-- 1. 平台管理表
CREATE TABLE `customers` (
    `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT COMMENT '客户ID',
    `name` varchar(100) NOT NULL COMMENT '客户名称',
    `email` varchar(100) NOT NULL COMMENT '客户邮箱',
    `phone` varchar(20) DEFAULT NULL COMMENT '联系电话',
    `company` varchar(200) DEFAULT NULL COMMENT '公司名称',
    `app_id` varchar(32) NOT NULL COMMENT '应用ID',
    `app_secret` varchar(64) NOT NULL COMMENT '应用密钥',
    `link_read_id` varchar(50) DEFAULT NULL COMMENT '链接其他系统的ID',
    `status` tinyint(1) NOT NULL DEFAULT 1 COMMENT '状态：1-启用，0-禁用',
    `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_app_id` (`app_id`),
    UNIQUE KEY `uk_email` (`email`),
    INDEX `idx_status` (`status`),
    INDEX `idx_link_read_id` (`link_read_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='平台管理表';

-- 2. 客户登录状态表
CREATE TABLE `customer_sessions` (
    `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT COMMENT '会话ID',
    `customer_id` bigint(20) unsigned NOT NULL COMMENT '客户ID',
    `session_token` varchar(128) NOT NULL COMMENT '会话令牌',
    `login_ip` varchar(45) DEFAULT NULL COMMENT '登录IP',
    `user_agent` text DEFAULT NULL COMMENT '用户代理',
    `login_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '登录时间',
    `last_activity` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '最后活动时间',
    `expires_at` timestamp NOT NULL COMMENT '过期时间',
    `is_active` tinyint(1) NOT NULL DEFAULT 1 COMMENT '是否活跃：1-活跃，0-已退出',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_session_token` (`session_token`),
    INDEX `idx_customer_id` (`customer_id`),
    INDEX `idx_expires_at` (`expires_at`),
    INDEX `idx_is_active` (`is_active`),
    FOREIGN KEY (`customer_id`) REFERENCES `customers`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='客户登录状态表';

-- 3. 自定义接口定义表
CREATE TABLE `custom_apis` (
    `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT COMMENT '接口ID',
    `customer_id` bigint(20) unsigned NOT NULL COMMENT '客户ID',
    `api_name` varchar(100) NOT NULL COMMENT '接口名称',
    `api_code` varchar(50) NOT NULL COMMENT '接口代码（用于生成URL）',
    `api_description` text DEFAULT NULL COMMENT '接口描述',
    `api_url` varchar(200) NOT NULL COMMENT '生成的接口URL',
    `http_method` varchar(10) NOT NULL DEFAULT 'POST' COMMENT 'HTTP方法：GET,POST,PUT,DELETE',
    `status` tinyint(1) NOT NULL DEFAULT 1 COMMENT '状态：1-开放，0-停用',
    `rate_limit` int(11) DEFAULT NULL COMMENT '频率限制（每分钟请求数）',
    `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_customer_api_code` (`customer_id`, `api_code`),
    INDEX `idx_status` (`status`),
    INDEX `idx_api_code` (`api_code`),
    FOREIGN KEY (`customer_id`) REFERENCES `customers`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='自定义接口定义表';

-- 4. 数据结构字段定义表
CREATE TABLE `api_fields` (
    `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT COMMENT '字段ID',
    `api_id` bigint(20) unsigned NOT NULL COMMENT '接口ID',
    `field_name` varchar(50) NOT NULL COMMENT '字段名称',
    `field_label` varchar(100) NOT NULL COMMENT '字段标签',
    `field_type` varchar(20) NOT NULL COMMENT '字段类型：string,int,float,boolean,date,datetime,json,file',
    `is_required` tinyint(1) NOT NULL DEFAULT 0 COMMENT '是否必填：1-必填，0-可选',
    `default_value` text DEFAULT NULL COMMENT '默认值',
    `max_length` int(11) DEFAULT NULL COMMENT '最大长度（字符串类型）',
    `min_length` int(11) DEFAULT NULL COMMENT '最小长度（字符串类型）',
    `max_value` decimal(20,6) DEFAULT NULL COMMENT '最大值（数值类型）',
    `min_value` decimal(20,6) DEFAULT NULL COMMENT '最小值（数值类型）',
    `allowed_values` text DEFAULT NULL COMMENT '允许的值（JSON数组格式）',
    `validation_regex` varchar(500) DEFAULT NULL COMMENT '验证正则表达式',
    `validation_message` varchar(200) DEFAULT NULL COMMENT '验证失败提示信息',
    `sort_order` int(11) NOT NULL DEFAULT 0 COMMENT '排序顺序',
    `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_api_field_name` (`api_id`, `field_name`),
    INDEX `idx_sort_order` (`sort_order`),
    FOREIGN KEY (`api_id`) REFERENCES `custom_apis`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='数据结构字段定义表';

-- 5. 接口使用日志表
CREATE TABLE `api_usage_logs` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT COMMENT '日志ID',
  `customer_id` bigint unsigned NOT NULL COMMENT '客户ID',
  `api_id` bigint unsigned NOT NULL COMMENT '接口ID',
  `request_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '请求ID（用于追踪）',
  `client_ip` varchar(45) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '客户端IP地址',
  `http_method` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'HTTP方法',
  `request_url` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '请求URL',
  `request_headers` json DEFAULT NULL COMMENT '请求头信息（JSON格式）',
  `request_params` json DEFAULT NULL COMMENT '请求参数（JSON格式）',
  `file_path` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '存储路径',
  `response_status` int NOT NULL COMMENT 'HTTP响应状态码',
  `response_headers` json DEFAULT NULL COMMENT '响应头信息（JSON格式）',
  `processing_time` decimal(10,6) DEFAULT NULL COMMENT '处理时间（秒）',
  `error_message` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '错误信息',
  `error_traceback` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '错误堆栈信息',
  `batch_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '批次ID（用于批量数据追踪）',
  `data_size` int DEFAULT NULL COMMENT '数据大小（字节）',
  `record_count` int DEFAULT NULL COMMENT '处理记录数',
  `user_agent` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '用户代理字符串',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `timestamp` bigint DEFAULT NULL COMMENT '请求时间戳（用于防重放攻击）',
  `nonce` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '随机字符串（用于增强请求唯一性）',
  `encrypted_data` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '加密后的业务数据（Base64编码）',
  `iv` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '初始化向量（IV），用于AES解密',
  `signature` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '数据签名值（HMAC-SHA256）',
  `needread` tinyint(1) DEFAULT '0' COMMENT '是否需要读取确认',
  `is_encrypted` tinyint(1) DEFAULT '0' COMMENT '是否为加密请求',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_request_id` (`request_id`),
  KEY `idx_customer_id` (`customer_id`),
  KEY `idx_api_id` (`api_id`),
  KEY `idx_request_id` (`request_id`),
  KEY `idx_created_at` (`created_at`),
  KEY `idx_response_status` (`response_status`),
  KEY `idx_api_usage_logs_customer_created` (`customer_id`,`created_at`),
  KEY `idx_log_customer_created` (`customer_id`,`created_at`),
  KEY `idx_log_api_created` (`api_id`,`created_at`),
  KEY `idx_log_status_created` (`response_status`,`created_at`),
  KEY `idx_log_ip_created` (`client_ip`,`created_at`),
  KEY `idx_log_processing_time` (`processing_time`),
  KEY `idx_log_batch` (`batch_id`),
  KEY `idx_log_batch_created` (`batch_id`,`created_at`),
  KEY `idx_log_timestamp` (`timestamp`),
  KEY `idx_log_nonce` (`nonce`),
  KEY `idx_log_encrypted` (`is_encrypted`),
  CONSTRAINT `api_usage_logs_ibfk_1` FOREIGN KEY (`customer_id`) REFERENCES `customers` (`id`) ON DELETE CASCADE,
  CONSTRAINT `api_usage_logs_ibfk_2` FOREIGN KEY (`api_id`) REFERENCES `custom_apis` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=235 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='接口使用日志表 - 记录所有接口调用的详细日志';

-- 6. 系统管理员表
CREATE TABLE `admin_users` (
    `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT COMMENT '管理员ID',
    `username` varchar(50) NOT NULL COMMENT '用户名',
    `password_hash` varchar(255) NOT NULL COMMENT '密码哈希（加密存储）',
    `email` varchar(100) NOT NULL COMMENT '邮箱',
    `real_name` varchar(100) DEFAULT NULL COMMENT '真实姓名',
    `is_active` tinyint(1) NOT NULL DEFAULT 1 COMMENT '是否激活：1-激活，0-禁用',
    `is_superuser` tinyint(1) NOT NULL DEFAULT 0 COMMENT '是否超级管理员：1-是，0-否',
    `permissions` json DEFAULT NULL COMMENT '权限列表（JSON数组）',
    `last_login_at` timestamp NULL DEFAULT NULL COMMENT '最后登录时间',
    `last_login_ip` varchar(45) DEFAULT NULL COMMENT '最后登录IP',
    `login_count` int(11) NOT NULL DEFAULT 0 COMMENT '登录次数',
    `failed_login_count` int(11) NOT NULL DEFAULT 0 COMMENT '失败登录次数',
    `locked_until` timestamp NULL DEFAULT NULL COMMENT '锁定到期时间',
    `password_changed_at` timestamp NULL DEFAULT NULL COMMENT '密码修改时间',
    `must_change_password` tinyint(1) NOT NULL DEFAULT 0 COMMENT '是否必须修改密码：1-是，0-否',
    `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_username` (`username`),
    UNIQUE KEY `uk_email` (`email`),
    INDEX `idx_admin_username` (`username`),
    INDEX `idx_admin_email` (`email`),
    INDEX `idx_admin_active` (`is_active`),
    INDEX `idx_admin_last_login` (`last_login_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='系统管理员表';

-- 7. 数据批次管理表
CREATE TABLE `data_batches` (
    `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT COMMENT '批次ID',
    `customer_id` bigint(20) unsigned NOT NULL COMMENT '客户ID',
    `api_id` bigint(20) unsigned NOT NULL COMMENT 'API ID',
    `batch_id` varchar(36) NOT NULL COMMENT '批次唯一标识符（UUID）',
    `batch_name` varchar(100) NOT NULL COMMENT '批次名称',
    `description` text DEFAULT NULL COMMENT '批次描述',
    `status` enum('pending','processing','completed','failed','cancelled') NOT NULL DEFAULT 'pending' COMMENT '批次状态',
    `expected_count` int(11) DEFAULT NULL COMMENT '预期数据条数',
    `total_count` int(11) NOT NULL DEFAULT 0 COMMENT '实际数据条数',
    `pending_count` int(11) NOT NULL DEFAULT 0 COMMENT '待处理数据条数',
    `processing_count` int(11) NOT NULL DEFAULT 0 COMMENT '处理中数据条数',
    `completed_count` int(11) NOT NULL DEFAULT 0 COMMENT '已完成数据条数',
    `failed_count` int(11) NOT NULL DEFAULT 0 COMMENT '失败数据条数',
    `processing_started_at` timestamp NULL DEFAULT NULL COMMENT '处理开始时间',
    `processing_completed_at` timestamp NULL DEFAULT NULL COMMENT '处理完成时间',
    `processing_duration` int(11) DEFAULT NULL COMMENT '处理耗时（秒）',
    `error_message` text DEFAULT NULL COMMENT '错误信息',
    `metadata` json DEFAULT NULL COMMENT '元数据（JSON格式）',
    `callback_url` varchar(500) DEFAULT NULL COMMENT '回调地址链接',
    `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_batch_id` (`batch_id`),
    INDEX `idx_customer_id` (`customer_id`),
    INDEX `idx_api_id` (`api_id`),
    INDEX `idx_status` (`status`),
    INDEX `idx_created_at` (`created_at`),
    INDEX `idx_customer_status` (`customer_id`, `status`),
    INDEX `idx_processing_times` (`processing_started_at`, `processing_completed_at`),
    FOREIGN KEY (`customer_id`) REFERENCES `customers`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`api_id`) REFERENCES `custom_apis`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='数据批次管理表';

-- 8. 数据上传记录表
CREATE TABLE `data_uploads` (
    `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT COMMENT '上传记录ID',
    `customer_id` bigint(20) unsigned NOT NULL COMMENT '客户ID',
    `api_id` bigint(20) unsigned NOT NULL COMMENT '接口ID',
    `batch_id` varchar(36) DEFAULT NULL COMMENT '关联的批次ID',
    `upload_data` longtext NOT NULL COMMENT '上传的数据（JSON格式）',
    `validation_status` tinyint(1) NOT NULL DEFAULT 1 COMMENT '验证状态：1-通过，0-失败',
    `validation_errors` text DEFAULT NULL COMMENT '验证错误信息（JSON格式）',
    `file_attachments` text DEFAULT NULL COMMENT '文件附件信息（JSON格式）',
    `processing_status` varchar(20) NOT NULL DEFAULT 'pending' COMMENT '处理状态：pending,processing,completed,failed',
    `processing_result` text DEFAULT NULL COMMENT '处理结果',
    `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    INDEX `idx_customer_id` (`customer_id`),
    INDEX `idx_api_id` (`api_id`),
    INDEX `idx_batch_id` (`batch_id`),
    INDEX `idx_validation_status` (`validation_status`),
    INDEX `idx_processing_status` (`processing_status`),
    INDEX `idx_created_at` (`created_at`),
    FOREIGN KEY (`customer_id`) REFERENCES `customers`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`api_id`) REFERENCES `custom_apis`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`batch_id`) REFERENCES `data_batches`(`batch_id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='数据上传记录表';

-- 9. 系统配置表
CREATE TABLE `system_configs` (
    `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT COMMENT '配置ID',
    `config_key` varchar(100) NOT NULL COMMENT '配置键',
    `config_value` text NOT NULL COMMENT '配置值',
    `config_type` varchar(20) NOT NULL DEFAULT 'string' COMMENT '配置类型：string,int,float,boolean,json',
    `description` varchar(200) DEFAULT NULL COMMENT '配置描述',
    `is_public` tinyint(1) NOT NULL DEFAULT 0 COMMENT '是否公开：1-公开，0-私有',
    `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_config_key` (`config_key`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='系统配置表';

-- 插入默认管理员账户（密码需要在应用中加密）
INSERT INTO `admin_users` (`username`, `password`, `email`, `real_name`, `role`) VALUES 
('admin', 'admin123', 'admin@example.com', '系统管理员', 'super_admin');

-- 插入默认系统配置
INSERT INTO `system_configs` (`config_key`, `config_value`, `config_type`, `description`, `is_public`) VALUES 
('system_name', '自定义接口管理系统', 'string', '系统名称', 1),
('max_api_per_customer', '10', 'int', '每个客户最大接口数量', 0),
('default_rate_limit', '100', 'int', '默认频率限制（每分钟）', 0),
('session_timeout', '7200', 'int', '会话超时时间（秒）', 0),
('max_upload_size', '10485760', 'int', '最大上传文件大小（字节）', 0);

-- 创建索引优化查询性能
CREATE INDEX `idx_customers_created_at` ON `customers`(`created_at`);
CREATE INDEX `idx_api_usage_logs_customer_created` ON `api_usage_logs`(`customer_id`, `created_at`);
CREATE INDEX `idx_data_uploads_customer_created` ON `data_uploads`(`customer_id`, `created_at`);
CREATE INDEX `idx_data_batches_customer_created` ON `data_batches`(`customer_id`, `created_at`);
CREATE INDEX `idx_data_uploads_batch_created` ON `data_uploads`(`batch_id`, `created_at`);

-- 创建批次统计视图
CREATE OR REPLACE VIEW `v_batch_stats` AS
SELECT 
    db.id,
    db.batch_id,
    db.batch_name,
    db.customer_id,
    c.name as customer_name,
    c.company as company_name,
    db.api_id,
    ca.api_name,
    db.status,
    db.expected_count,
    db.total_count,
    db.pending_count,
    db.processing_count,
    db.completed_count,
    db.failed_count,
    CASE 
        WHEN db.total_count > 0 THEN ROUND((db.completed_count / db.total_count) * 100, 2)
        ELSE 0
    END as completion_rate,
    db.processing_started_at,
    db.processing_completed_at,
    db.processing_duration,
    db.created_at,
    db.updated_at
FROM `data_batches` db
LEFT JOIN `customers` c ON db.customer_id = c.id
LEFT JOIN `custom_apis` ca ON db.api_id = ca.id;

-- 添加表注释
ALTER TABLE `customers` COMMENT = '平台管理表 - 存储客户基本信息和认证信息';
ALTER TABLE `customer_sessions` COMMENT = '客户登录状态表 - 管理客户登录会话';
ALTER TABLE `custom_apis` COMMENT = '自定义接口定义表 - 存储客户自定义的接口配置';
ALTER TABLE `api_fields` COMMENT = '数据结构字段定义表 - 定义接口的数据结构和验证规则';
ALTER TABLE `api_usage_logs` COMMENT = '接口使用日志表 - 记录所有接口调用的详细日志';
ALTER TABLE `admin_users` COMMENT = '系统管理员表 - 管理系统管理员账户';
ALTER TABLE `data_batches` COMMENT = '数据批次管理表 - 管理数据上传批次和状态跟踪';
ALTER TABLE `data_uploads` COMMENT = '数据上传记录表 - 记录通过接口上传的数据';
ALTER TABLE `system_configs` COMMENT = '系统配置表 - 存储系统全局配置参数';

-- 数据库初始化完成说明
-- 1. 包含完整的平台管理、接口定义、数据上传和批次管理功能
-- 2. 数据批次管理表支持批次状态跟踪和统计信息维护
-- 3. 批次统计视图提供便捷的批次数据查询
-- 4. 相关索引和外键约束确保数据完整性和查询性能
-- 5. 默认管理员账户和系统配置已初始化