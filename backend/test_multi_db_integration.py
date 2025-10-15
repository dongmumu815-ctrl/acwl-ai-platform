#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多数据库集成测试脚本

测试多数据库功能是否正确集成到现有项目中，包括：
1. 配置加载测试
2. 连接管理器测试
3. 路由功能测试
4. API接口测试

Author: System
Date: 2024
"""

import asyncio
import sys
import os
import logging
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_config_loading():
    """测试配置加载功能"""
    print("\n=== 测试1：配置加载 ===")
    
    try:
        from app.core.multi_db_config import multi_db_config
        
        # 获取所有数据库配置
        all_dbs = multi_db_config.get_all_databases()
        print(f"✅ 成功加载 {len(all_dbs)} 个数据库配置")
        
        for db_name, db_config in all_dbs.items():
            print(f"  - {db_name}: {db_config.type.value} @ {db_config.host}:{db_config.port}")
            print(f"    数据库: {db_config.database}")
            print(f"    业务标签: {db_config.business_tags}")
            print(f"    是否主库: {db_config.is_primary}")
            print(f"    是否激活: {db_config.is_active}")
            print()
        
        # 测试主数据库获取
        primary_db = multi_db_config.get_primary_database()
        if primary_db:
            print(f"✅ 主数据库: {primary_db.name}")
        else:
            print("❌ 未找到主数据库配置")
        
        # 测试按标签获取
        api_dbs = multi_db_config.get_databases_by_tag("api")
        print(f"✅ 找到 {len(api_dbs)} 个API相关数据库")
        
        return True
        
    except Exception as e:
        print(f"❌ 配置加载失败: {e}")
        return False


async def test_connection_manager():
    """测试连接管理器功能"""
    print("\n=== 测试2：连接管理器 ===")
    
    try:
        from app.core.multi_db_manager import get_multi_db_manager
        
        # 获取多数据库管理器
        db_manager = await get_multi_db_manager()
        print("✅ 多数据库管理器初始化成功")
        
        # 测试连接
        connection_results = await db_manager.test_all_connections()
        print("数据库连接测试结果:")
        
        success_count = 0
        for db_name, is_connected in connection_results.items():
            status = "✅ 连接成功" if is_connected else "❌ 连接失败"
            print(f"  - {db_name}: {status}")
            if is_connected:
                success_count += 1
        
        print(f"连接成功率: {success_count}/{len(connection_results)}")
        
        # 测试主数据库连接管理器
        primary_manager = await db_manager.get_primary_connection_manager()
        if primary_manager:
            print(f"✅ 主数据库连接管理器: {primary_manager.config.name}")
        else:
            print("❌ 未找到主数据库连接管理器")
        
        return success_count > 0
        
    except Exception as e:
        print(f"❌ 连接管理器测试失败: {e}")
        logger.exception("连接管理器异常")
        return False


async def test_smart_router():
    """测试智能路由功能"""
    print("\n=== 测试3：智能路由 ===")
    
    try:
        from app.core.db_router import get_smart_router, RoutingContext
        
        # 获取智能路由器
        router = await get_smart_router()
        print("✅ 智能路由器初始化成功")
        
        # 测试路由信息
        routing_info = router.get_routing_info()
        print(f"路由策略: {routing_info['strategy']}")
        print(f"路由规则数量: {routing_info['rules_count']}")
        print(f"可用数据库: {routing_info['available_databases']}")
        
        # 测试按标签路由
        api_manager = await router.route_by_tag("api", "read")
        if api_manager:
            print(f"✅ API标签路由到: {api_manager.config.name}")
        else:
            print("❌ API标签路由失败")
        
        # 测试按表名路由
        test_manager = await router.route_by_table("test_table", "write")
        if test_manager:
            print(f"✅ 表名路由到: {test_manager.config.name}")
        else:
            print("❌ 表名路由失败")
        
        return True
        
    except Exception as e:
        print(f"❌ 智能路由测试失败: {e}")
        logger.exception("智能路由异常")
        return False


async def test_sql_execution():
    """测试SQL执行功能"""
    print("\n=== 测试4：SQL执行 ===")
    
    try:
        from app.services.multi_db_service import execute_sql
        
        # 测试简单查询
        result = await execute_sql(
            query="SELECT 1 as test_value",
            business_tag="api"
        )
        print(f"✅ 简单查询结果: {result}")
        
        # 测试指定数据库查询
        result = await execute_sql(
            query="SELECT 'api_system' as db_name",
            db_name="api_system"
        )
        print(f"✅ 指定数据库查询结果: {result}")
        
        return True
        
    except Exception as e:
        print(f"❌ SQL执行测试失败: {e}")
        logger.exception("SQL执行异常")
        return False


async def test_api_endpoints():
    """测试API端点（模拟测试）"""
    print("\n=== 测试5：API端点 ===")
    
    try:
        # 这里只是验证模块能否正确导入
        from app.api.v1.multi_database import router
        print("✅ 多数据库API路由模块导入成功")
        
        # 检查路由数量
        route_count = len(router.routes)
        print(f"✅ 注册了 {route_count} 个API端点")
        
        # 列出主要端点
        main_endpoints = [
            "/databases",
            "/databases/{db_name}/test", 
            "/query",
            "/health"
        ]
        
        print("主要API端点:")
        for endpoint in main_endpoints:
            print(f"  - {endpoint}")
        
        return True
        
    except Exception as e:
        print(f"❌ API端点测试失败: {e}")
        logger.exception("API端点异常")
        return False


async def main():
    """主测试函数"""
    print("🚀 多数据库集成测试开始")
    print("=" * 50)
    
    test_results = []
    
    # 执行所有测试
    test_results.append(await test_config_loading())
    test_results.append(await test_connection_manager())
    test_results.append(await test_smart_router())
    test_results.append(await test_sql_execution())
    test_results.append(await test_api_endpoints())
    
    # 统计结果
    passed_tests = sum(test_results)
    total_tests = len(test_results)
    
    print("\n" + "=" * 50)
    print(f"📊 测试结果: {passed_tests}/{total_tests} 通过")
    
    if passed_tests == total_tests:
        print("🎉 所有测试通过！多数据库功能集成成功！")
        print("\n📝 使用说明:")
        print("1. 启动应用: python -m uvicorn app.main:app --reload --port 8082")
        print("2. 访问API文档: http://localhost:8082/docs")
        print("3. 测试健康检查: http://localhost:8082/api/v1/multi-db/health")
        print("4. 查看数据库配置: http://localhost:8082/api/v1/multi-db/databases")
    else:
        print("❌ 部分测试失败，请检查配置和连接")
        
        # 提供故障排除建议
        print("\n🔧 故障排除建议:")
        print("1. 检查 multi_db_config.json 配置文件")
        print("2. 确认数据库服务器可访问")
        print("3. 验证数据库用户名和密码")
        print("4. 检查网络连接和防火墙设置")
    
    return passed_tests == total_tests


if __name__ == "__main__":
    # 运行测试
    success = asyncio.run(main())
    sys.exit(0 if success else 1)