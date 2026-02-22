
import asyncio
import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
import paramiko
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.server import Server

async def check_master():
    async with AsyncSessionLocal() as db:
        # Get Master Server (assuming ID 25 is Master based on IP 10.20.1.215)
        # Or better, query by IP
        stmt = select(Server).where(Server.ip_address == '10.20.1.215')
        result = await db.execute(stmt)
        server = result.scalar_one_or_none()
        
        if not server:
            print("Master server 10.20.1.215 not found in DB")
            return

        print(f"Connecting to Master {server.ip_address}...")
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            client.connect(server.ip_address, username=server.ssh_username, password=server.ssh_password)
            
            # Check docker ps
            stdin, stdout, stderr = client.exec_command("docker ps | grep doris-fe")
            print(f"Docker PS:\n{stdout.read().decode()}")
            
            # Run SQL
            sql = "SHOW FRONTENDS"
            cmd = f"docker run --rm --network host mysql:5.7 mysql -h 127.0.0.1 -P 9030 -u root -e \"{sql}\""
            # Use sudo if needed (assuming root or sudo user)
            if server.ssh_username != 'root':
                cmd = f"echo '{server.ssh_password}' | sudo -S -p '' {cmd}"
            
            stdin, stdout, stderr = client.exec_command(cmd)
            out = stdout.read().decode()
            err = stderr.read().decode()
            print(f"SQL Result:\n{out}")
            if err:
                print(f"SQL Error:\n{err}")
                
        except Exception as e:
            print(f"Error: {e}")
        finally:
            client.close()

if __name__ == "__main__":
    asyncio.run(check_master())
