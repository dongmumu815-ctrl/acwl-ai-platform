
import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import AsyncSessionLocal
from app.models.application import AppInstance, AppTemplate
from sqlalchemy import select

async def check_instances():
    async with AsyncSessionLocal() as session:
        print("Checking AppTemplates...")
        stmt = select(AppTemplate).where(AppTemplate.name.ilike("%Harbor%"))
        result = await session.execute(stmt)
        templates = result.scalars().all()
        for t in templates:
            print(f"Template: {t.id} - {t.name}")
            
            print(f"Checking AppInstances for template {t.id}...")
            stmt_inst = select(AppInstance).where(AppInstance.template_id == t.id)
            res_inst = await session.execute(stmt_inst)
            instances = res_inst.scalars().all()
            for i in instances:
                print(f"  Instance: {i.id} - {i.name} (Config template length: {len(i.config.get('deploy_template', ''))})")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(check_instances())
