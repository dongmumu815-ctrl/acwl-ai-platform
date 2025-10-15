-- 迁移脚本: 024_fix_tag_status_enum.sql
-- 修复标签状态字段的枚举值，使其与 Python 枚举一致

-- 删除现有的 status 字段
ALTER TABLE acwl_data_resource_tags DROP COLUMN status;

-- 重新添加 status 字段，使用正确的枚举值
ALTER TABLE acwl_data_resource_tags 
ADD COLUMN status ENUM('ACTIVE', 'DISABLED') DEFAULT 'ACTIVE' COMMENT '标签状态：ACTIVE-启用，DISABLED-禁用';

-- 为现有数据设置默认状态为 ACTIVE
UPDATE acwl_data_resource_tags SET status = 'ACTIVE' WHERE status IS NULL;

-- 添加索引以提高查询性能
CREATE INDEX idx_acwl_data_resource_tags_status ON acwl_data_resource_tags(status);