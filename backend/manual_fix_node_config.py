import asyncio
import sys
import os
import json
from sqlalchemy import select, update, text

# Add project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import get_db
from app.models.unified_node import UnifiedNode

async def main():
    async for db in get_db():
        print("Manually updating node config for Python node...")
        
        # 找到那个 Python 节点
        # 根据之前的 debug 输出，ID 是 18
        node_id = 18
        
        config = {
            "type": "python-code",
            "config": {
                "code": "print(\"hello word2\")",
                "pythonVersion": "python3.11"
            },
            "name": "Python脚本"
        }
        
        # 更新
        await db.execute(
            update(UnifiedNode)
            .where(UnifiedNode.id == node_id)
            .values(node_config=config)
        )
        await db.commit()
        print(f"Updated node {node_id} config.")

if __name__ == "__main__":
    asyncio.run(main())
