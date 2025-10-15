#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API端点测试脚本

测试新增的API管理端点是否正常工作
"""

import asyncio
import aiohttp
import json
import sys

async def test_api_endpoints():
    """测试API端点"""
    base_url = "http://localhost:8082/api/v1"
    
    # 测试端点列表
    test_endpoints = [
        ("GET", "/customers", "获取客户列表"),
        ("GET", "/apis", "获取API列表"),
        ("GET", "/batches", "获取批次列表"),
        ("GET", "/stats/system", "获取系统统计"),
        ("GET", "/stats/batch-status", "获取批次状态统计"),
        ("GET", "/stats/api-calls", "获取API调用统计"),
        ("GET", "/stats/customer-activity", "获取客户活跃度统计")
    ]
    
    print("🚀 开始测试API端点")
    print("=" * 50)
    
    async with aiohttp.ClientSession() as session:
        success_count = 0
        total_count = len(test_endpoints)
        
        for method, endpoint, description in test_endpoints:
            url = f"{base_url}{endpoint}"
            
            try:
                async with session.request(method, url) as response:
                    if response.status == 200:
                        data = await response.json()
                        print(f"✅ {description}: {response.status}")
                        
                        # 显示部分响应数据
                        if 'data' in data:
                            if isinstance(data['data'], dict):
                                if 'items' in data['data']:
                                    print(f"   返回 {len(data['data']['items'])} 条记录")
                                else:
                                    print(f"   返回数据: {list(data['data'].keys())}")
                            else:
                                print(f"   返回数据类型: {type(data['data'])}")
                        
                        success_count += 1
                    else:
                        print(f"❌ {description}: {response.status}")
                        error_text = await response.text()
                        print(f"   错误: {error_text[:100]}...")
                        
            except Exception as e:
                print(f"❌ {description}: 连接失败")
                print(f"   错误: {str(e)}")
    
    print("\n" + "=" * 50)
    print(f"📊 测试结果: {success_count}/{total_count} 成功")
    
    if success_count == total_count:
        print("🎉 所有API端点测试通过！")
        print("\n📝 可用的API端点:")
        print("- GET /api/v1/customers - 客户列表")
        print("- GET /api/v1/apis - API列表")
        print("- GET /api/v1/batches - 批次列表")
        print("- GET /api/v1/stats/system - 系统统计")
        print("- POST /api/v1/customers - 创建客户")
        print("- POST /api/v1/apis - 创建API")
        print("- POST /api/v1/batches - 创建批次")
        print("\n🌐 API文档地址: http://localhost:8082/docs")
    else:
        print("❌ 部分API端点测试失败")
        print("请检查后端服务是否正常运行")
    
    return success_count == total_count

if __name__ == "__main__":
    try:
        success = asyncio.run(test_api_endpoints())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n测试过程中发生错误: {e}")
        sys.exit(1)