#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库路由器
根据业务需求和规则智能选择合适的数据库
"""

import logging
from typing import Optional, List, Dict, Any, Callable
from enum import Enum
from dataclasses import dataclass
from abc import ABC, abstractmethod

from .multi_db_manager import MultiDatabaseManager, DatabaseConnectionManager
from .multi_db_config import DatabaseConfig

logger = logging.getLogger(__name__)


class RoutingStrategy(str, Enum):
    """路由策略枚举"""
    PRIMARY_ONLY = "primary_only"  # 仅使用主数据库
    TAG_BASED = "tag_based"  # 基于标签路由
    LOAD_BALANCE = "load_balance"  # 负载均衡
    CUSTOM = "custom"  # 自定义路由


@dataclass
class RoutingContext:
    """路由上下文"""
    operation_type: str  # 操作类型：read, write, delete, update
    table_name: Optional[str] = None  # 表名
    business_tag: Optional[str] = None  # 业务标签
    user_id: Optional[int] = None  # 用户ID
    tenant_id: Optional[str] = None  # 租户ID
    priority: int = 0  # 优先级
    custom_params: Optional[Dict[str, Any]] = None  # 自定义参数


class DatabaseRouter(ABC):
    """数据库路由器抽象基类"""
    
    @abstractmethod
    async def route(self, context: RoutingContext) -> Optional[str]:
        """
        根据路由上下文选择数据库
        
        Args:
            context: 路由上下文
            
        Returns:
            str: 数据库名称
        """
        pass


class PrimaryOnlyRouter(DatabaseRouter):
    """仅使用主数据库的路由器"""
    
    def __init__(self, db_manager: MultiDatabaseManager):
        self.db_manager = db_manager
    
    async def route(self, context: RoutingContext) -> Optional[str]:
        """
        总是返回主数据库
        
        Args:
            context: 路由上下文
            
        Returns:
            str: 主数据库名称
        """
        primary_db = self.db_manager.config_manager.get_primary_database()
        return primary_db.name if primary_db else None


class TagBasedRouter(DatabaseRouter):
    """基于标签的路由器"""
    
    def __init__(self, db_manager: MultiDatabaseManager):
        self.db_manager = db_manager
    
    async def route(self, context: RoutingContext) -> Optional[str]:
        """
        根据业务标签选择数据库
        
        Args:
            context: 路由上下文
            
        Returns:
            str: 数据库名称
        """
        if context.business_tag:
            # 根据业务标签查找数据库
            db_configs = self.db_manager.config_manager.get_databases_by_tag(context.business_tag)
            
            if db_configs:
                # 优先选择第一个匹配的数据库
                return db_configs[0].name
        
        # 如果没有找到匹配的标签，使用主数据库
        primary_db = self.db_manager.config_manager.get_primary_database()
        return primary_db.name if primary_db else None


class LoadBalanceRouter(DatabaseRouter):
    """负载均衡路由器"""
    
    def __init__(self, db_manager: MultiDatabaseManager):
        self.db_manager = db_manager
        self._round_robin_counter = 0
    
    async def route(self, context: RoutingContext) -> Optional[str]:
        """
        使用轮询方式进行负载均衡
        
        Args:
            context: 路由上下文
            
        Returns:
            str: 数据库名称
        """
        # 获取所有活跃的数据库
        all_dbs = [
            db_config for db_config in self.db_manager.config_manager.get_all_databases().values()
            if db_config.is_active
        ]
        
        if not all_dbs:
            return None
        
        # 读操作可以使用所有数据库，写操作优先使用主数据库
        if context.operation_type in ['read', 'select']:
            # 轮询选择数据库
            selected_db = all_dbs[self._round_robin_counter % len(all_dbs)]
            self._round_robin_counter += 1
            return selected_db.name
        else:
            # 写操作使用主数据库
            primary_db = self.db_manager.config_manager.get_primary_database()
            return primary_db.name if primary_db else all_dbs[0].name


class CustomRouter(DatabaseRouter):
    """自定义路由器"""
    
    def __init__(self, db_manager: MultiDatabaseManager, routing_func: Callable[[RoutingContext], Optional[str]]):
        self.db_manager = db_manager
        self.routing_func = routing_func
    
    async def route(self, context: RoutingContext) -> Optional[str]:
        """
        使用自定义路由函数
        
        Args:
            context: 路由上下文
            
        Returns:
            str: 数据库名称
        """
        try:
            return self.routing_func(context)
        except Exception as e:
            logger.error(f"自定义路由函数执行失败: {e}")
            # 回退到主数据库
            primary_db = self.db_manager.config_manager.get_primary_database()
            return primary_db.name if primary_db else None


class SmartDatabaseRouter:
    """智能数据库路由器"""
    
    def __init__(self, db_manager: MultiDatabaseManager, strategy: RoutingStrategy = RoutingStrategy.TAG_BASED):
        """
        初始化智能数据库路由器
        
        Args:
            db_manager: 多数据库管理器
            strategy: 路由策略
        """
        self.db_manager = db_manager
        self.strategy = strategy
        self.router = self._create_router(strategy)
        self.routing_rules: List[Dict[str, Any]] = []
    
    def _create_router(self, strategy: RoutingStrategy) -> DatabaseRouter:
        """
        根据策略创建路由器
        
        Args:
            strategy: 路由策略
            
        Returns:
            DatabaseRouter: 路由器实例
        """
        if strategy == RoutingStrategy.PRIMARY_ONLY:
            return PrimaryOnlyRouter(self.db_manager)
        elif strategy == RoutingStrategy.TAG_BASED:
            return TagBasedRouter(self.db_manager)
        elif strategy == RoutingStrategy.LOAD_BALANCE:
            return LoadBalanceRouter(self.db_manager)
        else:
            raise ValueError(f"不支持的路由策略: {strategy}")
    
    def set_custom_router(self, routing_func: Callable[[RoutingContext], Optional[str]]):
        """
        设置自定义路由函数
        
        Args:
            routing_func: 自定义路由函数
        """
        self.strategy = RoutingStrategy.CUSTOM
        self.router = CustomRouter(self.db_manager, routing_func)
    
    def add_routing_rule(self, rule: Dict[str, Any]):
        """
        添加路由规则
        
        Args:
            rule: 路由规则字典
                - condition: 条件函数或字典
                - target_db: 目标数据库名称
                - priority: 优先级（数字越大优先级越高）
        """
        self.routing_rules.append(rule)
        # 按优先级排序
        self.routing_rules.sort(key=lambda x: x.get('priority', 0), reverse=True)
    
    def _match_rule(self, context: RoutingContext, rule: Dict[str, Any]) -> bool:
        """
        检查路由上下文是否匹配规则
        
        Args:
            context: 路由上下文
            rule: 路由规则
            
        Returns:
            bool: 是否匹配
        """
        condition = rule.get('condition')
        
        if callable(condition):
            try:
                return condition(context)
            except Exception as e:
                logger.error(f"路由规则条件函数执行失败: {e}")
                return False
        
        elif isinstance(condition, dict):
            # 字典形式的条件匹配
            for key, value in condition.items():
                context_value = getattr(context, key, None)
                if context_value != value:
                    return False
            return True
        
        return False
    
    async def route(self, context: RoutingContext) -> Optional[DatabaseConnectionManager]:
        """
        根据路由上下文选择数据库连接管理器
        
        Args:
            context: 路由上下文
            
        Returns:
            DatabaseConnectionManager: 数据库连接管理器
        """
        try:
            # 首先检查自定义路由规则
            for rule in self.routing_rules:
                if self._match_rule(context, rule):
                    target_db = rule.get('target_db')
                    if target_db:
                        manager = await self.db_manager.get_connection_manager(target_db)
                        if manager:
                            logger.debug(f"使用路由规则选择数据库: {target_db}")
                            return manager
            
            # 使用默认路由策略
            db_name = await self.router.route(context)
            if db_name:
                manager = await self.db_manager.get_connection_manager(db_name)
                if manager:
                    logger.debug(f"使用默认策略选择数据库: {db_name}")
                    return manager
            
            # 回退到主数据库
            primary_manager = await self.db_manager.get_primary_connection_manager()
            if primary_manager:
                logger.debug("回退到主数据库")
                return primary_manager
            
            logger.error("无法找到可用的数据库连接")
            return None
            
        except Exception as e:
            logger.error(f"数据库路由失败: {e}")
            # 尝试回退到主数据库
            try:
                return await self.db_manager.get_primary_connection_manager()
            except Exception:
                return None
    
    async def route_by_tag(self, tag: str, operation_type: str = "read") -> Optional[DatabaseConnectionManager]:
        """
        根据业务标签路由数据库
        
        Args:
            tag: 业务标签
            operation_type: 操作类型
            
        Returns:
            DatabaseConnectionManager: 数据库连接管理器
        """
        context = RoutingContext(
            operation_type=operation_type,
            business_tag=tag
        )
        return await self.route(context)
    
    async def route_by_table(self, table_name: str, operation_type: str = "read") -> Optional[DatabaseConnectionManager]:
        """
        根据表名路由数据库
        
        Args:
            table_name: 表名
            operation_type: 操作类型
            
        Returns:
            DatabaseConnectionManager: 数据库连接管理器
        """
        context = RoutingContext(
            operation_type=operation_type,
            table_name=table_name
        )
        return await self.route(context)
    
    def get_routing_info(self) -> Dict[str, Any]:
        """
        获取路由器信息
        
        Returns:
            Dict[str, Any]: 路由器信息
        """
        return {
            "strategy": self.strategy.value,
            "rules_count": len(self.routing_rules),
            "available_databases": list(self.db_manager.connection_managers.keys())
        }


# 全局智能数据库路由器实例
smart_router = None


async def get_smart_router() -> SmartDatabaseRouter:
    """
    获取全局智能数据库路由器实例
    
    Returns:
        SmartDatabaseRouter: 智能数据库路由器实例
    """
    global smart_router
    
    if smart_router is None:
        from .multi_db_manager import get_multi_db_manager
        db_manager = await get_multi_db_manager()
        smart_router = SmartDatabaseRouter(db_manager)
    
    return smart_router


async def route_database(business_tag: Optional[str] = None, 
                        table_name: Optional[str] = None,
                        operation_type: str = "read",
                        **kwargs) -> Optional[DatabaseConnectionManager]:
    """
    便捷的数据库路由函数
    
    Args:
        business_tag: 业务标签
        table_name: 表名
        operation_type: 操作类型
        **kwargs: 其他路由参数
        
    Returns:
        DatabaseConnectionManager: 数据库连接管理器
    """
    router = await get_smart_router()
    
    context = RoutingContext(
        operation_type=operation_type,
        table_name=table_name,
        business_tag=business_tag,
        **kwargs
    )
    
    return await router.route(context)