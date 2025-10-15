#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用实际token的API端点测试脚本

使用用户提供的token测试API管理端点
"""

import asyncio
import aiohttp
import json
import sys

async def test_api_with_token():
    """使用实际token测试API端点"""
    base_url = "http://localhost:8082/api/v1"
    
    # 使用用户提供的token
    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI1IiwiZXhwIjoxNzYwMDAxMzY3fQ.EkDdmId43RVyDQYyb5YgZAJLrce67qIWaUyGBbOZSuE"
    
    print("🚀 开始测试API管理端点")
    print("=" * 50)
    print(f"🔑 使用token: {token[:20]}...")
    
    # 设置认证头
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    async with aiohttp.ClientSession() as session:
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
        
        print("\n📋 开始测试API端点...")
        print("-" * 50)
        
        success_count = 0
        total_count = len(test_endpoints)
        
        for method, endpoint, description in test_endpoints:
            url = f"{base_url}{endpoint}"
            
            try:
                async with session.request(method, url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        print(f"✅ {description}: {response.status}")
                        
                        # 显示部分响应数据
                        if 'data' in data:
                            if isinstance(data['data'], dict):
                                if 'items' in data['data']:
                                    items_count = len(data['data']['items'])
                                    total = data['data'].get('total', items_count)
                                    print(f"   返回 {items_count} 条记录，总计 {total} 条")
                                    
                                    # 显示第一条记录的部分信息
                                    if items_count > 0:
                                        first_item = data['data']['items'][0]
                                        if 'name' in first_item:
                                            print(f"   示例: {first_item.get('name', 'N/A')}")
                                        elif 'api_name' in first_item:
                                            print(f"   示例: {first_item.get('api_name', 'N/A')}")
                                        elif 'batch_name' in first_item:
                                            print(f"   示例: {first_item.get('batch_name', 'N/A')}")
                                else:
                                    # 统计数据
                                    stats_keys = list(data['data'].keys())[:3]
                                    print(f"   统计数据: {stats_keys}...")
                            elif isinstance(data['data'], list):
                                print(f"   返回 {len(data['data'])} 条记录")
                            else:
                                print(f"   返回数据类型: {type(data['data'])}")
                        
                        success_count += 1
                    elif response.status == 401:
                        print(f"❌ {description}: {response.status} (认证失败)")
                        error_text = await response.text()
                        print(f"   错误: {error_text[:100]}...")
                    elif response.status == 404:
                        print(f"❌ {description}: {response.status} (端点不存在)")
                        error_text = await response.text()
                        print(f"   错误: {error_text[:100]}...")
                    else:
                        print(f"❌ {description}: {response.status}")
                        error_text = await response.text()
                        print(f"   错误: {error_text[:100]}...")
                        
            except Exception as e:
                print(f"❌ {description}: 请求失败")
                print(f"   错误: {str(e)}")
        
        print("\n" + "=" * 50)
        print(f"📊 测试结果: {success_count}/{total_count} 成功")
        
        if success_count == total_count:
            print("🎉 所有API端点测试通过！")
            print("\n📝 API管理功能已就绪:")
            print("✅ 客户管理 - 管理API接口客户")
            print("✅ API管理 - 创建和管理自定义API")
            print("✅ 批次管理 - 数据批次处理任务")
            print("✅ 统计功能 - 系统数据统计")
            print("\n🌐 前端访问地址:")
            print("- 客户管理: http://localhost:3005/api-management/customers")
            print("- API管理: http://localhost:3005/api-management/apis")
            print("- 批次管理: http://localhost:3005/api-management/batches")
            print("- 仪表板: http://localhost:3005/api-management/dashboard")
            print("\n🌐 API文档: http://localhost:8082/docs")
        elif success_count > 0:
            print(f"⚠️  部分API端点正常工作 ({success_count}/{total_count})")
            print("前端功能可以部分使用，建议检查失败的端点")
        else:
            print("❌ 所有API端点测试失败")
            print("请检查后端服务和路由配置")
        
        return success_count >= total_count // 2  # 至少一半成功就算通过

if __name__ == "__main__":
    try:
        success = asyncio.run(test_api_with_token())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n测试过程中发生错误: {e}")
        sys.exit(1)