
import asyncio
import os
import sys
import paramiko
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from app.core.database import AsyncSessionLocal
from app.models.server import Server
from sqlalchemy import select

async def register_remaining_backends():
    # Only need to connect to Master
    master_ip = '10.20.1.215'
    
    # Remaining BEs
    missing_bes = [
        ('10.20.1.218', 9050),
        ('10.20.1.219', 9050)
    ]
    
    async with AsyncSessionLocal() as db:
        stmt = select(Server).where(Server.ip_address == master_ip)
        master = (await db.execute(stmt)).scalar_one_or_none()
        
        if not master:
            print("Master not found")
            return

        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            client.connect(master.ip_address, username=master.ssh_username, password=master.ssh_password)
            
            for ip, port in missing_bes:
                print(f"Registering BE {ip}:{port}...")
                sql = f"ALTER SYSTEM ADD BACKEND '{ip}:{port}'"
                cmd = f"docker exec doris-fe mysql -uroot -P9030 -h127.0.0.1 -e \"{sql}\""
                
                print(f"Executing: {cmd}")
                stdin, stdout, stderr = client.exec_command(cmd)
                out = stdout.read().decode()
                err = stderr.read().decode()
                print(f"Output: {out}")
                if err:
                     print(f"Error/Warning: {err}")
            
            # Verify again
            print("\nVerifying Backends...")
            sql = "SHOW PROC '/backends'"
            cmd = f"docker exec doris-fe mysql -uroot -P9030 -h127.0.0.1 -e \"{sql}\""
            stdin, stdout, stderr = client.exec_command(cmd)
            print(stdout.read().decode())

        except Exception as e:
            print(f"Error: {e}")
        finally:
            client.close()

if __name__ == "__main__":
    asyncio.run(register_remaining_backends())
