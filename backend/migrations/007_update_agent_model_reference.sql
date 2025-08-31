-- 更新 Agent 表的模型引用
-- 将 model_id 改为 model_service_config_id，引用 acwl_model_service_configs 表

-- 1. 添加新的 model_service_config_id 字段
ALTER TABLE acwl_agents 
ADD COLUMN model_service_config_id INT NULL 
COMMENT '使用的模型服务配置ID' 
AFTER model_id;

-- 2. 添加外键约束到 acwl_model_service_configs 表
ALTER TABLE acwl_agents 
ADD CONSTRAINT fk_agents_model_service_config 
FOREIGN KEY (model_service_config_id) 
REFERENCES acwl_model_service_configs(id) 
ON DELETE RESTRICT;

-- 3. 迁移现有数据：将 model_id 映射到对应的 model_service_config_id
-- 注意：这里需要根据实际的数据映射关系来更新
-- 如果没有直接的映射关系，可能需要手动设置默认值

-- 方案1：如果有默认的模型服务配置，设置为默认值
UPDATE acwl_agents 
SET model_service_config_id = (
    SELECT id FROM acwl_model_service_configs 
    WHERE is_default = TRUE 
    LIMIT 1
)
WHERE model_service_config_id IS NULL;

-- 如果没有默认配置，使用第一个可用的配置
UPDATE acwl_agents 
SET model_service_config_id = (
    SELECT id FROM acwl_model_service_configs 
    ORDER BY id ASC 
    LIMIT 1
)
WHERE model_service_config_id IS NULL;

-- 方案2：如果需要根据模型名称进行映射（需要根据实际情况调整）
-- UPDATE acwl_agents a
-- JOIN acwl_models m ON a.model_id = m.id
-- JOIN acwl_model_service_configs msc ON m.name = msc.model_name
-- SET a.model_service_config_id = msc.id;

-- 4. 将 model_service_config_id 设置为 NOT NULL
ALTER TABLE acwl_agents 
MODIFY COLUMN model_service_config_id INT NOT NULL 
COMMENT '使用的模型服务配置ID';

-- 5. 删除旧的 model_id 字段（可选，建议先备份数据）
-- 注意：在生产环境中，建议先保留 model_id 字段一段时间，确认迁移成功后再删除
-- ALTER TABLE acwl_agents DROP COLUMN model_id;

-- 6. 添加索引以提高查询性能
CREATE INDEX idx_agents_model_service_config_id ON acwl_agents(model_service_config_id);