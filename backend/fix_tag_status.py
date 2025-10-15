#!/usr/bin/env python3
"""
修复标签状态字段的枚举值
"""

import asyncio
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import engine
from sqlalchemy import text

async def fix_tag_status():
    """修复标签状态字段的枚举值"""
    
    try:
        async with engine.begin() as conn:
            print("开始修复标签状态字段...")
            
            # 删除现有的 status 字段
            print("删除现有的 status 字段...")
            try:
                await conn.execute(text("ALTER TABLE acwl_data_resource_tags DROP COLUMN status"))
            except Exception as e:
                print(f"删除 status 字段时出错（可能字段不存在）: {e}")
                # 继续执行，可能字段不存在
            
            # 重新添加 status 字段，使用正确的枚举值
            print("重新添加 status 字段...")
            await conn.execute(text("""
                ALTER TABLE acwl_data_resource_tags 
                ADD COLUMN status ENUM('ACTIVE', 'DISABLED') DEFAULT 'ACTIVE' 
                COMMENT '标签状态：ACTIVE-启用，DISABLED-禁用'
            """))
            
            # 为现有数据设置默认状态为 ACTIVE
            print("设置现有数据的默认状态...")
            await conn.execute(text("UPDATE acwl_data_resource_tags SET status = 'ACTIVE' WHERE status IS NULL"))
            
            # 添加索引以提高查询性能
            print("添加索引...")
            try:
                await conn.execute(text("CREATE INDEX idx_acwl_data_resource_tags_status ON acwl_data_resource_tags(status)"))
            except Exception as e:
                print(f"创建索引时出错（可能索引已存在）: {e}")
                # 继续执行，可能索引已存在
            
            print("标签状态字段修复完成！")
            
    except Exception as e:
        print(f"修复失败: {e}")
        raise
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(fix_tag_status())