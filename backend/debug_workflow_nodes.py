import asyncio
import sys
import os
from sqlalchemy import select, text

# Add project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import get_db
from app.models.unified_node import UnifiedNode
from app.models.workflow import WorkflowInstance

async def main():
    async for db in get_db():
        print("Checking recent workflow instances...")
        # 获取最近的一个工作流实例
        stmt = select(WorkflowInstance).order_by(WorkflowInstance.created_at.desc()).limit(1)
        result = await db.execute(stmt)
        instance = result.scalar_one_or_none()
        
        if not instance:
            print("No workflow instances found.")
            return

        print(f"Latest Workflow Instance ID: {instance.id} (Instance ID: {instance.instance_id})")
        print(f"Workflow ID: {instance.workflow_id}")
        print(f"Status: {instance.status}")
        print(f"Error Message: {instance.error_message}")

        print("\nChecking nodes for this workflow...")
        # 获取该工作流的所有节点
        stmt = select(UnifiedNode).where(UnifiedNode.workflow_id == instance.workflow_id)
        result = await db.execute(stmt)
        nodes = result.scalars().all()
        
        print(f"Total nodes found: {len(nodes)}")
        for node in nodes:
            print(f"Node ID: {node.id}")
            print(f"  Name: {node.name}")
            print(f"  Type: {node.node_type} (Type: {type(node.node_type)})")
            print(f"  Config: {node.node_config}")
            print(f"  Config Type: {node.node_config.get('type') if node.node_config else 'N/A'}")
            
        # 直接使用 SQL 查询来查看原始值，避开 SQLAlchemy 的转换
        print("\nRaw DB values:")
        result = await db.execute(text(f"SELECT id, node_type FROM acwl_unified_nodes WHERE workflow_id = {instance.workflow_id}"))
        for row in result:
            print(f"  ID: {row[0]}, Raw Type: {row[1]}")

if __name__ == "__main__":
    asyncio.run(main())
