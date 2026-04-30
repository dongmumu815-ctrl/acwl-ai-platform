-- 创建微调任务表
-- 用于存储模型微调任务的配置和状态

CREATE TABLE IF NOT EXISTS acwl_fine_tuning_jobs (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '微调任务ID，自增主键',
    job_name VARCHAR(200) NOT NULL COMMENT '微调任务名称',
    job_id VARCHAR(100) NOT NULL UNIQUE COMMENT '任务唯一标识符，用于SSH远程调用',
    base_model_id INT NOT NULL COMMENT '基础模型ID',
    fine_tuned_model_name VARCHAR(200) COMMENT '微调后的模型名称',
    method ENUM('lora', 'qlora', 'full', 'adaptor') NOT NULL DEFAULT 'lora' COMMENT '微调方法',
    status ENUM('pending', 'queued', 'preparing', 'running', 'completed', 'failed', 'cancelled') NOT NULL DEFAULT 'pending' COMMENT '任务状态',
    dataset_name VARCHAR(100) NOT NULL COMMENT '训练数据集名称',
    dataset_path TEXT COMMENT '训练数据集路径',
    training_params TEXT COMMENT '训练参数JSON字符串',
    server_id INT COMMENT '执行的GPU服务器ID',
    server_ip VARCHAR(50) COMMENT '服务器IP地址',
    ssh_port INT DEFAULT 22 COMMENT 'SSH端口',
    ssh_username VARCHAR(100) COMMENT 'SSH用户名',
    ssh_password VARCHAR(500) COMMENT 'SSH密码（加密存储）',
    conda_env VARCHAR(100) DEFAULT 'msswift' COMMENT 'Conda环境名称',
    log_file TEXT COMMENT '训练日志文件路径',
    error_message TEXT COMMENT '错误信息',
    progress INT DEFAULT 0 COMMENT '训练进度百分比(0-100)',
    current_epoch INT COMMENT '当前训练轮次',
    total_epochs INT DEFAULT 3 COMMENT '总训练轮次',
    started_at DATETIME COMMENT '训练开始时间',
    completed_at DATETIME COMMENT '训练完成时间',
    output_path TEXT COMMENT '微调模型输出路径',
    model_size BIGINT COMMENT '微调后模型大小(字节)',
    remarks TEXT COMMENT '备注',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    created_by INT COMMENT '创建人',
    updated_by INT COMMENT '更新人',
    FOREIGN KEY (base_model_id) REFERENCES acwl_models(id) ON DELETE CASCADE,
    FOREIGN KEY (server_id) REFERENCES acwl_servers(id) ON DELETE SET NULL,
    FOREIGN KEY (created_by) REFERENCES acwl_users(id),
    FOREIGN KEY (updated_by) REFERENCES acwl_users(id),
    INDEX idx_job_id (job_id),
    INDEX idx_status (status),
    INDEX idx_method (method),
    INDEX idx_base_model (base_model_id),
    INDEX idx_created_by (created_by),
    INDEX idx_created_at (created_at)
) COMMENT '微调任务表，存储模型微调任务的配置和状态';

-- 更新触发器，自动更新 updated_at 字段
DELIMITER //
CREATE TRIGGER update_fine_tuning_jobs_updated_at
    BEFORE UPDATE ON acwl_fine_tuning_jobs
    FOR EACH ROW
BEGIN
    SET NEW.updated_at = CURRENT_TIMESTAMP;
END//
DELIMITER ;