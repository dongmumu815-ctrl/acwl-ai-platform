import asyncio
import sys
import os
import logging
import uuid
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import get_db
from app.models.workflow import Workflow, WorkflowConnection, WorkflowInstance, WorkflowNodeInstance, WorkflowStatus, InstanceStatus, TriggerType
from app.models.unified_node import UnifiedNode, UnifiedNodeType
from app.models.scheduler import SchedulerNode
from app.services.scheduler_cluster import SchedulerClusterService
from sqlalchemy import select

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def check_scheduler_status():
    async for db in get_db():
        try:
            service = SchedulerClusterService(db)
            status = await service.get_cluster_status()
            logger.info(f"Cluster Leader: {status.leader_node_id}")
            
            # Check nodes
            stmt = select(SchedulerNode)
            result = await db.execute(stmt)
            nodes = result.scalars().all()
            for node in nodes:
                logger.info(f"Node {node.node_id}: Status={node.status}, Last Heartbeat={node.last_heartbeat}")
        except Exception as e:
            logger.error(f"Error checking scheduler status: {e}")

async def create_test_workflow():
    async for db in get_db():
        try:
            # 1. Create Workflow
            logger.info("Creating test workflow...")
            workflow = Workflow(
                name=f"Test Workflow {datetime.now().strftime('%Y%m%d%H%M%S')}",
                description="Auto-generated test workflow",
                workflow_status=WorkflowStatus.active,
                workflow_version="1.0.0"
            )
            db.add(workflow)
            await db.flush()
            
            # 2. Create Nodes
            # Start Node
            start_node = UnifiedNode(
                name="Start",
                node_type=UnifiedNodeType.START,
                workflow_id=workflow.id,
                executor_group="default",
                node_config={},
                position_x=0,
                position_y=0
            )
            db.add(start_node)
            await db.flush()

            # Python Node (Print)
            shell_node = UnifiedNode(
                name="Python Task",
                node_type=UnifiedNodeType.PYTHON_CODE,
                workflow_id=workflow.id,
                executor_group="default",
                node_config={
                    "code": "print('Hello from Executor!')",
                },
                position_x=200,
                position_y=0
            )
            db.add(shell_node)
            await db.flush()
            
            # 3. Connect Nodes
            conn = WorkflowConnection(
                workflow_id=workflow.id,
                source_node_id=start_node.id,
                target_node_id=shell_node.id
            )
            db.add(conn)
            await db.commit()
            
            logger.info(f"Workflow created: ID {workflow.id}")
            return workflow.id
            
        except Exception as e:
            logger.error(f"Error creating workflow: {e}")
            await db.rollback()
            return None

async def trigger_workflow(workflow_id):
    async for db in get_db():
        try:
            logger.info(f"Triggering workflow {workflow_id}...")
            
            # Create Workflow Instance
            instance = WorkflowInstance(
                instance_id=str(uuid.uuid4()),
                workflow_id=workflow_id,
                status=InstanceStatus.PENDING, # Use Enum
                triggered_by=TriggerType.MANUAL,
                scheduled_time=datetime.now()
            )
            db.add(instance)
            await db.flush()
            await db.commit()
            
            logger.info(f"Workflow instance created: ID {instance.id}")
            return instance.id
            
        except Exception as e:
            logger.error(f"Error triggering workflow: {e}")
            return None

async def monitor_execution(instance_id):
    logger.info(f"Monitoring execution of instance {instance_id}...")
    
    max_retries = 30
    async for db in get_db():
        for i in range(max_retries):
            # Check Instance Status
            result = await db.execute(
                select(WorkflowInstance).where(WorkflowInstance.id == instance_id)
            )
            instance = result.scalar_one_or_none()
            
            if not instance:
                logger.error("Instance not found!")
                return
            
            logger.info(f"Instance Status: {instance.status}")
            
            if instance.status in [InstanceStatus.SUCCESS, InstanceStatus.FAILED, InstanceStatus.CANCELLED]:
                # Check Node Instances
                result = await db.execute(
                    select(WorkflowNodeInstance)
                    .where(WorkflowNodeInstance.workflow_instance_id == instance_id)
                    .order_by(WorkflowNodeInstance.id)
                )
                nodes = result.scalars().all()
                for node in nodes:
                    logger.info(f"Node Instance {node.id}: {node.status}")
                    if node.output_data:
                        logger.info(f"  Output: {node.output_data}")
                
                if instance.status == InstanceStatus.SUCCESS:
                    logger.info("Test PASSED!")
                else:
                    logger.info("Test FAILED!")
                return
            
            await asyncio.sleep(2)
            
    logger.error("Test TIMEOUT!")

async def main():
    await check_scheduler_status()
    workflow_id = await create_test_workflow()
    if workflow_id:
        instance_id = await trigger_workflow(workflow_id)
        if instance_id:
            await monitor_execution(instance_id)

if __name__ == "__main__":
    asyncio.run(main())
