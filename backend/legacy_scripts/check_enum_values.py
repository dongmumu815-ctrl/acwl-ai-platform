#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查数据库中risk_level枚举的实际值
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import get_db_context
from sqlalchemy import text

async def check_enum_values():
    """检查数据库中的枚举值"""
    try:
        async with get_db_context() as db:
            # 检查表结构中的枚举定义
            result = await db.execute(text("SHOW COLUMNS FROM instruction_nodes LIKE 'risk_level'"))
            column_info = result.fetchone()
            
            if column_info:
                print(f"Column definition: {column_info}")
                print(f"Type: {column_info[1]}")
            else:
                print("risk_level column not found")
                
            # 检查现有数据中的值
            result = await db.execute(text("SELECT DISTINCT risk_level FROM instruction_nodes WHERE risk_level IS NOT NULL LIMIT 10"))
            existing_values = result.fetchall()
            
            print(f"\nExisting values in database:")
            for value in existing_values:
                print(f"  - {value[0]} (type: {type(value[0])})")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(check_enum_values())