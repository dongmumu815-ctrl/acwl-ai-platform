#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
查看sql_query_templates表的结构
"""

import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from app.core.config import settings

async def check_table_structure():
    """
    查看sql_query_templates表的结构
    """
    # 创建异步数据库引擎
    database_url = f"mysql+aiomysql://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}?charset={settings.DB_CHARSET}"
    
    engine = create_async_engine(database_url, echo=False)
    
    try:
        async with engine.begin() as conn:
            print("=== sql_query_templates表结构 ===")
            
            # 查看表结构
            result = await conn.execute(text("DESCRIBE sql_query_templates"))
            rows = result.fetchall()
            
            print("字段名\t\t类型\t\t\t是否为空\t键\t默认值\t额外")
            print("-" * 80)
            for row in rows:
                print(f"{row[0]:<15}\t{row[1]:<20}\t{row[2]:<8}\t{row[3]:<8}\t{row[4] or 'NULL':<10}\t{row[5] or ''}")
            
            print("\n=== 查看所有记录的基本信息 ===")
            result = await conn.execute(text("SELECT id, name, description FROM sql_query_templates ORDER BY id"))
            rows = result.fetchall()
            
            for row in rows:
                print(f"ID: {row[0]}, Name: {row[1]}, Description: {row[2]}")
                
    except Exception as e:
        print(f"数据库连接或查询失败: {e}")
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(check_table_structure())