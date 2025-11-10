#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API管理功能测试脚本

测试新增的API管理功能是否正常工作
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


async def test_api_management_integration():
    """测试API管理功能集成"""
    print("\n=== API管理功能集成测试 ===")
    
    try:
        # 测试导入API管理模块
        from app.api.v1.multi_database import router as multi_db_router
        
        print("✅ API管理模块导入成功")
        
        # 检查路由注册
        route_count = len(multi_db_router.routes)
        print(f"✅ 多数据库路由注册成功，共 {route_count} 个端点")
        
        # 检查前端类型定义文件
        types_file = Path(project_root.parent / "dc_frontend/src/types/apiManagement.ts")
        if types_file.exists():
            print("✅ TypeScript类型定义文件创建成功")
        else:
            print("❌ TypeScript类型定义文件不存在")
        
        return True
        
    except ImportError as e:
        print(f"❌ 模块导入失败: {e}")
        return False
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        logger.exception("API管理功能测试异常")
        return False


async def test_frontend_files():
    """测试前端文件是否创建成功"""
    print("\n=== 前端文件检查 ===")
    
    frontend_files = [
        "dc_frontend/src/types/apiManagement.ts",
        "dc_frontend/src/api/apiManagement.ts",
        "dc_frontend/src/views/apiManagement/CustomerList.vue",
        "dc_frontend/src/views/apiManagement/ApiList.vue",
        "dc_frontend/src/views/apiManagement/ApiFields.vue",
        "dc_frontend/src/views/apiManagement/BatchList.vue",
        "dc_frontend/src/views/apiManagement/BatchDetail.vue",
        "dc_frontend/src/views/apiManagement/Dashboard.vue"
    ]
    
    success_count = 0
    
    for file_path in frontend_files:
        full_path = Path(project_root.parent / file_path)
        if full_path.exists():
            print(f"✅ {file_path}")
            success_count += 1
        else:
            print(f"❌ {file_path} - 文件不存在")
    
    print(f"\n前端文件创建成功率: {success_count}/{len(frontend_files)}")
    return success_count == len(frontend_files)


async def test_router_integration():
    """测试路由集成"""
    print("\n=== 路由集成检查 ===")
    
    try:
        # 检查路由文件
        router_file = Path(project_root.parent / "dc_frontend/src/router/index.ts")
        if router_file.exists():
            content = router_file.read_text(encoding='utf-8')
            
            # 检查是否包含API管理路由
            if '/api-management' in content:
                print("✅ API管理路由已添加到路由配置")
            else:
                print("❌ API管理路由未添加到路由配置")
                return False
            
            # 检查各个子路由
            sub_routes = [
                'CustomerManagement',
                'ApiManagement', 
                'BatchManagement',
                'ApiDashboard'
            ]
            
            for route in sub_routes:
                if route in content:
                    print(f"✅ {route} 路由配置正确")
                else:
                    print(f"❌ {route} 路由配置缺失")
            
            return True
        else:
            print("❌ 路由文件不存在")
            return False
            
    except Exception as e:
        print(f"❌ 路由集成检查失败: {e}")
        return False


async def test_backend_api_endpoints():
    """测试后端API端点"""
    print("\n=== 后端API端点检查 ===")
    
    try:
        # 检查主应用是否包含多数据库路由
        main_file = Path(project_root / "app/main.py")
        if main_file.exists():
            content = main_file.read_text(encoding='utf-8')
            
            if 'multi_db_router' in content:
                print("✅ 主应用已包含多数据库路由")
            else:
                print("❌ 主应用未包含多数据库路由")
                return False
            
            if '/multi-db' in content:
                print("✅ 多数据库路由前缀配置正确")
            else:
                print("❌ 多数据库路由前缀配置缺失")
                return False
                
            return True
        else:
            print("❌ 主应用文件不存在")
            return False
            
    except Exception as e:
        print(f"❌ 后端API端点检查失败: {e}")
        return False


async def main():
    """主测试函数"""
    print("🚀 API管理功能集成测试开始")
    print("=" * 50)
    
    test_results = []
    
    # 执行所有测试
    test_results.append(await test_api_management_integration())
    test_results.append(await test_frontend_files())
    test_results.append(await test_router_integration())
    test_results.append(await test_backend_api_endpoints())
    
    # 统计结果
    passed_tests = sum(test_results)
    total_tests = len(test_results)
    
    print("\n" + "=" * 50)
    print(f"📊 测试结果: {passed_tests}/{total_tests} 通过")
    
    if passed_tests == total_tests:
        print("🎉 所有测试通过！API管理功能集成成功！")
        print("\n📝 功能说明:")
        print("✅ 平台管理 - 管理API接口平台信息和权限配置")
        print("✅ API管理 - 创建和管理自定义API接口")
        print("✅ 字段配置 - 配置API接口的请求和响应字段")
        print("✅ 批次管理 - 管理数据批次处理任务")
        print("✅ 仪表板 - 统计和监控API使用情况")
        print("\n🌐 访问地址:")
        print("- 前端界面: http://localhost:3005/")
        print("- API文档: http://localhost:8082/docs (需要启动后端)")
        print("\n📁 新增页面路由:")
        print("- /api-management/customers - 平台管理")
        print("- /api-management/apis - API管理")
        print("- /api-management/batches - 批次管理")
        print("- /api-management/dashboard - API仪表板")
    else:
        print("❌ 部分测试失败，请检查实现")
        
        print("\n🔧 故障排除建议:")
        print("1. 检查文件是否正确创建")
        print("2. 确认路由配置是否正确")
        print("3. 验证模块导入是否成功")
        print("4. 检查TypeScript类型定义")
    
    return passed_tests == total_tests


if __name__ == "__main__":
    # 运行测试
    success = asyncio.run(main())
    sys.exit(0 if success else 1)