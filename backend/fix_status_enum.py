#!/usr/bin/env python3

import pymysql
import sys

# 使用应用配置中的数据库连接信息
config = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': '2wsx1QAZaczt',
    'database': 'acwl-ai-data',
    'charset': 'utf8mb4'
}

try:
    print(f"尝试连接数据库: {config['host']}:{config['port']}")
    connection = pymysql.connect(**config)
    cursor = connection.cursor()
    
    # 查看当前status字段定义
    cursor.execute("SHOW COLUMNS FROM acwl_scheduler_nodes WHERE Field = 'status'")
    result = cursor.fetchone()
    print(f"当前status字段定义: {result}")
    
    # 修改status字段，添加'starting'枚举值
    alter_sql = """
    ALTER TABLE acwl_scheduler_nodes 
    MODIFY COLUMN status ENUM('active', 'standby', 'offline', 'error', 'maintenance', 'starting') 
    NOT NULL DEFAULT 'standby' 
    COMMENT '节点状态'
    """
    
    cursor.execute(alter_sql)
    connection.commit()
    print("✅ 成功修改status字段，添加了'starting'枚举值")
    
    # 验证修改结果
    cursor.execute("SHOW COLUMNS FROM acwl_scheduler_nodes WHERE Field = 'status'")
    result = cursor.fetchone()
    print(f"修改后status字段定义: {result}")
    
    cursor.close()
    connection.close()
    print("✅ 数据库连接已关闭")
    
except Exception as e:
    print(f"❌ 操作失败: {e}")
    sys.exit(1)