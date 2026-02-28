import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import get_db
from sqlalchemy import text

async def list_users():
    async for db in get_db():
        result = await db.execute(text("SELECT id, username FROM acwl_users"))
        users = result.fetchall()
        print(f"Users: {users}")

if __name__ == "__main__":
    asyncio.run(list_users())
