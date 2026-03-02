
import asyncio
import sys
import os
from sqlalchemy import select

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import AsyncSessionLocal
from app.models.server import Server

async def get_server_info():
    async with AsyncSessionLocal() as session:
        stmt = select(Server).where(Server.ip_address == "10.20.1.204")
        result = await session.execute(stmt)
        server = result.scalar_one_or_none()
        
        if server:
            print(f"Server Found: {server.name}")
            print(f"IP: {server.ip_address}")
            print(f"Username: {server.ssh_username}")
            # Be careful with printing password, but for this debug session we need it or use it directly
            print(f"Password: {server.ssh_password}") 
            print(f"Key Path: {server.ssh_key_path}")
        else:
            print("Server 10.20.1.204 not found in DB")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(get_server_info())
