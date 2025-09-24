-- 迁移脚本：允许 resource_packages 表的 template_id 字段为 NULL
-- 创建时间：2025-01-25
-- 目的：修复创建资源包时 template_id 为 null 导致的验证错误

-- 修改 template_id 字段允许 NULL 值
ALTER TABLE resource_packages 
MODIFY COLUMN template_id INT NULL COMMENT '关联的查询模板ID';

-- 更新约束检查（如果存在的话）
-- 注意：这里假设之前可能有约束检查 template_id 不为 NULL
-- 如果有相关的约束，需要先删除再重新创建

-- 验证修改结果
SELECT 
    COLUMN_NAME,
    IS_NULLABLE,
    DATA_TYPE,
    COLUMN_COMMENT
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_SCHEMA = DATABASE() 
    AND TABLE_NAME = 'resource_packages' 
    AND COLUMN_NAME = 'template_id';