#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
将数据库中的group_type值更新为大写
"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text
from app.core.database import engine
from app.core.logger import logger

async def update_to_uppercase():
    """
    将数据库中的group_type值更新为大写
    """
    try:
        async with engine.begin() as conn:
            logger.info("开始更新group_type值为大写...")
            
            # 查看当前数据
            result = await conn.execute(text("SELECT id, group_name, group_type FROM acwl_executor_groups"))
            rows = result.fetchall()
            
            logger.info("当前分组信息:")
            for row in rows:
                logger.info(f"ID: {row[0]}, Name: {row[1]}, Type: {row[2]}")
            
            # 更新所有小写值为大写
            mappings = {
                'default': 'DEFAULT',
                'gpu': 'GPU', 
                'cpu_intensive': 'CPU_INTENSIVE',
                'memory_intensive': 'MEMORY_INTENSIVE',
                'custom': 'CUSTOM',
                'compute': 'COMPUTE',
                'io_intensive': 'IO_INTENSIVE'
            }
            
            for old_val, new_val in mappings.items():
                update_result = await conn.execute(
                    text(f"UPDATE acwl_executor_groups SET group_type = '{new_val}' WHERE group_type = '{old_val}'")
                )
                if update_result.rowcount > 0:
                    logger.info(f"已更新 {update_result.rowcount} 行记录: {old_val} -> {new_val}")
            
            # 查看更新后的数据
            result = await conn.execute(text("SELECT id, group_name, group_type FROM acwl_executor_groups"))
            rows = result.fetchall()
            
            logger.info("更新后的分组信息:")
            for row in rows:
                logger.info(f"ID: {row[0]}, Name: {row[1]}, Type: {row[2]}")
            
            logger.info("数据库更新完成")
                
    except Exception as e:
        logger.error(f"更新失败: {e}")
        raise

if __name__ == '__main__':
    asyncio.run(update_to_uppercase())