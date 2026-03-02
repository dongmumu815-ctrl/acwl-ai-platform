import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import AsyncSessionLocal
from app.models.application import AppInstance
from sqlalchemy import select

async def main():
    async with AsyncSessionLocal() as session:
        stmt = select(AppInstance).where(AppInstance.id == 96)
        result = await session.execute(stmt)
        instance = result.scalar_one_or_none()
        
        if not instance:
            print("Instance 96 not found")
            return
            
        print("Cleaning instance config...")
        new_config = dict(instance.config)
        
        # Remove pre_deploy_script so it uses the template's one
        if 'pre_deploy_script' in new_config:
            del new_config['pre_deploy_script']
            
        # Ensure port is 5000
        new_config['http_port'] = 5000
        new_config['external_url'] = "http://10.20.1.204:5000"
        
        instance.config = new_config
        session.add(instance)
        await session.commit()
        
        print("Instance config cleaned. Ready for redeploy.")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
