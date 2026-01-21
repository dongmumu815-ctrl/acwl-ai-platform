import asyncio
import sys
import os

# 添加 backend 目录到 path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend"))

from app.core.database import get_db
from sqlalchemy import text

async def show_create_table():
    table_name = "acwl_task_instances"
    if len(sys.argv) > 1:
        table_name = sys.argv[1]
        
    print(f"Checking schema for table: {table_name}")
    async for db in get_db():
        try:
            result = await db.execute(text(f"SHOW CREATE TABLE {table_name}"))
            row = result.fetchone()
            if row:
                print(f"Create Table: {row[1]}")
            else:
                print(f"Table {table_name} not found")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(show_create_table())
