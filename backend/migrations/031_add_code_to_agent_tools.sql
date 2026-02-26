-- 添加code字段到acwl_agent_tools表
ALTER TABLE acwl_agent_tools ADD COLUMN code TEXT NULL COMMENT '工具实现代码' AFTER default_config;
