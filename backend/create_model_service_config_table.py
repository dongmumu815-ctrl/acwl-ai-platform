#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建 acwl_model_service_configs 表
"""

import asyncio
from sqlalchemy import text
from app.core.database import engine

async def create_table():
    """创建 acwl_model_service_configs 表"""
    
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS `acwl_model_service_configs` (
        `id` int NOT NULL AUTO_INCREMENT COMMENT '主键ID',
        `name` varchar(100) NOT NULL COMMENT '服务配置名称',
        `display_name` varchar(100) NOT NULL COMMENT '显示名称',
        `provider` varchar(50) NOT NULL COMMENT '服务提供商',
        `model_name` varchar(100) NOT NULL COMMENT '模型名称',
        `api_endpoint` varchar(500) DEFAULT NULL COMMENT 'API端点URL',
        `api_key` varchar(500) DEFAULT NULL COMMENT 'API密钥',
        `api_version` varchar(20) DEFAULT NULL COMMENT 'API版本',
        `max_tokens` int DEFAULT 4096 COMMENT '最大token数',
        `temperature` decimal(3,2) DEFAULT 0.70 COMMENT '温度参数',
        `top_p` decimal(3,2) DEFAULT 0.90 COMMENT 'top_p参数',
        `frequency_penalty` decimal(3,2) DEFAULT 0.00 COMMENT '频率惩罚',
        `presence_penalty` decimal(3,2) DEFAULT 0.00 COMMENT '存在惩罚',
        `timeout` int DEFAULT 30 COMMENT '请求超时时间(秒)',
        `retry_count` int DEFAULT 3 COMMENT '重试次数',
        `extra_config` text COMMENT '额外配置(JSON格式)',
        `is_active` tinyint(1) DEFAULT 1 COMMENT '是否启用',
        `is_default` tinyint(1) DEFAULT 0 COMMENT '是否为默认配置',
        `description` text COMMENT '配置描述',
        `created_by` int DEFAULT NULL COMMENT '创建者ID',
        `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
        `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
        PRIMARY KEY (`id`),
        UNIQUE KEY `name` (`name`),
        KEY `provider` (`provider`),
        KEY `is_active` (`is_active`),
        KEY `is_default` (`is_default`),
        KEY `created_by` (`created_by`),
        CONSTRAINT `fk_model_service_configs_created_by` FOREIGN KEY (`created_by`) REFERENCES `acwl_users` (`id`) ON DELETE SET NULL
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='模型服务配置表';
    """
    
    # 插入默认配置
    insert_default_config_sql = """
    INSERT IGNORE INTO `acwl_model_service_configs` 
    (`name`, `display_name`, `provider`, `model_name`, `is_active`, `is_default`, `description`) 
    VALUES 
    ('default-gpt-3.5', 'GPT-3.5 Turbo', 'openai', 'gpt-3.5-turbo', 1, 1, '默认的GPT-3.5模型配置');
    """
    
    async with engine.begin() as conn:
        print("创建 acwl_model_service_configs 表...")
        await conn.execute(text(create_table_sql))
        print("表创建成功！")
        
        print("插入默认配置...")
        await conn.execute(text(insert_default_config_sql))
        print("默认配置插入成功！")
        
        print("\n验证表创建结果:")
        result = await conn.execute(text("DESCRIBE acwl_model_service_configs"))
        columns = result.fetchall()
        for column in columns:
            print(f"  {column[0]} - {column[1]}")

if __name__ == "__main__":
    asyncio.run(create_table())