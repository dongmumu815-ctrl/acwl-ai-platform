#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试API管理功能是否返回真实数据

先获取新的认证token，然后测试API端点是否从acwl_api_system数据库返回真实数据
"""

import asyncio
import aiohttp
import json
import sys

async def test_api_real_data():
    """测试API管理功能是否返回真实数据"""
    base_url = "http://localhost:8082/api/v1"
    
    print("🚀 开始测试API管理功能（真实数据）")
    print("=" * 50)
    
    async with aiohttp.ClientSession() as session:
        # 首先进行登录获取新token
        login_data = {
            "email": "admin@acwl.ai",
            "password": "admin123"
        }
        
        print("🔐 正在登录获取新的访问令牌...")
        
        try:
            async with session.post(f"{base_url}/auth/login/json", json=login_data) as response:
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
        
        print("\n📋 测试客户列表端点...")
        print("-" * 50)
        
        try:
            async with session.get(f"{base_url}/customers", headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ 客户列表请求成功: {response.status}")
                    
                    if 'data' in data and 'items' in data['data']:
                        items = data['data']['items']
                        total = data['data'].get('total', 0)
                        
                        print(f"📊 返回数据分析:")
                        print(f"   总记录数: {total}")
                        print(f"   当前页记录数: {len(items)}")
                        
                        if len(items) > 0:
                            first_customer = items[0]
                            print(f"\n🔍 第一条客户记录分析:")
                            print(f"   客户ID: {first_customer.get('id')}")
                            print(f"   客户名称: {first_customer.get('name')}")
                            print(f"   邮箱: {first_customer.get('email')}")
                            print(f"   公司: {first_customer.get('company')}")
                            print(f"   App ID: {first_customer.get('app_id')}")
                            
                            # 判断是否为测试数据
                            if first_customer.get('name') == '测试客户1' and first_customer.get('email') == 'customer1@example.com':
                                print("\n❌ 检测结果: 返回的是模拟测试数据")
                                print("   原因: 客户名称和邮箱匹配模拟数据模式")
                                print("   说明: API端点没有连接到acwl_api_system数据库")
                            else:
                                print("\n✅ 检测结果: 返回的是真实数据")
                                print("   说明: API端点成功连接到acwl_api_system数据库")
                        else:
                            print("\n⚠️  检测结果: 没有返回任何客户记录")
                            print("   可能原因: acwl_api_system数据库中没有客户数据")
                    else:
                        print("❌ 响应格式不正确，缺少data.items字段")
                        
                else:
                    error_text = await response.text()
                    print(f"❌ 客户列表请求失败: {response.status}")
                    print(f"错误: {error_text[:200]}...")
                    
        except Exception as e:
            print(f"❌ 客户列表请求异常: {e}")
        
        # 测试多数据库健康状态
        print("\n🗄️ 测试多数据库连接状态...")
        print("-" * 50)
        
        try:
            async with session.get(f"{base_url}/multi-db/health") as response:
                if response.status == 200:
                    health_data = await response.json()
                    print("✅ 多数据库健康检查成功")
                    
                    if 'data' in health_data:
                        connection_status = health_data['data'].get('connection_status', {})
                        print(f"📊 数据库连接状态:")
                        for db_name, status in connection_status.items():
                            status_icon = "✅" if status else "❌"
                            print(f"   {status_icon} {db_name}: {'连接正常' if status else '连接失败'}")
                        
                        # 特别检查api_system数据库
                        api_system_status = connection_status.get('api_system', False)
                        if api_system_status:
                            print("\n✅ api_system数据库连接正常")
                            print("   说明: 多数据库功能可以访问acwl_api_system")
                        else:
                            print("\n❌ api_system数据库连接失败")
                            print("   说明: 这可能是API端点返回测试数据的原因")
                else:
                    print(f"❌ 多数据库健康检查失败: {response.status}")
                    
        except Exception as e:
            print(f"❌ 多数据库健康检查异常: {e}")
        
        print("\n" + "=" * 50)
        print("📋 测试总结:")
        print("1. 检查了客户列表API是否返回真实数据")
        print("2. 检查了多数据库连接状态")
        print("3. 分析了数据来源（测试数据 vs 真实数据）")
        
        return True

if __name__ == "__main__":
    try:
        success = asyncio.run(test_api_real_data())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n测试过程中发生错误: {e}")
        sys.exit(1)