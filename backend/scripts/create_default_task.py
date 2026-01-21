import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import get_db
from app.models.task import TaskDefinition, TaskType, TaskPriority
from sqlalchemy import select

async def create_default_task():
    async for db in get_db():
        stmt = select(TaskDefinition).where(TaskDefinition.name == "System Default Task")
        result = await db.execute(stmt)
        default_task_def = result.scalar_one_or_none()
        
        if default_task_def:
            print(f"System Default Task already exists: ID {default_task_def.id}")
        else:
            print("Creating System Default Task...")
            default_task_def = TaskDefinition(
                name="System Default Task",
                task_type=TaskType.CUSTOM,
                executor_group="default",
                priority=TaskPriority.NORMAL,
                created_by=5  # admin
            )
            db.add(default_task_def)
            await db.commit()
            await db.refresh(default_task_def)
            print(f"System Default Task created: ID {default_task_def.id}")

if __name__ == "__main__":
    asyncio.run(create_default_task())
