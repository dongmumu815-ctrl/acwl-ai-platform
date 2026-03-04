import paramiko
import asyncio
import os
import sys

# Add project root to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)
sys.path.insert(0, backend_dir)

from app.core.database import AsyncSessionLocal
from app.models.server import Server
from sqlalchemy import select

HOST = "10.20.1.221"

async def get_server_credentials():
    async with AsyncSessionLocal() as session:
        stmt = select(Server).where(Server.ip_address == HOST)
        result = await session.execute(stmt)
        server = result.scalar_one_or_none()
        if not server:
            raise Exception(f"Server {HOST} not found in DB")
        return server.ssh_username, server.ssh_password

async def run_remote_command(command):
    client = None
    try:
        user, password = await get_server_credentials()
        print(f"Connecting to {HOST} as {user}...")
        
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(HOST, port=22, username=user, password=password, timeout=15)
        print(f"Executing: {command}")
        
        # Use sudo with password
        if "sudo" in command:
            command = f"echo '{password}' | sudo -S -p '' {command}"
            
        stdin, stdout, stderr = client.exec_command(command)
        
        output = stdout.read().decode('utf-8')
        error = stderr.read().decode('utf-8')
        
        if output:
            print("\n[STDOUT]:")
            print(output)
        if error:
            print("\n[STDERR]:")
            print(error)
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if client:
            client.close()

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        
    print("WARNING: This will remove all unused Docker images, containers, and volumes on 10.20.1.221.")
    # Prune everything
    cmd = "sudo docker system prune -a -f --volumes"
    asyncio.run(run_remote_command(cmd))
