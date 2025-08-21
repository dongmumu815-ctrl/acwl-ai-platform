-- 为数据集表添加状态字段和其他缺失字段
-- 迁移脚本: 002_add_dataset_status_field.sql

USE `acwl-ai`;

-- 添加状态字段
ALTER TABLE acwl_datasets 
ADD COLUMN status ENUM('pending', 'processing', 'ready', 'error') NOT NULL DEFAULT 'pending' COMMENT '数据集状态' AFTER is_public;

-- 添加标签字段
ALTER TABLE acwl_datasets 
ADD COLUMN tags TEXT COMMENT '标签，JSON格式存储' AFTER status;

-- 添加预览数据字段
ALTER TABLE acwl_datasets 
ADD COLUMN preview_data TEXT COMMENT '预览数据，JSON格式存储' AFTER tags;

-- 更新现有记录的状态为ready（如果有数据的话）
UPDATE acwl_datasets SET status = 'ready' WHERE record_count > 0;

-- 添加索引以提高查询性能
CREATE INDEX idx_datasets_status ON acwl_datasets(status);
CREATE INDEX idx_datasets_type ON acwl_datasets(dataset_type);
CREATE INDEX idx_datasets_created_by ON acwl_datasets(created_by);
CREATE INDEX idx_datasets_created_at ON acwl_datasets(created_at);