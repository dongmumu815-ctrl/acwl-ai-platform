#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查数据库中 task_type 列的枚举定义
"""

import pymysql
import sys

# 数据库配置
DB_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': 'root123',
    'database': 'acwl_ai_data',
    'charset': 'utf8mb4'
}

def check_enum_definition():
    """
    检查 acwl_task_definitions 表中 task_type 列的枚举定义
    """
    try:
        # 连接数据库
        connection = pymysql.connect(**DB_CONFIG)
        cursor = connection.cursor()
        
        print("检查 acwl_task_definitions 表的 task_type 列定义...")
        
        # 查询表结构
        cursor.execute("DESCRIBE acwl_task_definitions")
        columns = cursor.fetchall()
        
        for column in columns:
            if column[0] == 'task_type':
                print(f"task_type 列定义: {column[1]}")
                break
        
        # 查询实际的枚举值
        cursor.execute("""
            SELECT COLUMN_TYPE 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = 'acwl_ai_data' 
            AND TABLE_NAME = 'acwl_task_definitions' 
            AND COLUMN_NAME = 'task_type'
        """)
        
        result = cursor.fetchone()
        if result:
            print(f"详细枚举定义: {result[0]}")
        
        # 查询表中实际存在的 task_type 值
        cursor.execute("""
            SELECT DISTINCT task_type, COUNT(*) as count
            FROM acwl_task_definitions 
            GROUP BY task_type
            ORDER BY task_type
        """)
        
        values = cursor.fetchall()
        print("\n表中实际的 task_type 值:")
        for value, count in values:
            print(f"  {value}: {count} 条记录")
        
        cursor.close()
        connection.close()
        
        print("\n检查完成!")
        
    except Exception as e:
        print(f"错误: {e}")
        sys.exit(1)

if __name__ == "__main__":
    check_enum_definition()