-- 任务管理系统数据库表设计
-- 创建时间: 2024-01-20
-- 描述: 支持分布式任务调度和执行的完整数据库表结构
-- 特性: 执行器分组、调度器高可用、任务路由、负载均衡

-- ============================================
-- 1. 任务定义相关表（在当前后台系统中）
-- ============================================

-- 任务定义表
CREATE TABLE acwl_task_definitions (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '任务定义ID，自增主键',
    name VARCHAR(100) NOT NULL COMMENT '任务名称',
    display_name VARCHAR(200) COMMENT '任务显示名称',
    description TEXT COMMENT '任务描述',
    task_type ENUM('data_sync', 'model_training', 'data_analysis', 'etl', 'custom') NOT NULL COMMENT '任务类型',
    task_category VARCHAR(50) COMMENT '任务分类',
    executor_group VARCHAR(50) NOT NULL COMMENT '执行器分组名称，指定任务运行的执行器组',
    priority ENUM('low', 'normal', 'high', 'urgent') NOT NULL DEFAULT 'normal' COMMENT '任务优先级',
    timeout_seconds INT DEFAULT 3600 COMMENT '任务超时时间（秒）',
    max_retry_count INT DEFAULT 3 COMMENT '最大重试次数',
    retry_interval_seconds INT DEFAULT 60 COMMENT '重试间隔（秒）',
    task_config JSON COMMENT '任务配置参数',
    resource_requirements JSON COMMENT '资源需求配置（CPU、内存、GPU等）',
    environment_variables JSON COMMENT '环境变量配置',
    command_template TEXT COMMENT '命令模板',
    script_content TEXT COMMENT '脚本内容',
    dependencies JSON COMMENT '依赖的其他任务ID列表',
    project_id INT COMMENT '所属项目ID',
    created_by INT NOT NULL COMMENT '创建者ID',
    is_active BOOLEAN DEFAULT TRUE COMMENT '是否激活',
    version INT DEFAULT 1 COMMENT '版本号',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_task_type (task_type),
    INDEX idx_executor_group (executor_group),
    INDEX idx_project_id (project_id),
    INDEX idx_created_by (created_by),
    INDEX idx_is_active (is_active),
    FOREIGN KEY (project_id) REFERENCES acwl_projects(id) ON DELETE SET NULL,
    FOREIGN KEY (created_by) REFERENCES acwl_users(id) ON DELETE RESTRICT
) COMMENT '任务定义表，存储任务的基本配置和执行参数';

-- 任务模板表
CREATE TABLE acwl_task_templates (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '模板ID，自增主键',
    name VARCHAR(100) NOT NULL COMMENT '模板名称',
    description TEXT COMMENT '模板描述',
    task_type ENUM('data_sync', 'model_training', 'data_analysis', 'etl', 'custom') NOT NULL COMMENT '任务类型',
    default_executor_group VARCHAR(50) COMMENT '默认执行器分组',
    template_config JSON NOT NULL COMMENT '模板配置',
    default_resource_requirements JSON COMMENT '默认资源需求',
    is_system BOOLEAN DEFAULT FALSE COMMENT '是否为系统模板',
    created_by INT COMMENT '创建者ID',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_task_type (task_type),
    INDEX idx_is_system (is_system),
    FOREIGN KEY (created_by) REFERENCES acwl_users(id) ON DELETE SET NULL
) COMMENT '任务模板表，存储预定义的任务配置模板';

-- 任务依赖关系表
CREATE TABLE acwl_task_dependencies (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '依赖ID，自增主键',
    parent_task_id INT NOT NULL COMMENT '父任务ID',
    child_task_id INT NOT NULL COMMENT '子任务ID',
    dependency_type ENUM('success', 'failure', 'completion', 'conditional') NOT NULL DEFAULT 'success' COMMENT '依赖类型',
    condition_expression TEXT COMMENT '条件表达式（用于conditional类型）',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    UNIQUE KEY uk_parent_child (parent_task_id, child_task_id),
    INDEX idx_parent_task (parent_task_id),
    INDEX idx_child_task (child_task_id),
    FOREIGN KEY (parent_task_id) REFERENCES acwl_task_definitions(id) ON DELETE CASCADE,
    FOREIGN KEY (child_task_id) REFERENCES acwl_task_definitions(id) ON DELETE CASCADE
) COMMENT '任务依赖关系表，定义任务间的执行依赖关系';

-- ============================================
-- 2. 执行器节点管理表
-- ============================================

-- 执行器分组表
CREATE TABLE acwl_executor_groups (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '分组ID，自增主键',
    group_name VARCHAR(50) NOT NULL UNIQUE COMMENT '分组名称',
    display_name VARCHAR(100) COMMENT '分组显示名称',
    description TEXT COMMENT '分组描述',
    group_type ENUM('general', 'gpu', 'cpu_intensive', 'memory_intensive', 'custom') NOT NULL DEFAULT 'general' COMMENT '分组类型',
    resource_profile JSON COMMENT '资源配置文件',
    max_concurrent_tasks INT DEFAULT 10 COMMENT '最大并发任务数',
    task_types JSON COMMENT '支持的任务类型列表',
    load_balance_strategy ENUM('round_robin', 'least_connections', 'resource_based', 'random') DEFAULT 'round_robin' COMMENT '负载均衡策略',
    is_active BOOLEAN DEFAULT TRUE COMMENT '是否激活',
    created_by INT COMMENT '创建者ID',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_group_type (group_type),
    INDEX idx_is_active (is_active),
    FOREIGN KEY (created_by) REFERENCES acwl_users(id) ON DELETE SET NULL
) COMMENT '执行器分组表，管理执行器的逻辑分组和资源配置';

-- 执行器节点表
CREATE TABLE acwl_executor_nodes (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '执行器ID，自增主键',
    node_id VARCHAR(100) NOT NULL UNIQUE COMMENT '节点唯一标识',
    node_name VARCHAR(100) NOT NULL COMMENT '节点名称',
    group_id INT NOT NULL COMMENT '所属分组ID',
    host_ip VARCHAR(45) NOT NULL COMMENT '主机IP地址',
    port INT NOT NULL COMMENT '服务端口',
    status ENUM('online', 'offline', 'busy', 'maintenance', 'error') NOT NULL DEFAULT 'offline' COMMENT '节点状态',
    version VARCHAR(50) COMMENT '执行器版本',
    capabilities JSON COMMENT '节点能力配置',
    resource_info JSON COMMENT '资源信息（CPU、内存、GPU等）',
    current_load INT DEFAULT 0 COMMENT '当前负载（运行中的任务数）',
    max_concurrent_tasks INT DEFAULT 5 COMMENT '最大并发任务数',
    last_heartbeat TIMESTAMP NULL COMMENT '最后心跳时间',
    registration_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '注册时间',
    metadata JSON COMMENT '节点元数据',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_group_id (group_id),
    INDEX idx_status (status),
    INDEX idx_last_heartbeat (last_heartbeat),
    INDEX idx_host_ip (host_ip),
    FOREIGN KEY (group_id) REFERENCES acwl_executor_groups(id) ON DELETE RESTRICT
) COMMENT '执行器节点表，记录所有执行器实例的状态和配置';

-- ============================================
-- 3. 调度器集群管理表
-- ============================================

-- 调度器节点表
CREATE TABLE acwl_scheduler_nodes (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '调度器ID，自增主键',
    node_id VARCHAR(100) NOT NULL UNIQUE COMMENT '调度器节点唯一标识',
    node_name VARCHAR(100) NOT NULL COMMENT '节点名称',
    host_ip VARCHAR(45) NOT NULL COMMENT '主机IP地址',
    port INT NOT NULL COMMENT '服务端口',
    status ENUM('active', 'standby', 'offline', 'error') NOT NULL DEFAULT 'standby' COMMENT '节点状态',
    role ENUM('leader', 'follower') NOT NULL DEFAULT 'follower' COMMENT '集群角色',
    version VARCHAR(50) COMMENT '调度器版本',
    election_priority INT DEFAULT 100 COMMENT '选举优先级',
    last_heartbeat TIMESTAMP NULL COMMENT '最后心跳时间',
    leader_lease_expires TIMESTAMP NULL COMMENT 'Leader租约过期时间',
    registration_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '注册时间',
    metadata JSON COMMENT '节点元数据',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_status (status),
    INDEX idx_role (role),
    INDEX idx_last_heartbeat (last_heartbeat),
    INDEX idx_leader_lease_expires (leader_lease_expires)
) COMMENT '调度器节点表，管理调度器集群的节点状态和选举信息';

-- 调度器锁表（用于分布式锁和Leader选举）
CREATE TABLE acwl_scheduler_locks (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '锁ID，自增主键',
    lock_name VARCHAR(100) NOT NULL UNIQUE COMMENT '锁名称',
    lock_owner VARCHAR(100) NOT NULL COMMENT '锁持有者（调度器节点ID）',
    lock_value VARCHAR(255) COMMENT '锁值',
    acquired_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '获取时间',
    expires_at TIMESTAMP NOT NULL COMMENT '过期时间',
    metadata JSON COMMENT '锁元数据',
    INDEX idx_expires_at (expires_at),
    INDEX idx_lock_owner (lock_owner)
) COMMENT '调度器锁表，用于实现分布式锁和Leader选举机制';

-- ============================================
-- 4. 任务调度相关表
-- ============================================

-- 任务调度配置表
CREATE TABLE acwl_task_schedules (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '调度ID，自增主键',
    task_definition_id INT NOT NULL COMMENT '任务定义ID',
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
    created_by INT NOT NULL COMMENT '创建者ID',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_task_definition_id (task_definition_id),
    INDEX idx_schedule_type (schedule_type),
    INDEX idx_is_enabled (is_enabled),
    INDEX idx_start_time (start_time),
    INDEX idx_end_time (end_time),
    FOREIGN KEY (task_definition_id) REFERENCES acwl_task_definitions(id) ON DELETE CASCADE,
    FOREIGN KEY (created_by) REFERENCES acwl_users(id) ON DELETE RESTRICT
) COMMENT '任务调度配置表，定义任务的调度规则和时间配置';

-- 任务实例表
CREATE TABLE acwl_task_instances (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '实例ID，自增主键',
    instance_id VARCHAR(100) NOT NULL UNIQUE COMMENT '实例唯一标识',
    task_definition_id INT NOT NULL COMMENT '任务定义ID',
    schedule_id INT COMMENT '调度配置ID',
    parent_instance_id INT COMMENT '父实例ID（用于依赖任务）',
    status ENUM('pending', 'queued', 'running', 'success', 'failed', 'cancelled', 'timeout', 'retry') NOT NULL DEFAULT 'pending' COMMENT '实例状态',
    priority ENUM('low', 'normal', 'high', 'urgent') NOT NULL DEFAULT 'normal' COMMENT '实例优先级',
    executor_group VARCHAR(50) NOT NULL COMMENT '目标执行器分组',
    assigned_executor_node VARCHAR(100) COMMENT '分配的执行器节点ID',
    scheduled_time TIMESTAMP NOT NULL COMMENT '计划执行时间',
    actual_start_time TIMESTAMP NULL COMMENT '实际开始时间',
    actual_end_time TIMESTAMP NULL COMMENT '实际结束时间',
    duration_seconds INT COMMENT '执行时长（秒）',
    retry_count INT DEFAULT 0 COMMENT '重试次数',
    max_retry_count INT DEFAULT 3 COMMENT '最大重试次数',
    error_message TEXT COMMENT '错误信息',
    result_data JSON COMMENT '执行结果数据',
    runtime_config JSON COMMENT '运行时配置',
    resource_usage JSON COMMENT '资源使用情况',
    created_by_scheduler VARCHAR(100) COMMENT '创建该实例的调度器节点ID',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_task_definition_id (task_definition_id),
    INDEX idx_schedule_id (schedule_id),
    INDEX idx_status (status),
    INDEX idx_executor_group (executor_group),
    INDEX idx_assigned_executor_node (assigned_executor_node),
    INDEX idx_scheduled_time (scheduled_time),
    INDEX idx_actual_start_time (actual_start_time),
    INDEX idx_created_by_scheduler (created_by_scheduler),
    FOREIGN KEY (task_definition_id) REFERENCES acwl_task_definitions(id) ON DELETE CASCADE,
    FOREIGN KEY (schedule_id) REFERENCES acwl_task_schedules(id) ON DELETE SET NULL,
    FOREIGN KEY (parent_instance_id) REFERENCES acwl_task_instances(id) ON DELETE SET NULL
) COMMENT '任务实例表，记录每次任务执行的具体实例信息';

-- 任务队列表
CREATE TABLE acwl_task_queues (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '队列ID，自增主键',
    queue_name VARCHAR(100) NOT NULL COMMENT '队列名称',
    executor_group VARCHAR(50) NOT NULL COMMENT '目标执行器分组',
    task_instance_id INT NOT NULL COMMENT '任务实例ID',
    priority ENUM('low', 'normal', 'high', 'urgent') NOT NULL DEFAULT 'normal' COMMENT '队列优先级',
    queue_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '入队时间',
    estimated_start_time TIMESTAMP COMMENT '预计开始时间',
    queue_position INT COMMENT '队列位置',
    metadata JSON COMMENT '队列元数据',
    INDEX idx_executor_group (executor_group),
    INDEX idx_task_instance_id (task_instance_id),
    INDEX idx_priority (priority),
    INDEX idx_queue_time (queue_time),
    INDEX idx_estimated_start_time (estimated_start_time),
    FOREIGN KEY (task_instance_id) REFERENCES acwl_task_instances(id) ON DELETE CASCADE
) COMMENT '任务队列表，管理等待执行的任务实例队列';

-- ============================================
-- 5. 任务执行相关表
-- ============================================

-- 任务执行记录表
CREATE TABLE acwl_task_executions (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '执行ID，自增主键',
    execution_id VARCHAR(100) NOT NULL UNIQUE COMMENT '执行唯一标识',
    task_instance_id INT NOT NULL COMMENT '任务实例ID',
    executor_node_id VARCHAR(100) NOT NULL COMMENT '执行器节点ID',
    process_id VARCHAR(100) COMMENT '进程ID',
    status ENUM('starting', 'running', 'success', 'failed', 'cancelled', 'timeout') NOT NULL DEFAULT 'starting' COMMENT '执行状态',
    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '开始时间',
    end_time TIMESTAMP NULL COMMENT '结束时间',
    duration_seconds INT COMMENT '执行时长（秒）',
    exit_code INT COMMENT '退出码',
    stdout_log TEXT COMMENT '标准输出日志',
    stderr_log TEXT COMMENT '标准错误日志',
    resource_usage JSON COMMENT '资源使用情况（CPU、内存、GPU等）',
    performance_metrics JSON COMMENT '性能指标',
    execution_context JSON COMMENT '执行上下文信息',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_task_instance_id (task_instance_id),
    INDEX idx_executor_node_id (executor_node_id),
    INDEX idx_status (status),
    INDEX idx_start_time (start_time),
    INDEX idx_end_time (end_time),
    FOREIGN KEY (task_instance_id) REFERENCES acwl_task_instances(id) ON DELETE CASCADE
) COMMENT '任务执行记录表，记录任务在执行器上的详细执行过程';

-- 任务执行日志表
CREATE TABLE acwl_task_logs (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '日志ID，自增主键',
    execution_id VARCHAR(100) NOT NULL COMMENT '执行ID',
    log_level ENUM('DEBUG', 'INFO', 'WARN', 'ERROR', 'FATAL') NOT NULL COMMENT '日志级别',
    log_source ENUM('system', 'application', 'user') NOT NULL DEFAULT 'application' COMMENT '日志来源',
    log_message TEXT NOT NULL COMMENT '日志消息',
    log_context JSON COMMENT '日志上下文',
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '日志时间',
    INDEX idx_execution_id (execution_id),
    INDEX idx_log_level (log_level),
    INDEX idx_log_source (log_source),
    INDEX idx_timestamp (timestamp),
    FOREIGN KEY (execution_id) REFERENCES acwl_task_executions(execution_id) ON DELETE CASCADE
) COMMENT '任务执行日志表，记录任务执行过程中的详细日志信息';

-- 任务执行结果表
CREATE TABLE acwl_task_results (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '结果ID，自增主键',
    execution_id VARCHAR(100) NOT NULL COMMENT '执行ID',
    result_type ENUM('output', 'file', 'metrics', 'error', 'custom') NOT NULL COMMENT '结果类型',
    result_name VARCHAR(200) COMMENT '结果名称',
    result_value TEXT COMMENT '结果值',
    result_path VARCHAR(500) COMMENT '结果文件路径',
    result_size BIGINT COMMENT '结果大小（字节）',
    result_metadata JSON COMMENT '结果元数据',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    INDEX idx_execution_id (execution_id),
    INDEX idx_result_type (result_type),
    INDEX idx_result_name (result_name),
    FOREIGN KEY (execution_id) REFERENCES acwl_task_executions(execution_id) ON DELETE CASCADE
) COMMENT '任务执行结果表，存储任务执行产生的各种结果数据';

-- ============================================
-- 6. 系统监控和健康检查表
-- ============================================

-- 系统健康状态表
CREATE TABLE acwl_system_health (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '健康检查ID，自增主键',
    component_type ENUM('scheduler', 'executor', 'database', 'queue', 'storage') NOT NULL COMMENT '组件类型',
    component_id VARCHAR(100) NOT NULL COMMENT '组件标识',
    health_status ENUM('healthy', 'warning', 'critical', 'unknown') NOT NULL COMMENT '健康状态',
    check_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '检查时间',
    response_time_ms INT COMMENT '响应时间（毫秒）',
    error_message TEXT COMMENT '错误信息',
    metrics JSON COMMENT '健康指标',
    metadata JSON COMMENT '检查元数据',
    INDEX idx_component_type (component_type),
    INDEX idx_component_id (component_id),
    INDEX idx_health_status (health_status),
    INDEX idx_check_time (check_time)
) COMMENT '系统健康状态表，记录各组件的健康检查结果';

-- 性能监控表
CREATE TABLE acwl_performance_metrics (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '指标ID，自增主键',
    metric_type ENUM('system', 'task', 'queue', 'executor', 'scheduler') NOT NULL COMMENT '指标类型',
    component_id VARCHAR(100) NOT NULL COMMENT '组件标识',
    metric_name VARCHAR(100) NOT NULL COMMENT '指标名称',
    metric_value DECIMAL(15,4) NOT NULL COMMENT '指标值',
    metric_unit VARCHAR(20) COMMENT '指标单位',
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '记录时间',
    tags JSON COMMENT '标签信息',
    INDEX idx_metric_type (metric_type),
    INDEX idx_component_id (component_id),
    INDEX idx_metric_name (metric_name),
    INDEX idx_timestamp (timestamp)
) COMMENT '性能监控表，记录系统各组件的性能指标数据';

-- ============================================
-- 7. 系统配置和管理表
-- ============================================

-- 任务系统配置表
CREATE TABLE acwl_task_system_config (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '配置ID，自增主键',
    config_key VARCHAR(100) NOT NULL UNIQUE COMMENT '配置键',
    config_value TEXT COMMENT '配置值',
    config_type ENUM('string', 'number', 'boolean', 'json') NOT NULL DEFAULT 'string' COMMENT '配置类型',
    description TEXT COMMENT '配置描述',
    is_system BOOLEAN DEFAULT FALSE COMMENT '是否为系统配置',
    updated_by INT COMMENT '更新者ID',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_config_key (config_key),
    INDEX idx_is_system (is_system),
    FOREIGN KEY (updated_by) REFERENCES acwl_users(id) ON DELETE SET NULL
) COMMENT '任务系统配置表，存储任务管理系统的全局配置参数';

-- 任务事件表
CREATE TABLE acwl_task_events (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '事件ID，自增主键',
    event_type ENUM('task_created', 'task_started', 'task_completed', 'task_failed', 'task_cancelled', 'executor_registered', 'executor_offline', 'scheduler_elected', 'system_alert') NOT NULL COMMENT '事件类型',
    event_source VARCHAR(100) NOT NULL COMMENT '事件源',
    event_target VARCHAR(100) COMMENT '事件目标',
    event_data JSON COMMENT '事件数据',
    event_message TEXT COMMENT '事件消息',
    severity ENUM('info', 'warning', 'error', 'critical') NOT NULL DEFAULT 'info' COMMENT '严重程度',
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '事件时间',
    processed BOOLEAN DEFAULT FALSE COMMENT '是否已处理',
    INDEX idx_event_type (event_type),
    INDEX idx_event_source (event_source),
    INDEX idx_severity (severity),
    INDEX idx_timestamp (timestamp),
    INDEX idx_processed (processed)
) COMMENT '任务事件表，记录系统中发生的各种事件和告警信息';

-- ============================================
-- 8. 初始化数据
-- ============================================

-- 插入默认执行器分组
INSERT INTO acwl_executor_groups (group_name, display_name, description, group_type, max_concurrent_tasks, task_types) VALUES
('default', '默认分组', '默认的通用执行器分组', 'general', 10, '["data_sync", "etl", "custom"]'),
('gpu_group', 'GPU计算分组', '专用于GPU密集型任务的执行器分组', 'gpu', 5, '["model_training", "data_analysis"]'),
('cpu_intensive', 'CPU密集型分组', '专用于CPU密集型任务的执行器分组', 'cpu_intensive', 8, '["data_analysis", "etl"]'),
('memory_intensive', '内存密集型分组', '专用于内存密集型任务的执行器分组', 'memory_intensive', 6, '["data_sync", "data_analysis"]');

-- 插入默认任务模板
INSERT INTO acwl_task_templates (name, description, task_type, default_executor_group, template_config, is_system) VALUES
('数据同步模板', '用于数据库间数据同步的标准模板', 'data_sync', 'default', 
 '{"timeout_seconds": 1800, "max_retry_count": 3, "resource_requirements": {"cpu": "1", "memory": "2GB"}}', TRUE),
('模型训练模板', '用于机器学习模型训练的GPU模板', 'model_training', 'gpu_group',
 '{"timeout_seconds": 7200, "max_retry_count": 1, "resource_requirements": {"cpu": "4", "memory": "16GB", "gpu": "1"}}', TRUE),
('数据分析模板', '用于数据分析和报表生成的模板', 'data_analysis', 'cpu_intensive',
 '{"timeout_seconds": 3600, "max_retry_count": 2, "resource_requirements": {"cpu": "2", "memory": "8GB"}}', TRUE),
('ETL处理模板', '用于数据抽取转换加载的模板', 'etl', 'memory_intensive',
 '{"timeout_seconds": 2400, "max_retry_count": 3, "resource_requirements": {"cpu": "2", "memory": "12GB"}}', TRUE);

-- 插入系统配置
INSERT INTO acwl_task_system_config (config_key, config_value, config_type, description, is_system) VALUES
('scheduler.heartbeat_interval', '30', 'number', '调度器心跳间隔（秒）', TRUE),
('scheduler.leader_lease_duration', '60', 'number', 'Leader租约持续时间（秒）', TRUE),
('executor.heartbeat_interval', '15', 'number', '执行器心跳间隔（秒）', TRUE),
('executor.max_idle_time', '300', 'number', '执行器最大空闲时间（秒）', TRUE),
('task.default_timeout', '3600', 'number', '任务默认超时时间（秒）', TRUE),
('task.max_retry_count', '3', 'number', '任务最大重试次数', TRUE),
('queue.max_size', '10000', 'number', '任务队列最大大小', TRUE),
('system.log_retention_days', '30', 'number', '日志保留天数', TRUE);