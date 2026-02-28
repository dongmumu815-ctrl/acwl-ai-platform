import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import engine
from sqlalchemy import text

async def fix_fk():
    try:
        async with engine.begin() as conn:
            print("Disabling foreign key checks...")
            await conn.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
            
            print("Truncating workflow tables...")
            await conn.execute(text("TRUNCATE TABLE acwl_workflow_connections"))
            await conn.execute(text("TRUNCATE TABLE acwl_workflow_node_instances"))
            await conn.execute(text("TRUNCATE TABLE acwl_workflow_instances"))
            await conn.execute(text("TRUNCATE TABLE acwl_unified_nodes"))
            await conn.execute(text("TRUNCATE TABLE acwl_workflows"))
            
            print("Truncating scheduler tables...")
            await conn.execute(text("TRUNCATE TABLE acwl_scheduler_nodes"))
            await conn.execute(text("TRUNCATE TABLE acwl_scheduler_locks"))
            
            print("Dropping old FKs (if they exist)...")
            try:
                await conn.execute(text("ALTER TABLE acwl_workflow_connections DROP FOREIGN KEY acwl_workflow_connections_ibfk_2"))
            except Exception:
                pass
            try:
                await conn.execute(text("ALTER TABLE acwl_workflow_connections DROP FOREIGN KEY acwl_workflow_connections_ibfk_3"))
            except Exception:
                pass
            
            print("Adding new FKs to acwl_unified_nodes...")
            await conn.execute(text("ALTER TABLE acwl_workflow_connections ADD CONSTRAINT acwl_workflow_connections_ibfk_2 FOREIGN KEY (source_node_id) REFERENCES acwl_unified_nodes(id) ON DELETE CASCADE"))
            await conn.execute(text("ALTER TABLE acwl_workflow_connections ADD CONSTRAINT acwl_workflow_connections_ibfk_3 FOREIGN KEY (target_node_id) REFERENCES acwl_unified_nodes(id) ON DELETE CASCADE"))
            
            print("Enabling foreign key checks...")
            await conn.execute(text("SET FOREIGN_KEY_CHECKS = 1"))
            print("Done.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(fix_fk())
