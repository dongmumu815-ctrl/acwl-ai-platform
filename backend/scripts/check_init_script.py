
import asyncio
import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
import paramiko
from app.core.database import AsyncSessionLocal
from app.models.server import Server
from sqlalchemy import select

async def check_init_script():
    async with AsyncSessionLocal() as db:
        stmt = select(Server).where(Server.ip_address == '10.20.1.215')
        result = await db.execute(stmt)
        server = result.scalar_one_or_none()
        
        if not server:
            print("Server not found")
            return

        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            client.connect(server.ip_address, username=server.ssh_username, password=server.ssh_password)
            
            # Find where init_fe.sh is
            # It's likely in PATH or CWD.
            # docker exec doris-fe ls -l /opt/apache-doris/fe/bin/init_fe.sh
            # Or just cat it from known location or find it
            
            cmd = "docker exec doris-fe cat /opt/apache-doris/fe/bin/init_fe.sh"
            stdin, stdout, stderr = client.exec_command(cmd)
            out = stdout.read().decode()
            if not out:
                 # Try to find it
                 cmd = "docker exec doris-fe find / -name init_fe.sh"
                 stdin, stdout, stderr = client.exec_command(cmd)
                 path = stdout.read().decode().strip()
                 if path:
                     print(f"Found at {path}")
                     cmd = f"docker exec doris-fe cat {path}"
                     stdin, stdout, stderr = client.exec_command(cmd)
                     out = stdout.read().decode()
            
            print(out[6000:]) # Rest
            
        except Exception as e:
            print(f"Error: {e}")
        finally:
            client.close()

if __name__ == "__main__":
    asyncio.run(check_init_script())
