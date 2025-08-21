#!/usr/bin/env python3
"""
修复数据库schema和数据
"""

import asyncio
import sys
sys.path.append('backend')

from app.core.database import get_db_context
from sqlalchemy import text

async def fix_database():
    """
    修复数据库schema和数据
    """
    try:
        async with get_db_context() as db:
            print("开始修复数据库...")
            
            # 1. 先修改枚举类型定义，添加新的值
            print("1. 添加新的枚举值...")
            alter_enum_add = text("""
                ALTER TABLE acwl_models 
                MODIFY COLUMN model_type ENUM('LLM', 'Embedding', 'Multimodal', 'Other', 'EMBEDDING', 'MULTIMODAL', 'OTHER') NOT NULL
            """)
            await db.execute(alter_enum_add)
            print("   ✅ 已添加新的枚举值")
            
            # 2. 更新数据
            print("2. 更新数据...")
            
            # 更新 Embedding -> EMBEDDING
            update_embedding = text("UPDATE acwl_models SET model_type = 'EMBEDDING' WHERE model_type = 'Embedding'")
            result1 = await db.execute(update_embedding)
            print(f"   更新 Embedding -> EMBEDDING: {result1.rowcount} 条记录")
            
            # 更新 Multimodal -> MULTIMODAL
            update_multimodal = text("UPDATE acwl_models SET model_type = 'MULTIMODAL' WHERE model_type = 'Multimodal'")
            result2 = await db.execute(update_multimodal)
            print(f"   更新 Multimodal -> MULTIMODAL: {result2.rowcount} 条记录")
            
            # 更新 Other -> OTHER
            update_other = text("UPDATE acwl_models SET model_type = 'OTHER' WHERE model_type = 'Other'")
            result3 = await db.execute(update_other)
            print(f"   更新 Other -> OTHER: {result3.rowcount} 条记录")
            
            # 3. 移除旧的枚举值
            print("3. 移除旧的枚举值...")
            alter_enum_remove = text("""
                ALTER TABLE acwl_models 
                MODIFY COLUMN model_type ENUM('LLM', 'EMBEDDING', 'MULTIMODAL', 'OTHER') NOT NULL
            """)
            await db.execute(alter_enum_remove)
            print("   ✅ 已移除旧的枚举值")
            
            # 4. 验证结果
            print("4. 验证结果...")
            verify_query = text("SELECT id, name, model_type FROM acwl_models ORDER BY id")
            verify_result = await db.execute(verify_query)
            rows = verify_result.fetchall()
            
            print("\n最终数据:")
            print("ID\tName\t\t\tModel Type")
            print("-" * 50)
            
            for row in rows:
                print(f"{row[0]}\t{row[1][:20]:<20}\t{row[2]}")
            
            print("\n✅ 数据库修复完成!")
                
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(fix_database())