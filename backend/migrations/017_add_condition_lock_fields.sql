-- 为ES查询模板表添加条件锁定相关字段
ALTER TABLE es_query_templates 
ADD COLUMN condition_lock_types JSON COMMENT '条件锁定类型配置，key为conditionId，value为锁定类型(full/range/operator)';

ALTER TABLE es_query_templates 
ADD COLUMN condition_ranges JSON COMMENT '条件值范围限制配置，key为conditionId，value为范围对象{min, max}';

ALTER TABLE es_query_templates 
ADD COLUMN allowed_operators JSON COMMENT '允许的操作符配置，key为conditionId，value为操作符列表';