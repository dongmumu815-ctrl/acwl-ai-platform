-- 为 acwl_data_resource_tags 表添加 created_by 和 updated_by 字段
-- 这个迁移为标签表添加用户关联字段，使其符合 UserMixin 的要求

-- 添加 created_by 字段到 acwl_data_resource_tags 表
ALTER TABLE acwl_data_resource_tags ADD COLUMN created_by INTEGER;
ALTER TABLE acwl_data_resource_tags ADD CONSTRAINT fk_acwl_data_resource_tags_created_by 
    FOREIGN KEY (created_by) REFERENCES acwl_users(id) ON DELETE SET NULL;

-- 添加 updated_by 字段到 acwl_data_resource_tags 表
ALTER TABLE acwl_data_resource_tags ADD COLUMN updated_by INTEGER;
ALTER TABLE acwl_data_resource_tags ADD CONSTRAINT fk_acwl_data_resource_tags_updated_by 
    FOREIGN KEY (updated_by) REFERENCES acwl_users(id) ON DELETE SET NULL;

-- 为新字段添加索引以提高查询性能
CREATE INDEX idx_acwl_data_resource_tags_created_by ON acwl_data_resource_tags(created_by);
CREATE INDEX idx_acwl_data_resource_tags_updated_by ON acwl_data_resource_tags(updated_by);

-- 注释说明 (MySQL使用ALTER TABLE语法添加注释)
ALTER TABLE acwl_data_resource_tags MODIFY COLUMN created_by INTEGER COMMENT '创建者ID';
ALTER TABLE acwl_data_resource_tags MODIFY COLUMN updated_by INTEGER COMMENT '更新者ID';