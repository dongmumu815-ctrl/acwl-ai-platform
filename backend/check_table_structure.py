#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查instruction_nodes表结构
"""

import asyncio
from app.core.database import get_db
from sqlalchemy import text

async def check_table_structure():
    """检查instruction_nodes表结构"""
    async for db in get_db():
        try:
            result = await db.execute(text("DESCRIBE instruction_nodes"))
            columns = result.fetchall()
            print("instruction_nodes表结构:")
            for col in columns:
                print(f"  {col[0]} - {col[1]} - {col[2]} - {col[3]} - {col[4]} - {col[5]}")
            
            # 检查是否已有risk_level字段
            has_risk_level = any(col[0] == 'risk_level' for col in columns)
            print(f"\n是否已有risk_level字段: {has_risk_level}")
            
            break
        except Exception as e:
            print(f"错误: {e}")
            break

if __name__ == '__main__':
    asyncio.run(check_table_structure())