
import asyncio
import os
import sys
import paramiko
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from app.core.database import AsyncSessionLocal
from app.models.server import Server
from sqlalchemy import select

async def check_follower_logs():
    async with AsyncSessionLocal() as db:
        stmt = select(Server).where(Server.ip_address == '10.20.1.216')
        server = (await db.execute(stmt)).scalar_one_or_none()
        
        if not server:
            print("Server not found")
            return

        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            client.connect(server.ip_address, username=server.ssh_username, password=server.ssh_password)
            
            # Check docker ps
            cmd = "docker ps -a | grep doris-fe"
            stdin, stdout, stderr = client.exec_command(cmd)
            print(f"--- DOCKER PS ---\n{stdout.read().decode()}")

            # Check docker logs
            cmd = "docker logs --tail 100 doris-fe"
            stdin, stdout, stderr = client.exec_command(cmd)
            out = stdout.read().decode()
            err = stderr.read().decode()
            print(f"--- STDOUT ---\n{out}")
            print(f"--- STDERR ---\n{err}")
            
        except Exception as e:
            print(f"Error: {e}")
        finally:
            client.close()

if __name__ == "__main__":
    asyncio.run(check_follower_logs())
