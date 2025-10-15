-- 数据库迁移脚本：为 customers 表添加缺失字段
-- 执行前请确保已备份数据库

USE acwl_api_system;

-- 添加缺失的字段到 customers 表
ALTER TABLE `customers` 
ADD COLUMN `rate_limit` int(11) DEFAULT NULL COMMENT '频率限制（每分钟请求数），NULL表示使用系统默认值' AFTER `status`,
ADD COLUMN `max_apis` int(11) DEFAULT NULL COMMENT '最大API数量，NULL表示使用系统默认值' AFTER `rate_limit`,
ADD COLUMN `last_login_at` timestamp NULL DEFAULT NULL COMMENT '最后登录时间' AFTER `max_apis`,
ADD COLUMN `last_api_call_at` timestamp NULL DEFAULT NULL COMMENT '最后API调用时间' AFTER `last_login_at`,
ADD COLUMN `total_api_calls` int(11) NOT NULL DEFAULT 0 COMMENT '总API调用次数' AFTER `last_api_call_at`,
ADD COLUMN `secret_reset_at` timestamp NULL DEFAULT NULL COMMENT '密钥重置时间' AFTER `total_api_calls`;

-- 添加索引以提高查询性能
ALTER TABLE `customers` 
ADD INDEX `idx_customer_status_created` (`status`, `created_at`),
ADD INDEX `idx_customer_company` (`company`);

-- 验证表结构
DESCRIBE `customers`;

SELECT 'Migration completed successfully!' as status;