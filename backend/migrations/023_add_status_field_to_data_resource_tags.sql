-- 迁移脚本: 023_add_status_field_to_data_resource_tags.sql
-- 为数据资源标签表添加状态字段，支持启用/禁用功能

-- 添加 status 字段到 acwl_data_resource_tags 表
ALTER TABLE acwl_data_resource_tags 
ADD COLUMN status ENUM('ACTIVE', 'DISABLED') DEFAULT 'ACTIVE' COMMENT '标签状态：ACTIVE-启用，DISABLED-禁用';

-- 为现有数据设置默认状态为 ACTIVE
UPDATE acwl_data_resource_tags SET status = 'ACTIVE' WHERE status IS NULL;

-- 添加索引以提高查询性能
CREATE INDEX idx_acwl_data_resource_tags_status ON acwl_data_resource_tags(status);