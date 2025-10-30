-- 添加 is_lock 字段到 resource_packages 表
-- 用于标识资源包是否允许删除

ALTER TABLE resource_packages 
ADD COLUMN is_lock VARCHAR(10) DEFAULT 'false' COMMENT '是否允许删除';

-- 为新字段创建索引（可选，如果经常按此字段筛选）
CREATE INDEX idx_resource_packages_is_lock ON resource_packages(is_lock);

-- 更新现有记录，默认设置为 'false'（允许删除）
UPDATE resource_packages SET is_lock = 'false' WHERE is_lock IS NULL;