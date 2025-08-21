-- 项目管理模块
-- 创建时间: 2024-01-15
-- 描述: 添加项目管理功能，支持项目创建、成员管理和权限分配

-- 项目表
CREATE TABLE acwl_projects (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '项目ID，自增主键',
    name VARCHAR(100) NOT NULL COMMENT '项目名称',
    description TEXT COMMENT '项目描述',
    status ENUM('active', 'inactive', 'archived') NOT NULL DEFAULT 'active' COMMENT '项目状态：激活、未激活、已归档',
    project_type ENUM('data_analysis', 'model_training', 'etl_pipeline', 'general') NOT NULL DEFAULT 'general' COMMENT '项目类型：数据分析、模型训练、ETL管道、通用',
    start_date DATE COMMENT '项目开始日期',
    end_date DATE COMMENT '项目结束日期',
    members_count INT DEFAULT 1 COMMENT '团队成员数量',
    priority ENUM('low', 'medium', 'high', 'critical') NOT NULL DEFAULT 'medium' COMMENT '项目优先级',
    tags JSON COMMENT '项目标签',
    project_metadata JSON COMMENT '项目元数据',
    created_by INT NOT NULL COMMENT '创建者ID',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_status (status),
    INDEX idx_project_type (project_type),
    INDEX idx_created_by (created_by),
    INDEX idx_priority (priority),
    FOREIGN KEY (created_by) REFERENCES acwl_users(id) ON DELETE RESTRICT
) COMMENT '项目表，管理数据中台的各个项目';

-- 项目成员表
CREATE TABLE acwl_project_members (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '成员ID，自增主键',
    project_id INT NOT NULL COMMENT '项目ID',
    user_id INT NOT NULL COMMENT '用户ID',
    role ENUM('admin', 'developer', 'viewer') NOT NULL COMMENT '项目角色：管理员、开发者、访客',
    permissions JSON COMMENT '具体权限配置',
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '加入时间',
    invited_by INT COMMENT '邀请者ID',
    is_active BOOLEAN DEFAULT TRUE COMMENT '是否激活',
    notes TEXT COMMENT '备注信息',
    UNIQUE KEY uk_project_user (project_id, user_id),
    INDEX idx_user_id (user_id),
    INDEX idx_role (role),
    INDEX idx_is_active (is_active),
    FOREIGN KEY (project_id) REFERENCES acwl_projects(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES acwl_users(id) ON DELETE CASCADE,
    FOREIGN KEY (invited_by) REFERENCES acwl_users(id) ON DELETE SET NULL
) COMMENT '项目成员表，管理项目的成员和角色权限';

-- 项目数据源关联表
CREATE TABLE acwl_project_datasources (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '关联ID，自增主键',
    project_id INT NOT NULL COMMENT '项目ID',
    datasource_id INT NOT NULL COMMENT '数据源ID',
    access_type ENUM('read', 'write', 'admin') NOT NULL DEFAULT 'read' COMMENT '访问类型：只读、读写、管理',
    is_primary BOOLEAN DEFAULT FALSE COMMENT '是否为主数据源',
    config JSON COMMENT '数据源在项目中的配置',
    assigned_by INT COMMENT '分配者ID',
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '分配时间',
    expires_at TIMESTAMP NULL COMMENT '过期时间',
    is_active BOOLEAN DEFAULT TRUE COMMENT '是否激活',
    notes TEXT COMMENT '备注信息',
    UNIQUE KEY uk_project_datasource (project_id, datasource_id),
    INDEX idx_datasource_id (datasource_id),
    INDEX idx_access_type (access_type),
    INDEX idx_is_primary (is_primary),
    INDEX idx_is_active (is_active),
    FOREIGN KEY (project_id) REFERENCES acwl_projects(id) ON DELETE CASCADE,
    FOREIGN KEY (datasource_id) REFERENCES acwl_datasources(id) ON DELETE CASCADE,
    FOREIGN KEY (assigned_by) REFERENCES acwl_users(id) ON DELETE SET NULL
) COMMENT '项目数据源关联表，管理项目可访问的数据源及权限';

-- 项目资源配额表
CREATE TABLE acwl_project_quotas (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '配额ID，自增主键',
    project_id INT NOT NULL COMMENT '项目ID',
    resource_type ENUM('storage', 'compute', 'memory', 'gpu', 'api_calls') NOT NULL COMMENT '资源类型',
    quota_limit BIGINT NOT NULL COMMENT '配额限制',
    quota_used BIGINT DEFAULT 0 COMMENT '已使用配额',
    unit VARCHAR(20) NOT NULL COMMENT '单位，如GB、hours、calls等',
    reset_period ENUM('daily', 'weekly', 'monthly', 'yearly', 'never') DEFAULT 'monthly' COMMENT '重置周期',
    last_reset_at TIMESTAMP NULL COMMENT '最后重置时间',
    is_active BOOLEAN DEFAULT TRUE COMMENT '是否激活',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    UNIQUE KEY uk_project_resource (project_id, resource_type),
    INDEX idx_resource_type (resource_type),
    INDEX idx_is_active (is_active),
    FOREIGN KEY (project_id) REFERENCES acwl_projects(id) ON DELETE CASCADE
) COMMENT '项目资源配额表，管理项目的资源使用限制';

-- 项目活动日志表
CREATE TABLE acwl_project_activities (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '活动ID，自增主键',
    project_id INT NOT NULL COMMENT '项目ID',
    user_id INT COMMENT '操作用户ID',
    activity_type ENUM('create', 'update', 'delete', 'member_add', 'member_remove', 'datasource_add', 'datasource_remove', 'permission_change') NOT NULL COMMENT '活动类型',
    target_type ENUM('project', 'member', 'datasource', 'quota', 'other') NOT NULL COMMENT '目标类型',
    target_id INT COMMENT '目标ID',
    description TEXT NOT NULL COMMENT '活动描述',
    details JSON COMMENT '活动详情',
    ip_address VARCHAR(45) COMMENT 'IP地址',
    user_agent TEXT COMMENT '用户代理',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    INDEX idx_project_id (project_id),
    INDEX idx_user_id (user_id),
    INDEX idx_activity_type (activity_type),
    INDEX idx_target_type (target_type),
    INDEX idx_created_at (created_at),
    FOREIGN KEY (project_id) REFERENCES acwl_projects(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES acwl_users(id) ON DELETE SET NULL
) COMMENT '项目活动日志表，记录项目相关的所有操作活动';

-- 项目模板表
CREATE TABLE acwl_project_templates (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '模板ID，自增主键',
    name VARCHAR(100) NOT NULL COMMENT '模板名称',
    description TEXT COMMENT '模板描述',
    project_type ENUM('data_analysis', 'model_training', 'etl_pipeline', 'general') NOT NULL COMMENT '项目类型',
    template_config JSON NOT NULL COMMENT '模板配置',
    default_roles JSON COMMENT '默认角色配置',
    default_quotas JSON COMMENT '默认配额配置',
    is_system BOOLEAN DEFAULT FALSE COMMENT '是否系统模板',
    is_active BOOLEAN DEFAULT TRUE COMMENT '是否激活',
    created_by INT COMMENT '创建者ID',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_project_type (project_type),
    INDEX idx_is_system (is_system),
    INDEX idx_is_active (is_active),
    FOREIGN KEY (created_by) REFERENCES acwl_users(id) ON DELETE SET NULL
) COMMENT '项目模板表，存储项目创建的预定义模板';

-- 插入默认项目模板
INSERT INTO acwl_project_templates (name, description, project_type, template_config, default_roles, default_quotas, is_system) VALUES
('数据分析项目模板', '用于数据分析和报表生成的标准项目模板', 'data_analysis', 
 '{"features": ["data_visualization", "reporting", "analytics"], "tools": ["jupyter", "pandas", "matplotlib"]}',
 '{"admin": {"permissions": ["all"]}, "developer": {"permissions": ["read", "write", "execute"]}, "viewer": {"permissions": ["read"]}}',
 '{"storage": {"limit": 100, "unit": "GB"}, "compute": {"limit": 50, "unit": "hours"}}', TRUE),

('模型训练项目模板', '用于机器学习模型训练和部署的项目模板', 'model_training',
 '{"features": ["model_training", "hyperparameter_tuning", "model_deployment"], "tools": ["pytorch", "tensorflow", "mlflow"]}',
 '{"admin": {"permissions": ["all"]}, "developer": {"permissions": ["read", "write", "train", "deploy"]}, "viewer": {"permissions": ["read"]}}',
 '{"storage": {"limit": 500, "unit": "GB"}, "compute": {"limit": 200, "unit": "hours"}, "gpu": {"limit": 100, "unit": "hours"}}', TRUE),

('ETL数据管道模板', '用于数据抽取、转换和加载的ETL项目模板', 'etl_pipeline',
 '{"features": ["data_extraction", "data_transformation", "data_loading", "scheduling"], "tools": ["seatunnel", "airflow", "spark"]}',
 '{"admin": {"permissions": ["all"]}, "developer": {"permissions": ["read", "write", "execute", "schedule"]}, "viewer": {"permissions": ["read"]}}',
 '{"storage": {"limit": 1000, "unit": "GB"}, "compute": {"limit": 100, "unit": "hours"}, "api_calls": {"limit": 10000, "unit": "calls"}}', TRUE),

('通用项目模板', '适用于各种类型项目的通用模板', 'general',
 '{"features": ["basic_analytics", "data_access"], "tools": ["basic_tools"]}',
 '{"admin": {"permissions": ["all"]}, "developer": {"permissions": ["read", "write"]}, "viewer": {"permissions": ["read"]}}',
 '{"storage": {"limit": 50, "unit": "GB"}, "compute": {"limit": 20, "unit": "hours"}}', TRUE);

-- 更新现有数据源权限表，添加项目关联
ALTER TABLE acwl_datasource_permissions ADD COLUMN project_id INT COMMENT '项目ID（可选，用于项目级权限管理）';
ALTER TABLE acwl_datasource_permissions ADD INDEX idx_project_id (project_id);
ALTER TABLE acwl_datasource_permissions ADD FOREIGN KEY (project_id) REFERENCES acwl_projects(id) ON DELETE CASCADE;

-- 为现有表添加项目关联（可选）
ALTER TABLE acwl_datasets ADD COLUMN project_id INT COMMENT '所属项目ID';
ALTER TABLE acwl_datasets ADD INDEX idx_project_id (project_id);
ALTER TABLE acwl_datasets ADD FOREIGN KEY (project_id) REFERENCES acwl_projects(id) ON DELETE SET NULL;

ALTER TABLE acwl_models ADD COLUMN project_id INT COMMENT '所属项目ID';
ALTER TABLE acwl_models ADD INDEX idx_project_id (project_id);
ALTER TABLE acwl_models ADD FOREIGN KEY (project_id) REFERENCES acwl_projects(id) ON DELETE SET NULL;

ALTER TABLE acwl_fine_tuning_jobs ADD COLUMN project_id INT COMMENT '所属项目ID';
ALTER TABLE acwl_fine_tuning_jobs ADD INDEX idx_project_id (project_id);
ALTER TABLE acwl_fine_tuning_jobs ADD FOREIGN KEY (project_id) REFERENCES acwl_projects(id) ON DELETE SET NULL;