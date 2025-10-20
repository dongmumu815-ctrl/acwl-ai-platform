#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
直接修复数据库config字段
"""

import pymysql

def fix_config_field():
    """
    直接添加config字段到sql_query_templates表
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
    
    try:
        # 连接数据库
        connection = pymysql.connect(**config)
        print(f"✅ 成功连接到数据库: {config['database']}")
        
        with connection.cursor() as cursor:
            # 首先检查字段是否已存在
            cursor.execute("""
                SELECT COLUMN_NAME 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = 'acwl-ai-data' 
                AND TABLE_NAME = 'sql_query_templates' 
                AND COLUMN_NAME = 'config'
            """)
            
            result = cursor.fetchone()
            if result:
                print("✅ config字段已存在")
                return
            
            print("🔧 添加config字段...")
            
            # 添加config字段
            cursor.execute("""
                ALTER TABLE sql_query_templates 
                ADD COLUMN config JSON COMMENT 'JSON格式存储查询条件配置信息，包括必填条件、可选条件等'
            """)
            
            # 为现有记录设置默认值
            cursor.execute("""
                UPDATE sql_query_templates 
                SET config = JSON_OBJECT() 
                WHERE config IS NULL
            """)
            
            # 提交事务
            connection.commit()
            print("✅ config字段添加成功！")
            
    except Exception as e:
        print(f"❌ 操作失败: {str(e)}")
        raise
    finally:
        if 'connection' in locals():
            connection.close()
            print("数据库连接已关闭")

if __name__ == "__main__":
    fix_config_field()