-- 修复资源类型表(acwl_data_resource_types)的时间戳默认值
-- 目的：确保在插入记录时自动填充 create_time，并在更新时更新 update_time

ALTER TABLE `acwl_data_resource_types`
  MODIFY COLUMN `create_time` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  MODIFY COLUMN `update_time` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间';

-- 如需强制非空，可使用以下语句（请确认历史数据后再执行）
-- ALTER TABLE `acwl_data_resource_types`
--   MODIFY COLUMN `create_time` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
--   MODIFY COLUMN `update_time` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间';