-- 为ES查询模板表添加数据资源ID字段
-- 创建时间: 2024-01-16
-- 描述: 为es_query_templates表添加data_resource_id字段，建立与数据资源的关联

-- 添加数据资源ID字段
ALTER TABLE es_query_templates 
ADD COLUMN data_resource_id INT NULL COMMENT '数据资源ID' AFTER datasource_id;

-- 添加外键约束
ALTER TABLE es_query_templates 
ADD CONSTRAINT fk_es_templates_data_resource 
FOREIGN KEY (data_resource_id) REFERENCES acwl_data_resources(id) ON DELETE SET NULL;

-- 添加索引
CREATE INDEX idx_es_templates_data_resource_id ON es_query_templates(data_resource_id);

-- 添加复合索引，优化查询性能
CREATE INDEX idx_es_templates_datasource_resource ON es_query_templates(datasource_id, data_resource_id);