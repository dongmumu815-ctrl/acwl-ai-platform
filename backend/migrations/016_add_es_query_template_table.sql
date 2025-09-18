-- 创建ES查询模板表
CREATE TABLE es_query_templates (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    datasource_id INT NOT NULL,
    indices JSON NOT NULL COMMENT 'JSON格式存储索引列表',
    query JSON NOT NULL COMMENT 'JSON格式存储查询DSL',
    tags JSON COMMENT 'JSON格式存储标签列表',
    is_template BOOLEAN DEFAULT TRUE,
    created_by INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (datasource_id) REFERENCES acwl_datasources (id) ON DELETE CASCADE,
    FOREIGN KEY (created_by) REFERENCES acwl_users (id) ON DELETE CASCADE
);

-- 创建SQL查询模板表
CREATE TABLE sql_query_templates (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    datasource_id INT NOT NULL,
    query TEXT NOT NULL COMMENT 'SQL查询语句',
    tags JSON COMMENT 'JSON格式存储标签列表',
    is_template BOOLEAN DEFAULT TRUE,
    created_by INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (datasource_id) REFERENCES acwl_datasources (id) ON DELETE CASCADE,
    FOREIGN KEY (created_by) REFERENCES acwl_users (id) ON DELETE CASCADE
);

-- 创建索引
CREATE INDEX idx_es_query_templates_datasource_id ON es_query_templates(datasource_id);
CREATE INDEX idx_es_query_templates_created_by ON es_query_templates(created_by);
CREATE INDEX idx_es_query_templates_name ON es_query_templates(name);
CREATE INDEX idx_es_query_templates_is_template ON es_query_templates(is_template);