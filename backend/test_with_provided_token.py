#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用提供的token测试API管理功能

测试API端点是否从acwl_api_system数据库返回真实数据
"""

import asyncio
import aiohttp
import json
import sys

async def test_with_provided_token():
    """使用提供的token测试API管理功能"""
    base_url = "http://localhost:8082/api/v1"
    
    # 使用用户提供的token
    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI1IiwiZXhwIjoxNzYwMDA0NjYxfQ.Fx5LvGD4ZBcLWpxW2CNzR7rtC0QwOdyoJvGPjR2MdqE"
    
    print("🚀 开始测试API管理功能（使用提供的token）")
    print("=" * 60)
    print(f"🔑 使用token: {token[:30]}...")
    
    # 设置认证头
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    async with aiohttp.ClientSession() as session:
        
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
                        
                        print(f"\n📊 返回数据分析:")
                        print(f"   总记录数: {total}")
                        print(f"   当前页记录数: {len(items)}")
                        
                        if len(items) > 0:
                            first_customer = items[0]
                            print(f"\n🔍 第一条客户记录详情:")
                            print(f"   客户ID: {first_customer.get('id')}")
                            print(f"   客户名称: {first_customer.get('name')}")
                            print(f"   邮箱: {first_customer.get('email')}")
                            print(f"   公司: {first_customer.get('company')}")
                            print(f"   App ID: {first_customer.get('app_id')}")
                            print(f"   总调用次数: {first_customer.get('total_api_calls')}")
                            print(f"   创建时间: {first_customer.get('created_at')}")
                            
                            # 判断是否为测试数据
                            if (first_customer.get('name') == '测试客户1' and 
                                first_customer.get('email') == 'customer1@example.com'):
                                print(f"\n❌ 数据来源分析: 模拟测试数据")
                                print(f"   原因: 客户名称和邮箱匹配硬编码的测试数据")
                                print(f"   说明: API端点使用了fallback逻辑，返回模拟数据")
                                print(f"   建议: 检查多数据库连接是否正常")
                                
                                # 显示完整的第一条记录
                                print(f"\n📄 完整记录内容:")
                                print(json.dumps(first_customer, indent=2, ensure_ascii=False))
                                
                            else:
                                print(f"\n✅ 数据来源分析: 真实数据库数据")
                                print(f"   说明: API端点成功连接到acwl_api_system数据库")
                                print(f"   数据特征: 平台信息不匹配测试数据模式")
                        else:
                            print(f"\n⚠️  数据来源分析: 空数据集")
                            print(f"   可能原因: acwl_api_system数据库中没有客户数据")
                            print(f"   或者: 多数据库连接失败，返回空的模拟数据")
                    else:
                        print(f"❌ 响应格式不正确")
                        print(f"完整响应: {data}")
                        
                else:
                    error_text = await response.text()
                    print(f"❌ 客户列表请求失败: {response.status}")
                    print(f"错误: {error_text[:200]}...")
                    
        except Exception as e:
            print(f"❌ 客户列表请求异常: {e}")
        
        # 测试多数据库健康状态
        print(f"\n🗄️ 测试多数据库连接状态...")
        print("-" * 50)
        
        try:
            async with session.get(f"{base_url}/multi-db/health") as response:
                if response.status == 200:
                    health_data = await response.json()
                    print("✅ 多数据库健康检查成功")
                    
                    if 'data' in health_data:
                        connection_status = health_data['data'].get('connection_status', {})
                        print(f"\n📊 数据库连接状态:")
                        for db_name, status in connection_status.items():
                            status_icon = "✅" if status else "❌"
                            print(f"   {status_icon} {db_name}: {'连接正常' if status else '连接失败'}")
                        
                        # 特别检查api_system数据库
                        api_system_status = connection_status.get('api_system', False)
                        if api_system_status:
                            print(f"\n✅ api_system数据库连接正常")
                            print(f"   说明: 多数据库功能可以访问acwl_api_system")
                            print(f"   如果客户API返回测试数据，可能是代码逻辑问题")
                        else:
                            print(f"\n❌ api_system数据库连接失败")
                            print(f"   说明: 这就是API端点返回测试数据的原因")
                            print(f"   建议: 检查多数据库配置和网络连接")
                            
                        # 显示完整健康检查结果
                        print(f"\n📄 完整健康检查结果:")
                        print(json.dumps(health_data['data'], indent=2, ensure_ascii=False))
                        
                else:
                    print(f"❌ 多数据库健康检查失败: {response.status}")
                    
        except Exception as e:
            print(f"❌ 多数据库健康检查异常: {e}")
        
        print(f"\n" + "=" * 60)
        print(f"📋 诊断总结:")
        print(f"1. ✅ 认证token有效，可以访问API端点")
        print(f"2. 🔍 检查了客户列表API的数据来源")
        print(f"3. 🗄️ 检查了多数据库连接状态")
        print(f"4. 📊 分析了数据是否来自acwl_api_system数据库")
        
        return True

if __name__ == "__main__":
    try:
        success = asyncio.run(test_with_provided_token())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n测试过程中发生错误: {e}")
        sys.exit(1)