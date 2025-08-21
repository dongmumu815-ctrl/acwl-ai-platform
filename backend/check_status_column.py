#!/usr/bin/env python3

import pymysql

# 数据库连接配置
config = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': 'Flameaway3.1415',
    'database': 'acwl_ai_data',
    'charset': 'utf8mb4'
}

try:
    # 连接数据库
    connection = pymysql.connect(**config)
    cursor = connection.cursor()
    
    # 查看status字段的详细定义
    cursor.execute("SHOW COLUMNS FROM acwl_scheduler_nodes WHERE Field = 'status'")
    result = cursor.fetchone()
    
    if result:
        print(f"Status字段定义: {result}")
    else:
        print("未找到status字段")
    
    cursor.close()
    connection.close()
    
except Exception as e:
    print(f"错误: {e}")