-- 修复acwl_agents表结构，添加缺少的字段

-- 添加status字段
ALTER TABLE acwl_agents ADD COLUMN status ENUM('DRAFT', 'ACTIVE', 'INACTIVE', 'ARCHIVED') NOT NULL DEFAULT 'DRAFT' AFTER agent_type;

-- 添加system_prompt字段
ALTER TABLE acwl_agents ADD COLUMN system_prompt TEXT NULL AFTER model_id;

-- 添加user_prompt_template字段
ALTER TABLE acwl_agents ADD COLUMN user_prompt_template TEXT NULL AFTER system_prompt;

-- 添加model_params字段
ALTER TABLE acwl_agents ADD COLUMN model_params JSON NULL AFTER user_prompt_template;

-- 添加tool_config字段
ALTER TABLE acwl_agents ADD COLUMN tool_config JSON NULL AFTER tools;

-- 添加memory_enabled字段
ALTER TABLE acwl_agents ADD COLUMN memory_enabled BOOLEAN NOT NULL DEFAULT FALSE AFTER tool_config;

-- 添加memory_config字段
ALTER TABLE acwl_agents ADD COLUMN memory_config JSON NULL AFTER memory_enabled;

-- 添加is_public字段
ALTER TABLE acwl_agents ADD COLUMN is_public BOOLEAN NOT NULL DEFAULT FALSE AFTER memory_config;

-- 添加allowed_users字段
ALTER TABLE acwl_agents ADD COLUMN allowed_users JSON NULL AFTER is_public;

-- 添加usage_count字段
ALTER TABLE acwl_agents ADD COLUMN usage_count INT NOT NULL DEFAULT 0 AFTER allowed_users;

-- 添加last_used_at字段
ALTER TABLE acwl_agents ADD COLUMN last_used_at TIMESTAMP NULL AFTER usage_count;

-- 添加tags字段
ALTER TABLE acwl_agents ADD COLUMN tags JSON NULL AFTER last_used_at;

-- 添加meta_data字段
ALTER TABLE acwl_agents ADD COLUMN meta_data JSON NULL AFTER tags;

-- 添加updated_by字段
ALTER TABLE acwl_agents ADD COLUMN updated_by INT NULL AFTER created_by;

-- 删除不需要的字段
ALTER TABLE acwl_agents DROP COLUMN IF EXISTS prompt_template_id;
ALTER TABLE acwl_agents DROP COLUMN IF EXISTS config;
ALTER TABLE acwl_agents DROP COLUMN IF EXISTS is_active;

-- 添加外键约束
ALTER TABLE acwl_agents ADD CONSTRAINT fk_agent_updated_by FOREIGN KEY (updated_by) REFERENCES acwl_users(id);

-- 更新created_at和updated_at字段（如果不存在）
ALTER TABLE acwl_agents ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE acwl_agents ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP;