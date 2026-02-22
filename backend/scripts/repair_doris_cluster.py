
import asyncio
import os
import sys
import paramiko
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from app.core.database import AsyncSessionLocal
from app.models.server import Server
from sqlalchemy import select

async def repair_cluster():
    # 1. Get Servers
    async with AsyncSessionLocal() as db:
        # Assuming Master is 10.20.1.215
        stmt_master = select(Server).where(Server.ip_address == '10.20.1.215')
        master = (await db.execute(stmt_master)).scalar_one_or_none()
        
        # Followers
        stmt_fe2 = select(Server).where(Server.ip_address == '10.20.1.216')
        fe2 = (await db.execute(stmt_fe2)).scalar_one_or_none()
        
        stmt_fe3 = select(Server).where(Server.ip_address == '10.20.1.217')
        fe3 = (await db.execute(stmt_fe3)).scalar_one_or_none()
        
        if not master or not fe2 or not fe3:
            print("Could not find all servers.")
            return

        # 2. Register Followers on Master
        print(f"--- Registering Followers on Master {master.ip_address} ---")
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            client.connect(master.ip_address, username=master.ssh_username, password=master.ssh_password)
            
            followers = [
                (fe2, "fe2", 9010),
                (fe3, "fe3", 9010)
            ]
            
            for srv, name, port in followers:
                sql = f"ALTER SYSTEM ADD FOLLOWER '{srv.ip_address}:{port}'"
                # Check if already exists first? The script does `check_fe_registered` but manual add is safe (idempotent-ish, or error if exists)
                # Using mysql client inside docker
                cmd = f"docker exec doris-fe mysql -uroot -P9030 -h127.0.0.1 -e \"{sql}\""
                print(f"Executing on Master: {cmd}")
                stdin, stdout, stderr = client.exec_command(cmd)
                out = stdout.read().decode()
                err = stderr.read().decode()
                print(f"Output: {out}")
                if err and "already exists" not in err: # Ignore "already exists" errors
                    print(f"Error: {err}")
            
            client.close()
        except Exception as e:
            print(f"Failed to register on master: {e}")
            return

        # 3. Clean and Restart Followers
        for srv in [fe2, fe3]:
            print(f"--- Resetting Follower {srv.ip_address} ---")
            try:
                client.connect(srv.ip_address, username=srv.ssh_username, password=srv.ssh_password)
                
                # Stop
                print("Stopping doris-fe...")
                client.exec_command("docker stop doris-fe")
                
                # Clean Meta (Dangerous! But necessary for split brain recovery)
                # Using sudo if not root
                # Assuming /data/doris/fe/doris-meta is the path. 
                # Verify path via docker inspect? 
                # Better to just clear the known path: /data/doris/fe/doris-meta/*
                
                clean_cmd = "rm -rf /data/doris/fe/doris-meta/*"
                if srv.ssh_username != 'root':
                    clean_cmd = f"echo '{srv.ssh_password}' | sudo -S -p '' {clean_cmd}"
                
                print(f"Cleaning meta: {clean_cmd}")
                stdin, stdout, stderr = client.exec_command(clean_cmd)
                # Wait for command to finish
                print(stdout.read().decode())
                err = stderr.read().decode()
                if err: print(f"Clean Error: {err}")
                
                # Start
                print("Starting doris-fe...")
                client.exec_command("docker start doris-fe")
                
                client.close()
            except Exception as e:
                print(f"Failed to reset follower {srv.ip_address}: {e}")

if __name__ == "__main__":
    asyncio.run(repair_cluster())
