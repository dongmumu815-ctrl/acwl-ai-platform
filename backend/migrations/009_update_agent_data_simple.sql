-- 简单更新 Agent 表的数据

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