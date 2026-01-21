import asyncio
import sys
import os
import json
from sqlalchemy import select, update, text

# Add project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import get_db
from app.models.unified_node import UnifiedNode, UnifiedNodeType

async def main():
    async for db in get_db():
        print("Starting node type fix...")
        
        # 获取所有 UnifiedNode
        stmt = select(UnifiedNode)
        result = await db.execute(stmt)
        nodes = result.scalars().all()
        
        updated_count = 0
        
        for node in nodes:
            original_type = node.node_type
            new_type = None
            
            # 从 node_config 获取类型信息
            config_type = None
            if node.node_config:
                config_type = node.node_config.get('type')
            
            # 映射逻辑
            if config_type:
                type_mapping = {
                    'start': UnifiedNodeType.START,
                    'end': UnifiedNodeType.END,
                    'python_code': UnifiedNodeType.PYTHON_CODE,
                    'sql_query': UnifiedNodeType.SQL_QUERY,
                    'condition': UnifiedNodeType.CONDITION,
                    'loop': UnifiedNodeType.LOOP,
                    'shell-script': UnifiedNodeType.SHELL_SCRIPT,
                    'shell_script': UnifiedNodeType.SHELL_SCRIPT,
                    'custom': UnifiedNodeType.CUSTOM
                }
                
                mapped = type_mapping.get(config_type.lower())
                if mapped:
                    new_type = mapped
            
            # 如果从 config 没找到，尝试从 name/display_name 推断 (仅针对 workflow_id=4 的紧急修复)
            if not new_type and node.workflow_id == 4:
                if 'start' in node.name.lower() or node.display_name == '开始':
                    new_type = UnifiedNodeType.START
                elif 'end' in node.name.lower() or node.display_name == '结束':
                    new_type = UnifiedNodeType.END
                elif 'python' in node.name.lower() or 'python' in (node.display_name or '').lower():
                    new_type = UnifiedNodeType.PYTHON_CODE

            # 执行更新
            if new_type and new_type != original_type:
                print(f"Updating Node {node.id} ({node.name}): {original_type} -> {new_type}")
                # 直接使用 SQL 更新以避免 Enum 对象问题
                await db.execute(
                    text(f"UPDATE acwl_unified_nodes SET node_type = '{new_type.value}' WHERE id = {node.id}")
                )
                updated_count += 1
        
        await db.commit()
        print(f"Fixed {updated_count} nodes.")

if __name__ == "__main__":
    asyncio.run(main())
