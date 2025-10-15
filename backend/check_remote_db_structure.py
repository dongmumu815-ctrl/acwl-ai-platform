#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
查询远程数据库的表结构
"""

import asyncio
import aiomysql

async def check_remote_db_structure():
    """查询远程数据库的表结构"""
    
    print("🔍 查询远程数据库 10.20.1.200:3306/acwl_api_system 的表结构")
    print("=" * 60)
    
    # 数据库连接配置
    config = {
        'host': '10.20.1.200',
        'port': 3306,
        'user': 'root',
        'password': '2wsx1QAZaczt',
        'db': 'acwl_api_system',
        'charset': 'utf8mb4'
    }
    
    try:
        # 连接到数据库
        connection = await aiomysql.connect(**config)
        cursor = await connection.cursor()
        
        # 查询所有表
        print("📋 查询数据库中的所有表...")
        await cursor.execute("SHOW TABLES")
        tables = await cursor.fetchall()
        
        print(f"📊 数据库中的表:")
        for table in tables:
            table_name = table[0]
            await cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = (await cursor.fetchone())[0]
            print(f"   {table_name}: {count} 条记录")
        
        # 重点查询 customers 表结构
        print(f"\n🔍 查询 customers 表结构...")
        await cursor.execute("DESCRIBE customers")
        columns = await cursor.fetchall()
        
        print(f"📋 customers 表字段:")
        print("-" * 60)
        for column in columns:
            field_name = column[0]
            field_type = column[1]
            null_allowed = column[2]
            key_type = column[3]
            default_value = column[4]
            extra = column[5]
            print(f"   {field_name:20} {field_type:20} NULL:{null_allowed} KEY:{key_type} DEFAULT:{default_value} EXTRA:{extra}")
        
        # 查询 customers 表的实际数据
        print(f"\n📊 查询 customers 表的实际数据...")
        await cursor.execute("SELECT * FROM customers LIMIT 5")
        customers = await cursor.fetchall()
        
        if customers:
            # 获取列名
            column_names = [desc[0] for desc in cursor.description]
            print(f"📋 前5条客户记录:")
            print("-" * 80)
            
            for i, customer in enumerate(customers):
                print(f"\n[{i+1}] 客户记录:")
                for j, value in enumerate(customer):
                    if j < len(column_names):
                        print(f"   {column_names[j]:20}: {value}")
        else:
            print("❌ customers 表中没有数据")
        
        # 关闭连接
        await cursor.close()
        connection.close()
        
        return True
        
    except Exception as e:
        print(f"❌ 查询远程数据库时发生错误: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(check_remote_db_structure())