#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库迁移脚本：为data_batches表添加needread字段

此脚本用于在data_batches表中添加needread字段，用于记录批次是否需要回调通知。

Author: System
Date: 2024
"""

import sys
import os
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.config import get_settings

def migrate_add_needread_field():
    """
    为data_batches表添加needread字段
    """
    settings = get_settings()
    
    # 创建数据库连接
    engine = create_engine(settings.DATABASE_URL)
    
    try:
        with engine.connect() as connection:
            # 开始事务
            trans = connection.begin()
            
            try:
                # 检查字段是否已存在
                check_sql = """
                SELECT COUNT(*) as count
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = DATABASE()
                AND TABLE_NAME = 'data_batches'
                AND COLUMN_NAME = 'needread'
                """
                
                result = connection.execute(text(check_sql))
                field_exists = result.fetchone()[0] > 0
                
                if field_exists:
                    print("needread字段已存在，跳过迁移")
                    trans.rollback()
                    return True
                
                # 添加needread字段
                alter_sql = """
                ALTER TABLE data_batches 
                ADD COLUMN needread BOOLEAN DEFAULT TRUE 
                COMMENT '是否需要回调通知'
                """
                
                print("正在添加needread字段...")
                connection.execute(text(alter_sql))
                
                # 为现有记录设置默认值
                update_sql = """
                UPDATE data_batches 
                SET needread = TRUE 
                WHERE needread IS NULL
                """
                
                print("正在为现有记录设置默认值...")
                connection.execute(text(update_sql))
                
                # 提交事务
                trans.commit()
                print("needread字段添加成功！")
                return True
                
            except Exception as e:
                # 回滚事务
                trans.rollback()
                print(f"迁移过程中发生错误: {e}")
                return False
                
    except SQLAlchemyError as e:
        print(f"数据库连接错误: {e}")
        return False
    except Exception as e:
        print(f"未知错误: {e}")
        return False

def verify_migration():
    """
    验证迁移是否成功
    """
    settings = get_settings()
    engine = create_engine(settings.DATABASE_URL)
    
    try:
        with engine.connect() as connection:
            # 检查字段是否存在
            check_sql = """
            SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_DEFAULT, COLUMN_COMMENT
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = DATABASE()
            AND TABLE_NAME = 'data_batches'
            AND COLUMN_NAME = 'needread'
            """
            
            result = connection.execute(text(check_sql))
            row = result.fetchone()
            
            if row:
                print("\n迁移验证成功！")
                print(f"字段名: {row[0]}")
                print(f"数据类型: {row[1]}")
                print(f"是否可空: {row[2]}")
                print(f"默认值: {row[3]}")
                print(f"注释: {row[4]}")
                return True
            else:
                print("\n迁移验证失败：needread字段不存在")
                return False
                
    except Exception as e:
        print(f"验证过程中发生错误: {e}")
        return False

if __name__ == "__main__":
    print("开始数据库迁移：添加needread字段")
    print("=" * 50)
    
    # 执行迁移
    success = migrate_add_needread_field()
    
    if success:
        # 验证迁移
        verify_migration()
        print("\n迁移完成！")
    else:
        print("\n迁移失败！")
        sys.exit(1)