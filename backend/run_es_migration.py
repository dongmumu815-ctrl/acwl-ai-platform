#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
执行ES查询模板表字段迁移脚本
添加 condition_lock_types, condition_ranges, allowed_operators 字段
"""

import pymysql
import os
from pathlib import Path

def run_es_migration():
    """
    执行ES查询模板表字段迁移
    """
    # 数据库连接配置
    config = {
        'host': '10.20.1.200',
        'port': 3306,
        'user': 'root',
        'password': '2wsx1QAZaczt',
        'database': 'acwl-ai-data',
        'charset': 'utf8mb4'
    }
    
    # 迁移SQL语句
    migration_sqls = [
        """
        ALTER TABLE es_query_templates 
        ADD COLUMN condition_lock_types JSON COMMENT '条件锁定类型配置，key为conditionId，value为锁定类型(full/range/operator)'
        """,
        """
        ALTER TABLE es_query_templates 
        ADD COLUMN condition_ranges JSON COMMENT '条件值范围限制配置，key为conditionId，value为范围对象{min, max}'
        """,
        """
        ALTER TABLE es_query_templates 
        ADD COLUMN allowed_operators JSON COMMENT '允许的操作符配置，key为conditionId，value为操作符列表'
        """
    ]
    
    try:
        # 连接数据库
        connection = pymysql.connect(**config)
        print(f"✅ 成功连接到数据库: {config['database']}")
        
        with connection.cursor() as cursor:
            # 检查字段是否已存在
            cursor.execute("""
                SELECT COLUMN_NAME 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = %s 
                AND TABLE_NAME = 'es_query_templates' 
                AND COLUMN_NAME IN ('condition_lock_types', 'condition_ranges', 'allowed_operators')
            """, (config['database'],))
            
            existing_columns = [row[0] for row in cursor.fetchall()]
            print(f"已存在的字段: {existing_columns}")
            
            # 执行迁移SQL语句
            for i, sql in enumerate(migration_sqls, 1):
                field_name = ['condition_lock_types', 'condition_ranges', 'allowed_operators'][i-1]
                
                if field_name in existing_columns:
                    print(f"⚠️  字段 {field_name} 已存在，跳过")
                    continue
                
                try:
                    print(f"执行迁移 {i}: 添加字段 {field_name}...")
                    cursor.execute(sql)
                    print(f"✅ 成功添加字段: {field_name}")
                except Exception as e:
                    print(f"❌ 添加字段 {field_name} 失败: {str(e)}")
                    # 如果是字段已存在的错误，继续执行
                    if "Duplicate column name" in str(e):
                        print(f"⚠️  字段 {field_name} 已存在")
                        continue
                    else:
                        raise
            
            # 提交事务
            connection.commit()
            print("✅ ES查询模板表字段迁移执行成功！")
            
            # 验证字段是否添加成功
            cursor.execute("""
                SELECT COLUMN_NAME, DATA_TYPE, COLUMN_COMMENT
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = %s 
                AND TABLE_NAME = 'es_query_templates' 
                AND COLUMN_NAME IN ('condition_lock_types', 'condition_ranges', 'allowed_operators')
                ORDER BY COLUMN_NAME
            """, (config['database'],))
            
            result_columns = cursor.fetchall()
            print("\n验证结果:")
            for column in result_columns:
                print(f"  - {column[0]} ({column[1]}): {column[2]}")
            
            return True
            
    except Exception as e:
        print(f"❌ 数据库迁移执行失败: {str(e)}")
        return False
    finally:
        if 'connection' in locals():
            connection.close()
            print("数据库连接已关闭")

if __name__ == "__main__":
    print("=" * 60)
    print("ES查询模板表字段迁移脚本")
    print("=" * 60)
    run_es_migration()