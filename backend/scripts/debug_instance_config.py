import asyncio
import sys
import os
import paramiko

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import AsyncSessionLocal
from app.models.application import AppInstance
from sqlalchemy import select

HOST = "10.20.1.204"
USER = "ubuntu"
PASS = "cepiec1qaz@WSXaczt8912059Nxtektppyoud"

async def main():
    async with AsyncSessionLocal() as session:
        stmt = select(AppInstance).where(AppInstance.id == 96)
        result = await session.execute(stmt)
        instance = result.scalar_one_or_none()
        
        if not instance:
            print("Instance 96 not found")
            return
            
        print(f"Checking Instance Config...")
        print(f"HTTP Port: {instance.config.get('http_port')}")
        print(f"External URL: {instance.config.get('external_url')}")
        
        # Check pre_deploy_script
        script = instance.config.get('pre_deploy_script')
        if script:
            print("Pre-deploy script found in instance config.")
            if "5000" in script:
                print("Script contains '5000'.")
            else:
                print("Script DOES NOT contain '5000'. It might be outdated.")
                # Print first few lines
                print("\n--- Script Head ---")
                print('\n'.join(script.split('\n')[:20]))
                print("-------------------")
        else:
            print("No pre_deploy_script in instance config. Using template default.")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
