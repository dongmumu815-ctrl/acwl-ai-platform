import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import get_db
from sqlalchemy import text

async def show_create_table():
    async for db in get_db():
        result = await db.execute(text("SHOW CREATE TABLE acwl_workflow_connections"))
        row = result.fetchone()
        print(f"Create Table: {row[1]}")

if __name__ == "__main__":
    asyncio.run(show_create_table())
