import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend"))

from app.core.database import get_db
from app.models.task import TaskInstance, TaskStatus, TaskPriority, TriggerType
from sqlalchemy import select, text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_enum():
    async for db in get_db():
        try:
            logger.info("Testing TaskStatus Enum...")
            # 尝试插入一个简单的 TaskInstance（这可能会失败如果缺少外键，所以我们先只尝试查询）
            
            # 查询现有数据
            logger.info("Querying existing task instances...")
            result = await db.execute(select(TaskInstance).limit(1))
            instance = result.scalar_one_or_none()
            
            if instance:
                logger.info(f"Found instance: {instance.id}, status: {instance.status} (type: {type(instance.status)})")
                logger.info(f"Enum member: {TaskStatus.PENDING}, value: {TaskStatus.PENDING.value}")
                
                if instance.status == TaskStatus.PENDING:
                    logger.info("Status matches TaskStatus.PENDING")
                elif instance.status == "pending":
                    logger.info("Status matches 'pending' string")
                else:
                    logger.info(f"Status matches neither: {instance.status}")
            else:
                logger.info("No task instances found.")
                
        except Exception as e:
            logger.error(f"Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_enum())
