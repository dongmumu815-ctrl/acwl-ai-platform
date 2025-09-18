#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查数据库中的实际数据
"""

import asyncio
import sys
import os
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import get_db
from sqlalchemy import text

async def check_database():
    """
    检查数据库中的实际数据
    """
    print(f"\n检查数据库 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    try:
        async for db in get_db():
            # 检查执行器分组的类型
            print("\n=== 执行器分组类型 ===")
            result = await db.execute(text("SELECT DISTINCT group_type FROM acwl_executor_groups"))
            group_types = result.fetchall()
            print("数据库中的分组类型:")
            for row in group_types:
                print(f"  - {row[0]}")
            
            # 检查调度器节点状态
            print("\n=== 调度器节点状态 ===")
            result = await db.execute(text("SELECT DISTINCT status FROM acwl_scheduler_nodes"))
            statuses = result.fetchall()
            print("数据库中的节点状态:")
            for row in statuses:
                print(f"  - {row[0]}")
            
            # 检查执行器节点状态
            print("\n=== 执行器节点状态 ===")
            result = await db.execute(text("SELECT DISTINCT status FROM acwl_executor_nodes"))
            statuses = result.fetchall()
            print("数据库中的执行器状态:")
            for row in statuses:
                print(f"  - {row[0]}")
            
            break
            
    except Exception as e:
        print(f"检查失败: {e}")
        import traceback
        traceback.print_exc()
    
    print(f"\n检查完成 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(check_database())