-- 为权限表添加查询与排序相关索引，以优化 /permissions/tree 及列表查询
-- 注意：如索引已存在，请根据实际数据库版本手动调整为 DROP/CREATE 逻辑

CREATE INDEX ix_acwl_permissions_status_module_sort_created
  ON acwl_permissions (status, module, sort_order, created_at);

CREATE INDEX ix_acwl_permissions_module
  ON acwl_permissions (module);