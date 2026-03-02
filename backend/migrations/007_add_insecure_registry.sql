
-- 2026-03-01 Add insecure_registry to acwl_harbor_configs
ALTER TABLE acwl_harbor_configs ADD COLUMN insecure_registry BOOLEAN DEFAULT FALSE COMMENT '是否跳过HTTPS验证(Insecure Registry)';
