import asyncio
import sys
import os
import paramiko
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from app.core.config import settings
from app.models.application import AppInstance, AppDeployment
from app.models.server import Server

# Database URL
DATABASE_URL = f"mysql+aiomysql://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"

async def get_latest_doris_instance(session):
    stmt = select(AppInstance).where(AppInstance.name.like('%doris%')).order_by(AppInstance.created_at.desc()).limit(1)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()

async def get_deployments(session, instance_id):
    stmt = select(AppDeployment).where(AppDeployment.instance_id == instance_id)
    result = await session.execute(stmt)
    return result.scalars().all()

async def get_server(session, server_id):
    stmt = select(Server).where(Server.id == server_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()

def check_server(server, instance_id):
    print(f"\n--- Checking Server: {server.ip_address} ({server.name}) ---")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        # Connect
        if server.ssh_key_path:
            client.connect(server.ip_address, port=server.ssh_port, username=server.ssh_username, key_filename=server.ssh_key_path, timeout=10)
        elif server.ssh_password:
            client.connect(server.ip_address, port=server.ssh_port, username=server.ssh_username, password=server.ssh_password, timeout=10)
        else:
            print(f"❌ No credentials for {server.ip_address}")
            return

        # Helper for sudo
        def sudo_cmd(cmd):
            if server.ssh_username == 'root':
                return cmd
            elif server.ssh_password:
                safe_pass = server.ssh_password.replace("'", "'\\''")
                return f"echo '{safe_pass}' | sudo -S -p '' {cmd}"
            else:
                return f"sudo -n {cmd}"

        # Check directory
        deploy_path = f"/opt/acwl-apps/instances/{instance_id}"
        # Use sudo_cmd for ls
        cmd_ls = sudo_cmd(f"ls -ld {deploy_path}")
        stdin, stdout, stderr = client.exec_command(cmd_ls)
        if stdout.channel.recv_exit_status() != 0:
            print(f"❌ Deployment directory not found: {deploy_path}")
            # Try to list /opt/acwl-apps to see if parent exists
            stdin, stdout, stderr = client.exec_command(sudo_cmd(f"ls -ld /opt/acwl-apps"))
            if stdout.channel.recv_exit_status() == 0:
                 print(f"   (Parent /opt/acwl-apps exists)")
            return
        print(f"✅ Directory exists: {deploy_path}")

        # Check docker-compose.yml content
        cmd_cat = sudo_cmd(f"cat {deploy_path}/docker-compose.yml")
        stdin, stdout, stderr = client.exec_command(cmd_cat)
        content = stdout.read().decode()
        if "services:" not in content:
            print(f"❌ docker-compose.yml is invalid (missing 'services:'):")
            print(content[:200] + "..." if len(content) > 200 else content)
        else:
            print(f"✅ docker-compose.yml seems valid (contains 'services:')")
            # Check for specific service
            if "doris-fe" in content:
                print("   - Contains doris-fe service")
            if "doris-be" in content:
                print("   - Contains doris-be service")
            if "FE_ID" in content:
                print("   - Contains FE_ID")

        # Check Docker Containers
        print("Checking containers...")
        # Use sudo_cmd for docker commands
        cmd = f"cd {deploy_path} && {sudo_cmd('docker compose ps')}"
        stdin, stdout, stderr = client.exec_command(cmd)
        out = stdout.read().decode()
        err = stderr.read().decode()
        
        if "doris" in out:
             print(f"✅ Containers found:\n{out}")
             
             # Check for restarting containers and print logs
             for line in out.splitlines():
                 if "Restarting" in line or "Exit" in line:
                     parts = line.split()
                     # Docker compose ps output format varies, but usually first column is Name or Service
                     # In the output above: NAME IMAGE COMMAND SERVICE ...
                     # The output above shows "doris-fe ... Restarting"
                     # Let's try to get the container name or service name
                     container_name = parts[0]
                     print(f"\n⚠️ Container {container_name} is not healthy. Fetching logs...")
                     cmd_logs = sudo_cmd(f"docker logs --tail 20 {container_name}")
                     stdin, stdout, stderr = client.exec_command(cmd_logs)
                     logs = stdout.read().decode() + stderr.read().decode()
                     print(f"--- Logs for {container_name} ---\n{logs}\n-----------------------------")

        # Always print logs for FE to debug split brain
        if "doris-fe" in out:
             print(f"\n🔍 Fetching logs for doris-fe to debug startup...")
             cmd_logs = sudo_cmd(f"docker logs --tail 100 doris-fe")
             stdin, stdout, stderr = client.exec_command(cmd_logs)
             logs = stdout.read().decode() + stderr.read().decode()
             print(f"--- Logs for doris-fe ---\n{logs}\n-----------------------------")

             # Check remote docker-compose.yml content to verify template rendering
             print(f"--- Checking docker-compose.yml on {server.ip_address} ---")
             cmd_cat = sudo_cmd(f"cat {deploy_path}/docker-compose.yml")
             stdin, stdout, stderr = client.exec_command(cmd_cat)
             content = stdout.read().decode()
             print(content)
             print("-----------------------------------------------------------")
        else:
             print(f"⚠️ No running containers found with 'docker compose ps'.")
             if err: print(f"   Error: {err}")
             if out: print(f"   Output: {out}")
             
             # Try docker-compose v1
             cmd_v1 = f"cd {deploy_path} && {sudo_cmd('docker-compose ps')}"
             stdin, stdout, stderr = client.exec_command(cmd_v1)
             out_v1 = stdout.read().decode()
             if "doris" in out_v1:
                 print(f"✅ Containers found (v1):\n{out_v1}")

        # Check Docker Images
        print("Checking images...")
        cmd_img = sudo_cmd("docker images | grep doris")
        stdin, stdout, stderr = client.exec_command(cmd_img)
        out = stdout.read().decode()
        if out:
            print(f"✅ Images found:\n{out}")
        else:
            print("❌ No doris images found")

        # --- Internal Health Check (SQL) ---
        # Check if this node is a FE Master or Follower and is running
        # We try to connect to FE port 9030 (MySQL protocol)
        # Using docker run mysql client to avoid dependency on host tools
        if "doris-fe" in content:
            print("\nChecking Internal Cluster Health (SQL)...")
            # Determine FE IP (use 127.0.0.1 since we are on the node)
            # Try to run SHOW FRONTENDS
            sql_check = "SHOW FRONTENDS"
            # Note: 127.0.0.1 inside container might not work if using host network, but we run mysql container with --network host
            check_cmd = f"docker run --rm --network host mysql:5.7 mysql -h 127.0.0.1 -P 9030 -u root -e \"{sql_check}\""
            cmd_sql = sudo_cmd(check_cmd)
            
            print(f"Executing: {check_cmd}")
            stdin, stdout, stderr = client.exec_command(cmd_sql)
            out_sql = stdout.read().decode()
            err_sql = stderr.read().decode()
            
            if stdout.channel.recv_exit_status() == 0:
                print(f"✅ SQL Connection Successful. Cluster Members:\n{out_sql}")
            else:
                print(f"⚠️ SQL Connection Failed.")
                if "Can't connect" in err_sql:
                    print("   (Service might be starting up or port is not listening)")
                else:
                    print(f"   Error: {err_sql}")

    except Exception as e:
        print(f"❌ Connection/Execution error: {e}")
    finally:
        client.close()

async def main():
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        instance = await get_latest_doris_instance(session)
        if not instance:
            print("No Doris instance found.")
            return

        print(f"Checking Doris Instance: {instance.name} (ID: {instance.id})")
        deployments = await get_deployments(session, instance.id)
        
        for dep in deployments:
            server = await get_server(session, dep.server_id)
            if server:
                check_server(server, instance.id)
            else:
                print(f"Server not found for deployment {dep.id}")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())
