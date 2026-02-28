import asyncio
import sys
import os
from sqlalchemy import text

# Add project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import get_db

async def main():
    async for db in get_db():
        result = await db.execute(text("SHOW CREATE TABLE acwl_unified_nodes"))
        row = result.fetchone()
        print(row[1])

if __name__ == "__main__":
    asyncio.run(main())
