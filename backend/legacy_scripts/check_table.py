#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查数据库表是否存在
"""

import asyncio
from sqlalchemy import text
from app.core.database import get_db


async def check_table_exists(table_name: str):
    """
    检查表是否存在
    
    Args:
        table_name: 表名
    """
    async for db in get_db():
        try:
            result = await db.execute(text(f"SHOW TABLES LIKE '{table_name}'"))
            tables = result.fetchall()
            
            if tables:
                print(f"表 {table_name} 已存在")
                
                # 检查表结构
                result = await db.execute(text(f"DESCRIBE {table_name}"))
                columns = result.fetchall()
                print(f"表结构: {len(columns)} 列")
                for col in columns:
                    print(f"  {col[0]} - {col[1]}")
                
                # 检查索引
                result = await db.execute(text(f"SHOW INDEX FROM {table_name}"))
                indexes = result.fetchall()
                print(f"索引数量: {len(indexes)}")
                
                return True
            else:
                print(f"表 {table_name} 不存在")
                return False
                
        except Exception as e:
            print(f"检查表失败: {e}")
            return False
        finally:
            await db.close()
            break


if __name__ == "__main__":
    exists = asyncio.run(check_table_exists("acwl_model_service_configs"))
    print(f"表存在: {exists}")