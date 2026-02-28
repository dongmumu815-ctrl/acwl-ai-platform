import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.core.database import engine

async def add_column():
    try:
        async with engine.begin() as conn:
            print("Adding updated_by column to acwl_task_definitions...")
            await conn.execute(text("ALTER TABLE acwl_task_definitions ADD COLUMN updated_by INT NULL COMMENT '更新者ID'"))
            print("Column added successfully.")
    except Exception as e:
        print(f"Error adding column: {e}")

if __name__ == "__main__":
    asyncio.run(add_column())
