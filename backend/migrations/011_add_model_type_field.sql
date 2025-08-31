-- 添加model_type字段到模型服务配置表
-- Migration: 011_add_model_type_field.sql
-- Date: 2024-12-19
-- Description: 为模型服务配置表添加model_type字段，用于区分不同类型的模型（chat、embedding、image等）

ALTER TABLE acwl_model_service_configs 
ADD COLUMN model_type VARCHAR(50) DEFAULT 'chat' COMMENT '模型类型';

-- 为现有记录设置默认值
UPDATE acwl_model_service_configs 
SET model_type = 'chat' 
WHERE model_type IS NULL;

-- 添加索引以提高查询性能
CREATE INDEX idx_model_service_configs_model_type ON acwl_model_service_configs(model_type);