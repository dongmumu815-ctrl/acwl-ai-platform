-- 数据迁移脚本：将 acwl_task_definitions 和 acwl_workflow_nodes 整合到 acwl_unified_nodes
-- 执行前请备份数据库！

-- 1. 首先创建统一节点表（如果不存在）
CREATE TABLE IF NOT EXISTS acwl_unified_nodes (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '节点ID',
    name VARCHAR(255) NOT NULL COMMENT '节点名称',
    display_name VARCHAR(255) COMMENT '显示名称',
    description TEXT COMMENT '节点描述',
    
    -- 节点类型和分类
    node_type ENUM(
        'task', 'data_processing', 'model_training', 'model_inference', 
        'data_validation', 'notification', 'condition', 'loop', 'parallel',
        'start', 'end', 'decision', 'merge', 'custom'
    ) NOT NULL DEFAULT 'task' COMMENT '节点类型',
    node_category VARCHAR(100) COMMENT '节点分类',
    node_status ENUM('active', 'inactive', 'deprecated') NOT NULL DEFAULT 'active' COMMENT '节点状态',
    
    -- 关联信息
    project_id BIGINT COMMENT '所属项目ID',
    workflow_id BIGINT COMMENT '所属工作流ID（如果是工作流节点）',
    parent_node_id BIGINT COMMENT '父节点ID（用于子任务）',
    
    -- 执行配置
    executor_group VARCHAR(100) DEFAULT 'default' COMMENT '执行器分组',
    resource_requirements JSON COMMENT '资源需求配置',
    config JSON COMMENT '节点配置参数',
    input_schema JSON COMMENT '输入数据结构定义',
    output_schema JSON COMMENT '输出数据结构定义',
    
    -- 执行控制
    timeout_seconds INT DEFAULT 3600 COMMENT '超时时间（秒）',
    max_retry_count INT DEFAULT 3 COMMENT '最大重试次数',
    retry_delay_seconds INT DEFAULT 60 COMMENT '重试延迟（秒）',
    
    -- 调度配置
    is_parallel BOOLEAN DEFAULT FALSE COMMENT '是否支持并行执行',
    max_parallel_instances INT DEFAULT 1 COMMENT '最大并行实例数',
    priority ENUM('low', 'medium', 'high', 'urgent') DEFAULT 'medium' COMMENT '优先级',
    
    -- 位置信息（用于工作流图形化显示）
    position_x DECIMAL(10,2) COMMENT 'X坐标',
    position_y DECIMAL(10,2) COMMENT 'Y坐标',
    
    -- 模板和系统标识
    is_template BOOLEAN DEFAULT FALSE COMMENT '是否为模板',
    is_system BOOLEAN DEFAULT FALSE COMMENT '是否为系统节点',
    template_id BIGINT COMMENT '模板ID（如果基于模板创建）',
    
    -- 版本控制
    version VARCHAR(50) DEFAULT '1.0.0' COMMENT '版本号',
    
    -- 审计字段
    created_by BIGINT NOT NULL COMMENT '创建者ID',
    updated_by BIGINT COMMENT '更新者ID',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    -- 索引
    INDEX idx_name (name),
    INDEX idx_node_type (node_type),
    INDEX idx_node_status (node_status),
    INDEX idx_project_id (project_id),
    INDEX idx_workflow_id (workflow_id),
    INDEX idx_created_by (created_by),
    INDEX idx_created_at (created_at),
    
    -- 外键约束
    FOREIGN KEY (project_id) REFERENCES acwl_projects(id) ON DELETE CASCADE,
    FOREIGN KEY (workflow_id) REFERENCES acwl_workflows(id) ON DELETE CASCADE,
    FOREIGN KEY (parent_node_id) REFERENCES acwl_unified_nodes(id) ON DELETE CASCADE,
    FOREIGN KEY (template_id) REFERENCES acwl_unified_nodes(id) ON DELETE SET NULL,
    FOREIGN KEY (created_by) REFERENCES acwl_users(id),
    FOREIGN KEY (updated_by) REFERENCES acwl_users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='统一节点定义表';

-- 2. 创建统一节点实例表（如果不存在）
CREATE TABLE IF NOT EXISTS acwl_unified_node_instances (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '实例ID',
    node_id BIGINT NOT NULL COMMENT '节点ID',
    instance_name VARCHAR(255) NOT NULL COMMENT '实例名称',
    instance_status ENUM(
        'pending', 'running', 'completed', 'failed', 
        'cancelled', 'paused', 'skipped', 'timeout'
    ) NOT NULL DEFAULT 'pending' COMMENT '实例状态',
    
    -- 执行信息
    priority ENUM('low', 'medium', 'high', 'urgent') DEFAULT 'medium' COMMENT '优先级',
    progress DECIMAL(5,2) DEFAULT 0.00 COMMENT '执行进度（百分比）',
    
    -- 关联信息
    workflow_instance_id BIGINT COMMENT '所属工作流实例ID',
    parent_instance_id BIGINT COMMENT '父实例ID',
    
    -- 执行数据
    input_data JSON COMMENT '输入数据',
    output_data JSON COMMENT '输出数据',
    error_info JSON COMMENT '错误信息',
    config_override JSON COMMENT '配置覆盖',
    
    -- 执行器信息
    executor_node_id BIGINT COMMENT '执行器节点ID',
    executor_info JSON COMMENT '执行器信息',
    
    -- 时间信息
    triggered_by BIGINT NOT NULL COMMENT '触发者ID',
    started_at TIMESTAMP NULL COMMENT '开始时间',
    finished_at TIMESTAMP NULL COMMENT '完成时间',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    -- 索引
    INDEX idx_node_id (node_id),
    INDEX idx_instance_status (instance_status),
    INDEX idx_workflow_instance_id (workflow_instance_id),
    INDEX idx_triggered_by (triggered_by),
    INDEX idx_created_at (created_at),
    
    -- 外键约束
    FOREIGN KEY (node_id) REFERENCES acwl_unified_nodes(id) ON DELETE CASCADE,
    FOREIGN KEY (workflow_instance_id) REFERENCES acwl_workflow_instances(id) ON DELETE CASCADE,
    FOREIGN KEY (parent_instance_id) REFERENCES acwl_unified_node_instances(id) ON DELETE CASCADE,
    FOREIGN KEY (executor_node_id) REFERENCES acwl_executor_nodes(id) ON DELETE SET NULL,
    FOREIGN KEY (triggered_by) REFERENCES acwl_users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='统一节点实例表';

-- 3. 创建节点执行记录表（如果不存在）
CREATE TABLE IF NOT EXISTS acwl_node_executions (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '执行记录ID',
    instance_id BIGINT NOT NULL COMMENT '实例ID',
    execution_status ENUM(
        'pending', 'running', 'completed', 'failed', 
        'cancelled', 'timeout'
    ) NOT NULL DEFAULT 'pending' COMMENT '执行状态',
    
    -- 执行信息
    attempt_number INT DEFAULT 1 COMMENT '尝试次数',
    exit_code INT COMMENT '退出码',
    
    -- 资源使用情况
    cpu_usage DECIMAL(5,2) COMMENT 'CPU使用率',
    memory_usage DECIMAL(10,2) COMMENT '内存使用量(MB)',
    disk_usage DECIMAL(10,2) COMMENT '磁盘使用量(MB)',
    
    -- 时间信息
    started_at TIMESTAMP NULL COMMENT '开始时间',
    finished_at TIMESTAMP NULL COMMENT '完成时间',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    
    -- 索引
    INDEX idx_instance_id (instance_id),
    INDEX idx_execution_status (execution_status),
    INDEX idx_started_at (started_at),
    
    -- 外键约束
    FOREIGN KEY (instance_id) REFERENCES acwl_unified_node_instances(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='节点执行记录表';

-- 4. 创建节点日志表（如果不存在）
CREATE TABLE IF NOT EXISTS acwl_node_logs (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '日志ID',
    instance_id BIGINT NOT NULL COMMENT '实例ID',
    execution_id BIGINT COMMENT '执行记录ID',
    
    -- 日志信息
    log_level ENUM('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL') NOT NULL DEFAULT 'INFO' COMMENT '日志级别',
    message TEXT NOT NULL COMMENT '日志消息',
    source VARCHAR(255) COMMENT '日志来源',
    
    -- 时间信息
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    
    -- 索引
    INDEX idx_instance_id (instance_id),
    INDEX idx_execution_id (execution_id),
    INDEX idx_log_level (log_level),
    INDEX idx_created_at (created_at),
    
    -- 外键约束
    FOREIGN KEY (instance_id) REFERENCES acwl_unified_node_instances(id) ON DELETE CASCADE,
    FOREIGN KEY (execution_id) REFERENCES acwl_node_executions(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='节点日志表';

-- 5. 创建节点结果表（如果不存在）
CREATE TABLE IF NOT EXISTS acwl_node_results (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '结果ID',
    instance_id BIGINT NOT NULL COMMENT '实例ID',
    
    -- 结果信息
    result_type ENUM('success', 'error', 'warning', 'info') NOT NULL DEFAULT 'success' COMMENT '结果类型',
    result_data JSON COMMENT '结果数据',
    file_paths JSON COMMENT '输出文件路径列表',
    metrics JSON COMMENT '执行指标',
    
    -- 时间信息
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    
    -- 索引
    INDEX idx_instance_id (instance_id),
    INDEX idx_result_type (result_type),
    
    -- 外键约束
    FOREIGN KEY (instance_id) REFERENCES acwl_unified_node_instances(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='节点结果表';

-- 6. 开始数据迁移

-- 6.1 迁移任务定义数据到统一节点表
INSERT INTO acwl_unified_nodes (
    name, display_name, description, node_type, node_category, node_status,
    project_id, workflow_id, executor_group, resource_requirements, config,
    input_schema, output_schema, timeout_seconds, max_retry_count,
    is_parallel, max_parallel_instances, priority, is_template, is_system,
    template_id, version, created_by, updated_by, created_at, updated_at
)
SELECT 
    task_name as name,
    task_display_name as display_name,
    task_description as description,
    CASE 
        WHEN task_type = 'data_sync' THEN 'data_processing'
        WHEN task_type = 'model_train' THEN 'model_training'
        WHEN task_type = 'model_predict' THEN 'model_inference'
        WHEN task_type = 'data_validate' THEN 'data_validation'
        WHEN task_type = 'notification' THEN 'notification'
        ELSE 'task'
    END as node_type,
    task_category as node_category,
    CASE 
        WHEN task_status = 'active' THEN 'active'
        WHEN task_status = 'inactive' THEN 'inactive'
        ELSE 'deprecated'
    END as node_status,
    project_id,
    workflow_id,
    executor_group,
    resource_requirements,
    config,
    input_schema,
    output_schema,
    timeout_seconds,
    max_retry_count,
    is_parallel,
    max_parallel_instances,
    CASE 
        WHEN priority = 'low' THEN 'low'
        WHEN priority = 'high' THEN 'high'
        WHEN priority = 'urgent' THEN 'urgent'
        ELSE 'medium'
    END as priority,
    is_template,
    is_system,
    template_id,
    version,
    created_by,
    updated_by,
    created_at,
    updated_at
FROM acwl_task_definitions
WHERE NOT EXISTS (
    SELECT 1 FROM acwl_unified_nodes un 
    WHERE un.name = acwl_task_definitions.task_name 
    AND un.project_id = acwl_task_definitions.project_id
);

-- 6.2 迁移工作流节点数据到统一节点表
INSERT INTO acwl_unified_nodes (
    name, display_name, description, node_type, node_category, node_status,
    project_id, workflow_id, config, position_x, position_y,
    is_template, is_system, created_by, updated_by, created_at, updated_at
)
SELECT 
    node_name as name,
    node_display_name as display_name,
    node_description as description,
    CASE 
        WHEN node_type = 'start' THEN 'start'
        WHEN node_type = 'end' THEN 'end'
        WHEN node_type = 'task' THEN 'task'
        WHEN node_type = 'condition' THEN 'condition'
        WHEN node_type = 'parallel' THEN 'parallel'
        WHEN node_type = 'merge' THEN 'merge'
        ELSE 'custom'
    END as node_type,
    node_category,
    CASE 
        WHEN node_status = 'active' THEN 'active'
        WHEN node_status = 'inactive' THEN 'inactive'
        ELSE 'deprecated'
    END as node_status,
    (SELECT project_id FROM acwl_workflows WHERE id = acwl_workflow_nodes.workflow_id) as project_id,
    workflow_id,
    config,
    position_x,
    position_y,
    is_template,
    is_system,
    created_by,
    updated_by,
    created_at,
    updated_at
FROM acwl_workflow_nodes
WHERE NOT EXISTS (
    SELECT 1 FROM acwl_unified_nodes un 
    WHERE un.name = acwl_workflow_nodes.node_name 
    AND un.workflow_id = acwl_workflow_nodes.workflow_id
);

-- 6.3 迁移任务实例数据到统一节点实例表
INSERT INTO acwl_unified_node_instances (
    node_id, instance_name, instance_status, priority, progress,
    workflow_instance_id, input_data, output_data, error_info,
    executor_node_id, triggered_by, started_at, finished_at,
    created_at, updated_at
)
SELECT 
    (SELECT un.id FROM acwl_unified_nodes un 
     WHERE un.name = td.task_name 
     AND un.project_id = td.project_id 
     LIMIT 1) as node_id,
    ti.instance_name,
    CASE 
        WHEN ti.instance_status = 'pending' THEN 'pending'
        WHEN ti.instance_status = 'running' THEN 'running'
        WHEN ti.instance_status = 'completed' THEN 'completed'
        WHEN ti.instance_status = 'failed' THEN 'failed'
        WHEN ti.instance_status = 'cancelled' THEN 'cancelled'
        WHEN ti.instance_status = 'paused' THEN 'paused'
        WHEN ti.instance_status = 'skipped' THEN 'skipped'
        ELSE 'timeout'
    END as instance_status,
    CASE 
        WHEN ti.priority = 'low' THEN 'low'
        WHEN ti.priority = 'high' THEN 'high'
        WHEN ti.priority = 'urgent' THEN 'urgent'
        ELSE 'medium'
    END as priority,
    ti.progress,
    ti.workflow_instance_id,
    ti.input_data,
    ti.output_data,
    ti.error_info,
    ti.executor_node_id,
    ti.triggered_by,
    ti.started_at,
    ti.finished_at,
    ti.created_at,
    ti.updated_at
FROM acwl_task_instances ti
JOIN acwl_task_definitions td ON ti.task_definition_id = td.id
WHERE (SELECT un.id FROM acwl_unified_nodes un 
       WHERE un.name = td.task_name 
       AND un.project_id = td.project_id 
       LIMIT 1) IS NOT NULL;

-- 6.4 迁移工作流节点实例数据到统一节点实例表
INSERT INTO acwl_unified_node_instances (
    node_id, instance_name, instance_status, progress,
    workflow_instance_id, input_data, output_data, error_info,
    triggered_by, started_at, finished_at, created_at, updated_at
)
SELECT 
    (SELECT un.id FROM acwl_unified_nodes un 
     WHERE un.name = wn.node_name 
     AND un.workflow_id = wn.workflow_id 
     LIMIT 1) as node_id,
    wni.instance_name,
    CASE 
        WHEN wni.instance_status = 'pending' THEN 'pending'
        WHEN wni.instance_status = 'running' THEN 'running'
        WHEN wni.instance_status = 'completed' THEN 'completed'
        WHEN wni.instance_status = 'failed' THEN 'failed'
        WHEN wni.instance_status = 'cancelled' THEN 'cancelled'
        WHEN wni.instance_status = 'paused' THEN 'paused'
        WHEN wni.instance_status = 'skipped' THEN 'skipped'
        ELSE 'timeout'
    END as instance_status,
    wni.progress,
    wni.workflow_instance_id,
    wni.input_data,
    wni.output_data,
    wni.error_info,
    wni.triggered_by,
    wni.started_at,
    wni.finished_at,
    wni.created_at,
    wni.updated_at
FROM acwl_workflow_node_instances wni
JOIN acwl_workflow_nodes wn ON wni.node_id = wn.id
WHERE (SELECT un.id FROM acwl_unified_nodes un 
       WHERE un.name = wn.node_name 
       AND un.workflow_id = wn.workflow_id 
       LIMIT 1) IS NOT NULL;

-- 6.5 迁移任务执行记录到节点执行记录表
INSERT INTO acwl_node_executions (
    instance_id, execution_status, attempt_number, exit_code,
    cpu_usage, memory_usage, disk_usage, started_at, finished_at, created_at
)
SELECT 
    (SELECT uni.id FROM acwl_unified_node_instances uni 
     JOIN acwl_unified_nodes un ON uni.node_id = un.id
     JOIN acwl_task_definitions td ON un.name = td.task_name AND un.project_id = td.project_id
     WHERE uni.instance_name = ti.instance_name 
     LIMIT 1) as instance_id,
    CASE 
        WHEN te.execution_status = 'pending' THEN 'pending'
        WHEN te.execution_status = 'running' THEN 'running'
        WHEN te.execution_status = 'completed' THEN 'completed'
        WHEN te.execution_status = 'failed' THEN 'failed'
        WHEN te.execution_status = 'cancelled' THEN 'cancelled'
        ELSE 'timeout'
    END as execution_status,
    te.attempt_number,
    te.exit_code,
    te.cpu_usage,
    te.memory_usage,
    te.disk_usage,
    te.started_at,
    te.finished_at,
    te.created_at
FROM acwl_task_executions te
JOIN acwl_task_instances ti ON te.task_instance_id = ti.id
WHERE (SELECT uni.id FROM acwl_unified_node_instances uni 
       JOIN acwl_unified_nodes un ON uni.node_id = un.id
       JOIN acwl_task_definitions td ON un.name = td.task_name AND un.project_id = td.project_id
       WHERE uni.instance_name = ti.instance_name 
       LIMIT 1) IS NOT NULL;

-- 6.6 迁移任务日志到节点日志表
INSERT INTO acwl_node_logs (
    instance_id, execution_id, log_level, message, source, created_at
)
SELECT 
    (SELECT uni.id FROM acwl_unified_node_instances uni 
     JOIN acwl_unified_nodes un ON uni.node_id = un.id
     JOIN acwl_task_definitions td ON un.name = td.task_name AND un.project_id = td.project_id
     WHERE uni.instance_name = ti.instance_name 
     LIMIT 1) as instance_id,
    (SELECT ne.id FROM acwl_node_executions ne 
     JOIN acwl_unified_node_instances uni ON ne.instance_id = uni.id
     JOIN acwl_unified_nodes un ON uni.node_id = un.id
     JOIN acwl_task_definitions td ON un.name = td.task_name AND un.project_id = td.project_id
     WHERE uni.instance_name = ti.instance_name 
     AND ne.attempt_number = te.attempt_number
     LIMIT 1) as execution_id,
    tl.log_level,
    tl.message,
    tl.source,
    tl.created_at
FROM acwl_task_logs tl
JOIN acwl_task_instances ti ON tl.task_instance_id = ti.id
JOIN acwl_task_executions te ON tl.task_execution_id = te.id
WHERE (SELECT uni.id FROM acwl_unified_node_instances uni 
       JOIN acwl_unified_nodes un ON uni.node_id = un.id
       JOIN acwl_task_definitions td ON un.name = td.task_name AND un.project_id = td.project_id
       WHERE uni.instance_name = ti.instance_name 
       LIMIT 1) IS NOT NULL;

-- 6.7 迁移任务结果到节点结果表
INSERT INTO acwl_node_results (
    instance_id, result_type, result_data, file_paths, metrics, created_at
)
SELECT 
    (SELECT uni.id FROM acwl_unified_node_instances uni 
     JOIN acwl_unified_nodes un ON uni.node_id = un.id
     JOIN acwl_task_definitions td ON un.name = td.task_name AND un.project_id = td.project_id
     WHERE uni.instance_name = ti.instance_name 
     LIMIT 1) as instance_id,
    CASE 
        WHEN tr.result_type = 'success' THEN 'success'
        WHEN tr.result_type = 'error' THEN 'error'
        WHEN tr.result_type = 'warning' THEN 'warning'
        ELSE 'info'
    END as result_type,
    tr.result_data,
    tr.file_paths,
    tr.metrics,
    tr.created_at
FROM acwl_task_results tr
JOIN acwl_task_instances ti ON tr.task_instance_id = ti.id
WHERE (SELECT uni.id FROM acwl_unified_node_instances uni 
       JOIN acwl_unified_nodes un ON uni.node_id = un.id
       JOIN acwl_task_definitions td ON un.name = td.task_name AND un.project_id = td.project_id
       WHERE uni.instance_name = ti.instance_name 
       LIMIT 1) IS NOT NULL;

-- 7. 更新工作流连接表的外键引用
-- 备份原始连接数据
CREATE TABLE IF NOT EXISTS acwl_workflow_connections_backup AS 
SELECT * FROM acwl_workflow_connections;

-- 更新源节点ID
UPDATE acwl_workflow_connections wc
SET source_node_id = (
    SELECT un.id 
    FROM acwl_unified_nodes un 
    JOIN acwl_workflow_nodes wn ON un.name = wn.node_name AND un.workflow_id = wn.workflow_id
    WHERE wn.id = wc.source_node_id
    LIMIT 1
)
WHERE EXISTS (
    SELECT 1 
    FROM acwl_unified_nodes un 
    JOIN acwl_workflow_nodes wn ON un.name = wn.node_name AND un.workflow_id = wn.workflow_id
    WHERE wn.id = wc.source_node_id
);

-- 更新目标节点ID
UPDATE acwl_workflow_connections wc
SET target_node_id = (
    SELECT un.id 
    FROM acwl_unified_nodes un 
    JOIN acwl_workflow_nodes wn ON un.name = wn.node_name AND un.workflow_id = wn.workflow_id
    WHERE wn.id = wc.target_node_id
    LIMIT 1
)
WHERE EXISTS (
    SELECT 1 
    FROM acwl_unified_nodes un 
    JOIN acwl_workflow_nodes wn ON un.name = wn.node_name AND un.workflow_id = wn.workflow_id
    WHERE wn.id = wc.target_node_id
);

-- 8. 数据验证查询
-- 验证迁移的节点数量
SELECT 
    'Task Definitions' as source_table,
    COUNT(*) as original_count,
    (
        SELECT COUNT(*) 
        FROM acwl_unified_nodes un 
        WHERE un.node_type IN ('task', 'data_processing', 'model_training', 'model_inference', 'data_validation', 'notification')
    ) as migrated_count
FROM acwl_task_definitions

UNION ALL

SELECT 
    'Workflow Nodes' as source_table,
    COUNT(*) as original_count,
    (
        SELECT COUNT(*) 
        FROM acwl_unified_nodes un 
        WHERE un.node_type IN ('start', 'end', 'condition', 'parallel', 'merge', 'custom')
    ) as migrated_count
FROM acwl_workflow_nodes;

-- 验证迁移的实例数量
SELECT 
    'Task Instances' as source_table,
    COUNT(*) as original_count,
    (
        SELECT COUNT(*) 
        FROM acwl_unified_node_instances uni 
        JOIN acwl_unified_nodes un ON uni.node_id = un.id
        WHERE un.node_type IN ('task', 'data_processing', 'model_training', 'model_inference', 'data_validation', 'notification')
    ) as migrated_count
FROM acwl_task_instances

UNION ALL

SELECT 
    'Workflow Node Instances' as source_table,
    COUNT(*) as original_count,
    (
        SELECT COUNT(*) 
        FROM acwl_unified_node_instances uni 
        JOIN acwl_unified_nodes un ON uni.node_id = un.id
        WHERE un.node_type IN ('start', 'end', 'condition', 'parallel', 'merge', 'custom')
    ) as migrated_count
FROM acwl_workflow_node_instances;

-- 9. 创建视图以保持向后兼容性

-- 任务定义视图
CREATE OR REPLACE VIEW v_acwl_task_definitions AS
SELECT 
    id,
    name as task_name,
    display_name as task_display_name,
    description as task_description,
    CASE 
        WHEN node_type = 'data_processing' THEN 'data_sync'
        WHEN node_type = 'model_training' THEN 'model_train'
        WHEN node_type = 'model_inference' THEN 'model_predict'
        WHEN node_type = 'data_validation' THEN 'data_validate'
        WHEN node_type = 'notification' THEN 'notification'
        ELSE 'task'
    END as task_type,
    node_category as task_category,
    CASE 
        WHEN node_status = 'active' THEN 'active'
        WHEN node_status = 'inactive' THEN 'inactive'
        ELSE 'deprecated'
    END as task_status,
    project_id,
    workflow_id,
    executor_group,
    resource_requirements,
    config,
    input_schema,
    output_schema,
    timeout_seconds,
    max_retry_count,
    is_parallel,
    max_parallel_instances,
    CASE 
        WHEN priority = 'low' THEN 'low'
        WHEN priority = 'high' THEN 'high'
        WHEN priority = 'urgent' THEN 'urgent'
        ELSE 'medium'
    END as priority,
    is_template,
    is_system,
    template_id,
    version,
    created_by,
    updated_by,
    created_at,
    updated_at
FROM acwl_unified_nodes
WHERE node_type IN ('task', 'data_processing', 'model_training', 'model_inference', 'data_validation', 'notification');

-- 工作流节点视图
CREATE OR REPLACE VIEW v_acwl_workflow_nodes AS
SELECT 
    id,
    name as node_name,
    display_name as node_display_name,
    description as node_description,
    node_type,
    node_category,
    CASE 
        WHEN node_status = 'active' THEN 'active'
        WHEN node_status = 'inactive' THEN 'inactive'
        ELSE 'deprecated'
    END as node_status,
    workflow_id,
    config,
    position_x,
    position_y,
    is_template,
    is_system,
    created_by,
    updated_by,
    created_at,
    updated_at
FROM acwl_unified_nodes
WHERE node_type IN ('start', 'end', 'condition', 'parallel', 'merge', 'custom');

-- 任务实例视图
CREATE OR REPLACE VIEW v_acwl_task_instances AS
SELECT 
    uni.id,
    un.id as task_definition_id,
    uni.instance_name,
    CASE 
        WHEN uni.instance_status = 'pending' THEN 'pending'
        WHEN uni.instance_status = 'running' THEN 'running'
        WHEN uni.instance_status = 'completed' THEN 'completed'
        WHEN uni.instance_status = 'failed' THEN 'failed'
        WHEN uni.instance_status = 'cancelled' THEN 'cancelled'
        WHEN uni.instance_status = 'paused' THEN 'paused'
        WHEN uni.instance_status = 'skipped' THEN 'skipped'
        ELSE 'timeout'
    END as instance_status,
    CASE 
        WHEN uni.priority = 'low' THEN 'low'
        WHEN uni.priority = 'high' THEN 'high'
        WHEN uni.priority = 'urgent' THEN 'urgent'
        ELSE 'medium'
    END as priority,
    uni.progress,
    uni.workflow_instance_id,
    uni.input_data,
    uni.output_data,
    uni.error_info,
    uni.executor_node_id,
    uni.triggered_by,
    uni.started_at,
    uni.finished_at,
    uni.created_at,
    uni.updated_at
FROM acwl_unified_node_instances uni
JOIN acwl_unified_nodes un ON uni.node_id = un.id
WHERE un.node_type IN ('task', 'data_processing', 'model_training', 'model_inference', 'data_validation', 'notification');

-- 工作流节点实例视图
CREATE OR REPLACE VIEW v_acwl_workflow_node_instances AS
SELECT 
    uni.id,
    un.id as node_id,
    uni.instance_name,
    CASE 
        WHEN uni.instance_status = 'pending' THEN 'pending'
        WHEN uni.instance_status = 'running' THEN 'running'
        WHEN uni.instance_status = 'completed' THEN 'completed'
        WHEN uni.instance_status = 'failed' THEN 'failed'
        WHEN uni.instance_status = 'cancelled' THEN 'cancelled'
        WHEN uni.instance_status = 'paused' THEN 'paused'
        WHEN uni.instance_status = 'skipped' THEN 'skipped'
        ELSE 'timeout'
    END as instance_status,
    uni.progress,
    uni.workflow_instance_id,
    uni.input_data,
    uni.output_data,
    uni.error_info,
    uni.triggered_by,
    uni.started_at,
    uni.finished_at,
    uni.created_at,
    uni.updated_at
FROM acwl_unified_node_instances uni
JOIN acwl_unified_nodes un ON uni.node_id = un.id
WHERE un.node_type IN ('start', 'end', 'condition', 'parallel', 'merge', 'custom');

-- 10. 输出迁移完成信息
SELECT 
    '数据迁移完成' as status,
    NOW() as completion_time,
    '请验证数据完整性后，可考虑删除原始表' as next_steps;

-- 注意事项：
-- 1. 执行此脚本前请务必备份数据库
-- 2. 迁移完成后请验证数据完整性
-- 3. 确认应用程序正常运行后，可考虑删除原始表：
--    DROP TABLE acwl_task_definitions;
--    DROP TABLE acwl_workflow_nodes;
--    DROP TABLE acwl_task_instances;
--    DROP TABLE acwl_workflow_node_instances;
--    DROP TABLE acwl_task_executions;
--    DROP TABLE acwl_task_logs;
--    DROP TABLE acwl_task_results;
-- 4. 如需回滚，可使用备份数据恢复原始表结构