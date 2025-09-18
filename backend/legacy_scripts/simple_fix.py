#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单修复：直接替换枚举值
"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text
from app.core.database import engine
from app.core.logger import logger

async def simple_fix():
    """
    简单修复：直接替换枚举值
    """
    try:
        async with engine.begin() as conn:
            logger.info("开始简单修复...")
            
            # 直接修改枚举类型为大写值
            logger.info("修改枚举类型为大写值...")
            await conn.execute(text(
                "ALTER TABLE acwl_executor_groups MODIFY COLUMN group_type "
                "ENUM('DEFAULT','GPU','CPU_INTENSIVE','MEMORY_INTENSIVE','CUSTOM','COMPUTE','IO_INTENSIVE') "
                "NOT NULL DEFAULT 'DEFAULT' COMMENT '分组类型'"
            ))
            
            logger.info("枚举值修复完成")
                
    except Exception as e:
        logger.error(f"修复失败: {e}")
        # 如果失败，尝试恢复原状态
        try:
            async with engine.begin() as conn:
                await conn.execute(text(
                    "ALTER TABLE acwl_executor_groups MODIFY COLUMN group_type "
                    "ENUM('default','gpu','cpu_intensive','memory_intensive','custom','compute','io_intensive') "
                    "NOT NULL DEFAULT 'default' COMMENT '分组类型'"
                ))
                logger.info("已恢复原枚举定义")
        except:
            pass
        raise

if __name__ == '__main__':
    asyncio.run(simple_fix())