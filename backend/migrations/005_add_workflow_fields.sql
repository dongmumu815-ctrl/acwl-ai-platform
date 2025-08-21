-- 添加工作流表缺失的字段
-- 执行时间: 2024-01-01

USE `acwl-ai-data`;

-- 添加 acwl_workflows 表缺失的字段
ALTER TABLE `acwl_workflows` 
ADD COLUMN `display_name` VARCHAR(200) NULL COMMENT '工作流显示名称' AFTER `name`,
ADD COLUMN `workflow_category` VARCHAR(50) NULL COMMENT '工作流分类' AFTER `description`,
ADD COLUMN `workflow_version` VARCHAR(20) NOT NULL DEFAULT '1.0.0' COMMENT '工作流版本' AFTER `workflow_category`,
ADD COLUMN `workflow_status` ENUM('draft', 'active', 'inactive', 'archived') NOT NULL DEFAULT 'draft' COMMENT '工作流状态' AFTER `workflow_version`,
ADD COLUMN `workflow_config` JSON NULL COMMENT '工作流全局配置' AFTER `workflow_status`,
ADD COLUMN `input_parameters` JSON NULL COMMENT '工作流输入参数定义' AFTER `workflow_config`,
ADD COLUMN `output_parameters` JSON NULL COMMENT '工作流输出参数定义' AFTER `input_parameters`,
ADD COLUMN `global_variables` JSON NULL COMMENT '工作流全局变量' AFTER `output_parameters`,
ADD COLUMN `timeout_seconds` INT NOT NULL DEFAULT 7200 COMMENT '工作流超时时间（秒）' AFTER `global_variables`,
ADD COLUMN `max_retry_count` INT NOT NULL DEFAULT 1 COMMENT '工作流最大重试次数' AFTER `timeout_seconds`,
ADD COLUMN `project_id` INT NULL COMMENT '所属项目ID' AFTER `max_retry_count`,
ADD COLUMN `is_template` TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否为模板' AFTER `project_id`,
ADD COLUMN `is_system` TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否为系统工作流' AFTER `is_template`;

-- 删除旧的字段（如果存在）
ALTER TABLE `acwl_workflows` 
DROP COLUMN IF EXISTS `workflow_definition`,
DROP COLUMN IF EXISTS `is_active`;

-- 添加外键约束
ALTER TABLE `acwl_workflows` 
ADD CONSTRAINT `fk_workflows_project` FOREIGN KEY (`project_id`) REFERENCES `acwl_projects`(`id`) ON DELETE SET NULL,
ADD CONSTRAINT `fk_workflows_creator` FOREIGN KEY (`created_by`) REFERENCES `acwl_users`(`id`) ON DELETE RESTRICT;

-- 添加索引
CREATE INDEX `idx_workflow_name` ON `acwl_workflows`(`name`);
CREATE INDEX `idx_workflow_status` ON `acwl_workflows`(`workflow_status`);
CREATE INDEX `idx_project_id` ON `acwl_workflows`(`project_id`);
CREATE INDEX `idx_created_by` ON `acwl_workflows`(`created_by`);
CREATE INDEX `idx_is_template` ON `acwl_workflows`(`is_template`);

COMMIT;