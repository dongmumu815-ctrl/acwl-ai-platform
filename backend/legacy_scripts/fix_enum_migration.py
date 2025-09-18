#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复数据库枚举值问题
先修改枚举定义，再更新数据
"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text
from app.core.database import engine
from app.core.logger import logger

async def fix_enum_migration():
    """
    修复枚举值问题
    """
    try:
        async with engine.begin() as conn:
            logger.info("开始修复枚举值问题...")
            
            # 1. 先查看当前表结构
            result = await conn.execute(text("SHOW CREATE TABLE acwl_executor_groups"))
            table_def = result.fetchone()
            logger.info(f"当前表结构: {table_def[1]}")
            
            # 2. 修改枚举类型，添加新值
            logger.info("修改枚举类型，添加 'default' 值...")
            await conn.execute(text(
                "ALTER TABLE acwl_executor_groups MODIFY COLUMN group_type "
                "ENUM('general','gpu','cpu_intensive','memory_intensive','custom','default','compute','io_intensive') "
                "NOT NULL DEFAULT 'default' COMMENT '分组类型'"
            ))
            
            # 3. 更新现有数据
            logger.info("更新现有数据...")
            update_result = await conn.execute(
                text("UPDATE acwl_executor_groups SET group_type = 'default' WHERE group_type = 'general'")
            )
            logger.info(f"已更新 {update_result.rowcount} 行记录")
            
            # 4. 查看更新后的数据
            result = await conn.execute(text("SELECT id, group_name, group_type FROM acwl_executor_groups"))
            rows = result.fetchall()
            
            logger.info("更新后的分组信息:")
            for row in rows:
                logger.info(f"ID: {row[0]}, Name: {row[1]}, Type: {row[2]}")
            
            # 5. 最后移除旧的枚举值
            logger.info("移除旧的枚举值...")
            await conn.execute(text(
                "ALTER TABLE acwl_executor_groups MODIFY COLUMN group_type "
                "ENUM('default','gpu','cpu_intensive','memory_intensive','custom','compute','io_intensive') "
                "NOT NULL DEFAULT 'default' COMMENT '分组类型'"
            ))
            
            logger.info("枚举值修复完成")
                
    except Exception as e:
        logger.error(f"修复失败: {e}")
        raise

if __name__ == '__main__':
    asyncio.run(fix_enum_migration())