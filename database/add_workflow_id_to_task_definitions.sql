-- 添加 workflow_id 字段到 acwl_task_definitions 表
-- 这个脚本用于修复数据库结构，确保与模型定义一致

USE acwl_ai;

-- 检查字段是否已存在，如果不存在则添加
SET @sql = (
    SELECT IF(
        COUNT(*) = 0,
        'ALTER TABLE acwl_task_definitions ADD COLUMN workflow_id INT NULL COMMENT "所属工作流ID" AFTER project_id',
        'SELECT "workflow_id column already exists" as message'
    )
    FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_SCHEMA = 'acwl_ai' 
    AND TABLE_NAME = 'acwl_task_definitions' 
    AND COLUMN_NAME = 'workflow_id'
);

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 添加外键约束（如果不存在）
SET @sql = (
    SELECT IF(
        COUNT(*) = 0,
        'ALTER TABLE acwl_task_definitions ADD CONSTRAINT fk_task_definitions_workflow_id FOREIGN KEY (workflow_id) REFERENCES acwl_workflows(id) ON DELETE SET NULL',
        'SELECT "Foreign key constraint already exists" as message'
    )
    FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE 
    WHERE TABLE_SCHEMA = 'acwl_ai' 
    AND TABLE_NAME = 'acwl_task_definitions' 
    AND CONSTRAINT_NAME = 'fk_task_definitions_workflow_id'
);

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 检查字段是否已存在，如果不存在则添加 workflow_node_id
SET @sql = (
    SELECT IF(
        COUNT(*) = 0,
        'ALTER TABLE acwl_task_definitions ADD COLUMN workflow_node_id INT NULL COMMENT "对应的工作流节点ID" AFTER workflow_id',
        'SELECT "workflow_node_id column already exists" as message'
    )
    FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_SCHEMA = 'acwl_ai' 
    AND TABLE_NAME = 'acwl_task_definitions' 
    AND COLUMN_NAME = 'workflow_node_id'
);

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 添加外键约束（如果不存在）
SET @sql = (
    SELECT IF(
        COUNT(*) = 0,
        'ALTER TABLE acwl_task_definitions ADD CONSTRAINT fk_task_definitions_workflow_node_id FOREIGN KEY (workflow_node_id) REFERENCES acwl_workflow_nodes(id) ON DELETE SET NULL',
        'SELECT "Foreign key constraint already exists" as message'
    )
    FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE 
    WHERE TABLE_SCHEMA = 'acwl_ai' 
    AND TABLE_NAME = 'acwl_task_definitions' 
    AND CONSTRAINT_NAME = 'fk_task_definitions_workflow_node_id'
);

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SELECT 'Migration completed successfully' as result;