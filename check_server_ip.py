import asyncio
import sys
import os

# Adjust path to include the project root
sys.path.append(os.getcwd())

# Import from backend.app is causing issues because of how imports work
# Let's try to import directly from app if possible or adjust sys.path better
sys.path.append(os.path.join(os.getcwd(), 'backend'))

# We need to be careful about imports to avoid double definition of SQLAlchemy models
# The error suggests models are being imported twice under different paths
# Let's try to import using 'app' instead of 'backend.app' if backend is in sys.path

from app.core.database import AsyncSessionLocal
from app.models.server import Server
from sqlalchemy import select

async def main():
    try:
        async with AsyncSessionLocal() as db:
            print("Checking for server 10.20.1.204...")
            stmt = select(Server).where(Server.ip_address == '10.20.1.204')
            result = await db.execute(stmt)
            server = result.scalar_one_or_none()
            
            if server:
                print(f"Found Server: ID={server.id}")
                print(f"Name={server.name}")
                print(f"IP={server.ip_address}")
                print(f"SSH Port={server.ssh_port}")
                print(f"User={server.ssh_username}")
            else:
                print("Server not found for IP 10.20.1.204")
                
                print("\nAvailable Servers:")
                stmt_all = select(Server)
                res_all = await db.execute(stmt_all)
                servers = res_all.scalars().all()
                for s in servers:
                    print(f"ID={s.id}, IP={s.ip_address}, Name={s.name}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
