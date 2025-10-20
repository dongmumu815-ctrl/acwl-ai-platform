#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
执行SQL迁移脚本
"""

import pymysql
import os
from pathlib import Path

def run_migration():
    """
    执行数据库迁移脚本
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
    
    # 迁移脚本路径
    migration_file = Path(__file__).parent / 'migrations' / '017_add_config_to_sql_templates.sql'
    
    try:
        # 连接数据库
        connection = pymysql.connect(**config)
        print(f"✅ 成功连接到数据库: {config['database']}")
        
        with connection.cursor() as cursor:
            # 读取迁移脚本
            with open(migration_file, 'r', encoding='utf-8') as f:
                sql_content = f.read()
            
            # 分割SQL语句（按分号分割）
            sql_statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip() and not stmt.strip().startswith('--')]
            
            # 执行每个SQL语句
            for i, sql in enumerate(sql_statements, 1):
                if sql:
                    print(f"执行SQL语句 {i}: {sql[:50]}...")
                    cursor.execute(sql)
            
            # 提交事务
            connection.commit()
            print("✅ 数据库迁移执行成功！")
            
    except Exception as e:
        print(f"❌ 数据库迁移执行失败: {str(e)}")
        raise
    finally:
        if 'connection' in locals():
            connection.close()
            print("数据库连接已关闭")

if __name__ == "__main__":
    run_migration()