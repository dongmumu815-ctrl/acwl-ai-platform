#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多数据库使用示例
演示如何使用多数据库功能进行增删改查操作
"""

import asyncio
import logging
from typing import List, Dict, Any

# 导入多数据库相关模块
from app.core.multi_db_config import DatabaseConfig, DatabaseType, multi_db_config
from app.core.multi_db_manager import get_multi_db_manager
from app.core.db_router import get_smart_router, RoutingContext
from app.services.multi_db_service import (
    MultiDatabaseCRUDService,
    RawQueryService,
    DatabaseSwitchService,
    execute_sql
)

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def example_1_basic_configuration():
    """示例1：基本配置管理"""
    print("\n=== 示例1：基本配置管理 ===")
    
    # 添加新的数据库配置
    new_db_config = DatabaseConfig(
        name="test_db",
        type=DatabaseType.MYSQL,
        host="localhost",
        port=3306,
        username="root",
        password="password",
        database="test_database",
        business_tags=["test", "development"],
        is_primary=False
    )
    
    # 添加配置
    success = multi_db_config.add_database(new_db_config)
    print(f"添加数据库配置: {'成功' if success else '失败'}")
    
    # 获取所有数据库配置
    all_dbs = multi_db_config.get_all_databases()
    print(f"当前配置的数据库数量: {len(all_dbs)}")
    
    for db_name, db_config in all_dbs.items():
        print(f"  - {db_name}: {db_config.type.value} @ {db_config.host}:{db_config.port}")


async def example_2_connection_management():
    """示例2：连接管理"""
    print("\n=== 示例2：连接管理 ===")
    
    # 获取多数据库管理器
    db_manager = await get_multi_db_manager()
    
    # 测试所有数据库连接
    connection_results = await db_manager.test_all_connections()
    print("数据库连接测试结果:")
    for db_name, is_connected in connection_results.items():
        status = "✅ 连接成功" if is_connected else "❌ 连接失败"
        print(f"  - {db_name}: {status}")
    
    # 获取主数据库连接管理器
    primary_manager = await db_manager.get_primary_connection_manager()
    if primary_manager:
        print(f"主数据库: {primary_manager.config.name}")


async def example_3_smart_routing():
    """示例3：智能路由"""
    print("\n=== 示例3：智能路由 ===")
    
    # 获取智能路由器
    router = await get_smart_router()
    
    # 根据业务标签路由
    analytics_manager = await router.route_by_tag("analytics", "read")
    if analytics_manager:
        print(f"分析业务路由到: {analytics_manager.config.name}")
    
    # 根据表名路由
    logs_manager = await router.route_by_table("system_logs", "write")
    if logs_manager:
        print(f"日志表路由到: {logs_manager.config.name}")
    
    # 自定义路由规则
    def custom_routing_rule(context: RoutingContext) -> bool:
        """自定义路由规则：用户ID为偶数的使用analytics数据库"""
        return context.user_id is not None and context.user_id % 2 == 0
    
    router.add_routing_rule({
        "condition": custom_routing_rule,
        "target_db": "analytics",
        "priority": 10
    })
    
    # 测试自定义路由
    context = RoutingContext(
        operation_type="read",
        user_id=42,
        table_name="user_data"
    )
    
    routed_manager = await router.route(context)
    if routed_manager:
        print(f"用户ID 42 路由到: {routed_manager.config.name}")


async def example_4_raw_sql_operations():
    """示例4：原生SQL操作"""
    print("\n=== 示例4：原生SQL操作 ===")
    
    try:
        # 执行查询（自动路由到合适的数据库）
        result = await execute_sql(
            query="SELECT 1 as test_value",
            business_tag="primary"
        )
        print(f"查询结果: {result}")
        
        # 执行带参数的查询
        result = await execute_sql(
            query="SELECT ? as param_value",
            params={"param_value": "Hello World"},
            db_name="primary"
        )
        print(f"参数化查询结果: {result}")
        
        # 批量查询
        queries = [
            {"query": "SELECT 1 as first", "operation_type": "read"},
            {"query": "SELECT 2 as second", "operation_type": "read"},
            {"query": "SELECT 3 as third", "operation_type": "read"}
        ]
        
        batch_results = await RawQueryService.execute_batch_queries(
            queries=queries,
            business_tag="primary"
        )
        print(f"批量查询结果: {batch_results}")
        
    except Exception as e:
        print(f"SQL操作失败: {e}")


async def example_5_database_switching():
    """示例5：数据库切换和管理"""
    print("\n=== 示例5：数据库切换和管理 ===")
    
    # 获取所有可用数据库信息
    databases_info = await DatabaseSwitchService.get_available_databases()
    print("可用数据库:")
    for db_name, db_info in databases_info.items():
        print(f"  - {db_name}: {db_info['type']} @ {db_info['host']}:{db_info['port']}")
    
    # 测试特定数据库连接
    for db_name in databases_info.keys():
        is_connected = await DatabaseSwitchService.test_database_connection(db_name)
        status = "✅" if is_connected else "❌"
        print(f"  {status} {db_name}")


async def example_6_crud_operations():
    """示例6：CRUD操作（需要实际的模型类）"""
    print("\n=== 示例6：CRUD操作示例 ===")
    
    # 注意：这里需要实际的SQLAlchemy模型类
    # 由于没有具体的模型，这里只展示使用方式
    
    print("CRUD操作需要具体的SQLAlchemy模型类")
    print("使用方式示例:")
    print("""
    from app.models.user import User  # 假设有User模型
    from app.schemas.user import UserCreate, UserUpdate  # 假设有对应的schema
    
    # 创建CRUD服务
    user_service = MultiDatabaseCRUDService[User, UserCreate, UserUpdate](User)
    
    # 创建用户（自动路由到写数据库）
    new_user = await user_service.create(
        UserCreate(name="张三", email="zhangsan@example.com"),
        business_tag="user_management"
    )
    
    # 查询用户（自动路由到读数据库）
    user = await user_service.get(
        id=1,
        business_tag="user_management"
    )
    
    # 更新用户
    updated_user = await user_service.update(
        id=1,
        obj_in=UserUpdate(name="李四"),
        business_tag="user_management"
    )
    
    # 删除用户
    success = await user_service.delete(
        id=1,
        business_tag="user_management"
    )
    """)


async def example_7_api_usage():
    """示例7：API使用方式"""
    print("\n=== 示例7：API使用方式 ===")
    
    print("多数据库API端点已创建，可以通过HTTP请求使用:")
    print("""
    # 获取所有数据库配置
    GET /api/v1/multi-db/databases
    
    # 创建新数据库配置
    POST /api/v1/multi-db/databases
    {
        "name": "new_db",
        "type": "mysql",
        "host": "localhost",
        "port": 3306,
        "username": "root",
        "password": "password",
        "database": "new_database",
        "business_tags": ["new", "test"]
    }
    
    # 测试数据库连接
    GET /api/v1/multi-db/databases/primary/test
    
    # 执行SQL查询
    POST /api/v1/multi-db/query
    {
        "query": "SELECT * FROM users LIMIT 10",
        "business_tag": "user_management"
    }
    
    # 简单查询
    GET /api/v1/multi-db/query/simple?sql=SELECT 1&db_name=primary
    
    # 健康检查
    GET /api/v1/multi-db/health
    """)


async def main():
    """主函数：运行所有示例"""
    print("🚀 多数据库功能使用示例")
    print("=" * 50)
    
    try:
        await example_1_basic_configuration()
        await example_2_connection_management()
        await example_3_smart_routing()
        await example_4_raw_sql_operations()
        await example_5_database_switching()
        await example_6_crud_operations()
        await example_7_api_usage()
        
        print("\n✅ 所有示例运行完成！")
        
    except Exception as e:
        print(f"\n❌ 示例运行失败: {e}")
        logger.exception("示例运行异常")


if __name__ == "__main__":
    # 运行示例
    asyncio.run(main())