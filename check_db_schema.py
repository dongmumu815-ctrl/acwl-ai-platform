import asyncio
import sys
import os

sys.path.append(os.path.join(os.getcwd(), 'backend'))
from app.core.database import AsyncSessionLocal
from app.models.application import AppTemplate
from sqlalchemy import select

async def main():
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(AppTemplate).where(AppTemplate.name == 'apache-doris'))
        t = res.scalar_one_or_none()
        if t:
            print(t.config_schema)
        else:
            print("Template not found")

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except Exception as e:
        # Ignore event loop closed error
        pass
