-- 添加 agent_type 字段到 acwl_agents 表
-- Migration: 012_add_agent_type_field.sql
-- Date: 2025-01-21
-- Description: 为智能体表添加 agent_type 字段，用于区分不同类型的智能体（CUSTOM、REVIEW等）

USE `acwl-ai`;

-- 1. 添加 agent_type 字段
ALTER TABLE acwl_agents 
ADD COLUMN agent_type ENUM('CUSTOM', 'REVIEW') NOT NULL DEFAULT 'CUSTOM' 
COMMENT 'Agent类型：CUSTOM-自定义，REVIEW-审读' 
AFTER description;

-- 2. 为现有记录设置默认值
UPDATE acwl_agents 
SET agent_type = 'CUSTOM' 
WHERE agent_type IS NULL;

-- 3. 添加索引以提高查询性能
CREATE INDEX idx_agents_agent_type ON acwl_agents(agent_type);

-- 4. 验证字段添加成功
SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_DEFAULT, COLUMN_COMMENT
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_SCHEMA = 'acwl-ai' 
  AND TABLE_NAME = 'acwl_agents'
  AND COLUMN_NAME = 'agent_type';

COMMIT;