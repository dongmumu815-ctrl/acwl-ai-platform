
import asyncio
import sys
import os
import paramiko
import logging
from sqlalchemy import select

# Add backend to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import AsyncSessionLocal
from app.models.application import AppInstance

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SERVER_IP = "10.20.1.204"
SERVER_USER = "ubuntu"
SERVER_PASS = "cepiec1qaz@WSXaczt8912059Nxtektppyoud"

async def check_password():
    async with AsyncSessionLocal() as db:
        stmt = select(AppInstance).where(AppInstance.id == 95)
        result = await db.execute(stmt)
        instance = result.scalar_one_or_none()
        
        if instance:
            config = instance.config or {}
            pwd = config.get("harbor_admin_password", "Not Set")
            logger.info(f"Instance Config Password: {pwd}")
            
            # Now try to curl with this password
            verify_login(pwd)
        else:
            logger.error("Instance 95 not found")

def verify_login(password):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(SERVER_IP, username=SERVER_USER, password=SERVER_PASS)
        
        logger.info(f"Attempting Login with admin:{password}...")
        cmd = f"curl -i -u 'admin:{password}' http://127.0.0.1/api/v2.0/users/current"
        stdin, stdout, stderr = client.exec_command(cmd)
        out = stdout.read().decode()
        
        if "200 OK" in out or '"username":"admin"' in out:
            logger.info(">>> LOGIN SUCCESSFUL! <<<")
            print(f"\nSUCCESS: Login worked with password: {password}")
        else:
            logger.error(f"Login Failed with {password}")
            
    except Exception as e:
        logger.error(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(check_password())
