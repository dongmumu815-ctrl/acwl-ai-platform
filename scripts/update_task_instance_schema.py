import asyncio
import sys
import os
from sqlalchemy import text

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))
from app.core.database import engine

async def update_schema():
    async with engine.connect() as conn:
        print("Checking acwl_task_instances schema...")
        
        # Check if columns exist
        result = await conn.execute(text("SHOW COLUMNS FROM acwl_task_instances LIKE 'task_version'"))
        if not result.fetchone():
            print("Adding task_version column...")
            await conn.execute(text("ALTER TABLE acwl_task_instances ADD COLUMN task_version INT DEFAULT 1 COMMENT '任务版本'"))
        
        result = await conn.execute(text("SHOW COLUMNS FROM acwl_task_instances LIKE 'triggered_by'"))
        if not result.fetchone():
            print("Adding triggered_by column...")
            # Note: Ensure these enum values match the TriggerType enum definition
            await conn.execute(text("ALTER TABLE acwl_task_instances ADD COLUMN triggered_by ENUM('manual', 'scheduled', 'dependency', 'event', 'api') NOT NULL DEFAULT 'manual' COMMENT '触发方式'"))

        result = await conn.execute(text("SHOW COLUMNS FROM acwl_task_instances LIKE 'triggered_by_user'"))
        if not result.fetchone():
            print("Adding triggered_by_user column...")
            await conn.execute(text("ALTER TABLE acwl_task_instances ADD COLUMN triggered_by_user INT DEFAULT NULL COMMENT '触发用户ID'"))
            # Add FK only if it doesn't exist (hard to check easily in one go, but ADD CONSTRAINT usually fails if exists? No, duplicate names fail)
            # We'll assume if column didn't exist, constraint didn't either.
            try:
                await conn.execute(text("ALTER TABLE acwl_task_instances ADD CONSTRAINT fk_task_instances_user FOREIGN KEY (triggered_by_user) REFERENCES acwl_users(id) ON DELETE SET NULL"))
            except Exception as e:
                print(f"Warning adding FK: {e}")

        result = await conn.execute(text("SHOW COLUMNS FROM acwl_task_instances LIKE 'task_metadata'"))
        if not result.fetchone():
            print("Adding task_metadata column...")
            await conn.execute(text("ALTER TABLE acwl_task_instances ADD COLUMN task_metadata JSON DEFAULT NULL COMMENT '元数据'"))
            
        await conn.commit()
        print("Schema update completed.")

if __name__ == "__main__":
    asyncio.run(update_schema())
