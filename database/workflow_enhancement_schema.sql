-- 工作流增强数据库表设计
-- 创建时间: 2024-01-20
-- 描述: 为任务管理系统添加工作流支持，包括工作流定义、节点管理和执行流程
-- 特性: 支持代码执行、SQL执行、逻辑判断、条件分支等多种节点类型

-- ============================================
-- 1. 工作流定义相关表
-- ============================================

-- 工作流定义表
CREATE TABLE acwl_workflows (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '工作流ID，自增主键',
    workflow_name VARCHAR(100) NOT NULL COMMENT '工作流名称',
    display_name VARCHAR(200) COMMENT '工作流显示名称',
    description TEXT COMMENT '工作流描述',
    workflow_category VARCHAR(50) COMMENT '工作流分类',
    workflow_version VARCHAR(20) DEFAULT '1.0.0' COMMENT '工作流版本',
    workflow_status ENUM('draft', 'active', 'inactive', 'archived') NOT NULL DEFAULT 'draft' COMMENT '工作流状态',
    workflow_config JSON COMMENT '工作流全局配置',
    input_parameters JSON COMMENT '工作流输入参数定义',
    output_parameters JSON COMMENT '工作流输出参数定义',
    global_variables JSON COMMENT '工作流全局变量',
    timeout_seconds INT DEFAULT 7200 COMMENT '工作流超时时间（秒）',
    max_retry_count INT DEFAULT 1 COMMENT '工作流最大重试次数',
    project_id INT COMMENT '所属项目ID',
    created_by INT NOT NULL COMMENT '创建者ID',
    is_template BOOLEAN DEFAULT FALSE COMMENT '是否为模板',
    is_system BOOLEAN DEFAULT FALSE COMMENT '是否为系统工作流',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_workflow_name (workflow_name),
    INDEX idx_workflow_status (workflow_status),
    INDEX idx_project_id (project_id),
    INDEX idx_created_by (created_by),
    INDEX idx_is_template (is_template),
    FOREIGN KEY (project_id) REFERENCES acwl_projects(id) ON DELETE SET NULL,
    FOREIGN KEY (created_by) REFERENCES acwl_users(id) ON DELETE RESTRICT
) COMMENT '工作流定义表，存储工作流的基本信息和配置';

-- 工作流节点表
CREATE TABLE acwl_workflow_nodes (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '节点ID，自增主键',
    workflow_id INT NOT NULL COMMENT '所属工作流ID',
    node_name VARCHAR(100) NOT NULL COMMENT '节点名称',
    display_name VARCHAR(200) COMMENT '节点显示名称',
    description TEXT COMMENT '节点描述',
    node_type ENUM(
        'start',           -- 开始节点
        'end',             -- 结束节点
        'python_code',     -- Python代码执行
        'sql_query',       -- SQL查询执行
        'condition',       -- 条件判断
        'loop',            -- 循环节点
        'parallel',        -- 并行节点
        'merge',           -- 合并节点
        'data_transform',  -- 数据转换
        'api_call',        -- API调用
        'file_operation',  -- 文件操作
        'email_send',      -- 邮件发送
        'delay',           -- 延时节点
        'subprocess',      -- 子流程
        'custom'           -- 自定义节点
    ) NOT NULL COMMENT '节点类型',
    node_config JSON NOT NULL COMMENT '节点配置参数',
    input_parameters JSON COMMENT '节点输入参数定义',
    output_parameters JSON COMMENT '节点输出参数定义',
    position_x INT DEFAULT 0 COMMENT '节点在画布上的X坐标',
    position_y INT DEFAULT 0 COMMENT '节点在画布上的Y坐标',
    executor_group VARCHAR(50) COMMENT '执行器分组（继承自工作流或自定义）',
    timeout_seconds INT COMMENT '节点超时时间（秒）',
    max_retry_count INT DEFAULT 3 COMMENT '节点最大重试次数',
    retry_interval_seconds INT DEFAULT 60 COMMENT '重试间隔（秒）',
    error_handling ENUM('fail', 'skip', 'retry', 'custom') DEFAULT 'fail' COMMENT '错误处理策略',
    is_optional BOOLEAN DEFAULT FALSE COMMENT '是否为可选节点',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_workflow_id (workflow_id),
    INDEX idx_node_type (node_type),
    INDEX idx_node_name (node_name),
    FOREIGN KEY (workflow_id) REFERENCES acwl_workflows(id) ON DELETE CASCADE
) COMMENT '工作流节点表，存储工作流中各个执行节点的定义';

-- 工作流连接表（节点间的连接关系）
CREATE TABLE acwl_workflow_connections (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '连接ID，自增主键',
    workflow_id INT NOT NULL COMMENT '所属工作流ID',
    source_node_id INT NOT NULL COMMENT '源节点ID',
    target_node_id INT NOT NULL COMMENT '目标节点ID',
    connection_type ENUM('success', 'failure', 'conditional', 'always') NOT NULL DEFAULT 'success' COMMENT '连接类型',
    condition_expression TEXT COMMENT '条件表达式（用于conditional类型）',
    connection_config JSON COMMENT '连接配置参数',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    INDEX idx_workflow_id (workflow_id),
    INDEX idx_source_node_id (source_node_id),
    INDEX idx_target_node_id (target_node_id),
    UNIQUE KEY uk_workflow_source_target (workflow_id, source_node_id, target_node_id, connection_type),
    FOREIGN KEY (workflow_id) REFERENCES acwl_workflows(id) ON DELETE CASCADE,
    FOREIGN KEY (source_node_id) REFERENCES acwl_workflow_nodes(id) ON DELETE CASCADE,
    FOREIGN KEY (target_node_id) REFERENCES acwl_workflow_nodes(id) ON DELETE CASCADE
) COMMENT '工作流连接表，定义工作流节点间的执行流向和条件';

-- ============================================
-- 2. 工作流执行相关表
-- ============================================

-- 工作流实例表
CREATE TABLE acwl_workflow_instances (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '工作流实例ID，自增主键',
    instance_id VARCHAR(100) NOT NULL UNIQUE COMMENT '实例唯一标识',
    workflow_id INT NOT NULL COMMENT '工作流定义ID',
    workflow_version VARCHAR(20) COMMENT '执行时的工作流版本',
    instance_name VARCHAR(200) COMMENT '实例名称',
    status ENUM('pending', 'running', 'success', 'failed', 'cancelled', 'timeout', 'paused') NOT NULL DEFAULT 'pending' COMMENT '实例状态',
    priority ENUM('low', 'normal', 'high', 'urgent') NOT NULL DEFAULT 'normal' COMMENT '实例优先级',
    input_data JSON COMMENT '工作流输入数据',
    output_data JSON COMMENT '工作流输出数据',
    context_data JSON COMMENT '工作流上下文数据',
    scheduled_time TIMESTAMP NOT NULL COMMENT '计划执行时间',
    actual_start_time TIMESTAMP NULL COMMENT '实际开始时间',
    actual_end_time TIMESTAMP NULL COMMENT '实际结束时间',
    duration_seconds INT COMMENT '执行时长（秒）',
    current_node_id INT COMMENT '当前执行节点ID',
    retry_count INT DEFAULT 0 COMMENT '重试次数',
    max_retry_count INT DEFAULT 1 COMMENT '最大重试次数',
    error_message TEXT COMMENT '错误信息',
    triggered_by ENUM('manual', 'schedule', 'event', 'api', 'dependency') NOT NULL COMMENT '触发方式',
    triggered_by_user INT COMMENT '触发用户ID',
    parent_instance_id INT COMMENT '父工作流实例ID',
    created_by_scheduler VARCHAR(100) COMMENT '创建该实例的调度器节点ID',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_workflow_id (workflow_id),
    INDEX idx_status (status),
    INDEX idx_scheduled_time (scheduled_time),
    INDEX idx_actual_start_time (actual_start_time),
    INDEX idx_triggered_by_user (triggered_by_user),
    INDEX idx_parent_instance_id (parent_instance_id),
    FOREIGN KEY (workflow_id) REFERENCES acwl_workflows(id) ON DELETE CASCADE,
    FOREIGN KEY (current_node_id) REFERENCES acwl_workflow_nodes(id) ON DELETE SET NULL,
    FOREIGN KEY (triggered_by_user) REFERENCES acwl_users(id) ON DELETE SET NULL,
    FOREIGN KEY (parent_instance_id) REFERENCES acwl_workflow_instances(id) ON DELETE SET NULL
) COMMENT '工作流实例表，记录每次工作流执行的具体实例信息';

-- 工作流节点实例表
CREATE TABLE acwl_workflow_node_instances (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '节点实例ID，自增主键',
    instance_id VARCHAR(100) NOT NULL COMMENT '节点实例唯一标识',
    workflow_instance_id INT NOT NULL COMMENT '工作流实例ID',
    node_id INT NOT NULL COMMENT '节点定义ID',
    node_name VARCHAR(100) NOT NULL COMMENT '节点名称',
    node_type VARCHAR(50) NOT NULL COMMENT '节点类型',
    status ENUM('pending', 'running', 'success', 'failed', 'cancelled', 'timeout', 'skipped') NOT NULL DEFAULT 'pending' COMMENT '节点实例状态',
    input_data JSON COMMENT '节点输入数据',
    output_data JSON COMMENT '节点输出数据',
    context_data JSON COMMENT '节点上下文数据',
    scheduled_time TIMESTAMP NOT NULL COMMENT '计划执行时间',
    actual_start_time TIMESTAMP NULL COMMENT '实际开始时间',
    actual_end_time TIMESTAMP NULL COMMENT '实际结束时间',
    duration_seconds INT COMMENT '执行时长（秒）',
    retry_count INT DEFAULT 0 COMMENT '重试次数',
    max_retry_count INT DEFAULT 3 COMMENT '最大重试次数',
    error_message TEXT COMMENT '错误信息',
    executor_group VARCHAR(50) COMMENT '执行器分组',
    assigned_executor_node VARCHAR(100) COMMENT '分配的执行器节点ID',
    task_instance_id INT COMMENT '关联的任务实例ID（如果节点对应一个任务）',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_workflow_instance_id (workflow_instance_id),
    INDEX idx_node_id (node_id),
    INDEX idx_status (status),
    INDEX idx_scheduled_time (scheduled_time),
    INDEX idx_task_instance_id (task_instance_id),
    FOREIGN KEY (workflow_instance_id) REFERENCES acwl_workflow_instances(id) ON DELETE CASCADE,
    FOREIGN KEY (node_id) REFERENCES acwl_workflow_nodes(id) ON DELETE CASCADE,
    FOREIGN KEY (task_instance_id) REFERENCES acwl_task_instances(id) ON DELETE SET NULL
) COMMENT '工作流节点实例表，记录工作流执行过程中每个节点的执行状态';

-- ============================================
-- 3. 修改现有任务定义表，添加工作流支持
-- ============================================

-- 为任务定义表添加工作流相关字段
ALTER TABLE acwl_task_definitions 
ADD COLUMN workflow_id INT COMMENT '所属工作流ID' AFTER project_id,
ADD COLUMN workflow_node_id INT COMMENT '对应的工作流节点ID' AFTER workflow_id,
ADD INDEX idx_workflow_id (workflow_id),
ADD INDEX idx_workflow_node_id (workflow_node_id),
ADD CONSTRAINT fk_task_workflow FOREIGN KEY (workflow_id) REFERENCES acwl_workflows(id) ON DELETE SET NULL,
ADD CONSTRAINT fk_task_workflow_node FOREIGN KEY (workflow_node_id) REFERENCES acwl_workflow_nodes(id) ON DELETE SET NULL;

-- 扩展任务类型，支持更多节点类型
ALTER TABLE acwl_task_definitions 
MODIFY COLUMN task_type ENUM(
    'data_sync',        -- 数据同步
    'model_training',   -- 模型训练
    'data_analysis',    -- 数据分析
    'etl',              -- ETL处理
    'python_code',      -- Python代码执行
    'sql_query',        -- SQL查询执行
    'condition',        -- 条件判断
    'data_transform',   -- 数据转换
    'api_call',         -- API调用
    'file_operation',   -- 文件操作
    'email_send',       -- 邮件发送
    'custom'            -- 自定义
) NOT NULL COMMENT '任务类型';

-- 扩展任务模板表的任务类型
ALTER TABLE acwl_task_templates 
MODIFY COLUMN task_type ENUM(
    'data_sync',        -- 数据同步
    'model_training',   -- 模型训练
    'data_analysis',    -- 数据分析
    'etl',              -- ETL处理
    'python_code',      -- Python代码执行
    'sql_query',        -- SQL查询执行
    'condition',        -- 条件判断
    'data_transform',   -- 数据转换
    'api_call',         -- API调用
    'file_operation',   -- 文件操作
    'email_send',       -- 邮件发送
    'custom'            -- 自定义
) NOT NULL COMMENT '任务类型';

-- ============================================
-- 4. 工作流调度相关表
-- ============================================

-- 工作流调度配置表
CREATE TABLE acwl_workflow_schedules (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '调度ID，自增主键',
    workflow_id INT NOT NULL COMMENT '工作流定义ID',
    schedule_name VARCHAR(100) NOT NULL COMMENT '调度名称',
    schedule_type ENUM('cron', 'interval', 'once', 'manual', 'event_driven') NOT NULL COMMENT '调度类型',
    cron_expression VARCHAR(100) COMMENT 'Cron表达式',
    interval_seconds INT COMMENT '间隔秒数',
    start_time TIMESTAMP NULL COMMENT '开始时间',
    end_time TIMESTAMP NULL COMMENT '结束时间',
    timezone VARCHAR(50) DEFAULT 'UTC' COMMENT '时区',
    is_enabled BOOLEAN DEFAULT TRUE COMMENT '是否启用',
    max_instances INT DEFAULT 1 COMMENT '最大并发实例数',
    misfire_policy ENUM('ignore', 'fire_once', 'fire_all') DEFAULT 'fire_once' COMMENT '错过执行策略',
    schedule_config JSON COMMENT '调度配置参数',
    input_data JSON COMMENT '调度时的默认输入数据',
    created_by INT NOT NULL COMMENT '创建者ID',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_workflow_id (workflow_id),
    INDEX idx_schedule_type (schedule_type),
    INDEX idx_is_enabled (is_enabled),
    INDEX idx_start_time (start_time),
    INDEX idx_end_time (end_time),
    FOREIGN KEY (workflow_id) REFERENCES acwl_workflows(id) ON DELETE CASCADE,
    FOREIGN KEY (created_by) REFERENCES acwl_users(id) ON DELETE RESTRICT
) COMMENT '工作流调度配置表，定义工作流的调度规则和时间配置';

-- ============================================
-- 5. 工作流模板和示例数据
-- ============================================

-- 插入默认工作流模板
INSERT INTO acwl_workflows (workflow_name, display_name, description, workflow_category, workflow_status, is_template, is_system, created_by) VALUES
('simple_data_pipeline', '简单数据管道', '包含数据提取、转换和加载的基础数据管道模板', 'data_processing', 'active', TRUE, TRUE, 1),
('ml_training_pipeline', '机器学习训练管道', '包含数据预处理、模型训练和评估的机器学习管道模板', 'machine_learning', 'active', TRUE, TRUE, 1),
('conditional_workflow', '条件分支工作流', '演示条件判断和分支执行的工作流模板', 'control_flow', 'active', TRUE, TRUE, 1);

-- 为简单数据管道创建节点
INSERT INTO acwl_workflow_nodes (workflow_id, node_name, display_name, node_type, node_config, position_x, position_y) VALUES
(1, 'start', '开始', 'start', '{}', 100, 100),
(1, 'extract_data', '数据提取', 'sql_query', '{"query": "SELECT * FROM source_table", "connection": "source_db"}', 300, 100),
(1, 'transform_data', '数据转换', 'python_code', '{"script": "# 数据转换逻辑\nresult = input_data.copy()\nresult[\"processed\"] = True\nreturn result"}', 500, 100),
(1, 'load_data', '数据加载', 'sql_query', '{"query": "INSERT INTO target_table VALUES (?)", "connection": "target_db"}', 700, 100),
(1, 'end', '结束', 'end', '{}', 900, 100);

-- 为简单数据管道创建连接
INSERT INTO acwl_workflow_connections (workflow_id, source_node_id, target_node_id, connection_type) VALUES
(1, 1, 2, 'success'),  -- start -> extract_data
(1, 2, 3, 'success'),  -- extract_data -> transform_data
(1, 3, 4, 'success'),  -- transform_data -> load_data
(1, 4, 5, 'success');  -- load_data -> end

-- 插入新的任务模板
INSERT INTO acwl_task_templates (name, description, task_type, default_executor_group, template_config, is_system) VALUES
('Python代码执行模板', '用于执行Python脚本的标准模板', 'python_code', 'default', 
 '{"timeout_seconds": 1800, "max_retry_count": 3, "resource_requirements": {"cpu": "1", "memory": "2GB"}}', TRUE),
('SQL查询执行模板', '用于执行SQL查询的标准模板', 'sql_query', 'default',
 '{"timeout_seconds": 900, "max_retry_count": 2, "resource_requirements": {"cpu": "1", "memory": "1GB"}}', TRUE),
('条件判断模板', '用于条件判断和分支控制的模板', 'condition', 'default',
 '{"timeout_seconds": 60, "max_retry_count": 1, "resource_requirements": {"cpu": "0.5", "memory": "512MB"}}', TRUE),
('数据转换模板', '用于数据格式转换和处理的模板', 'data_transform', 'default',
 '{"timeout_seconds": 1200, "max_retry_count": 3, "resource_requirements": {"cpu": "2", "memory": "4GB"}}', TRUE),
('API调用模板', '用于调用外部API接口的模板', 'api_call', 'default',
 '{"timeout_seconds": 300, "max_retry_count": 3, "resource_requirements": {"cpu": "0.5", "memory": "1GB"}}', TRUE),
('文件操作模板', '用于文件读写和处理的模板', 'file_operation', 'default',
 '{"timeout_seconds": 600, "max_retry_count": 2, "resource_requirements": {"cpu": "1", "memory": "2GB"}}', TRUE);

-- 插入工作流相关的系统配置
INSERT INTO acwl_task_system_config (config_key, config_value, config_type, description, is_system) VALUES
('workflow.max_concurrent_instances', '100', 'number', '工作流最大并发实例数', TRUE),
('workflow.default_timeout', '7200', 'number', '工作流默认超时时间（秒）', TRUE),
('workflow.node_heartbeat_interval', '30', 'number', '工作流节点心跳间隔（秒）', TRUE),
('workflow.auto_cleanup_days', '90', 'number', '工作流实例自动清理天数', TRUE),
('workflow.enable_parallel_execution', 'true', 'boolean', '是否启用并行执行', TRUE),
('workflow.max_retry_count', '3', 'number', '工作流节点最大重试次数', TRUE);

-- ============================================
-- 6. 创建视图和索引优化
-- ============================================

-- 创建工作流执行状态视图
CREATE VIEW v_workflow_execution_status AS
SELECT 
    wi.id as workflow_instance_id,
    wi.instance_id,
    w.workflow_name,
    w.display_name as workflow_display_name,
    wi.status as workflow_status,
    wi.priority,
    wi.scheduled_time,
    wi.actual_start_time,
    wi.actual_end_time,
    wi.duration_seconds,
    wi.retry_count,
    wi.triggered_by,
    u.username as triggered_by_username,
    COUNT(wni.id) as total_nodes,
    SUM(CASE WHEN wni.status = 'success' THEN 1 ELSE 0 END) as completed_nodes,
    SUM(CASE WHEN wni.status = 'failed' THEN 1 ELSE 0 END) as failed_nodes,
    SUM(CASE WHEN wni.status = 'running' THEN 1 ELSE 0 END) as running_nodes
FROM acwl_workflow_instances wi
JOIN acwl_workflows w ON wi.workflow_id = w.id
LEFT JOIN acwl_users u ON wi.triggered_by_user = u.id
LEFT JOIN acwl_workflow_node_instances wni ON wi.id = wni.workflow_instance_id
GROUP BY wi.id, wi.instance_id, w.workflow_name, w.display_name, wi.status, 
         wi.priority, wi.scheduled_time, wi.actual_start_time, wi.actual_end_time, 
         wi.duration_seconds, wi.retry_count, wi.triggered_by, u.username;

-- 创建节点执行统计视图
CREATE VIEW v_node_execution_stats AS
SELECT 
    wn.id as node_id,
    wn.node_name,
    wn.node_type,
    w.workflow_name,
    COUNT(wni.id) as total_executions,
    SUM(CASE WHEN wni.status = 'success' THEN 1 ELSE 0 END) as success_count,
    SUM(CASE WHEN wni.status = 'failed' THEN 1 ELSE 0 END) as failure_count,
    AVG(wni.duration_seconds) as avg_duration_seconds,
    MAX(wni.duration_seconds) as max_duration_seconds,
    MIN(wni.duration_seconds) as min_duration_seconds
FROM acwl_workflow_nodes wn
JOIN acwl_workflows w ON wn.workflow_id = w.id
LEFT JOIN acwl_workflow_node_instances wni ON wn.id = wni.node_id
GROUP BY wn.id, wn.node_name, wn.node_type, w.workflow_name;

-- 添加复合索引优化查询性能
CREATE INDEX idx_workflow_instances_status_time ON acwl_workflow_instances(status, scheduled_time);
CREATE INDEX idx_workflow_node_instances_status_time ON acwl_workflow_node_instances(status, scheduled_time);
CREATE INDEX idx_workflow_connections_source_type ON acwl_workflow_connections(source_node_id, connection_type);
CREATE INDEX idx_workflow_nodes_type_workflow ON acwl_workflow_nodes(node_type, workflow_id);