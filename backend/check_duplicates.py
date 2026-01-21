import asyncio
import sys
import os
from sqlalchemy import text

# Add project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import get_db

async def main():
    async for db in get_db():
        print("Checking for duplicate WorkflowNodeInstance records...")
        
        # 查找是否有重复的 (workflow_instance_id, node_id) 组合
        stmt = text("""
            SELECT workflow_instance_id, node_id, COUNT(*) as count
            FROM acwl_workflow_node_instances
            GROUP BY workflow_instance_id, node_id
            HAVING count > 1
        """)
        
        result = await db.execute(stmt)
        duplicates = result.fetchall()
        
        if not duplicates:
            print("No duplicates found.")
        else:
            print(f"Found {len(duplicates)} sets of duplicates:")
            for row in duplicates:
                print(f"  Workflow Instance ID: {row[0]}, Node ID: {row[1]}, Count: {row[2]}")
                
                # 获取这些重复记录的详细信息
                detail_stmt = text(f"""
                    SELECT id, status, created_at 
                    FROM acwl_workflow_node_instances 
                    WHERE workflow_instance_id = {row[0]} AND node_id = {row[1]}
                """)
                details = await db.execute(detail_stmt)
                for d in details:
                    print(f"    - ID: {d[0]}, Status: {d[1]}, Created At: {d[2]}")

        # 检查 TaskDefinition 是否有重复的 "System Default Task"
        print("\nChecking TaskDefinition for 'System Default Task'...")
        stmt = text("SELECT id, name FROM acwl_task_definitions WHERE name = 'System Default Task'")
        result = await db.execute(stmt)
        tasks = result.fetchall()
        print(f"Found {len(tasks)} records:")
        for task in tasks:
            print(f"  ID: {task[0]}, Name: {task[1]}")

if __name__ == "__main__":
    asyncio.run(main())
