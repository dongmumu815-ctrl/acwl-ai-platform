#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多数据库连接管理器
支持多种数据库类型的连接池管理和会话管理
"""

import asyncio
import logging
from typing import Dict, Optional, Any, AsyncGenerator
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy import create_engine, text
import aiomysql
import asyncpg
import aiosqlite

from .multi_db_config import MultiDatabaseConfig, DatabaseConfig, DatabaseType

logger = logging.getLogger(__name__)


class DatabaseConnectionManager:
    """数据库连接管理器"""
    
    def __init__(self, db_config: DatabaseConfig):
        """
        初始化数据库连接管理器
        
        Args:
            db_config: 数据库配置对象
        """
        self.config = db_config
        self.async_engine = None
        self.sync_engine = None
        self.async_session_factory = None
        self.sync_session_factory = None
        self._connection_pool = None
        self._lock = asyncio.Lock()
    
    async def initialize(self):
        """初始化数据库连接和会话工厂"""
        try:
            # 创建异步引擎
            self.async_engine = create_async_engine(
                self.config.connection_url,
                pool_size=self.config.pool_size,
                max_overflow=self.config.max_overflow,
                pool_timeout=self.config.pool_timeout,
                pool_recycle=self.config.pool_recycle,
                pool_pre_ping=True,
                echo=False
            )
            
            # 创建同步引擎
            self.sync_engine = create_engine(
                self.config.sync_connection_url,
                pool_size=self.config.pool_size,
                max_overflow=self.config.max_overflow,
                pool_timeout=self.config.pool_timeout,
                pool_recycle=self.config.pool_recycle,
                pool_pre_ping=True,
                echo=False
            )
            
            # 创建会话工厂
            self.async_session_factory = async_sessionmaker(
                self.async_engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            
            self.sync_session_factory = sessionmaker(
                bind=self.sync_engine,
                autocommit=False,
                autoflush=False
            )
            
            logger.info(f"数据库连接管理器初始化成功: {self.config.name}")
            
        except Exception as e:
            logger.error(f"数据库连接管理器初始化失败: {self.config.name}, 错误: {e}")
            raise
    
    @asynccontextmanager
    async def get_async_session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        获取异步数据库会话
        
        Yields:
            AsyncSession: 异步数据库会话
        """
        if not self.async_session_factory:
            await self.initialize()
        
        session = self.async_session_factory()
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
    
    @asynccontextmanager
    async def get_sync_session(self):
        """
        获取同步数据库会话
        
        Yields:
            Session: 同步数据库会话
        """
        if not self.sync_session_factory:
            await self.initialize()
        
        session = self.sync_session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    async def execute_raw_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """
        执行原生SQL查询
        
        Args:
            query: SQL查询语句
            params: 查询参数
            
        Returns:
            Any: 查询结果
        """
        async with self.get_async_session() as session:
            result = await session.execute(text(query), params or {})
            if query.strip().upper().startswith('SELECT'):
                return result.fetchall()
            else:
                return result.rowcount
    
    async def test_connection(self) -> bool:
        """
        测试数据库连接
        
        Returns:
            bool: 连接是否成功
        """
        try:
            if self.config.type == DatabaseType.MYSQL:
                test_query = "SELECT 1"
            elif self.config.type == DatabaseType.POSTGRESQL:
                test_query = "SELECT 1"
            elif self.config.type == DatabaseType.SQLITE:
                test_query = "SELECT 1"
            elif self.config.type == DatabaseType.ORACLE:
                test_query = "SELECT 1 FROM DUAL"
            elif self.config.type == DatabaseType.SQLSERVER:
                test_query = "SELECT 1"
            else:
                return False
            
            await self.execute_raw_query(test_query)
            return True
            
        except Exception as e:
            logger.error(f"数据库连接测试失败: {self.config.name}, 错误: {e}")
            return False
    
    async def close(self):
        """关闭数据库连接"""
        try:
            if self.async_engine:
                await self.async_engine.dispose()
            if self.sync_engine:
                self.sync_engine.dispose()
            logger.info(f"数据库连接已关闭: {self.config.name}")
        except Exception as e:
            logger.error(f"关闭数据库连接失败: {self.config.name}, 错误: {e}")


class MultiDatabaseManager:
    """多数据库管理器"""
    
    def __init__(self, config_manager: MultiDatabaseConfig):
        """
        初始化多数据库管理器
        
        Args:
            config_manager: 多数据库配置管理器
        """
        self.config_manager = config_manager
        self.connection_managers: Dict[str, DatabaseConnectionManager] = {}
        self._lock = asyncio.Lock()
    
    async def initialize(self):
        """初始化所有数据库连接管理器"""
        async with self._lock:
            for db_name, db_config in self.config_manager.get_all_databases().items():
                if db_config.is_active:
                    try:
                        manager = DatabaseConnectionManager(db_config)
                        await manager.initialize()
                        self.connection_managers[db_name] = manager
                        logger.info(f"数据库管理器初始化成功: {db_name}")
                    except Exception as e:
                        logger.error(f"数据库管理器初始化失败: {db_name}, 错误: {e}")
    
    async def get_connection_manager(self, db_name: str) -> Optional[DatabaseConnectionManager]:
        """
        获取数据库连接管理器
        
        Args:
            db_name: 数据库名称
            
        Returns:
            DatabaseConnectionManager: 数据库连接管理器
        """
        if db_name not in self.connection_managers:
            # 尝试动态创建连接管理器
            db_config = self.config_manager.get_database(db_name)
            if db_config and db_config.is_active:
                async with self._lock:
                    if db_name not in self.connection_managers:
                        try:
                            manager = DatabaseConnectionManager(db_config)
                            await manager.initialize()
                            self.connection_managers[db_name] = manager
                        except Exception as e:
                            logger.error(f"动态创建数据库管理器失败: {db_name}, 错误: {e}")
                            return None
        
        return self.connection_managers.get(db_name)
    
    async def get_primary_connection_manager(self) -> Optional[DatabaseConnectionManager]:
        """
        获取主数据库连接管理器
        
        Returns:
            DatabaseConnectionManager: 主数据库连接管理器
        """
        primary_db = self.config_manager.get_primary_database()
        if primary_db:
            return await self.get_connection_manager(primary_db.name)
        return None
    
    async def get_connection_managers_by_tag(self, tag: str) -> Dict[str, DatabaseConnectionManager]:
        """
        根据业务标签获取数据库连接管理器
        
        Args:
            tag: 业务标签
            
        Returns:
            Dict[str, DatabaseConnectionManager]: 数据库连接管理器字典
        """
        managers = {}
        db_configs = self.config_manager.get_databases_by_tag(tag)
        
        for db_config in db_configs:
            manager = await self.get_connection_manager(db_config.name)
            if manager:
                managers[db_config.name] = manager
        
        return managers
    
    async def add_database(self, db_config: DatabaseConfig) -> bool:
        """
        添加新的数据库配置并初始化连接管理器
        
        Args:
            db_config: 数据库配置
            
        Returns:
            bool: 是否添加成功
        """
        try:
            # 添加到配置管理器
            if self.config_manager.add_database(db_config):
                # 创建连接管理器
                if db_config.is_active:
                    manager = DatabaseConnectionManager(db_config)
                    await manager.initialize()
                    
                    async with self._lock:
                        self.connection_managers[db_config.name] = manager
                
                logger.info(f"成功添加数据库: {db_config.name}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"添加数据库失败: {db_config.name}, 错误: {e}")
            return False
    
    async def remove_database(self, db_name: str) -> bool:
        """
        移除数据库配置和连接管理器
        
        Args:
            db_name: 数据库名称
            
        Returns:
            bool: 是否移除成功
        """
        try:
            # 关闭连接管理器
            if db_name in self.connection_managers:
                await self.connection_managers[db_name].close()
                
                async with self._lock:
                    del self.connection_managers[db_name]
            
            # 从配置管理器移除
            if self.config_manager.remove_database(db_name):
                logger.info(f"成功移除数据库: {db_name}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"移除数据库失败: {db_name}, 错误: {e}")
            return False
    
    async def test_all_connections(self) -> Dict[str, bool]:
        """
        测试所有数据库连接
        
        Returns:
            Dict[str, bool]: 数据库连接测试结果
        """
        results = {}
        
        for db_name, manager in self.connection_managers.items():
            results[db_name] = await manager.test_connection()
        
        return results
    
    async def close_all(self):
        """关闭所有数据库连接"""
        for db_name, manager in self.connection_managers.items():
            try:
                await manager.close()
            except Exception as e:
                logger.error(f"关闭数据库连接失败: {db_name}, 错误: {e}")
        
        self.connection_managers.clear()
        logger.info("所有数据库连接已关闭")


# 全局多数据库管理器实例
multi_db_manager = None


async def get_multi_db_manager() -> MultiDatabaseManager:
    """
    获取全局多数据库管理器实例
    
    Returns:
        MultiDatabaseManager: 多数据库管理器实例
    """
    global multi_db_manager
    
    if multi_db_manager is None:
        from .multi_db_config import multi_db_config
        multi_db_manager = MultiDatabaseManager(multi_db_config)
        await multi_db_manager.initialize()
    
    return multi_db_manager


async def get_db_session(db_name: str = "primary"):
    """
    获取指定数据库的会话
    
    Args:
        db_name: 数据库名称，默认为主数据库
        
    Yields:
        AsyncSession: 数据库会话
    """
    manager = await get_multi_db_manager()
    connection_manager = await manager.get_connection_manager(db_name)
    
    if not connection_manager:
        raise ValueError(f"未找到数据库连接管理器: {db_name}")
    
    async with connection_manager.get_async_session() as session:
        yield session