#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API使用日志表迁移脚本

创建 api_usage_logs 表，包含所有必要字段
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text
from app.core.database import engine

def migrate_api_usage_logs_table():
    """
    创建 api_usage_logs 表
    """
    
    # 创建 api_usage_logs 表的 SQL
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS `api_usage_logs` (
        `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT COMMENT '日志ID',
        `customer_id` int(11) NOT NULL COMMENT '客户ID',
        `api_id` bigint(20) unsigned NOT NULL COMMENT 'API ID',
        
        -- 请求信息
        `request_id` varchar(64) NOT NULL COMMENT '请求唯一标识',
        `http_method` varchar(10) NOT NULL COMMENT 'HTTP方法',
        `request_url` varchar(500) NOT NULL COMMENT '请求URL',
        `request_headers` json DEFAULT NULL COMMENT '请求头信息（JSON格式）',
        `request_params` json DEFAULT NULL COMMENT '请求参数（JSON格式）',
        
        -- 客户端信息
        `client_ip` varchar(45) DEFAULT NULL COMMENT '客户端IP地址',
        `user_agent` varchar(500) DEFAULT NULL COMMENT '用户代理字符串',
        
        -- 响应信息
        `response_status` int(11) NOT NULL COMMENT 'HTTP响应状态码',
        `response_headers` json DEFAULT NULL COMMENT '响应头信息（JSON格式）',
        
        -- 性能信息
        `processing_time` decimal(10,6) DEFAULT NULL COMMENT '处理时间（秒）',
        
        -- 错误信息
        `error_message` text DEFAULT NULL COMMENT '错误信息',
        `error_traceback` longtext DEFAULT NULL COMMENT '错误堆栈信息',
        
        -- 业务信息
        `data_size` int(11) DEFAULT NULL COMMENT '数据大小（字节）',
        `record_count` int(11) DEFAULT NULL COMMENT '处理记录数',
        `file_path` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '存储路径',

        -- 时间戳
        `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
        `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
        
        PRIMARY KEY (`id`),
        UNIQUE KEY `uk_request_id` (`request_id`),
        INDEX `idx_customer_id` (`customer_id`),
        INDEX `idx_api_id` (`api_id`),
        INDEX `idx_log_customer_created` (`customer_id`, `created_at`),
        INDEX `idx_log_api_created` (`api_id`, `created_at`),
        INDEX `idx_log_status_created` (`response_status`, `created_at`),
        INDEX `idx_log_ip_created` (`client_ip`, `created_at`),
        INDEX `idx_log_processing_time` (`processing_time`),
        
        FOREIGN KEY (`customer_id`) REFERENCES `customers`(`id`) ON DELETE CASCADE,
        FOREIGN KEY (`api_id`) REFERENCES `custom_apis`(`id`) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='API使用日志表';
    """
    
    try:
        with engine.connect() as connection:
            # 创建表
            print("正在创建 api_usage_logs 表...")
            connection.execute(text(create_table_sql))
            connection.commit()
            print("api_usage_logs 表创建成功！")
            
            # 验证表结构
            result = connection.execute(text("DESCRIBE api_usage_logs"))
            columns = result.fetchall()
            print(f"\napi_usage_logs 表包含 {len(columns)} 个字段:")
            for column in columns:
                print(f"  - {column[0]}: {column[1]}")
                
    except Exception as e:
        print(f"创建 api_usage_logs 表时出错: {e}")
        raise

if __name__ == "__main__":
    print("开始 api_usage_logs 表迁移...")
    migrate_api_usage_logs_table()
    print("迁移成功完成！")