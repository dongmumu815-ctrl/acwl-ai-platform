-- 优化后的资源包表结构
-- 移除冗余字段，基于查询模板的精简设计

CREATE TABLE `resource_packages_optimized` (
   `id` int NOT NULL AUTO_INCREMENT,
   `name` varchar(255) COLLATE utf8mb4_general_ci NOT NULL COMMENT '资源包名称',
   `description` text COLLATE utf8mb4_general_ci COMMENT '资源包描述',
   `type` enum('sql','elasticsearch') COLLATE utf8mb4_general_ci NOT NULL COMMENT '资源包类型',
   
   -- 核心关联字段
   `template_id` int NOT NULL COMMENT '关联的查询模板ID',
   `template_type` enum('sql','elasticsearch') COLLATE utf8mb4_general_ci NOT NULL COMMENT '模板类型',
   `dynamic_params` json DEFAULT NULL COMMENT '动态参数配置，用于覆盖模板中的参数',
   
   -- 保留的业务字段
   `datasource_id` int NOT NULL COMMENT '数据源ID（冗余字段，用于快速筛选）',
   `resource_id` int DEFAULT NULL COMMENT '数据资源ID（业务关联）',
   
   -- 系统字段
   `is_active` tinyint(1) DEFAULT 1 COMMENT '是否启用',
   `created_by` int NOT NULL COMMENT '创建者ID',
   `created_at` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
   `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
   
   PRIMARY KEY (`id`),
   KEY `template_id` (`template_id`),
   KEY `datasource_id` (`datasource_id`),
   KEY `resource_id` (`resource_id`),
   KEY `created_by` (`created_by`),
   KEY `ix_resource_packages_id` (`id`),
   
   -- 外键约束
   CONSTRAINT `resource_packages_optimized_ibfk_1` FOREIGN KEY (`datasource_id`) REFERENCES `acwl_datasources` (`id`) ON DELETE CASCADE,
   CONSTRAINT `resource_packages_optimized_ibfk_2` FOREIGN KEY (`resource_id`) REFERENCES `acwl_data_resources` (`id`) ON DELETE SET NULL,
   CONSTRAINT `resource_packages_optimized_ibfk_3` FOREIGN KEY (`created_by`) REFERENCES `acwl_users` (`id`) ON DELETE CASCADE,
   
   -- 模板关联约束（根据模板类型关联不同的模板表）
   -- 注意：这里需要根据实际的模板表结构来设置外键
   CONSTRAINT `resource_packages_optimized_template_check` CHECK (
       (template_type = 'sql' AND template_id IS NOT NULL) OR
       (template_type = 'elasticsearch' AND template_id IS NOT NULL)
   )
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- 移除的字段说明：
-- ❌ base_config - 现在从查询模板获取
-- ❌ locked_conditions - 现在在查询模板中定义
-- ❌ dynamic_conditions - 现在在查询模板中定义，资源包只存储参数值
-- ❌ order_config - 现在在查询模板中定义
-- ❌ limit_config - 可以通过 dynamic_params 或查询时指定

-- 保留的字段说明：
-- ✅ datasource_id - 用于快速筛选和权限控制
-- ✅ resource_id - 用于业务关联和数据资源管理