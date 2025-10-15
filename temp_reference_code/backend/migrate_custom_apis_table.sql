-- 迁移脚本：为 custom_apis 表添加缺失字段
-- 执行时间：2025-07-15

USE acwl_api_system;

-- 添加 require_authentication 字段
ALTER TABLE `custom_apis` 
ADD COLUMN `require_authentication` tinyint(1) NOT NULL DEFAULT 1 COMMENT '是否需要认证：1-需要，0-不需要';

-- 添加 response_format 字段
ALTER TABLE `custom_apis` 
ADD COLUMN `response_format` enum('JSON','XML','TEXT') NOT NULL DEFAULT 'JSON' COMMENT '响应格式';

-- 添加 total_calls 字段
ALTER TABLE `custom_apis` 
ADD COLUMN `total_calls` int(11) NOT NULL DEFAULT 0 COMMENT '总调用次数';

-- 添加 last_called_at 字段
ALTER TABLE `custom_apis` 
ADD COLUMN `last_called_at` timestamp NULL DEFAULT NULL COMMENT '最后调用时间';

-- 为新字段添加索引以提高查询性能
CREATE INDEX `idx_custom_apis_require_auth` ON `custom_apis`(`require_authentication`);
CREATE INDEX `idx_custom_apis_response_format` ON `custom_apis`(`response_format`);
CREATE INDEX `idx_custom_apis_total_calls` ON `custom_apis`(`total_calls`);
CREATE INDEX `idx_custom_apis_last_called` ON `custom_apis`(`last_called_at`);

-- 验证字段是否添加成功
SELECT 
    COLUMN_NAME,
    DATA_TYPE,
    IS_NULLABLE,
    COLUMN_DEFAULT,
    COLUMN_COMMENT
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_SCHEMA = 'acwl_api_system' 
    AND TABLE_NAME = 'custom_apis'
    AND COLUMN_NAME IN ('require_authentication', 'response_format', 'total_calls', 'last_called_at')
ORDER BY ORDINAL_POSITION;

SELECT 'custom_apis 表字段迁移完成！' AS message;