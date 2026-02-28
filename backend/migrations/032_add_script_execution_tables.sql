-- 创建脚本执行记录主表
CREATE TABLE IF NOT EXISTS acwl_script_execution_records (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '记录ID',
    title VARCHAR(255) NOT NULL COMMENT '执行标题/脚本名称',
    script_content TEXT NOT NULL COMMENT '脚本内容',
    executor_id INT NOT NULL COMMENT '执行人ID',
    status ENUM('pending', 'running', 'completed', 'partial_failed', 'failed') NOT NULL DEFAULT 'pending' COMMENT '总体执行状态',
    total_servers INT DEFAULT 0 COMMENT '目标服务器总数',
    success_count INT DEFAULT 0 COMMENT '成功数量',
    fail_count INT DEFAULT 0 COMMENT '失败数量',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    FOREIGN KEY (executor_id) REFERENCES acwl_users(id)
) COMMENT '脚本批量执行记录主表';

-- 创建脚本执行详情表
CREATE TABLE IF NOT EXISTS acwl_script_execution_details (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '详情ID',
    record_id INT NOT NULL COMMENT '主记录ID',
    server_id INT NOT NULL COMMENT '服务器ID',
    server_name VARCHAR(255) NOT NULL COMMENT '服务器名称',
    server_ip VARCHAR(50) NOT NULL COMMENT '服务器IP',
    status ENUM('pending', 'running', 'success', 'failed', 'timeout') NOT NULL DEFAULT 'pending' COMMENT '执行状态',
    exit_code INT COMMENT '退出码',
    stdout TEXT COMMENT '标准输出',
    stderr TEXT COMMENT '标准错误',
    error_message TEXT COMMENT '错误信息',
    start_time DATETIME COMMENT '开始时间',
    end_time DATETIME COMMENT '结束时间',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    FOREIGN KEY (record_id) REFERENCES acwl_script_execution_records(id) ON DELETE CASCADE,
    FOREIGN KEY (server_id) REFERENCES acwl_servers(id) ON DELETE CASCADE
) COMMENT '脚本执行详情表';
