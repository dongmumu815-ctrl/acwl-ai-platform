#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复数据库中的load_balance_strategy枚举值问题
"""

import asyncio
import sys
import os
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.config import settings
from app.core.logger import logger


async def fix_load_balance_strategy_enum():
    """
    修复数据库中的load_balance_strategy枚举值
    """
    # 创建数据库引擎（使用aiomysql驱动）
    database_url = settings.database_url.replace("mysql+pymysql://", "mysql+aiomysql://")
    engine = create_async_engine(
        database_url,
        echo=True,
        pool_pre_ping=True
    )
    
    # 创建会话
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    try:
        async with async_session() as session:
            # 1. 查看当前表结构
            logger.info("查看acwl_executor_groups表的load_balance_strategy列结构...")
            result = await session.execute(text(
                "SHOW COLUMNS FROM acwl_executor_groups LIKE 'load_balance_strategy'"
            ))
            column_info = result.fetchone()
            if column_info:
                logger.info(f"当前列定义: {column_info}")
            
            # 2. 查看当前数据
            logger.info("查看当前数据...")
            result = await session.execute(text(
                "SELECT id, group_name, load_balance_strategy FROM acwl_executor_groups"
            ))
            rows = result.fetchall()
            for row in rows:
                logger.info(f"ID: {row[0]}, 分组: {row[1]}, 策略: {row[2]}")
            
            # 3. 直接重新定义枚举类型为小写值
            logger.info("重新定义load_balance_strategy列的枚举类型为小写值...")
            await session.execute(text(
                "ALTER TABLE acwl_executor_groups MODIFY COLUMN load_balance_strategy "
                "ENUM('round_robin', 'least_connections', 'resource_based', 'random', "
                "'least_load', 'weighted', 'consistent_hash') "
                "DEFAULT 'round_robin'"
            ))
            
            # 4. 验证修复结果
            logger.info("验证修复结果...")
            result = await session.execute(text(
                "SELECT id, group_name, load_balance_strategy FROM acwl_executor_groups"
            ))
            rows = result.fetchall()
            for row in rows:
                logger.info(f"修复后 - ID: {row[0]}, 分组: {row[1]}, 策略: {row[2]}")
            
            await session.commit()
            logger.info("load_balance_strategy枚举值修复完成！")
            
    except Exception as e:
        logger.error(f"修复失败: {e}")
        raise
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(fix_load_balance_strategy_enum())