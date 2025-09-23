-- 为SQL查询模板表添加配置字段
-- Migration: 017_add_config_to_sql_templates.sql
-- Date: 2025-01-20
-- Description: 为sql_query_templates表添加config字段，用于存储查询条件的JSON配置信息

-- 添加config字段
ALTER TABLE sql_query_templates 
ADD COLUMN config JSON COMMENT 'JSON格式存储查询条件配置信息，包括必填条件、可选条件等';

-- 为现有记录设置默认值（空JSON对象）
UPDATE sql_query_templates 
SET config = JSON_OBJECT() 
WHERE config IS NULL;

-- 添加索引以提高查询性能（如果需要按配置内容查询）
-- CREATE INDEX idx_sql_templates_config ON sql_query_templates((JSON_EXTRACT(config, '$.required')));