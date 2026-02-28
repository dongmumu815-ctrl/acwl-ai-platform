import asyncio
import sys
import os
from sqlalchemy import select

# Add project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import get_db
from app.models.scheduler import SchedulerNode

async def main():
    async for db in get_db():
        stmt = select(SchedulerNode)
        result = await db.execute(stmt)
        nodes = result.scalars().all()
        print(f"Total nodes: {len(nodes)}")
        for node in nodes:
            print(f"Node: {node.node_name} ({node.node_id})")
            print(f"  Status: {node.status}")
            print(f"  Role: {node.role}")
            print(f"  IP: {node.host_ip}:{node.port}")
        break

if __name__ == "__main__":
    asyncio.run(main())
