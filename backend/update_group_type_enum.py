#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
更新数据库中的group_type枚举值
从 'general' 更新为 'default'
"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text
from app.core.database import engine
from app.core.logger import logger

async def update_group_type_enum():
    """
    更新数据库中的group_type枚举值
    """
    try:
        async with engine.begin() as conn:
            # 查看当前的group_type值
            result = await conn.execute(text("SELECT id, group_name, group_type FROM acwl_executor_groups"))
            rows = result.fetchall()
            
            logger.info("当前分组信息:")
            for row in rows:
                logger.info(f"ID: {row[0]}, Name: {row[1]}, Type: {row[2]}")
            
            # 更新group_type字段值
            update_result = await conn.execute(
                text("UPDATE acwl_executor_groups SET group_type = 'default' WHERE group_type = 'general'")
            )
            
            logger.info(f"已更新 {update_result.rowcount} 行记录")
            
            # 再次查看修复后的值
            result = await conn.execute(text("SELECT id, group_name, group_type FROM acwl_executor_groups"))
            rows = result.fetchall()
            
            logger.info("修复后的分组信息:")
            for row in rows:
                logger.info(f"ID: {row[0]}, Name: {row[1]}, Type: {row[2]}")
            
            logger.info("数据库更新完成")
                
    except Exception as e:
        logger.error(f"数据库操作失败: {e}")
        raise

if __name__ == '__main__':
    asyncio.run(update_group_type_enum())