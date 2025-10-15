#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查API系统数据库中的字段数据
"""

import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy import text

async def check_api_system_field_data():
    """检查api_system数据库中的字段数据"""
    
    # 连接到api_system数据库
    database_url = "mysql+aiomysql://root:2wsx1QAZaczt@10.20.1.200:3306/acwl_api_system"
    
    engine = create_async_engine(
        database_url,
        echo=True,  # 启用SQL日志
    )
    
    async with AsyncSession(engine) as session:
        # 1. 查看所有表
        print("=== 查看api_system数据库中的所有表 ===")
        result = await session.execute(text("SHOW TABLES"))
        tables = result.fetchall()
        for table in tables:
            print(f"表名: {table[0]}")
        
        print("\n=== 查找包含'field'的表 ===")
        field_tables = []
        for table in tables:
            table_name = table[0]
            if 'field' in table_name.lower():
                field_tables.append(table_name)
                print(f"找到相关表: {table_name}")
        
        # 2. 检查api_fields表
        if 'api_fields' in [t[0] for t in tables]:
            print(f"\n=== 检查api_fields表结构 ===")
            desc_result = await session.execute(text("DESCRIBE api_fields"))
            columns = desc_result.fetchall()
            for col in columns:
                print(f"  {col[0]} - {col[1]}")
            
            # 查看ID为315的记录
            print(f"\n=== 查看ID为315的字段记录 ===")
            try:
                count_result = await session.execute(text("SELECT COUNT(*) FROM api_fields WHERE id = 315"))
                count = count_result.scalar()
                print(f"ID为315的记录数: {count}")
                
                if count > 0:
                    data_result = await session.execute(text("SELECT * FROM api_fields WHERE id = 315"))
                    record = data_result.fetchone()
                    print(f"记录详情:")
                    print(f"  ID: {record[0]}")
                    print(f"  API_ID: {record[1]}")
                    print(f"  字段名: {record[2]}")
                    print(f"  字段标签: {record[3]}")
                    print(f"  字段类型: {record[4]}")
                    print(f"  是否必填: {record[5]}")
                    print(f"  默认值: {record[6]}")
                    print(f"  排序: {record[14]}")
                    print(f"  描述: {record[15]}")
                    print(f"  创建时间: {record[16]}")
                    print(f"  更新时间: {record[17]}")
                else:
                    print("未找到ID为315的记录")
                    
                    # 查看该API的所有字段
                    print(f"\n=== 查看API 15的所有字段 ===")
                    api_fields_result = await session.execute(text("SELECT id, field_name, field_type, sort_order, updated_at FROM api_fields WHERE api_id = 15 ORDER BY sort_order"))
                    api_fields = api_fields_result.fetchall()
                    for field in api_fields:
                        print(f"  ID: {field[0]}, 名称: {field[1]}, 类型: {field[2]}, 排序: {field[3]}, 更新时间: {field[4]}")
                        
            except Exception as e:
                print(f"查询记录时出错: {e}")
        else:
            print("未找到api_fields表")
    
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(check_api_system_field_data())