import asyncio
import sys
import os
import paramiko

# Add backend to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.application_service import ApplicationService
from app.core.database import AsyncSessionLocal
from app.models.application import AppInstance
from sqlalchemy import select

HOST = "10.20.1.204"
USER = "ubuntu"
PASS = "cepiec1qaz@WSXaczt8912059Nxtektppyoud"

def clean_remote():
    print("Cleaning remote server...")
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(HOST, username=USER, password=PASS)
        
        # Stop containers (Force remove)
        containers = "harbor-log harbor-db harbor-core registry registryctl harbor-jobservice harbor-portal nginx redis"
        cmd = f"echo '{PASS}' | sudo -S docker rm -f {containers}"
        print(f"Executing: {cmd}")
        ssh.exec_command(cmd)
        
        # Remove data directory
        cmd = f"echo '{PASS}' | sudo -S rm -rf /data/harbor"
        print(f"Executing: {cmd}")
        ssh.exec_command(cmd)
        
        print("Remote cleaned.")
    except Exception as e:
        print(f"Error cleaning remote: {e}")
    finally:
        ssh.close()

async def redeploy():
    async with AsyncSessionLocal() as session:
        # Get instance 96
        stmt = select(AppInstance).where(AppInstance.id == 96)
        result = await session.execute(stmt)
        instance = result.scalar_one_or_none()
        
        if not instance:
            print("Instance 96 not found!")
            return
            
        print(f"Redeploying instance {instance.id} ({instance.name})...")
        
        # Debug config
        script = instance.config.get('pre_deploy_script', '')
        print(f"Pre-deploy script length: {len(script)}")
        if '10.20.1.204' in script:
            print("Script contains 10.20.1.204 (Hardcoded check passed)")
        else:
            print("Script DOES NOT contain 10.20.1.204! (Hardcoded check FAILED)")
            
        # Deploy
        # Note: This runs the full deployment logic including pre_deploy_script
        service = ApplicationService(session)
        await service.deploy_app(96)
        print("Deployment triggered successfully.")

if __name__ == "__main__":
    clean_remote()
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(redeploy())
