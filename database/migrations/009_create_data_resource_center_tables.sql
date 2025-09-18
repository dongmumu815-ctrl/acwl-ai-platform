-- 数据资源中心相关表
-- 创建时间: 2024-01-15
-- 描述: 为数据资源中心添加资源管理、权限控制、分类管理等功能

-- 数据资源分类表
CREATE TABLE acwl_data_resource_categories (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '分类ID',
    name VARCHAR(50) NOT NULL COMMENT '分类名称',
    display_name VARCHAR(50) NOT NULL COMMENT '显示名称',
    description TEXT COMMENT '分类描述',
    parent_id INT COMMENT '父分类ID',
    sort_order INT DEFAULT 0 COMMENT '排序',
    is_active BOOLEAN DEFAULT TRUE COMMENT '是否启用',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    FOREIGN KEY (parent_id) REFERENCES acwl_data_resource_categories(id),
    UNIQUE KEY uk_name (name),
    INDEX idx_parent_id (parent_id),
    INDEX idx_sort_order (sort_order)
) COMMENT '数据资源分类表';

-- 数据资源表
CREATE TABLE acwl_data_resources (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '资源ID',
    name VARCHAR(100) NOT NULL COMMENT '资源名称',
    display_name VARCHAR(100) NOT NULL COMMENT '显示名称',
    description TEXT COMMENT '资源描述',
    resource_type ENUM('doris_table', 'elasticsearch_index') NOT NULL COMMENT '资源类型',
    datasource_id INT NOT NULL COMMENT '数据源ID',
    database_name VARCHAR(100) COMMENT '数据库名称(Doris)',
    table_name VARCHAR(100) COMMENT '表名称(Doris)',
    index_name VARCHAR(100) COMMENT '索引名称(ES)',
    schema_info JSON COMMENT '表结构信息',
    tags JSON COMMENT '标签信息',
    category_id INT COMMENT '分类ID',
    is_public BOOLEAN DEFAULT FALSE COMMENT '是否公开',
    status ENUM('active', 'inactive', 'archived') DEFAULT 'active' COMMENT '状态',
    view_count INT DEFAULT 0 COMMENT '查看次数',
    query_count INT DEFAULT 0 COMMENT '查询次数',
    last_accessed_at TIMESTAMP NULL COMMENT '最后访问时间',
    created_by INT NOT NULL COMMENT '创建者ID',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    FOREIGN KEY (datasource_id) REFERENCES acwl_datasources(id),
    FOREIGN KEY (category_id) REFERENCES acwl_data_resource_categories(id),
    FOREIGN KEY (created_by) REFERENCES acwl_users(id),
    UNIQUE KEY uk_resource_unique (datasource_id, database_name, table_name, index_name),
    INDEX idx_resource_type (resource_type),
    INDEX idx_category_id (category_id),
    INDEX idx_status (status),
    INDEX idx_created_by (created_by),
    INDEX idx_is_public (is_public)
) COMMENT '数据资源表';

-- 数据资源权限表
CREATE TABLE acwl_data_resource_permissions (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '权限ID',
    resource_id INT NOT NULL COMMENT '资源ID',
    user_id INT COMMENT '用户ID',
    role_id INT COMMENT '角色ID',
    permission_type ENUM('read', 'write', 'admin') NOT NULL COMMENT '权限类型',
    granted_by INT NOT NULL COMMENT '授权者ID',
    granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '授权时间',
    expires_at TIMESTAMP NULL COMMENT '过期时间',
    is_active BOOLEAN DEFAULT TRUE COMMENT '是否有效',
    notes TEXT COMMENT '备注',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    FOREIGN KEY (resource_id) REFERENCES acwl_data_resources(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES acwl_users(id),
    FOREIGN KEY (granted_by) REFERENCES acwl_users(id),
    UNIQUE KEY uk_resource_user (resource_id, user_id),
    INDEX idx_user_id (user_id),
    INDEX idx_permission_type (permission_type),
    INDEX idx_expires_at (expires_at),
    INDEX idx_is_active (is_active)
) COMMENT '数据资源权限表';

-- 数据资源访问日志表
CREATE TABLE acwl_data_resource_access_logs (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '日志ID',
    resource_id INT NOT NULL COMMENT '资源ID',
    user_id INT NOT NULL COMMENT '用户ID',
    access_type ENUM('view', 'query', 'download', 'preview', 'schema') NOT NULL COMMENT '访问类型',
    query_sql TEXT COMMENT '查询SQL',
    query_params JSON COMMENT '查询参数',
    result_count INT COMMENT '结果数量',
    execution_time INT COMMENT '执行时间(毫秒)',
    ip_address VARCHAR(45) COMMENT 'IP地址',
    user_agent TEXT COMMENT '用户代理',
    status ENUM('success', 'failed', 'timeout', 'permission_denied') NOT NULL COMMENT '状态',
    error_message TEXT COMMENT '错误信息',
    accessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '访问时间',
    FOREIGN KEY (resource_id) REFERENCES acwl_data_resources(id),
    FOREIGN KEY (user_id) REFERENCES acwl_users(id),
    INDEX idx_resource_user (resource_id, user_id),
    INDEX idx_accessed_at (accessed_at),
    INDEX idx_access_type (access_type),
    INDEX idx_status (status)
) COMMENT '数据资源访问日志表';

-- 数据资源收藏表
CREATE TABLE acwl_data_resource_favorites (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '收藏ID',
    resource_id INT NOT NULL COMMENT '资源ID',
    user_id INT NOT NULL COMMENT '用户ID',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '收藏时间',
    FOREIGN KEY (resource_id) REFERENCES acwl_data_resources(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES acwl_users(id),
    UNIQUE KEY uk_resource_user_favorite (resource_id, user_id),
    INDEX idx_user_id (user_id)
) COMMENT '数据资源收藏表';

-- 数据资源查询历史表
CREATE TABLE acwl_data_resource_query_history (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '历史ID',
    resource_id INT NOT NULL COMMENT '资源ID',
    user_id INT NOT NULL COMMENT '用户ID',
    query_name VARCHAR(100) COMMENT '查询名称',
    query_sql TEXT NOT NULL COMMENT '查询SQL',
    query_params JSON COMMENT '查询参数',
    result_count INT COMMENT '结果数量',
    execution_time INT COMMENT '执行时间(毫秒)',
    is_saved BOOLEAN DEFAULT FALSE COMMENT '是否保存',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    FOREIGN KEY (resource_id) REFERENCES acwl_data_resources(id),
    FOREIGN KEY (user_id) REFERENCES acwl_users(id),
    INDEX idx_resource_user (resource_id, user_id),
    INDEX idx_created_at (created_at),
    INDEX idx_is_saved (is_saved)
) COMMENT '数据资源查询历史表';

-- 数据资源标签表
CREATE TABLE acwl_data_resource_tags (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '标签ID',
    name VARCHAR(50) NOT NULL COMMENT '标签名称',
    color VARCHAR(7) DEFAULT '#409EFF' COMMENT '标签颜色',
    description TEXT COMMENT '标签描述',
    usage_count INT DEFAULT 0 COMMENT '使用次数',
    created_by INT COMMENT '创建者ID',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    FOREIGN KEY (created_by) REFERENCES acwl_users(id),
    UNIQUE KEY uk_tag_name (name),
    INDEX idx_usage_count (usage_count)
) COMMENT '数据资源标签表';

-- 数据资源标签关联表
CREATE TABLE acwl_data_resource_tag_relations (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '关联ID',
    resource_id INT NOT NULL COMMENT '资源ID',
    tag_id INT NOT NULL COMMENT '标签ID',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    FOREIGN KEY (resource_id) REFERENCES acwl_data_resources(id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES acwl_data_resource_tags(id) ON DELETE CASCADE,
    UNIQUE KEY uk_resource_tag (resource_id, tag_id),
    INDEX idx_tag_id (tag_id)
) COMMENT '数据资源标签关联表';

-- 插入默认分类数据
INSERT INTO acwl_data_resource_categories (name, display_name, description, sort_order) VALUES
('ods', 'ODS层', '原始数据层，存储从各个业务系统抽取的原始数据', 1),
('dwd', 'DWD层', '数据仓库明细层，经过清洗和标准化的明细数据', 2),
('dws', 'DWS层', '数据仓库汇总层，按主题域汇总的数据', 3),
('ads', 'ADS层', '应用数据服务层，面向应用的数据服务', 4),
('dim', '维度表', '维度数据，包括各种字典和维度信息', 5),
('fact', '事实表', '事实数据，记录业务过程的度量数据', 6),
('report', '报表数据', '用于报表展示的汇总数据', 7),
('realtime', '实时数据', '实时计算产生的数据', 8),
('external', '外部数据', '来自外部系统的数据', 9),
('temp', '临时数据', '临时处理过程中产生的数据', 10);

-- 插入默认标签数据
INSERT INTO acwl_data_resource_tags (name, color, description) VALUES
('核心业务', '#E6A23C', '核心业务相关的重要数据'),
('财务数据', '#F56C6C', '财务相关的敏感数据'),
('用户数据', '#409EFF', '用户相关的数据'),
('订单数据', '#67C23A', '订单交易相关数据'),
('日志数据', '#909399', '系统日志和行为数据'),
('实时数据', '#E6A23C', '实时更新的数据'),
('历史数据', '#909399', '历史归档数据'),
('测试数据', '#F56C6C', '测试环境数据'),
('敏感数据', '#F56C6C', '包含敏感信息的数据'),
('公开数据', '#67C23A', '可以公开访问的数据');

-- 创建视图：用户可访问的资源
CREATE VIEW v_user_accessible_resources AS
SELECT DISTINCT
    r.id,
    r.name,
    r.display_name,
    r.description,
    r.resource_type,
    r.datasource_id,
    r.database_name,
    r.table_name,
    r.index_name,
    r.category_id,
    c.display_name as category_name,
    r.is_public,
    r.status,
    r.view_count,
    r.query_count,
    r.last_accessed_at,
    r.created_by,
    r.created_at,
    r.updated_at,
    COALESCE(p.permission_type, CASE WHEN r.is_public THEN 'read' ELSE NULL END) as permission_type
FROM acwl_data_resources r
LEFT JOIN acwl_data_resource_categories c ON r.category_id = c.id
LEFT JOIN acwl_data_resource_permissions p ON r.id = p.resource_id 
    AND p.is_active = TRUE 
    AND (p.expires_at IS NULL OR p.expires_at > NOW())
WHERE r.status = 'active'
    AND (r.is_public = TRUE OR p.user_id IS NOT NULL);

-- 创建存储过程：更新资源访问统计
DELIMITER //
CREATE PROCEDURE UpdateResourceAccessStats(
    IN p_resource_id INT,
    IN p_access_type ENUM('view', 'query', 'download', 'preview', 'schema')
)
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;
    
    START TRANSACTION;
    
    -- 更新访问统计
    IF p_access_type = 'view' THEN
        UPDATE acwl_data_resources 
        SET view_count = view_count + 1,
            last_accessed_at = NOW()
        WHERE id = p_resource_id;
    ELSEIF p_access_type = 'query' THEN
        UPDATE acwl_data_resources 
        SET query_count = query_count + 1,
            last_accessed_at = NOW()
        WHERE id = p_resource_id;
    ELSE
        UPDATE acwl_data_resources 
        SET last_accessed_at = NOW()
        WHERE id = p_resource_id;
    END IF;
    
    COMMIT;
END //
DELIMITER ;

-- 创建触发器：自动更新标签使用次数
DELIMITER //
CREATE TRIGGER tr_update_tag_usage_count_insert
AFTER INSERT ON acwl_data_resource_tag_relations
FOR EACH ROW
BEGIN
    UPDATE acwl_data_resource_tags 
    SET usage_count = usage_count + 1 
    WHERE id = NEW.tag_id;
END //

CREATE TRIGGER tr_update_tag_usage_count_delete
AFTER DELETE ON acwl_data_resource_tag_relations
FOR EACH ROW
BEGIN
    UPDATE acwl_data_resource_tags 
    SET usage_count = usage_count - 1 
    WHERE id = OLD.tag_id AND usage_count > 0;
END //
DELIMITER ;

-- 创建索引优化查询性能
CREATE INDEX idx_resources_composite ON acwl_data_resources(status, is_public, category_id);
CREATE INDEX idx_permissions_composite ON acwl_data_resource_permissions(user_id, is_active, expires_at);
CREATE INDEX idx_access_logs_composite ON acwl_data_resource_access_logs(resource_id, accessed_at, status);