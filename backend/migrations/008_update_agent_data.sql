-- 更新 Agent 表的数据，设置 model_service_config_id 值

-- 1. 将所有 NULL 的 model_service_config_id 设置为默认配置
UPDATE acwl_agents 
SET model_service_config_id = (
    SELECT id FROM acwl_model_service_configs 
    WHERE is_default = TRUE 
    LIMIT 1
)
WHERE model_service_config_id IS NULL;

-- 2. 如果没有默认配置，使用第一个可用的配置
UPDATE acwl_agents 
SET model_service_config_id = (
    SELECT id FROM acwl_model_service_configs 
    ORDER BY id ASC 
    LIMIT 1
)
WHERE model_service_config_id IS NULL;

-- 3. 将 model_service_config_id 设置为 NOT NULL
ALTER TABLE acwl_agents 
MODIFY COLUMN model_service_config_id INT NOT NULL 
COMMENT '使用的模型服务配置ID';

-- 4. 添加外键约束到 acwl_model_service_configs 表（如果不存在）
ALTER TABLE acwl_agents 
ADD CONSTRAINT fk_agents_model_service_config 
FOREIGN KEY (model_service_config_id) 
REFERENCES acwl_model_service_configs(id) 
ON DELETE RESTRICT;

-- 5. 添加索引以提高查询性能（如果不存在）
CREATE INDEX idx_agents_model_service_config_id ON acwl_agents(model_service_config_id);