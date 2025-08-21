#!/usr/bin/env python3
"""
更新数据库中的模型类型数据
"""

import asyncio
import sys
sys.path.append('backend')

from app.core.database import get_db_context
from sqlalchemy import text

async def update_model_types():
    """
    更新数据库中的模型类型数据为全大写格式
    """
    try:
        async with get_db_context() as db:
            # 更新 Embedding -> EMBEDDING
            update_embedding = text("UPDATE acwl_models SET model_type = 'EMBEDDING' WHERE model_type = 'Embedding'")
            result1 = await db.execute(update_embedding)
            print(f"更新 Embedding -> EMBEDDING: {result1.rowcount} 条记录")
            
            # 更新 Multimodal -> MULTIMODAL
            update_multimodal = text("UPDATE acwl_models SET model_type = 'MULTIMODAL' WHERE model_type = 'Multimodal'")
            result2 = await db.execute(update_multimodal)
            print(f"更新 Multimodal -> MULTIMODAL: {result2.rowcount} 条记录")
            
            # 更新 Other -> OTHER
            update_other = text("UPDATE acwl_models SET model_type = 'OTHER' WHERE model_type = 'Other'")
            result3 = await db.execute(update_other)
            print(f"更新 Other -> OTHER: {result3.rowcount} 条记录")
            
            # 验证更新结果
            verify_query = text("SELECT id, name, model_type FROM acwl_models ORDER BY id")
            verify_result = await db.execute(verify_query)
            rows = verify_result.fetchall()
            
            print("\n更新后的数据:")
            print("ID\tName\t\t\tModel Type")
            print("-" * 50)
            
            for row in rows:
                print(f"{row[0]}\t{row[1][:20]:<20}\t{row[2]}")
            
            # 检查是否还有旧格式的数据
            old_format_query = text("SELECT COUNT(*) FROM acwl_models WHERE model_type IN ('Embedding', 'Multimodal', 'Other')")
            old_result = await db.execute(old_format_query)
            old_count = old_result.scalar()
            
            print(f"\n剩余旧格式记录数: {old_count}")
            
            if old_count == 0:
                print("✅ 所有数据已成功更新为全大写格式!")
            else:
                print("❌ 仍有数据未更新")
                
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(update_model_types())