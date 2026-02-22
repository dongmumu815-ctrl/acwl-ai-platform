
import asyncio
import os
import sys
import paramiko
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from app.core.database import AsyncSessionLocal
from app.models.server import Server
from sqlalchemy import select

async def check_backends():
    # Target IPs
    target_ips = ['10.20.1.215', '10.20.1.216', '10.20.1.217']
    
    async with AsyncSessionLocal() as db:
        # 1. Query Master for registered backends
        print("=== Checking Registered Backends on Master (10.20.1.215) ===")
        stmt_master = select(Server).where(Server.ip_address == '10.20.1.215')
        master = (await db.execute(stmt_master)).scalar_one_or_none()
        
        if master:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            try:
                client.connect(master.ip_address, username=master.ssh_username, password=master.ssh_password)
                
                # Query SHOW PROC '/backends'
                # Note: Default BE heartbeat port is 9050
                sql = "SHOW PROC '/backends'"
                cmd = f"docker exec doris-fe mysql -uroot -P9030 -h127.0.0.1 -e \"{sql}\""
                stdin, stdout, stderr = client.exec_command(cmd)
                print(stdout.read().decode())
                
                client.close()
            except Exception as e:
                print(f"Error querying master: {e}")

        # 2. Check docker process on all nodes
        print("\n=== Checking BE Containers on All Nodes ===")
        for ip in target_ips:
            print(f"\n>>> Checking Node: {ip}")
            stmt = select(Server).where(Server.ip_address == ip)
            server = (await db.execute(stmt)).scalar_one_or_none()
            
            if not server:
                print("Server not found")
                continue

            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            try:
                client.connect(server.ip_address, username=server.ssh_username, password=server.ssh_password)
                
                # Check PS
                cmd = "docker ps -a | grep doris-be"
                stdin, stdout, stderr = client.exec_command(cmd)
                print(stdout.read().decode().strip())
                
                # Check logs tail if running
                # cmd = "docker logs --tail 5 doris-be"
                # stdin, stdout, stderr = client.exec_command(cmd)
                # print(stdout.read().decode().strip())
                
            except Exception as e:
                print(f"Error checking {ip}: {e}")
            finally:
                client.close()

if __name__ == "__main__":
    asyncio.run(check_backends())
