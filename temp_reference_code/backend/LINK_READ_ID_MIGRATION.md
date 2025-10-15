# link_read_id 字段迁移指南

## 背景

本迁移将 `customers` 表中的 `link_read_id` 字段迁移至 `custom_apis` 表中。这样做的目的是将外部系统关联ID与具体的API直接关联，而不仅仅是与客户关联，从而提供更精细的集成能力。

## 迁移内容

1. 在 `custom_apis` 表中添加 `link_read_id` 字段
2. 将 `customers` 表中的 `link_read_id` 值迁移到对应客户的所有 `custom_apis` 记录中
3. 为新字段添加索引以提高查询性能

## 迁移方法

### 方法一：使用 Python 脚本迁移（推荐）

1. 确保已安装所有依赖项
2. 执行迁移脚本：

```bash
python migrate_link_read_id.py
```

3. 验证迁移结果：

```bash
python test_link_read_id_migration.py
```

### 方法二：直接执行 SQL 脚本

1. 登录到 MySQL 数据库
2. 执行 SQL 迁移脚本：

```bash
mysql -u username -p < migrate_link_read_id.sql
```

或者在 MySQL 客户端中直接执行脚本内容。

> **注意**：SQL脚本已经更新为兼容性更好的版本，使用动态SQL检查字段和索引是否存在，避免了使用IF NOT EXISTS语法可能导致的兼容性问题。

## 注意事项

1. **备份数据**：执行迁移前，请确保已备份数据库
2. **测试环境**：建议先在测试环境中执行迁移，验证无误后再在生产环境执行
3. **应用代码**：迁移后，需要更新应用代码中使用 `link_read_id` 的相关逻辑
4. **向后兼容**：为保持向后兼容，`customers` 表中的 `link_read_id` 字段暂时保留

## 迁移后的数据结构

### custom_apis 表

```sql
CREATE TABLE `custom_apis` (
    `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT COMMENT '接口ID',
    `customer_id` bigint(20) unsigned NOT NULL COMMENT '客户ID',
    `api_name` varchar(100) NOT NULL COMMENT '接口名称',
    `api_code` varchar(50) NOT NULL COMMENT '接口代码（用于生成URL）',
    `api_description` text DEFAULT NULL COMMENT '接口描述',
    `api_url` varchar(200) NOT NULL COMMENT '生成的接口URL',
    `http_method` varchar(10) NOT NULL DEFAULT 'POST' COMMENT 'HTTP方法：GET,POST,PUT,DELETE',
    `status` tinyint(1) NOT NULL DEFAULT 1 COMMENT '状态：1-开放，0-停用',
    `rate_limit` int(11) DEFAULT NULL COMMENT '频率限制（每分钟请求数）',
    `link_read_id` varchar(50) DEFAULT NULL COMMENT '链接其他系统的ID',
    `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_customer_api_code` (`customer_id`, `api_code`),
    INDEX `idx_status` (`status`),
    INDEX `idx_api_code` (`api_code`),
    INDEX `idx_link_read_id` (`link_read_id`),
    FOREIGN KEY (`customer_id`) REFERENCES `customers`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='自定义接口定义表';
```

## 后续工作

1. 更新应用代码中使用 `link_read_id` 的相关逻辑
2. 在适当的时机，考虑从 `customers` 表中移除 `link_read_id` 字段（需要单独的迁移计划）
3. 更新相关文档和API说明