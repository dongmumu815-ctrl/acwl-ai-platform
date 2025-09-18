-- 创建资源包相关表
-- 创建时间: 2024-01-17
-- 描述: 创建资源包管理相关的数据表，支持SQL和ES资源包的创建和管理

-- 创建资源包表
CREATE TABLE resource_packages (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(255) NOT NULL COMMENT '资源包名称',
    description TEXT COMMENT '资源包描述',
    type ENUM('sql', 'elasticsearch') NOT NULL COMMENT '资源包类型',
    datasource_id INT NOT NULL COMMENT '数据源ID',
    resource_id INT COMMENT '数据资源ID',
    base_config JSON COMMENT '基础配置(schema, table, fields等)',
    locked_conditions JSON COMMENT '锁定条件配置',
    dynamic_conditions JSON COMMENT '动态条件配置',
    order_config JSON COMMENT '排序配置',
    limit_config INT DEFAULT 1000 COMMENT '默认限制条数',
    is_active BOOLEAN DEFAULT TRUE COMMENT '是否启用',
    created_by INT NOT NULL COMMENT '创建者ID',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- 添加索引
    INDEX idx_datasource_id (datasource_id),
    INDEX idx_resource_id (resource_id),
    INDEX idx_created_by (created_by),
    INDEX idx_type (type),
    INDEX idx_name (name),
    INDEX idx_active (is_active),
    
    -- 添加外键约束
    FOREIGN KEY (datasource_id) REFERENCES datasources(id) ON DELETE CASCADE,
    FOREIGN KEY (resource_id) REFERENCES acwl_data_resources(id) ON DELETE SET NULL,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE CASCADE
) COMMENT='资源包表';

-- 创建资源包权限表
CREATE TABLE resource_package_permissions (
    id INT PRIMARY KEY AUTO_INCREMENT,
    package_id INT NOT NULL COMMENT '资源包ID',
    user_id INT NOT NULL COMMENT '用户ID',
    permission_type ENUM('read', 'write', 'admin') NOT NULL COMMENT '权限类型',
    granted_by INT NOT NULL COMMENT '授权者ID',
    granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NULL COMMENT '过期时间',
    is_active BOOLEAN DEFAULT TRUE COMMENT '是否有效',
    
    -- 添加索引
    INDEX idx_package_id (package_id),
    INDEX idx_user_id (user_id),
    INDEX idx_permission_type (permission_type),
    INDEX idx_granted_by (granted_by),
    INDEX idx_expires_at (expires_at),
    
    -- 添加唯一约束
    UNIQUE KEY uk_package_user (package_id, user_id),
    
    -- 添加外键约束
    FOREIGN KEY (package_id) REFERENCES resource_packages(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (granted_by) REFERENCES users(id) ON DELETE CASCADE
) COMMENT='资源包权限表';

-- 创建资源包查询历史表
CREATE TABLE resource_package_query_history (
    id INT PRIMARY KEY AUTO_INCREMENT,
    package_id INT NOT NULL COMMENT '资源包ID',
    user_id INT NOT NULL COMMENT '查询用户ID',
    dynamic_params JSON COMMENT '动态参数值',
    generated_query TEXT COMMENT '生成的查询语句',
    result_count INT DEFAULT 0 COMMENT '结果行数',
    execution_time INT DEFAULT 0 COMMENT '执行时间(毫秒)',
    status ENUM('success', 'error', 'timeout') DEFAULT 'success' COMMENT '执行状态',
    error_message TEXT COMMENT '错误信息',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- 添加索引
    INDEX idx_package_id (package_id),
    INDEX idx_user_id (user_id),
    INDEX idx_created_at (created_at),
    INDEX idx_status (status),
    
    -- 添加外键约束
    FOREIGN KEY (package_id) REFERENCES resource_packages(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) COMMENT='资源包查询历史表';

-- 创建资源包标签关联表
CREATE TABLE resource_package_tags (
    id INT PRIMARY KEY AUTO_INCREMENT,
    package_id INT NOT NULL COMMENT '资源包ID',
    tag_name VARCHAR(100) NOT NULL COMMENT '标签名称',
    tag_color VARCHAR(20) DEFAULT '#409EFF' COMMENT '标签颜色',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- 添加索引
    INDEX idx_package_id (package_id),
    INDEX idx_tag_name (tag_name),
    
    -- 添加唯一约束
    UNIQUE KEY uk_package_tag (package_id, tag_name),
    
    -- 添加外键约束
    FOREIGN KEY (package_id) REFERENCES resource_packages(id) ON DELETE CASCADE
) COMMENT='资源包标签关联表';

-- 插入示例数据
INSERT INTO resource_packages (
    name, 
    description, 
    type, 
    datasource_id, 
    resource_id,
    base_config,
    locked_conditions,
    dynamic_conditions,
    order_config,
    created_by
) VALUES (
    '活跃用户查询包',
    '查询状态为活跃的用户数据，支持按注册时间筛选',
    'sql',
    8,
    NULL,
    JSON_OBJECT(
        'schema', 'acwl-agents',
        'table', 'users',
        'fields', JSON_ARRAY('id', 'username', 'email', 'status', 'created_at', 'last_login_at')
    ),
    JSON_ARRAY(
        JSON_OBJECT(
            'field', 'status',
            'operator', '=',
            'value', '1',
            'logic', 'AND'
        )
    ),
    JSON_ARRAY(
        JSON_OBJECT(
            'field', 'created_at',
            'operator', '>=',
            'default_value', '2024-01-01',
            'required', false,
            'description', '注册时间起始日期',
            'logic', 'AND'
        ),
        JSON_OBJECT(
            'field', 'last_login_at',
            'operator', '>=',
            'default_value', '',
            'required', false,
            'description', '最后登录时间',
            'logic', 'AND'
        )
    ),
    JSON_OBJECT(
        'field', 'created_at',
        'direction', 'DESC'
    ),
    1
);

-- 插入权限示例数据
INSERT INTO resource_package_permissions (package_id, user_id, permission_type, granted_by)
VALUES (1, 1, 'admin', 1);

-- 插入标签示例数据
INSERT INTO resource_package_tags (package_id, tag_name, tag_color)
VALUES 
(1, '用户管理', '#409EFF'),
(1, '运营分析', '#67C23A');