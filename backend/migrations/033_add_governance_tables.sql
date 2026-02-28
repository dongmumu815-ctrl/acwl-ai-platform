-- 创建治理表元数据表
CREATE TABLE IF NOT EXISTS acwl_governance_tables (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '表ID',
    datasource_id INT NOT NULL COMMENT '数据源ID',
    schema_name VARCHAR(100) NOT NULL COMMENT '数据库/模式名',
    table_name VARCHAR(100) NOT NULL COMMENT '表名',
    description TEXT COMMENT '表描述',
    owner VARCHAR(100) COMMENT '负责人',
    classification_level VARCHAR(50) COMMENT '分级分类',
    retention_period INT COMMENT '保留周期(天)',
    tags VARCHAR(500) COMMENT '标签(逗号分隔)',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    created_by INT COMMENT '创建人',
    updated_by INT COMMENT '更新人',
    FOREIGN KEY (datasource_id) REFERENCES acwl_datasources(id) ON DELETE CASCADE,
    FOREIGN KEY (created_by) REFERENCES acwl_users(id),
    FOREIGN KEY (updated_by) REFERENCES acwl_users(id)
) COMMENT '数据治理-表元数据';

-- 创建治理字段元数据表
CREATE TABLE IF NOT EXISTS acwl_governance_columns (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '字段ID',
    table_id INT NOT NULL COMMENT '表ID',
    column_name VARCHAR(100) NOT NULL COMMENT '字段名',
    data_type VARCHAR(50) NOT NULL COMMENT '数据类型',
    is_nullable BOOLEAN DEFAULT TRUE COMMENT '是否可空',
    is_primary_key BOOLEAN DEFAULT FALSE COMMENT '是否主键',
    description TEXT COMMENT '字段描述',
    security_level VARCHAR(50) COMMENT '安全等级',
    data_standard VARCHAR(100) COMMENT '数据标准映射',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    created_by INT COMMENT '创建人',
    updated_by INT COMMENT '更新人',
    FOREIGN KEY (table_id) REFERENCES acwl_governance_tables(id) ON DELETE CASCADE,
    FOREIGN KEY (created_by) REFERENCES acwl_users(id),
    FOREIGN KEY (updated_by) REFERENCES acwl_users(id)
) COMMENT '数据治理-字段元数据';
