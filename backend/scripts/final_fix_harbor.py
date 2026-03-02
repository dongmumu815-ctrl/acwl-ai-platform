
import asyncio
import sys
import os
import time
import paramiko
import logging
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# Add backend to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import AsyncSessionLocal
from app.models.application import AppInstance, AppStatus
from app.services.application_service import ApplicationService

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SERVER_IP = "10.20.1.204"
SERVER_USER = "ubuntu"
SERVER_PASS = "cepiec1qaz@WSXaczt8912059Nxtektppyoud"

def ssh_exec(client, cmd, sudo=False):
    if sudo:
        cmd = f"echo '{SERVER_PASS}' | sudo -S {cmd}"
    logger.info(f"SSH Exec: {cmd}")
    stdin, stdout, stderr = client.exec_command(cmd)
    out = stdout.read().decode().strip()
    err = stderr.read().decode().strip()
    if err and "password" not in err.lower(): # Ignore sudo prompt
        logger.warning(f"SSH Stderr: {err}")
    return out

def nuke_remote_environment():
    logger.info(">>> STEP 1: Nuking Remote Environment...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(SERVER_IP, username=SERVER_USER, password=SERVER_PASS)
        
        # 1. Stop and remove containers
        containers = ssh_exec(client, "docker ps -a -q -f name=harbor -f name=registry -f name=redis -f name=nginx")
        if containers:
            ssh_exec(client, f"docker rm -f {containers.replace(chr(10), ' ')}", sudo=True)
        
        # 2. Prune networks
        ssh_exec(client, "docker network prune -f", sudo=True)
        
        # 3. Move Data Directory
        ts = int(time.time())
        ssh_exec(client, f"mv /data/harbor /data/harbor_bak_{ts}", sudo=True)
        
        # 4. Verify
        check = ssh_exec(client, "ls -d /data/harbor")
        if "No such file" in check or "cannot access" in check:
            logger.info("Data directory successfully moved.")
        else:
            logger.info(f"Check result: {check}")

    except Exception as e:
        logger.error(f"SSH Error: {e}")
        raise
    finally:
        client.close()

async def trigger_deployment():
    logger.info(">>> STEP 2: Triggering Deployment via ApplicationService...")
    
    async with AsyncSessionLocal() as db:
        # 1. Find Harbor Instance
        stmt = select(AppInstance).where(AppInstance.name.ilike("%Harbor%"))
        result = await db.execute(stmt)
        instance = result.scalar_one_or_none()
        
        if not instance:
            logger.error("Harbor instance not found in DB!")
            return
        
        logger.info(f"Found Harbor Instance: {instance.id} ({instance.name})")
        
        # 2. Reset Status
        instance.status = AppStatus.stopped
        await db.commit()
        
        # 3. Deploy
        service = ApplicationService(db)
        logger.info("Calling deploy_app...")
        await service.deploy_app(instance.id)
        logger.info("Deployment task finished (async).")

def verify_login():
    logger.info(">>> STEP 3: Verifying Login...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(SERVER_IP, username=SERVER_USER, password=SERVER_PASS)
        
        # Wait loop
        for i in range(12): # Wait up to 2 minutes
            logger.info(f"Waiting for services... ({i*10}s)")
            time.sleep(10)
            
            # Check containers
            out = ssh_exec(client, "docker ps | grep harbor-core")
            if "healthy" in out:
                logger.info("Harbor Core is HEALTHY.")
                break
        
        # Curl Login
        logger.info("Attempting Login with admin:Harbor12345...")
        cmd = "curl -i -u 'admin:Harbor12345' http://127.0.0.1/api/v2.0/users/current"
        out = ssh_exec(client, cmd)
        
        if "200 OK" in out or '"username":"admin"' in out:
            logger.info(">>> LOGIN SUCCESSFUL! <<<")
            print("\nSUCCESS: Harbor has been reset and deployed. Password is 'Harbor12345'.")
        else:
            logger.error(f"Login Failed. Output:\n{out}")
            
    except Exception as e:
        logger.error(f"Verification Error: {e}")
    finally:
        client.close()

async def main():
    nuke_remote_environment()
    await trigger_deployment()
    verify_login()

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
