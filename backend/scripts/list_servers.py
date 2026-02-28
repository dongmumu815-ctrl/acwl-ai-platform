
import asyncio
import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from app.core.database import AsyncSessionLocal
from app.models.server import Server
from sqlalchemy import select

async def list_all_servers():
    async with AsyncSessionLocal() as db:
        stmt = select(Server)
        result = await db.execute(stmt)
        servers = result.scalars().all()
        
        print(f"Total Servers Found: {len(servers)}")
        for s in servers:
            print(f"ID: {s.id}, IP: {s.ip_address}, Name: {s.name}")

if __name__ == "__main__":
    asyncio.run(list_all_servers())
