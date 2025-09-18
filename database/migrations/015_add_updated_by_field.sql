-- 为数据资源表添加updated_by字段
-- 创建时间: 2024-01-01
-- 描述: 为acwl_data_resources表添加updated_by字段及外键约束

-- 为acwl_data_resources表添加updated_by字段
ALTER TABLE acwl_data_resources ADD COLUMN updated_by INT;
ALTER TABLE acwl_data_resources ADD CONSTRAINT fk_data_resources_updated_by FOREIGN KEY (updated_by) REFERENCES acwl_users(id);

-- 为acwl_datasources表添加updated_by字段
ALTER TABLE acwl_datasources ADD COLUMN updated_by INT;
ALTER TABLE acwl_datasources ADD CONSTRAINT fk_datasources_updated_by FOREIGN KEY (updated_by) REFERENCES acwl_users(id);

-- 为acwl_datasets表添加updated_by字段
ALTER TABLE acwl_datasets ADD COLUMN updated_by INT;
ALTER TABLE acwl_datasets ADD CONSTRAINT fk_datasets_updated_by FOREIGN KEY (updated_by) REFERENCES acwl_users(id);

-- 为acwl_projects表添加updated_by字段
ALTER TABLE acwl_projects ADD COLUMN updated_by INT;
ALTER TABLE acwl_projects ADD CONSTRAINT fk_projects_updated_by FOREIGN KEY (updated_by) REFERENCES acwl_users(id);

-- 为acwl_project_members表添加updated_by字段
ALTER TABLE acwl_project_members ADD COLUMN updated_by INT;
ALTER TABLE acwl_project_members ADD CONSTRAINT fk_project_members_updated_by FOREIGN KEY (updated_by) REFERENCES acwl_users(id);

-- 为acwl_project_datasources表添加updated_by字段
ALTER TABLE acwl_project_datasources ADD COLUMN updated_by INT;
ALTER TABLE acwl_project_datasources ADD CONSTRAINT fk_project_datasources_updated_by FOREIGN KEY (updated_by) REFERENCES acwl_users(id);

-- 为acwl_project_quotas表添加updated_by字段
ALTER TABLE acwl_project_quotas ADD COLUMN updated_by INT;
ALTER TABLE acwl_project_quotas ADD CONSTRAINT fk_project_quotas_updated_by FOREIGN KEY (updated_by) REFERENCES acwl_users(id);

-- 为acwl_project_activities表添加updated_by字段
ALTER TABLE acwl_project_activities ADD COLUMN updated_by INT;
ALTER TABLE acwl_project_activities ADD CONSTRAINT fk_project_activities_updated_by FOREIGN KEY (updated_by) REFERENCES acwl_users(id);

-- 为acwl_project_templates表添加updated_by字段
ALTER TABLE acwl_project_templates ADD COLUMN updated_by INT;
ALTER TABLE acwl_project_templates ADD CONSTRAINT fk_project_templates_updated_by FOREIGN KEY (updated_by) REFERENCES acwl_users(id);