-- 删除 acwl_agents 表中多余的 model_id 字段
-- 执行时间: 2024-01-XX
-- 说明: 由于已经迁移到 model_service_config_id，需要删除旧的 model_id 字段

USE `acwl-ai-data`;

-- 1. 检查 model_id 字段是否存在
SELECT COLUMN_NAME 
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_SCHEMA = 'acwl-ai-data' 
  AND TABLE_NAME = 'acwl_agents' 
  AND COLUMN_NAME = 'model_id';

-- 2. 删除 model_id 字段（如果存在）
ALTER TABLE acwl_agents DROP COLUMN IF EXISTS model_id;

-- 3. 验证字段已删除
SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_DEFAULT
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_SCHEMA = 'acwl-ai-data' 
  AND TABLE_NAME = 'acwl_agents'
ORDER BY ORDINAL_POSITION;

-- 4. 验证 model_service_config_id 字段存在且配置正确
SELECT 
    COLUMN_NAME,
    DATA_TYPE,
    IS_NULLABLE,
    COLUMN_KEY,
    REFERENCED_TABLE_NAME,
    REFERENCED_COLUMN_NAME
FROM INFORMATION_SCHEMA.COLUMNS c
LEFT JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE kcu 
    ON c.TABLE_SCHEMA = kcu.TABLE_SCHEMA 
    AND c.TABLE_NAME = kcu.TABLE_NAME 
    AND c.COLUMN_NAME = kcu.COLUMN_NAME
WHERE c.TABLE_SCHEMA = 'acwl-ai-data' 
  AND c.TABLE_NAME = 'acwl_agents'
  AND c.COLUMN_NAME = 'model_service_config_id';

COMMIT;