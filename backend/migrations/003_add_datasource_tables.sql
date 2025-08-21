-- 数据源管理相关表
-- 创建时间: 2024-01-01
-- 描述: 添加数据源管理功能，支持多种数据库类型的配置和管理

-- 数据源表
CREATE TABLE acwl_datasources (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '数据源ID，自增主键',
    name VARCHAR(100) NOT NULL COMMENT '数据源名称',
    description TEXT COMMENT '数据源描述',
    datasource_type ENUM('mysql', 'doris', 'oracle', 'postgresql', 'sqlserver', 'clickhouse', 'mongodb', 'redis', 'elasticsearch', 'minio') NOT NULL COMMENT '数据源类型',
    host VARCHAR(255) NOT NULL COMMENT '主机地址',
    port INT NOT NULL COMMENT '端口号',
    database_name VARCHAR(100) COMMENT '数据库名称',
    username VARCHAR(100) COMMENT '用户名',
    password VARCHAR(255) COMMENT '密码（加密存储）',
    connection_params JSON COMMENT '连接参数，如SSL配置、超时设置等',
    pool_config JSON COMMENT '连接池配置',
    status ENUM('active', 'inactive', 'testing', 'error') NOT NULL DEFAULT 'inactive' COMMENT '数据源状态：激活、未激活、测试中、错误',
    last_test_time TIMESTAMP NULL COMMENT '最后测试时间',
    last_test_result TEXT COMMENT '最后测试结果',
    is_enabled BOOLEAN DEFAULT TRUE COMMENT '是否启用',
    created_by INT COMMENT '创建者ID',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_datasource_type (datasource_type),
    INDEX idx_status (status),
    INDEX idx_created_by (created_by)
) COMMENT '数据源表，存储各种类型数据库的连接配置信息';

-- 数据源连接测试日志表
CREATE TABLE acwl_datasource_test_logs (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '测试日志ID，自增主键',
    datasource_id INT NOT NULL COMMENT '数据源ID',
    test_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '测试时间',
    test_result ENUM('success', 'failed') NOT NULL COMMENT '测试结果：成功、失败',
    response_time INT COMMENT '响应时间（毫秒）',
    error_message TEXT COMMENT '错误信息',
    test_details JSON COMMENT '测试详情',
    tested_by INT COMMENT '测试者ID',
    INDEX idx_datasource_id (datasource_id),
    INDEX idx_test_time (test_time),
    FOREIGN KEY (datasource_id) REFERENCES acwl_datasources(id) ON DELETE CASCADE
) COMMENT '数据源连接测试日志表，记录数据源连接测试的历史记录';

-- 数据源使用统计表
CREATE TABLE acwl_datasource_usage_stats (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '统计ID，自增主键',
    datasource_id INT NOT NULL COMMENT '数据源ID',
    date DATE NOT NULL COMMENT '统计日期',
    connection_count INT DEFAULT 0 COMMENT '连接次数',
    query_count INT DEFAULT 0 COMMENT '查询次数',
    total_response_time BIGINT DEFAULT 0 COMMENT '总响应时间（毫秒）',
    error_count INT DEFAULT 0 COMMENT '错误次数',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    UNIQUE KEY uk_datasource_date (datasource_id, date),
    INDEX idx_date (date),
    FOREIGN KEY (datasource_id) REFERENCES acwl_datasources(id) ON DELETE CASCADE
) COMMENT '数据源使用统计表，记录数据源的使用情况和性能指标';

-- 数据源权限表
CREATE TABLE acwl_datasource_permissions (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '权限ID，自增主键',
    datasource_id INT NOT NULL COMMENT '数据源ID',
    user_id INT NOT NULL COMMENT '用户ID',
    permission_type ENUM('read', 'write', 'admin') NOT NULL COMMENT '权限类型：只读、读写、管理员',
    granted_by INT COMMENT '授权者ID',
    granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '授权时间',
    expires_at TIMESTAMP NULL COMMENT '过期时间',
    is_active BOOLEAN DEFAULT TRUE COMMENT '是否激活',
    UNIQUE KEY uk_datasource_user (datasource_id, user_id),
    INDEX idx_user_id (user_id),
    INDEX idx_permission_type (permission_type),
    FOREIGN KEY (datasource_id) REFERENCES acwl_datasources(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES acwl_users(id) ON DELETE CASCADE
) COMMENT '数据源权限表，管理用户对数据源的访问权限';

-- 数据源配置模板表
CREATE TABLE acwl_datasource_templates (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '模板ID，自增主键',
    name VARCHAR(100) NOT NULL COMMENT '模板名称',
    description TEXT COMMENT '模板描述',
    datasource_type ENUM('mysql', 'doris', 'oracle', 'postgresql', 'sqlserver', 'clickhouse', 'mongodb', 'redis', 'elasticsearch') NOT NULL COMMENT '数据源类型',
    default_port INT COMMENT '默认端口',
    default_params JSON COMMENT '默认连接参数',
    connection_url_template VARCHAR(500) COMMENT '连接URL模板',
    driver_class VARCHAR(200) COMMENT '驱动类名',
    validation_query VARCHAR(200) COMMENT '验证查询语句',
    is_system BOOLEAN DEFAULT FALSE COMMENT '是否系统模板',
    created_by INT COMMENT '创建者ID',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_datasource_type (datasource_type),
    INDEX idx_is_system (is_system)
) COMMENT '数据源配置模板表，存储不同数据库类型的默认配置模板';

-- 插入默认数据源模板
INSERT INTO acwl_datasource_templates (name, description, datasource_type, default_port, default_params, connection_url_template, driver_class, validation_query, is_system) VALUES
('MySQL 默认配置', 'MySQL 数据库默认连接配置', 'mysql', 3306, '{"charset": "utf8mb4", "autocommit": true, "connect_timeout": 10}', 'mysql+pymysql://{username}:{password}@{host}:{port}/{database}?charset=utf8mb4', 'com.mysql.cj.jdbc.Driver', 'SELECT 1', TRUE),
('Apache Doris 默认配置', 'Apache Doris 数据库默认连接配置', 'doris', 9030, '{"charset": "utf8mb4", "autocommit": true, "connect_timeout": 10}', 'mysql+pymysql://{username}:{password}@{host}:{port}/{database}?charset=utf8mb4', 'com.mysql.cj.jdbc.Driver', 'SELECT 1', TRUE),
('Oracle 默认配置', 'Oracle 数据库默认连接配置', 'oracle', 1521, '{"encoding": "UTF-8", "nls_lang": "AMERICAN_AMERICA.AL32UTF8"}', 'oracle+cx_oracle://{username}:{password}@{host}:{port}/{database}', 'oracle.jdbc.driver.OracleDriver', 'SELECT 1 FROM DUAL', TRUE),
('PostgreSQL 默认配置', 'PostgreSQL 数据库默认连接配置', 'postgresql', 5432, '{"client_encoding": "utf8", "connect_timeout": 10}', 'postgresql+psycopg2://{username}:{password}@{host}:{port}/{database}', 'org.postgresql.Driver', 'SELECT 1', TRUE),
('SQL Server 默认配置', 'Microsoft SQL Server 数据库默认连接配置', 'sqlserver', 1433, '{"driver": "ODBC Driver 17 for SQL Server", "timeout": 10}', 'mssql+pyodbc://{username}:{password}@{host}:{port}/{database}?driver=ODBC+Driver+17+for+SQL+Server', 'com.microsoft.sqlserver.jdbc.SQLServerDriver', 'SELECT 1', TRUE),
('ClickHouse 默认配置', 'ClickHouse 数据库默认连接配置', 'clickhouse', 9000, '{"compression": true, "connect_timeout": 10}', 'clickhouse+native://{username}:{password}@{host}:{port}/{database}', 'ru.yandex.clickhouse.ClickHouseDriver', 'SELECT 1', TRUE),
('MongoDB 默认配置', 'MongoDB 数据库默认连接配置', 'mongodb', 27017, '{"authSource": "admin", "connectTimeoutMS": 10000}', 'mongodb://{username}:{password}@{host}:{port}/{database}', 'mongodb.jdbc.MongoDriver', 'db.runCommand({ping: 1})', TRUE),
('Redis 默认配置', 'Redis 数据库默认连接配置', 'redis', 6379, '{"decode_responses": true, "socket_timeout": 10}', 'redis://{username}:{password}@{host}:{port}/{database}', 'redis.clients.jedis.Jedis', 'PING', TRUE),
('Elasticsearch 默认配置', 'Elasticsearch 搜索引擎默认连接配置', 'elasticsearch', 9200, '{"timeout": 10, "max_retries": 3}', 'http://{host}:{port}', 'org.elasticsearch.client.RestHighLevelClient', 'GET /_cluster/health', TRUE),
('MinIO 默认配置', 'MinIO 对象存储默认连接配置', 'minio', 9000, '{"secure": false, "region": "us-east-1"}', 'http://{host}:{port}', 'io.minio.MinioClient', 'listBuckets', TRUE);