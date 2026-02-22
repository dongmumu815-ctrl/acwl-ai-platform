
import asyncio
import os
import sys
import json
import paramiko
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from app.core.database import AsyncSessionLocal
from app.models.server import Server
from sqlalchemy import select

async def fix_and_start():
    # Only target followers
    target_ips = ['10.20.1.216', '10.20.1.217']
    
    async with AsyncSessionLocal() as db:
        for ip in target_ips:
            print(f"\n>>> Processing Follower: {ip}")
            stmt = select(Server).where(Server.ip_address == ip)
            server = (await db.execute(stmt)).scalar_one_or_none()
            
            if not server:
                print("Server not found")
                continue

            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            try:
                client.connect(server.ip_address, username=server.ssh_username, password=server.ssh_password)
                
                # 1. Get Volume Path from Inspect
                print("Getting volume path...")
                cmd = "docker inspect doris-fe"
                stdin, stdout, stderr = client.exec_command(cmd)
                output = stdout.read().decode().strip()
                
                meta_path = None
                if output:
                    try:
                        data = json.loads(output)
                        mounts = data[0].get('Mounts', [])
                        for m in mounts:
                            # destination in container is /opt/apache-doris/fe/doris-meta
                            if m['Destination'] == '/opt/apache-doris/fe/doris-meta':
                                meta_path = m['Source']
                                break
                    except Exception as e:
                        print(f"JSON Parse Error: {e}")
                
                if not meta_path:
                    print("Could not find host path for /opt/apache-doris/fe/doris-meta. Checking manually...")
                    # Fallback to standard location check
                    # Or check docker-compose.yml location? Usually /data/acwl_data/app_.../data/fe/doris-meta
                    # But we need to be sure.
                    print("Skipping cleaning to avoid data loss if path is wrong. Trying to start only.")
                else:
                    print(f"Found Host Meta Path: {meta_path}")
                    
                    # 2. Stop
                    print("Stopping container...")
                    client.exec_command("docker stop doris-fe")
                    
                    # 3. Clean
                    print(f"Cleaning {meta_path}/* ...")
                    clean_cmd = f"rm -rf {meta_path}/*"
                    if server.ssh_username != 'root':
                        clean_cmd = f"echo '{server.ssh_password}' | sudo -S -p '' {clean_cmd}"
                    
                    stdin, stdout, stderr = client.exec_command(clean_cmd)
                    print(stdout.read().decode())
                    err = stderr.read().decode()
                    if err: print(f"Clean Error: {err}")

                # 4. Start
                print("Starting container...")
                client.exec_command("docker start doris-fe")
                
                # 5. Monitor Logs
                print("Monitoring logs (5 seconds)...")
                await asyncio.sleep(5)
                stdin, stdout, stderr = client.exec_command("docker logs --tail 20 doris-fe")
                print("--- LOGS ---")
                print(stdout.read().decode())
                print(stderr.read().decode())
                
                # 6. Check PS
                stdin, stdout, stderr = client.exec_command("docker ps | grep doris-fe")
                print("--- PS ---")
                print(stdout.read().decode())

            except Exception as e:
                print(f"Error on {ip}: {e}")
            finally:
                client.close()

if __name__ == "__main__":
    asyncio.run(fix_and_start())
