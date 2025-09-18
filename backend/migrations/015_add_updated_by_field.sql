-- 添加 updated_by 字段到所有继承 UserMixin 的表
-- 这个迁移为所有使用 UserMixin 的表添加 updated_by 字段

-- 添加 updated_by 字段到 acwl_data_resources 表
ALTER TABLE acwl_data_resources ADD COLUMN updated_by INTEGER;
ALTER TABLE acwl_data_resources ADD CONSTRAINT fk_acwl_data_resources_updated_by FOREIGN KEY (updated_by) REFERENCES acwl_users(id);

-- 添加 updated_by 字段到 datasources 表
ALTER TABLE datasources ADD COLUMN updated_by INTEGER;
ALTER TABLE datasources ADD CONSTRAINT fk_datasources_updated_by FOREIGN KEY (updated_by) REFERENCES users(id);

-- 添加 updated_by 字段到 datasets 表
ALTER TABLE datasets ADD COLUMN updated_by INTEGER;
ALTER TABLE datasets ADD CONSTRAINT fk_datasets_updated_by FOREIGN KEY (updated_by) REFERENCES users(id);

-- 添加 updated_by 字段到 projects 表
ALTER TABLE projects ADD COLUMN updated_by INTEGER;
ALTER TABLE projects ADD CONSTRAINT fk_projects_updated_by FOREIGN KEY (updated_by) REFERENCES users(id);

-- 添加 updated_by 字段到 agents 表
ALTER TABLE agents ADD COLUMN updated_by INTEGER;
ALTER TABLE agents ADD CONSTRAINT fk_agents_updated_by FOREIGN KEY (updated_by) REFERENCES users(id);

-- 添加 updated_by 字段到 workflows 表
ALTER TABLE workflows ADD COLUMN updated_by INTEGER;
ALTER TABLE workflows ADD CONSTRAINT fk_workflows_updated_by FOREIGN KEY (updated_by) REFERENCES users(id);

-- 添加 updated_by 字段到 tasks 表
ALTER TABLE tasks ADD COLUMN updated_by INTEGER;
ALTER TABLE tasks ADD CONSTRAINT fk_tasks_updated_by FOREIGN KEY (updated_by) REFERENCES users(id);

-- 添加 updated_by 字段到 models 表
ALTER TABLE models ADD COLUMN updated_by INTEGER;
ALTER TABLE models ADD CONSTRAINT fk_models_updated_by FOREIGN KEY (updated_by) REFERENCES users(id);

-- 添加 updated_by 字段到 servers 表
ALTER TABLE servers ADD COLUMN updated_by INTEGER;
ALTER TABLE servers ADD CONSTRAINT fk_servers_updated_by FOREIGN KEY (updated_by) REFERENCES users(id);

-- 添加 updated_by 字段到 executors 表
ALTER TABLE executors ADD COLUMN updated_by INTEGER;
ALTER TABLE executors ADD CONSTRAINT fk_executors_updated_by FOREIGN KEY (updated_by) REFERENCES users(id);

-- 添加 updated_by 字段到 schedulers 表
ALTER TABLE schedulers ADD COLUMN updated_by INTEGER;
ALTER TABLE schedulers ADD CONSTRAINT fk_schedulers_updated_by FOREIGN KEY (updated_by) REFERENCES users(id);

-- 添加 updated_by 字段到 deployments 表
ALTER TABLE deployments ADD COLUMN updated_by INTEGER;
ALTER TABLE deployments ADD CONSTRAINT fk_deployments_updated_by FOREIGN KEY (updated_by) REFERENCES users(id);

-- 添加 updated_by 字段到 unified_nodes 表
ALTER TABLE unified_nodes ADD COLUMN updated_by INTEGER;
ALTER TABLE unified_nodes ADD CONSTRAINT fk_unified_nodes_updated_by FOREIGN KEY (updated_by) REFERENCES users(id);

-- 添加 updated_by 字段到 instruction_sets 表
ALTER TABLE instruction_sets ADD COLUMN updated_by INTEGER;
ALTER TABLE instruction_sets ADD CONSTRAINT fk_instruction_sets_updated_by FOREIGN KEY (updated_by) REFERENCES users(id);

-- 添加 updated_by 字段到 model_service_configs 表
ALTER TABLE model_service_configs ADD COLUMN updated_by INTEGER;
ALTER TABLE model_service_configs ADD CONSTRAINT fk_model_service_configs_updated_by FOREIGN KEY (updated_by) REFERENCES users(id);