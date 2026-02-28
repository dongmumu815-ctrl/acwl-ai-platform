import asyncio
import sys
import os
from sqlalchemy import select, desc

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))
from app.core.database import AsyncSessionLocal
from app.models.task import TaskInstance
from app.schemas.task import TaskInstance as TaskInstanceSchema

async def verify_schema():
    print("Verifying TaskInstance schema validation...")
    async with AsyncSessionLocal() as db:
        stmt = select(TaskInstance).order_by(desc(TaskInstance.id)).limit(5)
        result = await db.execute(stmt)
        instances = result.scalars().all()
        
        if not instances:
            print("No instances found.")
            return

        for instance in instances:
            print(f"Checking instance {instance.id}...")
            try:
                # Pydantic validation
                schema_instance = TaskInstanceSchema.model_validate(instance)
                print(f"Validation successful for instance {instance.id}")
                # print(schema_instance.model_dump())
            except Exception as e:
                print(f"Validation FAILED for instance {instance.id}: {e}")
                # Print attributes to debug
                print(f"Instance attributes: task_version={getattr(instance, 'task_version', 'N/A')}, triggered_by={getattr(instance, 'triggered_by', 'N/A')}, task_metadata={getattr(instance, 'task_metadata', 'N/A')}")
                # Check for metadata attribute
                if hasattr(instance, 'metadata'):
                    print(f"Instance has metadata attribute: {type(instance.metadata)}")

if __name__ == "__main__":
    asyncio.run(verify_schema())
