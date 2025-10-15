#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多数据库CRUD服务
提供统一的数据库操作接口，支持多数据库的增删改查操作
"""

import logging
from typing import Any, Dict, List, Optional, Union, Type, Generic, TypeVar
from sqlalchemy import text, select, insert, update, delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase
from pydantic import BaseModel

from app.core.db_router import route_database, RoutingContext
from app.core.multi_db_manager import get_multi_db_manager, DatabaseConnectionManager

logger = logging.getLogger(__name__)

# 泛型类型变量
ModelType = TypeVar("ModelType", bound=DeclarativeBase)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class MultiDatabaseCRUDService(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """多数据库CRUD服务基类"""
    
    def __init__(self, model: Type[ModelType]):
        """
        初始化CRUD服务
        
        Args:
            model: SQLAlchemy模型类
        """
        self.model = model
        self.table_name = model.__tablename__ if hasattr(model, '__tablename__') else model.__name__.lower()
    
    async def _get_session(self, 
                          business_tag: Optional[str] = None,
                          operation_type: str = "read",
                          db_name: Optional[str] = None) -> AsyncSession:
        """
        获取数据库会话
        
        Args:
            business_tag: 业务标签
            operation_type: 操作类型
            db_name: 指定数据库名称
            
        Returns:
            AsyncSession: 数据库会话
        """
        if db_name:
            # 直接使用指定的数据库
            db_manager = await get_multi_db_manager()
            connection_manager = await db_manager.get_connection_manager(db_name)
            if not connection_manager:
                raise ValueError(f"未找到数据库连接管理器: {db_name}")
        else:
            # 使用路由器选择数据库
            connection_manager = await route_database(
                business_tag=business_tag,
                table_name=self.table_name,
                operation_type=operation_type
            )
            if not connection_manager:
                raise ValueError("无法获取数据库连接管理器")
        
        return connection_manager.get_async_session()
    
    async def create(self, 
                    obj_in: CreateSchemaType,
                    business_tag: Optional[str] = None,
                    db_name: Optional[str] = None) -> ModelType:
        """
        创建记录
        
        Args:
            obj_in: 创建数据模型
            business_tag: 业务标签
            db_name: 指定数据库名称
            
        Returns:
            ModelType: 创建的记录
        """
        async with await self._get_session(business_tag, "write", db_name) as session:
            # 将Pydantic模型转换为字典
            if isinstance(obj_in, BaseModel):
                obj_data = obj_in.dict(exclude_unset=True)
            else:
                obj_data = obj_in
            
            # 创建模型实例
            db_obj = self.model(**obj_data)
            session.add(db_obj)
            await session.flush()
            await session.refresh(db_obj)
            
            logger.info(f"创建记录成功: {self.table_name}, ID: {getattr(db_obj, 'id', 'N/A')}")
            return db_obj
    
    async def get(self, 
                 id: Any,
                 business_tag: Optional[str] = None,
                 db_name: Optional[str] = None) -> Optional[ModelType]:
        """
        根据ID获取记录
        
        Args:
            id: 记录ID
            business_tag: 业务标签
            db_name: 指定数据库名称
            
        Returns:
            ModelType: 记录对象
        """
        async with await self._get_session(business_tag, "read", db_name) as session:
            result = await session.get(self.model, id)
            return result
    
    async def get_multi(self,
                       skip: int = 0,
                       limit: int = 100,
                       filters: Optional[Dict[str, Any]] = None,
                       business_tag: Optional[str] = None,
                       db_name: Optional[str] = None) -> List[ModelType]:
        """
        获取多条记录
        
        Args:
            skip: 跳过记录数
            limit: 限制记录数
            filters: 过滤条件
            business_tag: 业务标签
            db_name: 指定数据库名称
            
        Returns:
            List[ModelType]: 记录列表
        """
        async with await self._get_session(business_tag, "read", db_name) as session:
            query = select(self.model)
            
            # 应用过滤条件
            if filters:
                for key, value in filters.items():
                    if hasattr(self.model, key):
                        query = query.where(getattr(self.model, key) == value)
            
            # 应用分页
            query = query.offset(skip).limit(limit)
            
            result = await session.execute(query)
            return result.scalars().all()
    
    async def update(self,
                    id: Any,
                    obj_in: Union[UpdateSchemaType, Dict[str, Any]],
                    business_tag: Optional[str] = None,
                    db_name: Optional[str] = None) -> Optional[ModelType]:
        """
        更新记录
        
        Args:
            id: 记录ID
            obj_in: 更新数据
            business_tag: 业务标签
            db_name: 指定数据库名称
            
        Returns:
            ModelType: 更新后的记录
        """
        async with await self._get_session(business_tag, "write", db_name) as session:
            # 获取现有记录
            db_obj = await session.get(self.model, id)
            if not db_obj:
                return None
            
            # 准备更新数据
            if isinstance(obj_in, BaseModel):
                update_data = obj_in.dict(exclude_unset=True)
            else:
                update_data = obj_in
            
            # 更新字段
            for field, value in update_data.items():
                if hasattr(db_obj, field):
                    setattr(db_obj, field, value)
            
            await session.flush()
            await session.refresh(db_obj)
            
            logger.info(f"更新记录成功: {self.table_name}, ID: {id}")
            return db_obj
    
    async def delete(self,
                    id: Any,
                    business_tag: Optional[str] = None,
                    db_name: Optional[str] = None) -> bool:
        """
        删除记录
        
        Args:
            id: 记录ID
            business_tag: 业务标签
            db_name: 指定数据库名称
            
        Returns:
            bool: 是否删除成功
        """
        async with await self._get_session(business_tag, "write", db_name) as session:
            db_obj = await session.get(self.model, id)
            if not db_obj:
                return False
            
            await session.delete(db_obj)
            await session.flush()
            
            logger.info(f"删除记录成功: {self.table_name}, ID: {id}")
            return True
    
    async def count(self,
                   filters: Optional[Dict[str, Any]] = None,
                   business_tag: Optional[str] = None,
                   db_name: Optional[str] = None) -> int:
        """
        统计记录数量
        
        Args:
            filters: 过滤条件
            business_tag: 业务标签
            db_name: 指定数据库名称
            
        Returns:
            int: 记录数量
        """
        async with await self._get_session(business_tag, "read", db_name) as session:
            query = select(func.count(self.model.id))
            
            # 应用过滤条件
            if filters:
                for key, value in filters.items():
                    if hasattr(self.model, key):
                        query = query.where(getattr(self.model, key) == value)
            
            result = await session.execute(query)
            return result.scalar()
    
    async def exists(self,
                    id: Any,
                    business_tag: Optional[str] = None,
                    db_name: Optional[str] = None) -> bool:
        """
        检查记录是否存在
        
        Args:
            id: 记录ID
            business_tag: 业务标签
            db_name: 指定数据库名称
            
        Returns:
            bool: 记录是否存在
        """
        async with await self._get_session(business_tag, "read", db_name) as session:
            query = select(self.model.id).where(self.model.id == id)
            result = await session.execute(query)
            return result.first() is not None


class RawQueryService:
    """原生SQL查询服务"""
    
    @staticmethod
    async def execute_query(query: str,
                           params: Optional[Dict[str, Any]] = None,
                           business_tag: Optional[str] = None,
                           db_name: Optional[str] = None,
                           operation_type: str = "read") -> Any:
        """
        执行原生SQL查询
        
        Args:
            query: SQL查询语句
            params: 查询参数
            business_tag: 业务标签
            db_name: 指定数据库名称
            operation_type: 操作类型
            
        Returns:
            Any: 查询结果
        """
        # 获取数据库连接管理器
        if db_name:
            db_manager = await get_multi_db_manager()
            connection_manager = await db_manager.get_connection_manager(db_name)
            if not connection_manager:
                raise ValueError(f"未找到数据库连接管理器: {db_name}")
        else:
            connection_manager = await route_database(
                business_tag=business_tag,
                operation_type=operation_type
            )
            if not connection_manager:
                raise ValueError("无法获取数据库连接管理器")
        
        # 执行查询
        return await connection_manager.execute_raw_query(query, params)
    
    @staticmethod
    async def execute_batch_queries(queries: List[Dict[str, Any]],
                                   business_tag: Optional[str] = None,
                                   db_name: Optional[str] = None) -> List[Any]:
        """
        批量执行SQL查询
        
        Args:
            queries: 查询列表，每个元素包含 query 和 params
            business_tag: 业务标签
            db_name: 指定数据库名称
            
        Returns:
            List[Any]: 查询结果列表
        """
        results = []
        
        for query_info in queries:
            query = query_info.get('query')
            params = query_info.get('params')
            operation_type = query_info.get('operation_type', 'read')
            
            if not query:
                continue
            
            try:
                result = await RawQueryService.execute_query(
                    query=query,
                    params=params,
                    business_tag=business_tag,
                    db_name=db_name,
                    operation_type=operation_type
                )
                results.append(result)
            except Exception as e:
                logger.error(f"批量查询执行失败: {query}, 错误: {e}")
                results.append(None)
        
        return results


class DatabaseSwitchService:
    """数据库切换服务"""
    
    @staticmethod
    async def get_available_databases() -> Dict[str, Dict[str, Any]]:
        """
        获取所有可用的数据库信息
        
        Returns:
            Dict[str, Dict[str, Any]]: 数据库信息字典
        """
        db_manager = await get_multi_db_manager()
        databases_info = {}
        
        for db_name, connection_manager in db_manager.connection_managers.items():
            config = connection_manager.config
            databases_info[db_name] = {
                "name": config.name,
                "type": config.type.value,
                "host": config.host,
                "port": config.port,
                "database": config.database,
                "business_tags": config.business_tags,
                "is_primary": config.is_primary,
                "is_active": config.is_active
            }
        
        return databases_info
    
    @staticmethod
    async def test_database_connection(db_name: str) -> bool:
        """
        测试指定数据库的连接
        
        Args:
            db_name: 数据库名称
            
        Returns:
            bool: 连接是否成功
        """
        db_manager = await get_multi_db_manager()
        connection_manager = await db_manager.get_connection_manager(db_name)
        
        if not connection_manager:
            return False
        
        return await connection_manager.test_connection()
    
    @staticmethod
    async def test_all_connections() -> Dict[str, bool]:
        """
        测试所有数据库连接
        
        Returns:
            Dict[str, bool]: 连接测试结果
        """
        db_manager = await get_multi_db_manager()
        return await db_manager.test_all_connections()


# 便捷函数
async def create_crud_service(model: Type[ModelType]) -> MultiDatabaseCRUDService:
    """
    创建CRUD服务实例
    
    Args:
        model: SQLAlchemy模型类
        
    Returns:
        MultiDatabaseCRUDService: CRUD服务实例
    """
    return MultiDatabaseCRUDService(model)


async def execute_sql(query: str,
                     params: Optional[Dict[str, Any]] = None,
                     business_tag: Optional[str] = None,
                     db_name: Optional[str] = None) -> Any:
    """
    便捷的SQL执行函数
    
    Args:
        query: SQL查询语句
        params: 查询参数
        business_tag: 业务标签
        db_name: 指定数据库名称
        
    Returns:
        Any: 查询结果
    """
    operation_type = "write" if any(keyword in query.upper() for keyword in ["INSERT", "UPDATE", "DELETE"]) else "read"
    
    return await RawQueryService.execute_query(
        query=query,
        params=params,
        business_tag=business_tag,
        db_name=db_name,
        operation_type=operation_type
    )