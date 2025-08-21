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

-- 7. 插入示例数据

-- 示例服务器数据
INSERT OR IGNORE INTO servers (
    name, ip_address, ssh_port, ssh_username, status, 
    cpu_cores, memory_size, disk_size, os_type, os_version,
    docker_version, nvidia_driver_version, cuda_version, description
) VALUES 
('GPU-Server-01', '192.168.1.100', 22, 'ubuntu', 'online', 
 32, '128GB', '2TB', 'Ubuntu', '22.04 LTS',
 '24.0.7', '535.129.03', '12.2', 'AI训练主服务器'),
('GPU-Server-02', '192.168.1.101', 22, 'ubuntu', 'online',
 24, '64GB', '1TB', 'Ubuntu', '20.04 LTS', 
 '24.0.7', '525.147.05', '11.8', 'AI推理服务器'),
('GPU-Server-03', '192.168.1.102', 22, 'ubuntu', 'maintenance',
 16, '32GB', '500GB', 'Ubuntu', '22.04 LTS',
 '24.0.7', '535.129.03', '12.2', '开发测试服务器');

-- 示例GPU资源数据
INSERT OR IGNORE INTO gpu_resources (
    server_id, device_id, gpu_name, memory_size, compute_capability,
    driver_version, is_available, memory_total
) VALUES 
-- GPU-Server-01 的GPU
(1, 0, 'NVIDIA RTX 4090', '24GB', '8.9', '535.129.03', TRUE, 24576),
(1, 1, 'NVIDIA RTX 4090', '24GB', '8.9', '535.129.03', TRUE, 24576),
(1, 2, 'NVIDIA RTX 4090', '24GB', '8.9', '535.129.03', FALSE, 24576),
(1, 3, 'NVIDIA RTX 4090', '24GB', '8.9', '535.129.03', TRUE, 24576),
-- GPU-Server-02 的GPU
(2, 0, 'NVIDIA RTX 3080', '10GB', '8.6', '525.147.05', TRUE, 10240),
(2, 1, 'NVIDIA RTX 3080', '10GB', '8.6', '525.147.05', TRUE, 10240),
-- GPU-Server-03 的GPU
(3, 0, 'NVIDIA GTX 1080 Ti', '11GB', '6.1', '535.129.03', TRUE, 11264);

-- 示例服务器监控数据
INSERT OR IGNORE INTO server_metrics (
    server_id, cpu_usage, memory_usage, disk_usage, 
    network_in, network_out, load_average, uptime
) VALUES 
(1, 45.2, 68.5, 35.8, 1024.5, 2048.3, 2.1, 86400),
(2, 32.1, 52.3, 28.9, 512.8, 1024.6, 1.5, 172800),
(3, 15.6, 25.4, 45.2, 256.4, 512.1, 0.8, 259200);

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