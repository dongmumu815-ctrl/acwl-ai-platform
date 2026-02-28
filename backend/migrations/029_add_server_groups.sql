-- 创建服务器分组表并添加外键
-- 创建时间: 2026-01-14
-- 描述: 添加服务器分组管理功能

-- 1. 创建服务器分组表
CREATE TABLE IF NOT EXISTS acwl_server_groups (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(50) NOT NULL UNIQUE,
    description VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER,
    updated_by INTEGER,
    FOREIGN KEY (created_by) REFERENCES acwl_users(id) ON DELETE SET NULL,
    FOREIGN KEY (updated_by) REFERENCES acwl_users(id) ON DELETE SET NULL
);

-- 2. 为 servers 表添加 group_id 列
ALTER TABLE acwl_servers ADD COLUMN group_id INTEGER;
ALTER TABLE acwl_servers ADD CONSTRAINT fk_server_group FOREIGN KEY (group_id) REFERENCES acwl_server_groups(id) ON DELETE SET NULL;

-- 3. 创建默认分组
INSERT INTO acwl_server_groups (name, description) VALUES ('默认分组', '系统默认服务器分组');

-- 4. 将现有服务器归入默认分组
UPDATE acwl_servers SET group_id = (SELECT id FROM acwl_server_groups WHERE name = '默认分组') WHERE group_id IS NULL;
