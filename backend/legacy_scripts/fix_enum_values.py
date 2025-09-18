#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复数据库中的枚举值，确保与代码定义一致
"""

import asyncio
from sqlalchemy import text
from app.core.database import get_db

async def fix_enum_values():
    """
    修复数据库中的枚举值
    """
    print("🔧 开始修复数据库枚举值...")
    
    async for db in get_db():
        try:
            # 检查当前枚举定义
            result = await db.execute(text("""
                SELECT COLUMN_TYPE 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = DATABASE() 
                AND TABLE_NAME = 'acwl_task_definitions' 
                AND COLUMN_NAME = 'task_type'
            """))
            current_enum = result.fetchone()
            print(f"当前 task_type 枚举定义: {current_enum[0] if current_enum else 'None'}")
            
            # 修改枚举定义，将 CUSTOM 改为 custom
            print("修改 task_type 枚举定义...")
            await db.execute(text("""
                ALTER TABLE acwl_task_definitions 
                MODIFY COLUMN task_type ENUM(
                    'data_sync', 'model_training', 'data_analysis', 'etl', 
                    'python_code', 'sql_query', 'condition', 'data_transform', 
                    'api_call', 'file_operation', 'email_send', 'custom'
                )
            """))
            
            # 更新数据中的 CUSTOM 值为 custom
            print("更新数据中的枚举值...")
            result = await db.execute(text("""
                UPDATE acwl_task_definitions 
                SET task_type = 'custom' 
                WHERE task_type = 'CUSTOM'
            """))
            print(f"更新了 {result.rowcount} 条记录")
            
            await db.commit()
            print("✅ 枚举值修复完成！")
            
        except Exception as e:
            print(f"❌ 修复失败: {e}")
            await db.rollback()
        finally:
            await db.close()
            break

if __name__ == "__main__":
    asyncio.run(fix_enum_values())