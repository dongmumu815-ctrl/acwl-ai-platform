-- 统一节点定义表设计
-- 创建时间: 2024-01-20
-- 描述: 整合 acwl_task_definitions 和 acwl_workflow_nodes，创建统一的节点定义表
-- 目标: 简化表结构，减少数据冗余，提高系统维护性

-- ============================================
-- 1. 统一节点定义表
-- ============================================

-- 统一节点定义表（整合任务定义和工作流节点）
CREATE TABLE acwl_unified_nodes (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '节点ID，自增主键',
    
    -- 基本信息
    name VARCHAR(100) NOT NULL COMMENT '节点名称',
    display_name VARCHAR(200) COMMENT '节点显示名称',
    description TEXT COMMENT '节点描述',
    
    -- 节点类型和分类
    node_type ENUM(
        -- 工作流控制节点
        'start',           -- 开始节点
        'end',             -- 结束节点
        'condition',       -- 条件判断
        'loop',            -- 循环节点
        'parallel',        -- 并行节点
        'merge',           -- 合并节点
        'delay',           -- 延时节点
        'subprocess',      -- 子流程
        
        -- 执行任务节点
        'python_code',     -- Python代码执行
        'sql_query',       -- SQL查询执行
        'data_transform',  -- 数据转换
        'api_call',        -- API调用
        'file_operation',  -- 文件操作
        'email_send',      -- 邮件发送
        'data_sync',       -- 数据同步
        'model_training',  -- 模型训练
        'data_analysis',   -- 数据分析
        'etl',             -- ETL处理
        'custom'           -- 自定义节点
    ) NOT NULL COMMENT '节点类型',
    
    node_category VARCHAR(50) COMMENT '节点分类（control/task/custom）',
    
    -- 所属关系
    workflow_id INT COMMENT '所属工作流ID（NULL表示独立任务）',
    project_id INT COMMENT '所属项目ID',
    
    -- 执行配置
    executor_group VARCHAR(50) NOT NULL DEFAULT 'default' COMMENT '执行器分组名称',
    priority ENUM('low', 'normal', 'high', 'urgent') NOT NULL DEFAULT 'normal' COMMENT '执行优先级',
    timeout_seconds INT DEFAULT 3600 COMMENT '超时时间（秒）',
    max_retry_count INT DEFAULT 3 COMMENT '最大重试次数',
    retry_interval_seconds INT DEFAULT 60 COMMENT '重试间隔（秒）',
    error_handling ENUM('fail', 'skip', 'retry', 'custom') DEFAULT 'fail' COMMENT '错误处理策略',
    
    -- 节点配置和参数
    node_config JSON NOT NULL COMMENT '节点配置参数',
    input_parameters JSON COMMENT '输入参数定义',
    output_parameters JSON COMMENT '输出参数定义',
    resource_requirements JSON COMMENT '资源需求配置（CPU、内存、GPU等）',
    environment_variables JSON COMMENT '环境变量配置',
    
    -- 执行内容
    command_template TEXT COMMENT '命令模板',
    script_content TEXT COMMENT '脚本内容',
    
    -- 依赖关系
    dependencies JSON COMMENT '依赖的其他节点ID列表',
    
    -- 工作流画布位置（仅工作流节点使用）
    position_x INT DEFAULT 0 COMMENT '节点在画布上的X坐标',
    position_y INT DEFAULT 0 COMMENT '节点在画布上的Y坐标',
    
    -- 状态和版本
    is_active BOOLEAN DEFAULT TRUE COMMENT '是否激活',
    is_optional BOOLEAN DEFAULT FALSE COMMENT '是否为可选节点（仅工作流节点）',
    is_template BOOLEAN DEFAULT FALSE COMMENT '是否为模板',
    version INT DEFAULT 1 COMMENT '版本号',
    
    -- 创建信息
    created_by INT NOT NULL COMMENT '创建者ID',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    -- 索引
    INDEX idx_node_type (node_type),
    INDEX idx_node_category (node_category),
    INDEX idx_workflow_id (workflow_id),
    INDEX idx_project_id (project_id),
    INDEX idx_executor_group (executor_group),
    INDEX idx_created_by (created_by),
    INDEX idx_is_active (is_active),
    INDEX idx_is_template (is_template),
    INDEX idx_name (name),
    
    -- 外键约束
    FOREIGN KEY (workflow_id) REFERENCES acwl_workflows(id) ON DELETE CASCADE,
    FOREIGN KEY (project_id) REFERENCES acwl_projects(id) ON DELETE SET NULL,
    FOREIGN KEY (created_by) REFERENCES acwl_users(id) ON DELETE RESTRICT
) COMMENT '统一节点定义表，整合任务定义和工作流节点功能';

-- ============================================
-- 2. 统一节点实例表（替代 acwl_task_instances 和 acwl_workflow_node_instances）
-- ============================================

-- 统一节点实例表
CREATE TABLE acwl_unified_node_instances (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '节点实例ID，自增主键',
    instance_id VARCHAR(100) NOT NULL UNIQUE COMMENT '实例唯一标识',
    
    -- 关联信息
    node_id INT NOT NULL COMMENT '节点定义ID',
    workflow_instance_id INT COMMENT '工作流实例ID（NULL表示独立任务实例）',
    schedule_id INT COMMENT '调度配置ID（独立任务使用）',
    parent_instance_id INT COMMENT '父实例ID（用于依赖任务）',
    
    -- 基本信息
    node_name VARCHAR(100) NOT NULL COMMENT '节点名称',
    node_type VARCHAR(50) NOT NULL COMMENT '节点类型',
    
    -- 执行状态
    status ENUM('pending', 'queued', 'running', 'success', 'failed', 'cancelled', 'timeout', 'retry', 'skipped') NOT NULL DEFAULT 'pending' COMMENT '实例状态',
    priority ENUM('low', 'normal', 'high', 'urgent') NOT NULL DEFAULT 'normal' COMMENT '实例优先级',
    
    -- 执行器分配
    executor_group VARCHAR(50) NOT NULL COMMENT '目标执行器分组',
    assigned_executor_node VARCHAR(100) COMMENT '分配的执行器节点ID',
    
    -- 时间信息
    scheduled_time TIMESTAMP NOT NULL COMMENT '计划执行时间',
    actual_start_time TIMESTAMP NULL COMMENT '实际开始时间',
    actual_end_time TIMESTAMP NULL COMMENT '实际结束时间',
    duration_seconds INT COMMENT '执行时长（秒）',
    
    -- 重试信息
    retry_count INT DEFAULT 0 COMMENT '重试次数',
    max_retry_count INT DEFAULT 3 COMMENT '最大重试次数',
    
    -- 数据和结果
    input_data JSON COMMENT '输入数据',
    output_data JSON COMMENT '输出数据',
    context_data JSON COMMENT '上下文数据',
    result_data JSON COMMENT '执行结果数据',
    runtime_config JSON COMMENT '运行时配置',
    resource_usage JSON COMMENT '资源使用情况',
    
    -- 错误信息
    error_message TEXT COMMENT '错误信息',
    
    -- 创建信息
    triggered_by ENUM('manual', 'schedule', 'event', 'api', 'dependency', 'workflow') NOT NULL COMMENT '触发方式',
    created_by_scheduler VARCHAR(100) COMMENT '创建该实例的调度器节点ID',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    -- 索引
    INDEX idx_node_id (node_id),
    INDEX idx_workflow_instance_id (workflow_instance_id),
    INDEX idx_schedule_id (schedule_id),
    INDEX idx_status (status),
    INDEX idx_executor_group (executor_group),
    INDEX idx_assigned_executor_node (assigned_executor_node),
    INDEX idx_scheduled_time (scheduled_time),
    INDEX idx_actual_start_time (actual_start_time),
    INDEX idx_created_by_scheduler (created_by_scheduler),
    INDEX idx_parent_instance_id (parent_instance_id),
    
    -- 外键约束
    FOREIGN KEY (node_id) REFERENCES acwl_unified_nodes(id) ON DELETE CASCADE,
    FOREIGN KEY (workflow_instance_id) REFERENCES acwl_workflow_instances(id) ON DELETE CASCADE,
    FOREIGN KEY (schedule_id) REFERENCES acwl_task_schedules(id) ON DELETE SET NULL,
    FOREIGN KEY (parent_instance_id) REFERENCES acwl_unified_node_instances(id) ON DELETE SET NULL
) COMMENT '统一节点实例表，记录所有节点（任务和工作流节点）的执行实例';

-- ============================================
-- 3. 更新工作流连接表
-- ============================================

-- 更新工作流连接表，引用统一节点表
ALTER TABLE acwl_workflow_connections 
DROP FOREIGN KEY IF EXISTS fk_source_node,
DROP FOREIGN KEY IF EXISTS fk_target_node;

ALTER TABLE acwl_workflow_connections 
ADD CONSTRAINT fk_source_node FOREIGN KEY (source_node_id) REFERENCES acwl_unified_nodes(id) ON DELETE CASCADE,
ADD CONSTRAINT fk_target_node FOREIGN KEY (target_node_id) REFERENCES acwl_unified_nodes(id) ON DELETE CASCADE;

-- ============================================
-- 4. 创建视图以保持向后兼容
-- ============================================

-- 任务定义视图（向后兼容）
CREATE VIEW v_task_definitions AS
SELECT 
    id,
    name,
    display_name,
    description,
    node_type as task_type,
    node_category as task_category,
    executor_group,
    priority,
    timeout_seconds,
    max_retry_count,
    retry_interval_seconds,
    node_config as task_config,
    resource_requirements,
    environment_variables,
    command_template,
    script_content,
    dependencies,
    project_id,
    created_by,
    is_active,
    version,
    created_at,
    updated_at
FROM acwl_unified_nodes
WHERE workflow_id IS NULL  -- 独立任务
AND node_type IN ('python_code', 'sql_query', 'data_transform', 'api_call', 'file_operation', 'email_send', 'data_sync', 'model_training', 'data_analysis', 'etl', 'custom');

-- 工作流节点视图（向后兼容）
CREATE VIEW v_workflow_nodes AS
SELECT 
    id,
    workflow_id,
    name as node_name,
    display_name,
    description,
    node_type,
    node_config,
    input_parameters,
    output_parameters,
    position_x,
    position_y,
    executor_group,
    timeout_seconds,
    max_retry_count,
    retry_interval_seconds,
    error_handling,
    is_optional,
    created_at,
    updated_at
FROM acwl_unified_nodes
WHERE workflow_id IS NOT NULL;  -- 工作流节点

-- 任务实例视图（向后兼容）
CREATE VIEW v_task_instances AS
SELECT 
    id,
    instance_id,
    node_id as task_definition_id,
    schedule_id,
    parent_instance_id,
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
    error_message,
    result_data,
    runtime_config,
    resource_usage,
    created_by_scheduler,
    created_at,
    updated_at
FROM acwl_unified_node_instances
WHERE workflow_instance_id IS NULL;  -- 独立任务实例

-- 工作流节点实例视图（向后兼容）
CREATE VIEW v_workflow_node_instances AS
SELECT 
    id,
    instance_id,
    workflow_instance_id,
    node_id,
    node_name,
    node_type,
    status,
    input_data,
    output_data,
    context_data,
    scheduled_time,
    actual_start_time,
    actual_end_time,
    duration_seconds,
    retry_count,
    max_retry_count,
    error_message,
    executor_group,
    assigned_executor_node,
    created_at,
    updated_at
FROM acwl_unified_node_instances
WHERE workflow_instance_id IS NOT NULL;  -- 工作流节点实例

-- ============================================
-- 5. 索引优化
-- ============================================

-- 为统一表创建复合索引以优化查询性能
CREATE INDEX idx_unified_nodes_workflow_type ON acwl_unified_nodes(workflow_id, node_type);
CREATE INDEX idx_unified_nodes_project_active ON acwl_unified_nodes(project_id, is_active);
CREATE INDEX idx_unified_nodes_category_active ON acwl_unified_nodes(node_category, is_active);

CREATE INDEX idx_unified_instances_status_time ON acwl_unified_node_instances(status, scheduled_time);
CREATE INDEX idx_unified_instances_workflow_status ON acwl_unified_node_instances(workflow_instance_id, status);
CREATE INDEX idx_unified_instances_executor_status ON acwl_unified_node_instances(executor_group, status);

-- ============================================
-- 6. 数据迁移说明
-- ============================================

/*
数据迁移步骤：

1. 迁移 acwl_task_definitions 数据到 acwl_unified_nodes
   - workflow_id 设置为 NULL
   - node_category 设置为 'task'
   - 保留所有原有字段

2. 迁移 acwl_workflow_nodes 数据到 acwl_unified_nodes
   - 保留 workflow_id
   - node_category 设置为 'control' 或 'task'
   - 合并配置字段

3. 迁移 acwl_task_instances 数据到 acwl_unified_node_instances
   - workflow_instance_id 设置为 NULL
   - 更新外键引用

4. 迁移 acwl_workflow_node_instances 数据到 acwl_unified_node_instances
   - 保留 workflow_instance_id
   - 更新外键引用

5. 更新所有相关的外键引用

6. 删除原有表（在确认迁移成功后）
   - DROP TABLE acwl_task_definitions;
   - DROP TABLE acwl_workflow_nodes;
   - DROP TABLE acwl_task_instances;
   - DROP TABLE acwl_workflow_node_instances;
*/