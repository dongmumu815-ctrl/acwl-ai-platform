-- 为模型表添加下载状态相关字段
-- 迁移脚本: 003_add_model_download_fields.sql

USE `acwl-ai`;

-- 添加下载状态字段
ALTER TABLE acwl_models 
ADD COLUMN download_status ENUM('PENDING', 'DOWNLOADING', 'COMPLETED', 'FAILED', 'UPLOADED') NULL DEFAULT NULL COMMENT '下载状态' AFTER is_active;

-- 添加下载进度字段
ALTER TABLE acwl_models 
ADD COLUMN download_progress DECIMAL(5,2) NULL DEFAULT NULL COMMENT '下载进度百分比(0-100)' AFTER download_status;

-- 添加下载错误信息字段
ALTER TABLE acwl_models 
ADD COLUMN download_error TEXT NULL DEFAULT NULL COMMENT '下载错误信息' AFTER download_progress;

-- 添加索引以提高查询性能
CREATE INDEX idx_models_download_status ON acwl_models(download_status);

-- 验证字段添加成功
DESCRIBE acwl_models;

SELECT 'Model download fields migration completed successfully!' as status;