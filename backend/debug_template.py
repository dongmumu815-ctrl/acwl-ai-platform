
import asyncio
import sys
import os

# 添加 backend 目录到 sys.path
sys.path.append(os.getcwd())

from app.core.database import AsyncSessionLocal
from app.crud.application import app_template
from sqlalchemy import select
from app.models.application import AppTemplate

async def main():
    async with AsyncSessionLocal() as db:
        # 列出所有模板名称
        stmt = select(AppTemplate.name)
        result = await db.execute(stmt)
        names = result.scalars().all()
        print(f"Available templates: {names}")
        
        # 尝试获取 Harbor 模板
        target_name = "Harbor"
        if "harbor" in names:
            target_name = "harbor"
        elif "Harbor" in names:
            target_name = "Harbor"
            
        stmt = select(AppTemplate).where(AppTemplate.name == target_name)
        result = await db.execute(stmt)
        t = result.scalar_one_or_none()
        
        if t:
            print(f"\n--- Template: {t.name} ---")
            print(f"Deploy Template:\n{t.deploy_template}")
            print(f"\nDefault Config:\n{t.default_config}")
        else:
            print(f"\nTemplate '{target_name}' not found.")

if __name__ == "__main__":
    asyncio.run(main())
