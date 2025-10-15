-- 更新标签颜色字段长度以支持RGB格式
-- 从 VARCHAR(7) 更新为 VARCHAR(30)

-- 更新数据资源标签表的颜色字段长度
ALTER TABLE acwl_data_resource_tags MODIFY COLUMN color VARCHAR(30) DEFAULT '#409EFF' COMMENT '标签颜色';

-- 更新资源包标签表的颜色字段长度（如果存在）
ALTER TABLE resource_package_tags MODIFY COLUMN tag_color VARCHAR(30) DEFAULT '#409EFF' COMMENT '标签颜色';