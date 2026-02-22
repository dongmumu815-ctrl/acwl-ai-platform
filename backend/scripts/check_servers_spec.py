import sys
import os
import asyncio
import paramiko
from sqlalchemy import select

# Add backend directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
# current_dir is backend/scripts, we need backend
backend_dir = os.path.dirname(current_dir)
sys.path.insert(0, backend_dir)

from app.core.database import AsyncSessionLocal
from app.models.server import Server

async def get_server_specs(ip, port, username, password):
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(ip, port=port, username=username, password=password, timeout=5)
        
        # Get Memory
        stdin, stdout, stderr = client.exec_command("free -h | grep Mem | awk '{print $2}'")
        mem_total = stdout.read().decode().strip()
        
        # Get CPU Cores
        stdin, stdout, stderr = client.exec_command("nproc")
        cpu_cores = stdout.read().decode().strip()
        
        # Get Disk Space (Root and Data)
        stdin, stdout, stderr = client.exec_command("df -h / | awk 'NR==2 {print $2}'")
        root_disk = stdout.read().decode().strip()
        
        # Comprehensive Disk Check using lsblk to find large disks
        # filter out loop devices and ram disks, show name, size, mountpoint
        cmd = "lsblk -o NAME,SIZE,MOUNTPOINT,TYPE | grep -E 'disk|part' | grep -v 'loop'"
        stdin, stdout, stderr = client.exec_command(cmd)
        disk_info = stdout.read().decode().strip()
        
        client.close()
        return {
            "ip": ip,
            "cpu": cpu_cores,
            "memory": mem_total,
            "root_disk": root_disk,
            "disk_info": disk_info
        }
    except Exception as e:
        return {"ip": ip, "error": str(e)}

async def main():
    target_ips = ["10.20.1.215", "10.20.1.216", "10.20.1.217", "10.20.1.218", "10.20.1.219"]
    
    async with AsyncSessionLocal() as db:
        stmt = select(Server).where(Server.ip_address.in_(target_ips))
        result = await db.execute(stmt)
        servers = result.scalars().all()
        
        if not servers:
            print("No servers found with these IPs.")
            return

        print(f"{'IP Address':<15} | {'CPU':<5} | {'Memory':<10} | {'Root Disk':<10}")
        print("-" * 70)
        
        tasks = []
        for server in servers:
            tasks.append(get_server_specs(server.ip_address, server.ssh_port, server.ssh_username, server.ssh_password))
            
        results = await asyncio.gather(*tasks)
        
        for res in results:
            if "error" in res:
                print(f"{res['ip']:<15} | Error: {res['error']}")
            else:
                print(f"{res['ip']:<15} | {res['cpu']:<5} | {res['memory']:<10} | {res['root_disk']:<10}")
                print(f"  Disk Detail:\n{res['disk_info']}")
                print("-" * 70)

if __name__ == "__main__":
    asyncio.run(main())
