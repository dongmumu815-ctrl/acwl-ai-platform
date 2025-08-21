-- 数据迁移脚本：从分离的表结构迁移到统一节点表结构
-- 创建时间: 2024-01-20
-- 描述: 将 acwl_task_definitions、acwl_workflow_nodes、acwl_task_instances、acwl_workflow_node_instances 迁移到统一表

-- ============================================
-- 迁移前准备工作
-- ============================================

-- 1. 备份原有表
CREATE TABLE backup_task_definitions AS SELECT * FROM acwl_task_definitions;
CREATE TABLE backup_workflow_nodes AS SELECT * FROM acwl_workflow_nodes;
CREATE TABLE backup_task_instances AS SELECT * FROM acwl_task_instances;
CREATE TABLE backup_workflow_node_instances AS SELECT * FROM acwl_workflow_node_instances;

-- 2. 禁用外键检查（迁移期间）
SET FOREIGN_KEY_CHECKS = 0;

-- ============================================
-- 第一步：迁移节点定义数据
-- ============================================

-- 迁移任务定义到统一节点表
INSERT INTO acwl_unified_nodes (
    id,
    name,
    display_name,
    description,
    node_type,
    node_category,
    workflow_id,
    project_id,
    executor_group,
    priority,
    timeout_seconds,
    max_retry_count,
    retry_interval_seconds,
    error_handling,
    node_config,
    input_parameters,
    output_parameters,
    resource_requirements,
    environment_variables,
    command_template,
    script_content,
    dependencies,
    position_x,
    position_y,
    is_active,
    is_optional,
    is_template,
    version,
    created_by,
    created_at,
    updated_at
)
SELECT 
    td.id,
    td.name,
    td.display_name,
    td.description,
    -- 映射任务类型到节点类型
    CASE 
        WHEN td.task_type = 'python_script' THEN 'python_code'
        WHEN td.task_type = 'sql_script' THEN 'sql_query'
        WHEN td.task_type = 'data_processing' THEN 'data_transform'
        WHEN td.task_type = 'api_request' THEN 'api_call'
        WHEN td.task_type = 'file_processing' THEN 'file_operation'
        WHEN td.task_type = 'email_notification' THEN 'email_send'
        WHEN td.task_type = 'data_synchronization' THEN 'data_sync'
        WHEN td.task_type = 'ml_training' THEN 'model_training'
        WHEN td.task_type = 'data_analytics' THEN 'data_analysis'
        WHEN td.task_type = 'etl_process' THEN 'etl'
        ELSE 'custom'
    END,
    'task' as node_category,
    NULL as workflow_id,  -- 独立任务
    td.project_id,
    td.executor_group,
    td.priority,
    td.timeout_seconds,
    td.max_retry_count,
    td.retry_interval_seconds,
    COALESCE(td.error_handling, 'fail'),
    td.task_config as node_config,
    td.input_parameters,
    td.output_parameters,
    td.resource_requirements,
    td.environment_variables,
    td.command_template,
    td.script_content,
    td.dependencies,
    0 as position_x,  -- 独立任务无位置
    0 as position_y,
    td.is_active,
    FALSE as is_optional,
    td.is_template,
    td.version,
    td.created_by,
    td.created_at,
    td.updated_at
FROM acwl_task_definitions td;

-- 迁移工作流节点到统一节点表
INSERT INTO acwl_unified_nodes (
    id,
    name,
    display_name,
    description,
    node_type,
    node_category,
    workflow_id,
    project_id,
    executor_group,
    priority,
    timeout_seconds,
    max_retry_count,
    retry_interval_seconds,
    error_handling,
    node_config,
    input_parameters,
    output_parameters,
    resource_requirements,
    environment_variables,
    command_template,
    script_content,
    dependencies,
    position_x,
    position_y,
    is_active,
    is_optional,
    is_template,
    version,
    created_by,
    created_at,
    updated_at
)
SELECT 
    -- 为工作流节点分配新的ID，避免与任务定义ID冲突
    wn.id + (SELECT COALESCE(MAX(id), 0) FROM acwl_task_definitions) as id,
    wn.node_name as name,
    wn.display_name,
    wn.description,
    wn.node_type,
    -- 根据节点类型确定分类
    CASE 
        WHEN wn.node_type IN ('start', 'end', 'condition', 'loop', 'parallel', 'merge', 'delay', 'subprocess') THEN 'control'
        ELSE 'task'
    END as node_category,
    wn.workflow_id,
    w.project_id,  -- 从工作流获取项目ID
    COALESCE(wn.executor_group, 'default'),
    COALESCE(wn.priority, 'normal'),
    COALESCE(wn.timeout_seconds, 3600),
    COALESCE(wn.max_retry_count, 3),
    COALESCE(wn.retry_interval_seconds, 60),
    COALESCE(wn.error_handling, 'fail'),
    wn.node_config,
    wn.input_parameters,
    wn.output_parameters,
    NULL as resource_requirements,  -- 工作流节点原本没有此字段
    NULL as environment_variables,
    NULL as command_template,
    NULL as script_content,
    NULL as dependencies,  -- 依赖关系通过连接表管理
    wn.position_x,
    wn.position_y,
    TRUE as is_active,
    COALESCE(wn.is_optional, FALSE),
    FALSE as is_template,
    1 as version,
    w.created_by,  -- 从工作流获取创建者
    wn.created_at,
    wn.updated_at
FROM acwl_workflow_nodes wn
JOIN acwl_workflows w ON wn.workflow_id = w.id;

-- ============================================
-- 第二步：更新ID映射表（用于实例迁移）
-- ============================================

-- 创建临时映射表
CREATE TEMPORARY TABLE temp_node_id_mapping (
    old_id INT,
    new_id INT,
    source_table VARCHAR(50),
    PRIMARY KEY (old_id, source_table)
);

-- 插入任务定义ID映射（ID保持不变）
INSERT INTO temp_node_id_mapping (old_id, new_id, source_table)
SELECT id, id, 'task_definitions' FROM acwl_task_definitions;

-- 插入工作流节点ID映射（ID有偏移）
INSERT INTO temp_node_id_mapping (old_id, new_id, source_table)
SELECT 
    wn.id, 
    wn.id + (SELECT COALESCE(MAX(id), 0) FROM acwl_task_definitions),
    'workflow_nodes'
FROM acwl_workflow_nodes wn;

-- ============================================
-- 第三步：迁移实例数据
-- ============================================

-- 迁移任务实例到统一节点实例表
INSERT INTO acwl_unified_node_instances (
    id,
    instance_id,
    node_id,
    workflow_instance_id,
    schedule_id,
    parent_instance_id,
    node_name,
    node_type,
    status,
    priority,
    executor_group,
    assigned_executor_node,
    scheduled_time,
    actual_start_time,
    actual_end_time,
    duration_seconds,
    retry_count,
    max_retry_count,
    input_data,
    output_data,
    context_data,
    result_data,
    runtime_config,
    resource_usage,
    error_message,
    triggered_by,
    created_by_scheduler,
    created_at,
    updated_at
)
SELECT 
    ti.id,
    ti.instance_id,
    tm.new_id as node_id,  -- 使用映射后的节点ID
    NULL as workflow_instance_id,  -- 独立任务实例
    ti.schedule_id,
    ti.parent_instance_id,
    td.name as node_name,
    CASE 
        WHEN td.task_type = 'python_script' THEN 'python_code'
        WHEN td.task_type = 'sql_script' THEN 'sql_query'
        WHEN td.task_type = 'data_processing' THEN 'data_transform'
        WHEN td.task_type = 'api_request' THEN 'api_call'
        WHEN td.task_type = 'file_processing' THEN 'file_operation'
        WHEN td.task_type = 'email_notification' THEN 'email_send'
        WHEN td.task_type = 'data_synchronization' THEN 'data_sync'
        WHEN td.task_type = 'ml_training' THEN 'model_training'
        WHEN td.task_type = 'data_analytics' THEN 'data_analysis'
        WHEN td.task_type = 'etl_process' THEN 'etl'
        ELSE 'custom'
    END as node_type,
    ti.status,
    ti.priority,
    ti.executor_group,
    ti.assigned_executor_node,
    ti.scheduled_time,
    ti.actual_start_time,
    ti.actual_end_time,
    ti.duration_seconds,
    ti.retry_count,
    ti.max_retry_count,
    NULL as input_data,  -- 任务实例原本没有此字段
    NULL as output_data,
    NULL as context_data,
    ti.result_data,
    ti.runtime_config,
    ti.resource_usage,
    ti.error_message,
    COALESCE(ti.triggered_by, 'manual'),
    ti.created_by_scheduler,
    ti.created_at,
    ti.updated_at
FROM acwl_task_instances ti
JOIN temp_node_id_mapping tm ON ti.task_definition_id = tm.old_id AND tm.source_table = 'task_definitions'
JOIN acwl_task_definitions td ON ti.task_definition_id = td.id;

-- 迁移工作流节点实例到统一节点实例表
INSERT INTO acwl_unified_node_instances (
    id,
    instance_id,
    node_id,
    workflow_instance_id,
    schedule_id,
    parent_instance_id,
    node_name,
    node_type,
    status,
    priority,
    executor_group,
    assigned_executor_node,
    scheduled_time,
    actual_start_time,
    actual_end_time,
    duration_seconds,
    retry_count,
    max_retry_count,
    input_data,
    output_data,
    context_data,
    result_data,
    runtime_config,
    resource_usage,
    error_message,
    triggered_by,
    created_by_scheduler,
    created_at,
    updated_at
)
SELECT 
    -- 为工作流节点实例分配新的ID，避免与任务实例ID冲突
    wni.id + (SELECT COALESCE(MAX(id), 0) FROM acwl_task_instances) as id,
    wni.instance_id,
    tm.new_id as node_id,  -- 使用映射后的节点ID
    wni.workflow_instance_id,
    NULL as schedule_id,  -- 工作流节点实例不使用调度
    NULL as parent_instance_id,
    wni.node_name,
    wni.node_type,
    wni.status,
    'normal' as priority,  -- 工作流节点实例原本没有优先级
    wni.executor_group,
    wni.assigned_executor_node,
    wni.scheduled_time,
    wni.actual_start_time,
    wni.actual_end_time,
    wni.duration_seconds,
    wni.retry_count,
    wni.max_retry_count,
    wni.input_data,
    wni.output_data,
    wni.context_data,
    NULL as result_data,  -- 工作流节点实例使用output_data
    NULL as runtime_config,
    NULL as resource_usage,
    wni.error_message,
    'workflow' as triggered_by,
    NULL as created_by_scheduler,
    wni.created_at,
    wni.updated_at
FROM acwl_workflow_node_instances wni
JOIN temp_node_id_mapping tm ON wni.node_id = tm.old_id AND tm.source_table = 'workflow_nodes';

-- ============================================
-- 第四步：更新外键引用
-- ============================================

-- 更新工作流连接表的外键引用
UPDATE acwl_workflow_connections wc
JOIN temp_node_id_mapping tm_source ON wc.source_node_id = tm_source.old_id AND tm_source.source_table = 'workflow_nodes'
SET wc.source_node_id = tm_source.new_id;

UPDATE acwl_workflow_connections wc
JOIN temp_node_id_mapping tm_target ON wc.target_node_id = tm_target.old_id AND tm_target.source_table = 'workflow_nodes'
SET wc.target_node_id = tm_target.new_id;

-- 更新任务队列表的外键引用（如果存在）
UPDATE acwl_task_queues tq
JOIN temp_node_id_mapping tm ON tq.task_definition_id = tm.old_id AND tm.source_table = 'task_definitions'
SET tq.task_definition_id = tm.new_id
WHERE EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'acwl_task_queues' AND column_name = 'task_definition_id');

-- 更新任务执行表的外键引用（如果存在）
UPDATE acwl_task_executions te
JOIN acwl_unified_node_instances uni ON te.task_instance_id = uni.id
SET te.task_instance_id = uni.id
WHERE EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'acwl_task_executions' AND column_name = 'task_instance_id');

-- ============================================
-- 第五步：数据验证
-- ============================================

-- 验证迁移结果
SELECT 
    '节点定义迁移验证' as check_type,
    (SELECT COUNT(*) FROM acwl_task_definitions) as original_tasks,
    (SELECT COUNT(*) FROM acwl_workflow_nodes) as original_workflow_nodes,
    (SELECT COUNT(*) FROM acwl_unified_nodes) as unified_nodes,
    CASE 
        WHEN (SELECT COUNT(*) FROM acwl_unified_nodes) = 
             (SELECT COUNT(*) FROM acwl_task_definitions) + (SELECT COUNT(*) FROM acwl_workflow_nodes)
        THEN '✓ 数据完整'
        ELSE '✗ 数据不完整'
    END as validation_result;

SELECT 
    '实例迁移验证' as check_type,
    (SELECT COUNT(*) FROM acwl_task_instances) as original_task_instances,
    (SELECT COUNT(*) FROM acwl_workflow_node_instances) as original_workflow_instances,
    (SELECT COUNT(*) FROM acwl_unified_node_instances) as unified_instances,
    CASE 
        WHEN (SELECT COUNT(*) FROM acwl_unified_node_instances) = 
             (SELECT COUNT(*) FROM acwl_task_instances) + (SELECT COUNT(*) FROM acwl_workflow_node_instances)
        THEN '✓ 数据完整'
        ELSE '✗ 数据不完整'
    END as validation_result;

-- 验证外键完整性
SELECT 
    '外键完整性验证' as check_type,
    COUNT(*) as orphaned_instances
FROM acwl_unified_node_instances uni
LEFT JOIN acwl_unified_nodes un ON uni.node_id = un.id
WHERE un.id IS NULL;

-- ============================================
-- 第六步：清理工作（在验证通过后执行）
-- ============================================

-- 重新启用外键检查
SET FOREIGN_KEY_CHECKS = 1;

-- 删除临时映射表
DROP TEMPORARY TABLE temp_node_id_mapping;

-- 注意：以下删除操作需要在确认迁移成功后手动执行
/*
-- 删除原有表（谨慎操作！）
DROP TABLE acwl_workflow_node_instances;
DROP TABLE acwl_task_instances;
DROP TABLE acwl_workflow_nodes;
DROP TABLE acwl_task_definitions;

-- 删除备份表（在确认系统运行正常后）
DROP TABLE backup_task_definitions;
DROP TABLE backup_workflow_nodes;
DROP TABLE backup_task_instances;
DROP TABLE backup_workflow_node_instances;
*/

-- ============================================
-- 迁移完成提示
-- ============================================

SELECT 
    '迁移完成' as status,
    '请验证数据完整性后，手动执行清理脚本删除原有表' as next_steps,
    NOW() as completion_time;