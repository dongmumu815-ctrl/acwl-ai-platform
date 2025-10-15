#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
带认证的API端点测试脚本

测试修复后的API管理端点是否正常工作
"""

import asyncio
import aiohttp
import json
import sys

async def test_api_with_auth():
    """测试带认证的API端点"""
    base_url = "http://localhost:8082/api/v1"
    
    print("🚀 开始测试带认证的API端点")
    print("=" * 50)
    
    async with aiohttp.ClientSession() as session:
        # 首先进行登录获取token
        login_data = {
            "username": "admin",
            "password": "admin123"
        }
        
        print("🔐 正在登录获取访问令牌...")
        
        try:
            async with session.post(f"{base_url}/auth/login", json=login_data) as response:
                if response.status == 200:
                    auth_data = await response.json()
                    if auth_data.get('success') and 'data' in auth_data:
                        token = auth_data['data'].get('access_token')
                        print(f"✅ 登录成功，获取到token: {token[:20]}...")
                    else:
                        print("❌ 登录失败：响应格式不正确")
                        print(f"响应: {auth_data}")
                        return False
                else:
                    error_text = await response.text()
                    print(f"❌ 登录失败: {response.status}")
                    print(f"错误: {error_text}")
                    return False
        except Exception as e:
            print(f"❌ 登录请求失败: {e}")
            return False
        
        # 设置认证头
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
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
                                    print(f"   返回 {len(data['data']['items'])} 条记录")
                                else:
                                    print(f"   返回数据: {list(data['data'].keys())}")
                            elif isinstance(data['data'], list):
                                print(f"   返回 {len(data['data'])} 条记录")
                            else:
                                print(f"   返回数据类型: {type(data['data'])}")
                        
                        success_count += 1
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
            print("\n📝 可用的API端点:")
            print("- GET /api/v1/customers - 客户列表")
            print("- GET /api/v1/apis - API列表")
            print("- GET /api/v1/batches - 批次列表")
            print("- GET /api/v1/stats/system - 系统统计")
            print("- POST /api/v1/customers - 创建客户")
            print("- POST /api/v1/apis - 创建API")
            print("- POST /api/v1/batches - 创建批次")
            print("\n🌐 前端访问地址: http://localhost:3005/api-management/customers")
            print("🌐 API文档地址: http://localhost:8082/docs")
        else:
            print("❌ 部分API端点测试失败")
            print("请检查后端服务是否正常运行")
        
        return success_count == total_count

if __name__ == "__main__":
    try:
        success = asyncio.run(test_api_with_auth())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n测试过程中发生错误: {e}")
        sys.exit(1)