#!/usr/bin/env python3
"""
检查数据库中的模型类型数据
"""

import asyncio
import sys
sys.path.append('backend')

from app.core.database import get_db_context
from sqlalchemy import text

async def check_model_types():
    """
    检查数据库中的模型类型数据
    """
    try:
        # 获取数据库连接
        async with get_db_context() as db:
            # 查询所有模型的类型
            query = text("SELECT id, name, model_type FROM acwl_models ORDER BY id")
            result = await db.execute(query)
            rows = result.fetchall()
            
            print("数据库中的模型数据:")
            print("ID\tName\t\t\tModel Type")
            print("-" * 50)
            
            for row in rows:
                print(f"{row[0]}\t{row[1][:20]:<20}\t{row[2]}")
                
            # 检查是否有旧格式的枚举值
            old_format_query = text("SELECT COUNT(*) FROM acwl_models WHERE model_type IN ('Embedding', 'Multimodal', 'Other')")
            old_result = await db.execute(old_format_query)
            old_count = old_result.scalar()
            
            print(f"\n使用旧格式枚举值的记录数: {old_count}")
            
            if old_count > 0:
                print("\n需要更新的记录:")
                old_records_query = text("SELECT id, name, model_type FROM acwl_models WHERE model_type IN ('Embedding', 'Multimodal', 'Other')")
                old_records = await db.execute(old_records_query)
                for record in old_records.fetchall():
                    print(f"ID: {record[0]}, Name: {record[1]}, Type: {record[2]}")
        
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(check_model_types())