#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库迁移脚本：为 customers 表添加缺失字段

执行前请确保已备份数据库

Author: System
Date: 2024
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text
from app.core.database import engine
from app.core.config import settings

def migrate_customers_table():
    """
    为 customers 表添加缺失的字段
    """
    print("开始数据库迁移...")
    
    # 迁移 SQL 语句
    migration_sql = """
    -- 添加缺失的字段到 customers 表
    ALTER TABLE `customers` 
    ADD COLUMN `rate_limit` int(11) DEFAULT NULL COMMENT '频率限制（每分钟请求数），NULL表示使用系统默认值' AFTER `status`,
    ADD COLUMN `max_apis` int(11) DEFAULT NULL COMMENT '最大API数量，NULL表示使用系统默认值' AFTER `rate_limit`,
    ADD COLUMN `last_login_at` timestamp NULL DEFAULT NULL COMMENT '最后登录时间' AFTER `max_apis`,
    ADD COLUMN `last_api_call_at` timestamp NULL DEFAULT NULL COMMENT '最后API调用时间' AFTER `last_login_at`,
    ADD COLUMN `total_api_calls` int(11) NOT NULL DEFAULT 0 COMMENT '总API调用次数' AFTER `last_api_call_at`,
    ADD COLUMN `secret_reset_at` timestamp NULL DEFAULT NULL COMMENT '密钥重置时间' AFTER `total_api_calls`;
    """
    
    index_sql = """
    -- 添加索引以提高查询性能
    ALTER TABLE `customers` 
    ADD INDEX `idx_customer_status_created` (`status`, `created_at`),
    ADD INDEX `idx_customer_company` (`company`);
    """
    
    try:
        with engine.connect() as connection:
            # 首先检查字段是否已存在
            check_sql = """
            SELECT COLUMN_NAME 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = DATABASE() 
            AND TABLE_NAME = 'customers' 
            AND COLUMN_NAME IN ('rate_limit', 'max_apis', 'last_login_at', 'last_api_call_at', 'total_api_calls', 'secret_reset_at')
            """
            
            result = connection.execute(text(check_sql))
            existing_columns = [row[0] for row in result.fetchall()]
            
            if existing_columns:
                print(f"以下字段已存在，跳过迁移: {', '.join(existing_columns)}")
                return
            
            print("执行字段添加...")
            # 执行迁移
            connection.execute(text(migration_sql))
            connection.commit()
            
            print("添加索引...")
            # 添加索引（忽略已存在的索引错误）
            try:
                connection.execute(text(index_sql))
                connection.commit()
            except Exception as e:
                if "Duplicate key name" in str(e):
                    print("索引已存在，跳过索引创建")
                else:
                    print(f"添加索引时出现错误: {e}")
            
            # 验证表结构
            print("验证表结构...")
            verify_sql = """
            SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_DEFAULT, COLUMN_COMMENT
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = DATABASE() 
            AND TABLE_NAME = 'customers'
            ORDER BY ORDINAL_POSITION
            """
            
            result = connection.execute(text(verify_sql))
            columns = result.fetchall()
            
            print("\n当前 customers 表结构:")
            print("-" * 80)
            for col in columns:
                print(f"{col[0]:<20} {col[1]:<15} {col[2]:<10} {str(col[3]):<15} {col[4] or ''}")
            
            print("\n数据库迁移完成！")
            
    except Exception as e:
        print(f"迁移失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    migrate_customers_table()