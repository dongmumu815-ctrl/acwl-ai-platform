
import asyncio
import os
import sys
import paramiko
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from app.core.database import AsyncSessionLocal
from app.models.server import Server
from sqlalchemy import select

async def diagnose_cluster():
    target_ips = ['10.20.1.215', '10.20.1.216', '10.20.1.217']
    
    async with AsyncSessionLocal() as db:
        print("=== Starting Cluster Diagnosis ===")
        for ip in target_ips:
            print(f"\n>>> Checking Node: {ip}")
            stmt = select(Server).where(Server.ip_address == ip)
            server = (await db.execute(stmt)).scalar_one_or_none()
            
            if not server:
                print(f"Server {ip} not found in DB")
                continue

            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            try:
                client.connect(server.ip_address, username=server.ssh_username, password=server.ssh_password)
                
                # 1. Docker Process Status
                print("[Docker PS]")
                stdin, stdout, stderr = client.exec_command("docker ps -a | grep doris-fe")
                print(stdout.read().decode().strip())
                
                # 2. Environment Variables
                print("[Env Vars]")
                # Use sudo if needed? Usually docker inspect works if user in docker group
                cmd = "docker inspect doris-fe | grep -E 'FE_SERVERS|FE_ID|FE_MASTER_IP'"
                stdin, stdout, stderr = client.exec_command(cmd)
                print(stdout.read().decode().strip())
                
                # 3. Port Status
                print("[Port 9010]")
                cmd = "netstat -tulpn | grep 9010"
                if server.ssh_username != 'root':
                     cmd = f"echo '{server.ssh_password}' | sudo -S -p '' {cmd}"
                stdin, stdout, stderr = client.exec_command(cmd)
                print(stdout.read().decode().strip())
                
                # 4. Logs (Last 20 lines)
                print("[Logs Tail]")
                stdin, stdout, stderr = client.exec_command("docker logs --tail 20 doris-fe")
                print(stdout.read().decode().strip())
                print(stderr.read().decode().strip()) # logs often go to stderr
                
            except Exception as e:
                print(f"Error connecting/executing on {ip}: {e}")
            finally:
                client.close()

if __name__ == "__main__":
    asyncio.run(diagnose_cluster())
