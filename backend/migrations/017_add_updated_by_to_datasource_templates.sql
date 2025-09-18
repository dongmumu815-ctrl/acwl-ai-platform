-- 为数据源模板表添加updated_by字段
-- 创建时间: 2024-01-22
-- 描述: 为acwl_datasource_templates表添加updated_by字段及外键约束

-- 为acwl_datasource_templates表添加updated_by字段
ALTER TABLE acwl_datasource_templates ADD COLUMN updated_by INT;
ALTER TABLE acwl_datasource_templates ADD CONSTRAINT fk_datasource_templates_updated_by FOREIGN KEY (updated_by) REFERENCES acwl_users(id);