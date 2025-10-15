#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库迁移脚本：为api_usage_logs表添加file_path字段

此脚本用于在现有的api_usage_logs表中添加file_path字段，
以支持MinIO文件存储路径的记录功能。
"""

import os
import sys
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import engine
from sqlalchemy import text

def check_file_path_column_exists():
    """
    检查file_path字段是否已存在
    """
    try:
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT COLUMN_NAME 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = DATABASE() 
                AND TABLE_NAME = 'api_usage_logs' 
                AND COLUMN_NAME = 'file_path'
            """))
            
            return result.fetchone() is not None
    except Exception as e:
        print(f"检查字段失败: {e}")
        return False

def add_file_path_column():
    """
    为api_usage_logs表添加file_path字段
    """
    try:
        with engine.connect() as conn:
            # 开始事务
            trans = conn.begin()
            
            try:
                # 添加file_path字段
                conn.execute(text("""
                    ALTER TABLE api_usage_logs 
                    ADD COLUMN file_path VARCHAR(500) NULL 
                    COMMENT '文件存储路径'
                """))
                
                print("✅ 成功添加file_path字段到api_usage_logs表")
                
                # 提交事务
                trans.commit()
                return True
                
            except Exception as e:
                # 回滚事务
                trans.rollback()
                print(f"❌ 添加字段失败: {e}")
                return False
                
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        return False

def verify_migration():
    """
    验证迁移是否成功
    """
    try:
        with engine.connect() as conn:
            # 检查字段信息
            result = conn.execute(text("""
                SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_COMMENT
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = DATABASE() 
                AND TABLE_NAME = 'api_usage_logs' 
                AND COLUMN_NAME = 'file_path'
            """))
            
            row = result.fetchone()
            if row:
                print(f"\n字段验证信息:")
                print(f"  字段名: {row[0]}")
                print(f"  数据类型: {row[1]}")
                print(f"  允许NULL: {row[2]}")
                print(f"  注释: {row[3]}")
                return True
            else:
                print("❌ 字段验证失败：未找到file_path字段")
                return False
                
    except Exception as e:
        print(f"❌ 验证失败: {e}")
        return False

def show_table_structure():
    """
    显示api_usage_logs表的结构
    """
    try:
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_DEFAULT, COLUMN_COMMENT
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = DATABASE() 
                AND TABLE_NAME = 'api_usage_logs'
                ORDER BY ORDINAL_POSITION
            """))
            
            print("\napi_usage_logs表结构:")
            print("-" * 80)
            print(f"{'字段名':<20} {'类型':<15} {'允许NULL':<10} {'默认值':<15} {'注释':<20}")
            print("-" * 80)
            
            for row in result:
                column_name = row[0]
                data_type = row[1]
                is_nullable = row[2]
                default_value = row[3] or ''
                comment = row[4] or ''
                
                print(f"{column_name:<20} {data_type:<15} {is_nullable:<10} {str(default_value):<15} {comment:<20}")
                
    except Exception as e:
        print(f"❌ 获取表结构失败: {e}")

def main():
    """
    主函数
    """
    print("API使用日志表file_path字段迁移脚本")
    print("=" * 50)
    print(f"开始时间: {datetime.now()}")
    
    # 1. 检查字段是否已存在
    print("\n1. 检查file_path字段是否已存在...")
    if check_file_path_column_exists():
        print("✅ file_path字段已存在，无需迁移")
        verify_migration()
        show_table_structure()
        return
    
    print("📝 file_path字段不存在，需要添加")
    
    # 2. 添加字段
    print("\n2. 添加file_path字段...")
    if not add_file_path_column():
        print("❌ 迁移失败")
        return
    
    # 3. 验证迁移
    print("\n3. 验证迁移结果...")
    if verify_migration():
        print("✅ 迁移验证成功")
    else:
        print("❌ 迁移验证失败")
        return
    
    # 4. 显示表结构
    print("\n4. 显示更新后的表结构...")
    show_table_structure()
    
    print(f"\n✅ 迁移完成！时间: {datetime.now()}")
    print("\n说明:")
    print("- file_path字段已添加到api_usage_logs表")
    print("- 字段类型: VARCHAR(500)")
    print("- 允许NULL值")
    print("- 用于存储MinIO文件路径")
    print("- 路径格式: /bucket_name/batchfile/batch_id/filename.json")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断操作")
    except Exception as e:
        print(f"\n\n❌ 脚本执行失败: {e}")
        import traceback
        traceback.print_exc()