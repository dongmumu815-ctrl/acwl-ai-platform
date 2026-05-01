-- 服务器和GPU资源管理表结构迁移脚本
-- 创建时间: 2024-01-01
-- 描述: 添加服务器管理、GPU资源管理和部署关联表

-- 1. 创建服务器表
CREATE TABLE IF NOT EXISTS servers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL UNIQUE,
    ip_address VARCHAR(45) NOT NULL,
    ssh_port INTEGER DEFAULT 22,
    ssh_username VARCHAR(50),
    ssh_key_path VARCHAR(255),
    status VARCHAR(20) DEFAULT 'offline' CHECK (status IN ('online', 'offline', 'maintenance', 'error')),
    cpu_cores INTEGER,
    memory_size VARCHAR(20),
    disk_size VARCHAR(20),
    os_type VARCHAR(50),
    os_version VARCHAR(50),
    docker_version VARCHAR(50),
    nvidia_driver_version VARCHAR(50),
    cuda_version VARCHAR(50),
    description TEXT,
    tags TEXT, -- JSON格式存储标签
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_heartbeat TIMESTAMP
);

-- 2. 创建GPU资源表
CREATE TABLE IF NOT EXISTS gpu_resources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    server_id INTEGER NOT NULL,
    device_id INTEGER NOT NULL, -- GPU设备ID (0, 1, 2...)
    gpu_name VARCHAR(100) NOT NULL,
    memory_size VARCHAR(20) NOT NULL,
    compute_capability VARCHAR(10),
    driver_version VARCHAR(50),
    is_available BOOLEAN DEFAULT TRUE,
    temperature FLOAT,
    memory_used FLOAT DEFAULT 0,
    memory_total FLOAT,
    utilization FLOAT DEFAULT 0,
    power_usage FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (server_id) REFERENCES servers(id) ON DELETE CASCADE,
    UNIQUE(server_id, device_id)
);

-- 3. 创建服务器监控指标表
CREATE TABLE IF NOT EXISTS server_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    server_id INTEGER NOT NULL,
    cpu_usage FLOAT,
    memory_usage FLOAT,
    disk_usage FLOAT,
    network_in FLOAT,
    network_out FLOAT,
    load_average FLOAT,
    uptime INTEGER,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (server_id) REFERENCES servers(id) ON DELETE CASCADE
);

-- 4. 更新部署表，添加服务器关联
ALTER TABLE deployments ADD COLUMN server_id INTEGER;
ALTER TABLE deployments ADD FOREIGN KEY (server_id) REFERENCES servers(id);

-- 5. 创建部署GPU关联表
CREATE TABLE IF NOT EXISTS deployment_gpus (
    deployment_id INTEGER NOT NULL,
    gpu_id INTEGER NOT NULL,
    memory_limit INTEGER, -- GPU显存限制(GB)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (deployment_id, gpu_id),
    FOREIGN KEY (deployment_id) REFERENCES deployments(id) ON DELETE CASCADE,
    FOREIGN KEY (gpu_id) REFERENCES gpu_resources(id) ON DELETE CASCADE
);

-- 6. 创建索引以提高查询性能
CREATE INDEX IF NOT EXISTS idx_servers_status ON servers(status);
CREATE INDEX IF NOT EXISTS idx_servers_ip ON servers(ip_address);
CREATE INDEX IF NOT EXISTS idx_gpu_resources_server ON gpu_resources(server_id);
CREATE INDEX IF NOT EXISTS idx_gpu_resources_available ON gpu_resources(is_available);
CREATE INDEX IF NOT EXISTS idx_server_metrics_server_time ON server_metrics(server_id, recorded_at);
CREATE INDEX IF NOT EXISTS idx_deployments_server ON deployments(server_id);
CREATE INDEX IF NOT EXISTS idx_deployment_gpus_deployment ON deployment_gpus(deployment_id);
CREATE INDEX IF NOT EXISTS idx_deployment_gpus_gpu ON deployment_gpus(gpu_id);

-- 7. 示例数据已移除，部署者可根据实际需求自行添加服务器配置

-- 8. 创建触发器，自动更新 updated_at 字段
CREATE TRIGGER IF NOT EXISTS update_servers_timestamp 
    AFTER UPDATE ON servers
    FOR EACH ROW
    BEGIN
        UPDATE servers SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
    END;

CREATE TRIGGER IF NOT EXISTS update_gpu_resources_timestamp 
    AFTER UPDATE ON gpu_resources
    FOR EACH ROW
    BEGIN
        UPDATE gpu_resources SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
    END;

-- 9. 创建视图，方便查询服务器和GPU信息
CREATE VIEW IF NOT EXISTS server_gpu_summary AS
SELECT 
    s.id as server_id,
    s.name as server_name,
    s.ip_address,
    s.status as server_status,
    COUNT(g.id) as total_gpus,
    COUNT(CASE WHEN g.is_available = TRUE THEN 1 END) as available_gpus,
    COUNT(CASE WHEN g.is_available = FALSE THEN 1 END) as occupied_gpus,
    GROUP_CONCAT(g.gpu_name) as gpu_models,
    s.created_at,
    s.last_heartbeat
FROM servers s
LEFT JOIN gpu_resources g ON s.id = g.server_id
GROUP BY s.id, s.name, s.ip_address, s.status, s.created_at, s.last_heartbeat;

-- 10. 创建部署资源使用视图
CREATE VIEW IF NOT EXISTS deployment_resource_usage AS
SELECT 
    d.id as deployment_id,
    d.deployment_name,
    d.status as deployment_status,
    s.name as server_name,
    s.ip_address as server_ip,
    COUNT(dg.gpu_id) as gpu_count,
    GROUP_CONCAT(g.gpu_name) as gpu_models,
    SUM(dg.memory_limit) as total_memory_limit,
    d.created_at as deployment_created_at
FROM deployments d
JOIN servers s ON d.server_id = s.id
LEFT JOIN deployment_gpus dg ON d.id = dg.deployment_id
LEFT JOIN gpu_resources g ON dg.gpu_id = g.id
GROUP BY d.id, d.deployment_name, d.status, s.name, s.ip_address, d.created_at;

COMMIT;