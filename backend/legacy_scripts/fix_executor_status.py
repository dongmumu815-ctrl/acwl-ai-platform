#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复执行器节点状态枚举值

将数据库中的小写状态值更新为大写
"""

import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text
from app.core.database import engine
from app.core.logger import logger


async def fix_executor_status():
    """
    修复执行器节点状态枚举值
    """
    
    async with engine.begin() as conn:
        # 查询当前状态值
        result = await conn.execute(
            text("SELECT DISTINCT status FROM acwl_executor_nodes")
        )
        current_statuses = [row[0] for row in result.fetchall()]
        logger.info(f"当前状态值: {current_statuses}")
        
        # 更新状态值映射
        status_mapping = {
            'online': 'ONLINE',
            'offline': 'OFFLINE', 
            'busy': 'BUSY',
            'idle': 'IDLE',
            'maintenance': 'MAINTENANCE',
            'error': 'ERROR'
        }
        
        # 更新每个状态值
        for old_status, new_status in status_mapping.items():
            if old_status in current_statuses:
                await conn.execute(
                    text("UPDATE acwl_executor_nodes SET status = :new_status WHERE status = :old_status"),
                    {"new_status": new_status, "old_status": old_status}
                )
                logger.info(f"已更新状态: {old_status} -> {new_status}")
        
        # 验证修复结果
        result = await conn.execute(
            text("SELECT DISTINCT status FROM acwl_executor_nodes")
        )
        updated_statuses = [row[0] for row in result.fetchall()]
        logger.info(f"修复后状态值: {updated_statuses}")
        
        # 修改枚举类型定义
        logger.info("正在修改枚举类型定义...")
        await conn.execute(
            text("ALTER TABLE acwl_executor_nodes MODIFY COLUMN status ENUM('ONLINE', 'OFFLINE', 'BUSY', 'IDLE', 'MAINTENANCE', 'ERROR') NOT NULL DEFAULT 'OFFLINE'")
        )
        logger.info("枚举类型定义已更新")
        
        # 最终验证
        result = await conn.execute(
            text("SELECT DISTINCT status FROM acwl_executor_nodes")
        )
        final_statuses = [row[0] for row in result.fetchall()]
        logger.info(f"最终状态值: {final_statuses}")
        
    # 不需要手动dispose，因为engine是全局的
    logger.info("执行器状态枚举值修复完成")


if __name__ == "__main__":
    asyncio.run(fix_executor_status())