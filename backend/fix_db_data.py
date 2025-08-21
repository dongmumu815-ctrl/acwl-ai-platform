#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复数据库中的枚举值数据
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


async def fix_db_data():
    """
    修复数据库中的枚举值数据
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
            # 1. 查看当前数据
            logger.info("查看当前数据...")
            result = await session.execute(text(
                "SELECT id, group_name, load_balance_strategy FROM acwl_executor_groups"
            ))
            rows = result.fetchall()
            for row in rows:
                logger.info(f"修复前 - ID: {row[0]}, 分组: {row[1]}, 策略: {row[2]}")
            
            # 2. 更新数据为大写值
            logger.info("更新数据为大写值...")
            
            # 更新各种可能的小写值为大写
            updates = [
                ("round_robin", "ROUND_ROBIN"),
                ("least_connections", "LEAST_CONNECTIONS"),
                ("resource_based", "RESOURCE_BASED"),
                ("random", "RANDOM"),
                ("least_load", "LEAST_LOAD"),
                ("weighted", "WEIGHTED"),
                ("consistent_hash", "CONSISTENT_HASH")
            ]
            
            for old_value, new_value in updates:
                result = await session.execute(text(
                    f"UPDATE acwl_executor_groups SET load_balance_strategy = '{new_value}' "
                    f"WHERE load_balance_strategy = '{old_value}'"
                ))
                if result.rowcount > 0:
                    logger.info(f"已更新 {result.rowcount} 行: {old_value} -> {new_value}")
            
            # 3. 验证修复结果
            logger.info("验证修复结果...")
            result = await session.execute(text(
                "SELECT id, group_name, load_balance_strategy FROM acwl_executor_groups"
            ))
            rows = result.fetchall()
            for row in rows:
                logger.info(f"修复后 - ID: {row[0]}, 分组: {row[1]}, 策略: {row[2]}")
            
            await session.commit()
            logger.info("数据修复完成！")
            
    except Exception as e:
        logger.error(f"修复失败: {e}")
        raise
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(fix_db_data())