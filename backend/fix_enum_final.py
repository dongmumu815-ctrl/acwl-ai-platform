#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最终修复数据库枚举值问题
"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text
from app.core.database import engine
from app.core.logger import logger

async def fix_enum_final():
    """
    最终修复枚举值问题
    """
    try:
        async with engine.begin() as conn:
            logger.info("开始最终修复枚举值问题...")
            
            # 1. 先修改枚举类型，添加所有可能的值（大写和小写）
            logger.info("修改枚举类型，添加大写值...")
            await conn.execute(text(
                "ALTER TABLE acwl_executor_groups MODIFY COLUMN group_type "
                "ENUM('default','gpu','cpu_intensive','memory_intensive','custom','compute','io_intensive',"
                "'DEFAULT','GPU','CPU_INTENSIVE','MEMORY_INTENSIVE','CUSTOM','COMPUTE','IO_INTENSIVE') "
                "NOT NULL DEFAULT 'DEFAULT' COMMENT '分组类型'"
            ))
            
            # 2. 更新现有数据为大写
            logger.info("更新现有数据为大写...")
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
            
            # 3. 查看更新后的数据
            result = await conn.execute(text("SELECT id, group_name, group_type FROM acwl_executor_groups"))
            rows = result.fetchall()
            
            logger.info("更新后的分组信息:")
            for row in rows:
                logger.info(f"ID: {row[0]}, Name: {row[1]}, Type: {row[2]}")
            
            # 4. 最后移除小写的枚举值
            logger.info("移除小写的枚举值...")
            await conn.execute(text(
                "ALTER TABLE acwl_executor_groups MODIFY COLUMN group_type "
                "ENUM('DEFAULT','GPU','CPU_INTENSIVE','MEMORY_INTENSIVE','CUSTOM','COMPUTE','IO_INTENSIVE') "
                "NOT NULL DEFAULT 'DEFAULT' COMMENT '分组类型'"
            ))
            
            logger.info("枚举值最终修复完成")
                
    except Exception as e:
        logger.error(f"修复失败: {e}")
        raise

if __name__ == '__main__':
    asyncio.run(fix_enum_final())