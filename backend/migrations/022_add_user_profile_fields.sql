-- 为用户表 acwl_users 添加部门、手机号、状态、备注字段

ALTER TABLE `acwl_users`
  ADD COLUMN `department` VARCHAR(100) NULL COMMENT '部门' AFTER `role`,
  ADD COLUMN `phone` VARCHAR(20) NULL COMMENT '手机号' AFTER `department`,
  ADD COLUMN `status` VARCHAR(20) NOT NULL DEFAULT 'active' COMMENT '用户状态：active/disabled/pending' AFTER `phone`,
  ADD COLUMN `remark` TEXT NULL COMMENT '备注' AFTER `status`;

-- 为状态添加索引以提升查询性能
CREATE INDEX `idx_users_status` ON `acwl_users`(`status`);