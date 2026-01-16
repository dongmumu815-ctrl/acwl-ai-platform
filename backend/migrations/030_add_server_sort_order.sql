-- 添加 sort_order 字段到 acwl_servers 表
ALTER TABLE acwl_servers ADD COLUMN sort_order INT DEFAULT 0 COMMENT '排序权重，值越小越靠前';
