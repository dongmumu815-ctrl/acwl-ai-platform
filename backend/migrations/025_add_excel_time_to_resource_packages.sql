-- 添加excel_time字段到resource_packages表
-- 说明: 记录资源包Excel最新生成时间，用于前端弹窗展示与生成过滤

ALTER TABLE `resource_packages`
  ADD COLUMN `excel_time` DATETIME NULL COMMENT 'Excel最新生成时间' AFTER `download_url`;

-- 可选索引（如需按时间查询）
-- CREATE INDEX `idx_excel_time` ON `resource_packages`(`excel_time`);