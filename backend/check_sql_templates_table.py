#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查MySQL数据库中sql_query_templates表的结构和数据
"""

import asyncio
import json
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

async def check_sql_templates_table():
    """
    检查sql_query_templates表的结构和数据
    """
    
    # 创建异步数据库引擎
    database_url = f"mysql+aiomysql://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}?charset={settings.DB_CHARSET}"
    
    engine = create_async_engine(database_url, echo=True)
    
    try:
        async with engine.begin() as conn:
            print("=== 检查sql_query_templates表结构 ===")
            
            # 查看表结构
            result = await conn.execute(text("DESCRIBE sql_query_templates"))
            columns = result.fetchall()
            
            print("表字段信息：")
            for column in columns:
                print(f"  {column[0]} - {column[1]} - {column[2]} - {column[3]} - {column[4]} - {column[5]}")
            
            print("\n=== 查看表中的数据 ===")
            
            # 查看表中的数据
            result = await conn.execute(text("SELECT id, name, query, config FROM sql_query_templates LIMIT 5"))
            rows = result.fetchall()
            
            print(f"找到 {len(rows)} 条记录：")
            for row in rows:
                print(f"\nID: {row[0]}")
                print(f"Name: {row[1]}")
                print(f"Query: {row[2][:200]}...")  # 只显示前200个字符
                print(f"Config: {row[3]}")
                
                # 如果config是JSON字符串，尝试解析
                if row[3]:
                    try:
                        config_data = json.loads(row[3]) if isinstance(row[3], str) else row[3]
                        print(f"Config解析后: {json.dumps(config_data, indent=2, ensure_ascii=False)}")
                    except Exception as e:
                        print(f"Config解析失败: {e}")
                
                print("-" * 50)
            
            print("\n=== 检查是否有locked_conditions ===")
            
            # 查找包含locked_conditions的记录
            result = await conn.execute(text("""
                SELECT id, name, config 
                FROM sql_query_templates 
                WHERE config IS NOT NULL 
                AND JSON_EXTRACT(config, '$.locked_conditions') IS NOT NULL
                LIMIT 3
            """))
            
            locked_rows = result.fetchall()
            print(f"找到 {len(locked_rows)} 条包含locked_conditions的记录：")
            
            for row in locked_rows:
                print(f"\nID: {row[0]}, Name: {row[1]}")
                if row[2]:
                    try:
                        config_data = json.loads(row[2]) if isinstance(row[2], str) else row[2]
                        locked_conditions = config_data.get('locked_conditions', [])
                        print(f"Locked Conditions: {json.dumps(locked_conditions, indent=2, ensure_ascii=False)}")
                    except Exception as e:
                        print(f"解析失败: {e}")
                        
    except Exception as e:
        print(f"数据库连接或查询失败: {e}")
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(check_sql_templates_table())