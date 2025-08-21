-- 任务和工作流管理系统数据库迁移脚本
-- 创建时间: 2024-01-01
-- 描述: 添加任务管理和工作流管理相关表结构

-- ================================
-- 工作流管理表
-- ================================

-- 工作流定义表
CREATE TABLE IF NOT EXISTS acwl_workflows (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '工作流ID',
    name VARCHAR(255) NOT NULL COMMENT '工作流名称',
    description TEXT COMMENT '工作流描述',
    version VARCHAR(50) NOT NULL DEFAULT '1.0.0' COMMENT '版本号',
    status ENUM('DRAFT', 'ACTIVE', 'INACTIVE', 'ARCHIVED') NOT NULL DEFAULT 'DRAFT' COMMENT '状态',
    project_id BIGINT COMMENT '所属项目ID',
    created_by BIGINT NOT NULL COMMENT '创建者ID',
    updated_by BIGINT COMMENT '更新者ID',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    INDEX idx_project_id (project_id),
    INDEX idx_created_by (created_by),
    INDEX idx_status (status),
    INDEX idx_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='工作流定义表';

-- 工作流节点表
CREATE TABLE IF NOT EXISTS acwl_workflow_nodes (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '节点ID',
    workflow_id BIGINT NOT NULL COMMENT '工作流ID',
    name VARCHAR(255) NOT NULL COMMENT '节点名称',
    node_type ENUM('START', 'END', 'TASK', 'CONDITION', 'PARALLEL', 'MERGE') NOT NULL COMMENT '节点类型',
    position_x INT DEFAULT 0 COMMENT 'X坐标',
    position_y INT DEFAULT 0 COMMENT 'Y坐标',
    config JSON COMMENT '节点配置',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    INDEX idx_workflow_id (workflow_id),
    INDEX idx_node_type (node_type),
    FOREIGN KEY (workflow_id) REFERENCES acwl_workflows(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='工作流节点表';

-- 工作流连接表
CREATE TABLE IF NOT EXISTS acwl_workflow_connections (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '连接ID',
    workflow_id BIGINT NOT NULL COMMENT '工作流ID',
    source_node_id BIGINT NOT NULL COMMENT '源节点ID',
    target_node_id BIGINT NOT NULL COMMENT '目标节点ID',
    connection_type ENUM('SEQUENCE', 'CONDITION', 'PARALLEL') NOT NULL DEFAULT 'SEQUENCE' COMMENT '连接类型',
    condition_expression TEXT COMMENT '条件表达式',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    
    INDEX idx_workflow_id (workflow_id),
    INDEX idx_source_node (source_node_id),
    INDEX idx_target_node (target_node_id),
    FOREIGN KEY (workflow_id) REFERENCES acwl_workflows(id) ON DELETE CASCADE,
    FOREIGN KEY (source_node_id) REFERENCES acwl_workflow_nodes(id) ON DELETE CASCADE,
    FOREIGN KEY (target_node_id) REFERENCES acwl_workflow_nodes(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='工作流连接表';

-- 工作流实例表
CREATE TABLE IF NOT EXISTS acwl_workflow_instances (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '实例ID',
    workflow_id BIGINT NOT NULL COMMENT '工作流ID',
    name VARCHAR(255) COMMENT '实例名称',
    status ENUM('PENDING', 'RUNNING', 'COMPLETED', 'FAILED', 'CANCELLED', 'PAUSED') NOT NULL DEFAULT 'PENDING' COMMENT '状态',
    priority ENUM('LOW', 'NORMAL', 'HIGH', 'URGENT') NOT NULL DEFAULT 'NORMAL' COMMENT '优先级',
    input_data JSON COMMENT '输入数据',
    output_data JSON COMMENT '输出数据',
    error_message TEXT COMMENT '错误信息',
    started_by BIGINT COMMENT '启动者ID',
    started_at TIMESTAMP NULL COMMENT '开始时间',
    completed_at TIMESTAMP NULL COMMENT '完成时间',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    
    INDEX idx_workflow_id (workflow_id),
    INDEX idx_status (status),
    INDEX idx_priority (priority),
    INDEX idx_started_by (started_by),
    INDEX idx_started_at (started_at),
    FOREIGN KEY (workflow_id) REFERENCES acwl_workflows(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='工作流实例表';

-- 工作流节点实例表
CREATE TABLE IF NOT EXISTS acwl_workflow_node_instances (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '节点实例ID',
    workflow_instance_id BIGINT NOT NULL COMMENT '工作流实例ID',
    workflow_node_id BIGINT NOT NULL COMMENT '工作流节点ID',
    status ENUM('PENDING', 'RUNNING', 'COMPLETED', 'FAILED', 'SKIPPED', 'CANCELLED') NOT NULL DEFAULT 'PENDING' COMMENT '状态',
    input_data JSON COMMENT '输入数据',
    output_data JSON COMMENT '输出数据',
    error_message TEXT COMMENT '错误信息',
    retry_count INT DEFAULT 0 COMMENT '重试次数',
    started_at TIMESTAMP NULL COMMENT '开始时间',
    completed_at TIMESTAMP NULL COMMENT '完成时间',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    
    INDEX idx_workflow_instance_id (workflow_instance_id),
    INDEX idx_workflow_node_id (workflow_node_id),
    INDEX idx_status (status),
    INDEX idx_started_at (started_at),
    FOREIGN KEY (workflow_instance_id) REFERENCES acwl_workflow_instances(id) ON DELETE CASCADE,
    FOREIGN KEY (workflow_node_id) REFERENCES acwl_workflow_nodes(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='工作流节点实例表';

-- 工作流调度配置表
CREATE TABLE IF NOT EXISTS acwl_workflow_schedules (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '调度ID',
    workflow_id BIGINT NOT NULL COMMENT '工作流ID',
    name VARCHAR(255) NOT NULL COMMENT '调度名称',
    trigger_type ENUM('MANUAL', 'CRON', 'EVENT', 'API') NOT NULL DEFAULT 'MANUAL' COMMENT '触发类型',
    schedule_type ENUM('ONCE', 'RECURRING', 'CONDITIONAL') NOT NULL DEFAULT 'ONCE' COMMENT '调度类型',
    cron_expression VARCHAR(255) COMMENT 'Cron表达式',
    start_time TIMESTAMP NULL COMMENT '开始时间',
    end_time TIMESTAMP NULL COMMENT '结束时间',
    timezone VARCHAR(50) DEFAULT 'UTC' COMMENT '时区',
    is_active BOOLEAN DEFAULT TRUE COMMENT '是否激活',
    misfire_policy ENUM('DO_NOTHING', 'FIRE_ONCE_NOW', 'FIRE_ALL_MISSED') DEFAULT 'DO_NOTHING' COMMENT '错过执行策略',
    max_instances INT DEFAULT 1 COMMENT '最大并发实例数',
    input_data JSON COMMENT '默认输入数据',
    created_by BIGINT NOT NULL COMMENT '创建者ID',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    INDEX idx_workflow_id (workflow_id),
    INDEX idx_trigger_type (trigger_type),
    INDEX idx_is_active (is_active),
    INDEX idx_start_time (start_time),
    FOREIGN KEY (workflow_id) REFERENCES acwl_workflows(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='工作流调度配置表';

-- ================================
-- 任务管理表（更新现有表结构）
-- ================================

-- 更新任务定义表，添加工作流相关字段
ALTER TABLE acwl_task_definitions 
ADD COLUMN workflow_id BIGINT COMMENT '所属工作流ID' AFTER project_id,
ADD COLUMN workflow_node_id BIGINT COMMENT '对应工作流节点ID' AFTER workflow_id,
ADD INDEX idx_workflow_id (workflow_id),
ADD INDEX idx_workflow_node_id (workflow_node_id);

-- 添加外键约束（如果工作流表已存在）
-- ALTER TABLE acwl_task_definitions 
-- ADD FOREIGN KEY (workflow_id) REFERENCES acwl_workflows(id) ON DELETE SET NULL,
-- ADD FOREIGN KEY (workflow_node_id) REFERENCES acwl_workflow_nodes(id) ON DELETE SET NULL;

-- 更新任务类型枚举，添加新的任务类型
ALTER TABLE acwl_task_definitions 
MODIFY COLUMN task_type ENUM(
    'BATCH', 'STREAMING', 'SCHEDULED', 'MANUAL', 'PYTHON_CODE', 
    'SQL_QUERY', 'CONDITION', 'DATA_PROCESSING', 'MODEL_TRAINING', 
    'MODEL_INFERENCE', 'DATA_VALIDATION', 'NOTIFICATION'
) NOT NULL DEFAULT 'BATCH' COMMENT '任务类型';

-- ================================
-- 初始化数据
-- ================================

-- 插入默认工作流模板
INSERT IGNORE INTO acwl_workflows (id, name, description, version, status, created_by) VALUES
(1, '数据处理工作流模板', '用于数据处理的标准工作流模板', '1.0.0', 'ACTIVE', 1),
(2, '模型训练工作流模板', '用于机器学习模型训练的工作流模板', '1.0.0', 'ACTIVE', 1),
(3, '数据验证工作流模板', '用于数据质量验证的工作流模板', '1.0.0', 'ACTIVE', 1);

-- 为数据处理工作流模板创建节点
INSERT IGNORE INTO acwl_workflow_nodes (id, workflow_id, name, node_type, position_x, position_y, config) VALUES
(1, 1, '开始', 'START', 100, 100, '{}'),
(2, 1, '数据提取', 'TASK', 300, 100, '{"task_type": "DATA_PROCESSING", "timeout": 3600}'),
(3, 1, '数据转换', 'TASK', 500, 100, '{"task_type": "DATA_PROCESSING", "timeout": 3600}'),
(4, 1, '数据加载', 'TASK', 700, 100, '{"task_type": "DATA_PROCESSING", "timeout": 3600}'),
(5, 1, '结束', 'END', 900, 100, '{}');

-- 为数据处理工作流模板创建连接
INSERT IGNORE INTO acwl_workflow_connections (workflow_id, source_node_id, target_node_id, connection_type) VALUES
(1, 1, 2, 'SEQUENCE'),
(1, 2, 3, 'SEQUENCE'),
(1, 3, 4, 'SEQUENCE'),
(1, 4, 5, 'SEQUENCE');

-- 为模型训练工作流模板创建节点
INSERT IGNORE INTO acwl_workflow_nodes (id, workflow_id, name, node_type, position_x, position_y, config) VALUES
(6, 2, '开始', 'START', 100, 100, '{}'),
(7, 2, '数据准备', 'TASK', 300, 100, '{"task_type": "DATA_PROCESSING", "timeout": 3600}'),
(8, 2, '模型训练', 'TASK', 500, 100, '{"task_type": "MODEL_TRAINING", "timeout": 7200}'),
(9, 2, '模型评估', 'TASK', 700, 100, '{"task_type": "MODEL_INFERENCE", "timeout": 1800}'),
(10, 2, '结束', 'END', 900, 100, '{}');

-- 为模型训练工作流模板创建连接
INSERT IGNORE INTO acwl_workflow_connections (workflow_id, source_node_id, target_node_id, connection_type) VALUES
(2, 6, 7, 'SEQUENCE'),
(2, 7, 8, 'SEQUENCE'),
(2, 8, 9, 'SEQUENCE'),
(2, 9, 10, 'SEQUENCE');

COMMIT;