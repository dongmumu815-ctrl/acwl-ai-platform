#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
from app.core.database import engine
from sqlalchemy import text

async def check_table_structure():
    """检查执行器节点表结构"""
    async with engine.begin() as conn:
        result = await conn.execute(text('DESCRIBE acwl_executor_nodes'))
        print("acwl_executor_nodes 表结构:")
        for row in result:
            print(f"{row[0]}: {row[1]} {row[2]} {row[3]} {row[4]} {row[5]}")

if __name__ == "__main__":
    asyncio.run(check_table_structure())