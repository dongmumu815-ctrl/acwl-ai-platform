#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API使用日志表迁移脚本：添加 batch_id 字段

为 api_usage_logs 表添加 batch_id 字段，以支持批次数据追踪，
从而可以减少对 data_uploads 表的依赖，提高接口响应性能。

Author: System
Date: 2024
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text
from app.core.database import engine

def migrate_add_batch_id_field():
    """
    为 api_usage_logs 表添加 batch_id 字段和相关索引
    """
    print("开始为 api_usage_logs 表添加 batch_id 字段...")
    
    # 检查字段是否已存在
    check_field_sql = """
    SELECT COUNT(*) as field_exists
    FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_SCHEMA = DATABASE() 
        AND TABLE_NAME = 'api_usage_logs'
        AND COLUMN_NAME = 'batch_id'
    """
    
    # 添加 batch_id 字段的 SQL
    add_field_sql = """
    ALTER TABLE `api_usage_logs` 
    ADD COLUMN `batch_id` varchar(64) DEFAULT NULL COMMENT '批次ID（用于批量数据追踪）' 
    AFTER `error_traceback`
    """
    
    # 添加索引的 SQL
    add_indexes_sql = [
        "ALTER TABLE `api_usage_logs` ADD INDEX `idx_log_batch` (`batch_id`)",
        "ALTER TABLE `api_usage_logs` ADD INDEX `idx_log_batch_created` (`batch_id`, `created_at`)"
    ]
    
    try:
        with engine.connect() as connection:
            # 检查字段是否已存在
            result = connection.execute(text(check_field_sql))
            field_exists = result.fetchone()[0]
            
            if field_exists > 0:
                print("batch_id 字段已存在，跳过字段添加")
            else:
                print("添加 batch_id 字段...")
                connection.execute(text(add_field_sql))
                connection.commit()
                print("✅ batch_id 字段添加成功")
            
            # 添加索引
            print("添加相关索引...")
            for i, index_sql in enumerate(add_indexes_sql, 1):
                try:
                    connection.execute(text(index_sql))
                    connection.commit()
                    print(f"✅ 索引 {i} 添加成功")
                except Exception as e:
                    if "Duplicate key name" in str(e):
                        print(f"⚠️ 索引 {i} 已存在，跳过")
                    else:
                        print(f"❌ 添加索引 {i} 失败: {e}")
            
            # 验证字段添加结果
            verify_sql = """
            SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_DEFAULT, COLUMN_COMMENT
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = DATABASE() 
                AND TABLE_NAME = 'api_usage_logs'
                AND COLUMN_NAME = 'batch_id'
            """
            
            result = connection.execute(text(verify_sql))
            field_info = result.fetchone()
            
            if field_info:
                print("\n✅ 字段验证成功:")
                print(f"   字段名: {field_info[0]}")
                print(f"   数据类型: {field_info[1]}")
                print(f"   可为空: {field_info[2]}")
                print(f"   默认值: {field_info[3]}")
                print(f"   注释: {field_info[4]}")
            else:
                print("❌ 字段验证失败，batch_id 字段未找到")
                return False
            
            # 显示索引信息
            show_indexes_sql = """
            SHOW INDEX FROM `api_usage_logs` 
            WHERE Key_name LIKE '%batch%'
            """
            
            result = connection.execute(text(show_indexes_sql))
            indexes = result.fetchall()
            
            if indexes:
                print("\n📊 相关索引信息:")
                for idx in indexes:
                    print(f"   索引名: {idx[2]}, 字段: {idx[4]}")
            
            print("\n🎉 api_usage_logs 表 batch_id 字段迁移完成！")
            print("\n💡 优化说明:")
            print("   - 现在可以在 api_usage_logs 表中记录 batch_id")
            print("   - 减少对 data_uploads 表的写入操作")
            print("   - 提高接口响应性能")
            print("   - 保持数据完整性和可追踪性")
            
            return True
            
    except Exception as e:
        print(f"❌ 迁移失败: {e}")
        return False

def rollback_batch_id_field():
    """
    回滚 batch_id 字段的添加（仅在需要时使用）
    """
    print("开始回滚 batch_id 字段...")
    
    rollback_sql = [
        "ALTER TABLE `api_usage_logs` DROP INDEX IF EXISTS `idx_log_batch`",
        "ALTER TABLE `api_usage_logs` DROP INDEX IF EXISTS `idx_log_batch_created`",
        "ALTER TABLE `api_usage_logs` DROP COLUMN IF EXISTS `batch_id`"
    ]
    
    try:
        with engine.connect() as connection:
            for sql in rollback_sql:
                try:
                    connection.execute(text(sql))
                    connection.commit()
                    print(f"✅ 执行成功: {sql}")
                except Exception as e:
                    print(f"⚠️ 执行失败: {sql} - {e}")
            
            print("🔄 batch_id 字段回滚完成")
            
    except Exception as e:
        print(f"❌ 回滚失败: {e}")

if __name__ == "__main__":
    print("=" * 60)
    print("API使用日志表 batch_id 字段迁移脚本")
    print("=" * 60)
    
    import argparse
    parser = argparse.ArgumentParser(description='API使用日志表 batch_id 字段迁移')
    parser.add_argument('--rollback', action='store_true', help='回滚 batch_id 字段的添加')
    args = parser.parse_args()
    
    if args.rollback:
        rollback_batch_id_field()
    else:
        success = migrate_add_batch_id_field()
        if success:
            print("\n✅ 迁移成功完成！")
        else:
            print("\n❌ 迁移失败！")
            sys.exit(1)