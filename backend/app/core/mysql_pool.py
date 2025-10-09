#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MySQL连接池管理器
用于管理MySQL数据源连接，避免'Too many connections'错误
"""

import asyncio
import logging
from typing import Dict, Optional
from contextlib import asynccontextmanager
import aiomysql
from app.core.security import decrypt_datasource_password

logger = logging.getLogger(__name__)

class MySQLConnectionPool:
    """
    MySQL连接池管理器
    为每个数据源维护一个连接池，避免频繁创建和销毁连接
    """
    
    def __init__(self):
        self._pools: Dict[str, aiomysql.Pool] = {}
        self._lock = asyncio.Lock()
    
    def _get_pool_key(self, datasource) -> str:
        """
        生成数据源的唯一标识符
        
        Args:
            datasource: 数据源对象
            
        Returns:
            str: 数据源唯一标识符
        """
        return f"{datasource.host}:{datasource.port}:{datasource.username}:{datasource.database_name or ''}"
    
    async def get_pool(self, datasource) -> aiomysql.Pool:
        """
        获取或创建数据源的连接池
        
        Args:
            datasource: 数据源对象
            
        Returns:
            aiomysql.Pool: 连接池对象
        """
        pool_key = self._get_pool_key(datasource)
        
        async with self._lock:
            if pool_key not in self._pools:
                try:
                    # 解密密码
                    password = decrypt_datasource_password(datasource.password) if datasource.password else None
                    
                    # 创建连接池
                    pool = await aiomysql.create_pool(
                        host=datasource.host,
                        port=datasource.port or 3306,
                        user=datasource.username,
                        password=password,
                        db=datasource.database_name,
                        minsize=1,           # 最小连接数
                        maxsize=5,           # 最大连接数，避免过多连接
                        pool_recycle=3600,   # 连接回收时间（秒）
                        connect_timeout=30,  # 连接超时
                        autocommit=True,     # 自动提交
                        charset='utf8mb4'    # 字符集
                    )
                    
                    self._pools[pool_key] = pool
                    logger.info(f"为数据源 {pool_key} 创建了连接池")
                    
                except Exception as e:
                    logger.error(f"创建数据源 {pool_key} 的连接池失败: {str(e)}")
                    raise
            
            return self._pools[pool_key]
    
    @asynccontextmanager
    async def get_connection(self, datasource):
        """
        获取数据库连接的上下文管理器
        
        Args:
            datasource: 数据源对象
            
        Yields:
            aiomysql.Connection: 数据库连接
        """
        pool = await self.get_pool(datasource)
        connection = None
        
        try:
            # 从连接池获取连接
            connection = await pool.acquire()
            yield connection
        except Exception as e:
            logger.error(f"获取数据库连接失败: {str(e)}")
            raise
        finally:
            # 将连接返回到连接池
            if connection:
                try:
                    pool.release(connection)
                except Exception as e:
                    logger.warning(f"释放数据库连接失败: {str(e)}")
    
    async def close_pool(self, datasource):
        """
        关闭指定数据源的连接池
        
        Args:
            datasource: 数据源对象
        """
        pool_key = self._get_pool_key(datasource)
        
        async with self._lock:
            if pool_key in self._pools:
                pool = self._pools.pop(pool_key)
                try:
                    pool.close()
                    await pool.wait_closed()
                    logger.info(f"已关闭数据源 {pool_key} 的连接池")
                except Exception as e:
                    logger.error(f"关闭数据源 {pool_key} 的连接池失败: {str(e)}")
    
    async def close_all_pools(self):
        """
        关闭所有连接池
        """
        async with self._lock:
            for pool_key, pool in list(self._pools.items()):
                try:
                    pool.close()
                    await pool.wait_closed()
                    logger.info(f"已关闭连接池: {pool_key}")
                except Exception as e:
                    logger.error(f"关闭连接池 {pool_key} 失败: {str(e)}")
            
            self._pools.clear()
            logger.info("所有MySQL连接池已关闭")

# 全局连接池管理器实例
mysql_pool_manager = MySQLConnectionPool()

# 注意：连接池的清理应该在应用的lifespan中处理，而不是在atexit中
# 因为atexit时事件循环可能已经关闭，无法执行异步操作