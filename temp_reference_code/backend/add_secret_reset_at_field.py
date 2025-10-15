#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
添加 secret_reset_at 字段到 customers 表

专门用于添加缺失的 secret_reset_at 字段的迁移脚本

Author: System
Date: 2025-07-15
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text
from app.core.database import engine

def add_secret_reset_at_field():
    """
    为 customers 表添加 secret_reset_at 字段
    """
    print("开始添加 secret_reset_at 字段...")
    
    try:
        with engine.connect() as connection:
            # 检查字段是否已存在
            check_sql = """
            SELECT COLUMN_NAME 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = DATABASE() 
            AND TABLE_NAME = 'customers' 
            AND COLUMN_NAME = 'secret_reset_at'
            """
            
            result = connection.execute(text(check_sql))
            existing_column = result.fetchone()
            
            if existing_column:
                print("secret_reset_at 字段已存在，跳过添加")
                return
            
            print("添加 secret_reset_at 字段...")
            
            # 添加字段的 SQL
            add_field_sql = """
            ALTER TABLE `customers` 
            ADD COLUMN `secret_reset_at` timestamp NULL DEFAULT NULL COMMENT '密钥重置时间' AFTER `total_api_calls`
            """
            
            # 执行添加字段
            connection.execute(text(add_field_sql))
            connection.commit()
            
            print("✓ secret_reset_at 字段添加成功")
            
            # 验证字段是否添加成功
            verify_sql = """
            SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_DEFAULT, COLUMN_COMMENT
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = DATABASE() 
            AND TABLE_NAME = 'customers'
            AND COLUMN_NAME = 'secret_reset_at'
            """
            
            result = connection.execute(text(verify_sql))
            column_info = result.fetchone()
            
            if column_info:
                print(f"\n验证成功 - 字段信息:")
                print(f"字段名: {column_info[0]}")
                print(f"类型: {column_info[1]}")
                print(f"允许NULL: {column_info[2]}")
                print(f"默认值: {column_info[3]}")
                print(f"注释: {column_info[4]}")
            else:
                print("警告: 无法验证字段是否添加成功")
            
            print("\n✓ secret_reset_at 字段迁移完成！")
            
    except Exception as e:
        print(f"添加字段失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    add_secret_reset_at_field()