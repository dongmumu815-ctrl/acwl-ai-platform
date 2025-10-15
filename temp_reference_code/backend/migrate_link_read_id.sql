-- 迁移脚本：将customers表中的link_read_id字段迁移至custom_apis表
-- 执行时间：2024-07-20

USE acwl_api_system;

-- 1. 在custom_apis表中添加link_read_id字段（如果不存在）
-- 首先检查字段是否存在
SET @column_exists = 0;
SELECT COUNT(*) INTO @column_exists FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'custom_apis' AND COLUMN_NAME = 'link_read_id';

-- 如果字段不存在，则添加
SET @sql = IF(@column_exists = 0, 'ALTER TABLE `custom_apis` ADD COLUMN `link_read_id` varchar(50) DEFAULT NULL COMMENT \'链接其他系统的ID\'', 'SELECT "字段已存在，跳过添加" AS message');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 2. 为新字段添加索引以提高查询性能
-- 首先检查索引是否存在
SET @index_exists = 0;
SELECT COUNT(*) INTO @index_exists FROM INFORMATION_SCHEMA.STATISTICS
WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'custom_apis' AND INDEX_NAME = 'idx_custom_apis_link_read_id';

-- 如果索引不存在，则创建
SET @sql = IF(@index_exists = 0, 'CREATE INDEX `idx_custom_apis_link_read_id` ON `custom_apis`(`link_read_id`)', 'SELECT "索引已存在，跳过创建" AS message');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 3. 将customers表中的link_read_id值迁移到对应客户的所有custom_apis记录中
UPDATE `custom_apis` ca
JOIN `customers` c ON ca.customer_id = c.id
SET ca.link_read_id = c.link_read_id
WHERE c.link_read_id IS NOT NULL AND c.link_read_id != '';

-- 4. 验证迁移结果
SELECT 
    c.id as customer_id, 
    c.name as customer_name, 
    c.link_read_id as customer_link_id,
    ca.id as api_id, 
    ca.api_name, 
    ca.link_read_id as api_link_id
FROM `customers` c
JOIN `custom_apis` ca ON c.id = ca.customer_id
WHERE c.link_read_id IS NOT NULL AND c.link_read_id != ''
LIMIT 10;

-- 5. 统计迁移结果
SELECT 
    COUNT(*) as total_apis_updated,
    COUNT(DISTINCT customer_id) as total_customers_affected
FROM `custom_apis`
WHERE link_read_id IS NOT NULL AND link_read_id != '';

SELECT 'link_read_id 字段迁移完成！' AS message;