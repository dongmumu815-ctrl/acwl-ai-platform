-- 创建模型服务配置表
-- 用于管理各种AI服务提供商的接口配置，如通义千问、豆包、Ollama、vLLM等

CREATE TABLE IF NOT EXISTS acwl_model_service_configs (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL COMMENT '服务配置名称',
    display_name VARCHAR(100) NOT NULL COMMENT '显示名称',
    provider VARCHAR(50) NOT NULL COMMENT '服务提供商：qwen, doubao, openai, claude, ollama, vllm等',
    model_name VARCHAR(100) NOT NULL COMMENT '模型名称',
    api_endpoint VARCHAR(500) COMMENT 'API端点URL',
    api_key VARCHAR(500) COMMENT 'API密钥',
    api_version VARCHAR(20) COMMENT 'API版本',
    max_tokens INTEGER DEFAULT 4096 COMMENT '最大token数',
    temperature DECIMAL(3,2) DEFAULT 0.7 COMMENT '温度参数',
    top_p DECIMAL(3,2) DEFAULT 0.9 COMMENT 'top_p参数',
    frequency_penalty DECIMAL(3,2) DEFAULT 0.0 COMMENT '频率惩罚',
    presence_penalty DECIMAL(3,2) DEFAULT 0.0 COMMENT '存在惩罚',
    timeout INTEGER DEFAULT 30 COMMENT '请求超时时间(秒)',
    retry_count INTEGER DEFAULT 3 COMMENT '重试次数',
    extra_config TEXT COMMENT '额外配置(JSON格式)',
    is_active BOOLEAN DEFAULT TRUE COMMENT '是否启用',
    is_default BOOLEAN DEFAULT FALSE COMMENT '是否为默认配置',
    description TEXT COMMENT '配置描述',
    created_by INTEGER COMMENT '创建者ID',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '更新时间',
    
    UNIQUE(name),
    FOREIGN KEY (created_by) REFERENCES acwl_users(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 创建索引
CREATE INDEX idx_model_service_configs_provider ON acwl_model_service_configs(provider);
CREATE INDEX idx_model_service_configs_active ON acwl_model_service_configs(is_active);
CREATE INDEX idx_model_service_configs_default ON acwl_model_service_configs(is_default);

-- 插入一些默认的模型服务配置
INSERT INTO acwl_model_service_configs (
    name, display_name, provider, model_name, api_endpoint, 
    max_tokens, temperature, description, is_active, is_default
) VALUES 
-- OpenAI GPT模型
('gpt-4', 'GPT-4', 'openai', 'gpt-4', 'https://api.openai.com/v1/chat/completions', 
 8192, 0.7, 'OpenAI GPT-4 模型，强大的通用语言模型', TRUE, TRUE),
 
('gpt-3.5-turbo', 'GPT-3.5 Turbo', 'openai', 'gpt-3.5-turbo', 'https://api.openai.com/v1/chat/completions', 
 4096, 0.7, 'OpenAI GPT-3.5 Turbo 模型，快速且经济的选择', TRUE, FALSE),

-- Claude模型
('claude-3-sonnet', 'Claude-3 Sonnet', 'claude', 'claude-3-sonnet-20240229', 'https://api.anthropic.com/v1/messages', 
 4096, 0.7, 'Anthropic Claude-3 Sonnet 模型，平衡性能和速度', TRUE, FALSE),
 
('claude-3-haiku', 'Claude-3 Haiku', 'claude', 'claude-3-haiku-20240307', 'https://api.anthropic.com/v1/messages', 
 4096, 0.7, 'Anthropic Claude-3 Haiku 模型，快速响应', TRUE, FALSE),

-- 通义千问
('qwen-turbo', '通义千问 Turbo', 'qwen', 'qwen-turbo', 'https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation', 
 8192, 0.7, '阿里云通义千问 Turbo 模型', TRUE, FALSE),
 
('qwen-plus', '通义千问 Plus', 'qwen', 'qwen-plus', 'https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation', 
 8192, 0.7, '阿里云通义千问 Plus 模型', TRUE, FALSE),

-- 豆包
('doubao-pro', '豆包 Pro', 'doubao', 'doubao-pro-4k', 'https://ark.cn-beijing.volces.com/api/v3/chat/completions', 
 4096, 0.7, '字节跳动豆包 Pro 模型', TRUE, FALSE),

-- 本地部署示例
('ollama-llama2', 'Ollama Llama2', 'ollama', 'llama2', 'http://localhost:11434/api/chat', 
 4096, 0.7, '本地部署的 Ollama Llama2 模型', FALSE, FALSE),
 
('vllm-local', 'vLLM Local', 'vllm', 'local-model', 'http://localhost:8000/v1/chat/completions', 
 4096, 0.7, '本地部署的 vLLM 模型服务', FALSE, FALSE);

-- 更新触发器，自动更新 updated_at 字段
DELIMITER //
CREATE TRIGGER update_model_service_configs_updated_at
    BEFORE UPDATE ON acwl_model_service_configs
    FOR EACH ROW
BEGIN
    SET NEW.updated_at = CURRENT_TIMESTAMP;
END//
DELIMITER ;

-- 确保只有一个默认配置的触发器
CREATE TRIGGER ensure_single_default_model_service_config
    AFTER UPDATE OF is_default ON acwl_model_service_configs
    FOR EACH ROW
    WHEN NEW.is_default = TRUE
BEGIN
    UPDATE acwl_model_service_configs 
    SET is_default = FALSE 
    WHERE id != NEW.id AND is_default = TRUE;
END;

CREATE TRIGGER ensure_single_default_model_service_config_insert
    AFTER INSERT ON acwl_model_service_configs
    FOR EACH ROW
    WHEN NEW.is_default = TRUE
BEGIN
    UPDATE acwl_model_service_configs 
    SET is_default = FALSE 
    WHERE id != NEW.id AND is_default = TRUE;
END;