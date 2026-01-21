import asyncio
import sys
import os
import logging
import uuid
from datetime import datetime

# 添加 backend 目录到 path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend"))

from app.core.database import get_db
from app.services.workflow_engine import workflow_engine
from app.models.workflow import WorkflowInstance, InstanceStatus, Workflow, WorkflowNodeInstance
from app.models.task import TaskInstance, TriggerType
from sqlalchemy import select, update, text
from sqlalchemy.orm import selectinload

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def verify_execution():
    async for db in get_db():
        try:
            logger.info("Starting workflow verification...")
            
            # 1. 获取工作流 ID=4
            workflow_id = 4
            result = await db.execute(select(Workflow).filter(Workflow.id == workflow_id))
            workflow = result.scalar_one_or_none()
            if not workflow:
                logger.error(f"Workflow {workflow_id} not found!")
                return
            
            logger.info(f"Found workflow: {workflow.name}")
            
            # 2. 创建工作流实例
            instance = WorkflowInstance(
                instance_id=f"wf-ins-{uuid.uuid4().hex[:8]}",
                workflow_id=workflow_id,
                status=InstanceStatus.PENDING,
                scheduled_time=datetime.now(),
                triggered_by_user=5,  # admin
                triggered_by=TriggerType.MANUAL
            )
            db.add(instance)
            await db.commit()
            await db.refresh(instance)
            logger.info(f"Created workflow instance: {instance.id}")
            
            # 3. 启动工作流实例 (这将触发 workflow_engine.start_instance)
            # 注意：workflow_engine.start_instance 内部会 commit，所以这里不需要再 commit
            success = await workflow_engine.start_instance(instance.id, db)
            if success:
                logger.info("Workflow instance started successfully.")
            else:
                logger.error("Failed to start workflow instance.")
                return

            # 4. 检查生成的节点实例
            result = await db.execute(
                select(WorkflowNodeInstance)
                .filter(WorkflowNodeInstance.workflow_instance_id == instance.id)
            )
            node_instances = result.scalars().all()
            logger.info(f"Generated {len(node_instances)} node instances:")
            for node in node_instances:
                logger.info(f"  - Node {node.node_id} ({node.node_type}): {node.status}, TaskInstanceID: {node.task_instance_id}")
                
                # 如果有 task_instance_id，检查 task instance
                if node.task_instance_id:
                    task_res = await db.execute(select(TaskInstance).filter(TaskInstance.id == node.task_instance_id))
                    task = task_res.scalar_one_or_none()
                    if task:
                        logger.info(f"    -> TaskInstance: {task.instance_id}, Status: {task.status}")
                    else:
                        logger.error(f"    -> TaskInstance {node.task_instance_id} NOT FOUND!")

        except Exception as e:
            logger.error(f"Error during verification: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(verify_execution())
