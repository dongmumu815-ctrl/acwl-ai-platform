#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
直接查询数据库，确认实际数据
"""

import asyncio
import aiomysql

async def check_database_data():
    """检查数据库中的实际数据"""
    
    print("🔍 直接查询 acwl_api_system 数据库")
    print("=" * 50)
    
    # 数据库连接配置
    config = {
        'host': 'localhost',
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
        
        # 查询所有客户数据
        print("📋 查询 customers 表中的所有数据...")
        await cursor.execute("SELECT * FROM customers ORDER BY created_at DESC")
        customers = await cursor.fetchall()
        
        print(f"📊 总记录数: {len(customers)}")
        print("\n客户详情:")
        print("-" * 80)
        
        if customers:
            # 获取列名
            await cursor.execute("DESCRIBE customers")
            columns = await cursor.fetchall()
            column_names = [col[0] for col in columns]
            
            for i, customer in enumerate(customers):
                print(f"\n[{i+1}] 客户记录:")
                for j, value in enumerate(customer):
                    if j < len(column_names):
                        print(f"   {column_names[j]}: {value}")
        else:
            print("❌ 没有找到任何客户记录")
        
        # 检查其他可能的表
        print(f"\n🔍 检查数据库中的所有表...")
        await cursor.execute("SHOW TABLES")
        tables = await cursor.fetchall()
        
        print(f"📋 数据库中的表:")
        for table in tables:
            table_name = table[0]
            await cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = (await cursor.fetchone())[0]
            print(f"   {table_name}: {count} 条记录")
        
        # 关闭连接
        await cursor.close()
        connection.close()
        
        return True
        
    except Exception as e:
        print(f"❌ 查询数据库时发生错误: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(check_database_data())