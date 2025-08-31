#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查数据库中的表名
"""

import asyncio
from app.core.database import get_db
from sqlalchemy import text

async def check_tables():
    """检查指令相关的表"""
    async for db in get_db():
        try:
            # 查看所有表
            result = await db.execute(text("SHOW TABLES"))
            tables = result.fetchall()
            print("数据库中的所有表:")
            for table in tables:
                print(f"  {table[0]}")
            
            print("\n指令相关的表:")
            for table in tables:
                if 'instruction' in table[0].lower():
                    print(f"  {table[0]}")
            
            break
        except Exception as e:
            print(f"错误: {e}")
            break

if __name__ == '__main__':
    asyncio.run(check_tables())