import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import AsyncSessionLocal
from app.models.application import AppInstance, AppTemplate
from sqlalchemy import select

async def main():
    async with AsyncSessionLocal() as session:
        # 1. Get Template
        stmt = select(AppTemplate).where(AppTemplate.id == 4)
        result = await session.execute(stmt)
        template = result.scalar_one_or_none()
        
        if not template:
            print("Template 4 not found!")
            return
            
        default_script = template.default_config.get('pre_deploy_script')
        if not default_script:
            print("Template 4 has no pre_deploy_script in default_config!")
            return
            
        print(f"Found template script (Length: {len(default_script)})")
        
        # 2. Get Instance
        stmt = select(AppInstance).where(AppInstance.id == 96)
        result = await session.execute(stmt)
        instance = result.scalar_one_or_none()
        
        if not instance:
            print("Instance 96 not found!")
            return
            
        # 3. Update Instance Config
        new_config = dict(instance.config)
        new_config['pre_deploy_script'] = default_script
        new_config['http_port'] = 5000
        new_config['external_url'] = "http://10.20.1.204:5000"
        
        # Ensure other defaults
        if 'harbor_admin_password' not in new_config:
            new_config['harbor_admin_password'] = "Harbor12345"
        if 'data_volume' not in new_config:
            new_config['data_volume'] = "/data/harbor"
            
        instance.config = new_config
        session.add(instance)
        await session.commit()
        
        print("Instance config updated with template script and correct ports.")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
