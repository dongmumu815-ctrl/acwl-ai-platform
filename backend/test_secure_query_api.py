#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试secure query API接口
验证新的SQL动态修改逻辑在实际API中的工作情况
"""

import asyncio
import aiohttp
import json


async def test_secure_query_api():
    """
    测试secure query API接口
    """
    print("=== 测试Secure Query API ===\n")
    
    # API配置
    base_url = "http://localhost:8082"
    
    # 首先需要登录获取token
    login_data = {
        "username": "admin",  # 根据实际情况修改
        "password": "admin123"  # 根据实际情况修改
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            # 登录获取token
            print("1. 尝试登录...")
            async with session.post(f"{base_url}/api/v1/auth/login/json", json=login_data) as response:
                if response.status == 200:
                    login_result = await response.json()
                    token = login_result.get("data", {}).get("access_token")
                    if not token:
                        print("登录失败：未获取到token")
                        return
                    print(f"登录成功，获取到token: {token[:20]}...")
                else:
                    print(f"登录失败，状态码: {response.status}")
                    text = await response.text()
                    print(f"响应内容: {text}")
                    return
            
            # 设置认证头
            headers = {"Authorization": f"Bearer {token}"}
            
            # 测试secure query接口
            package_id = 4  # 使用ID=4的资源包
            
            # 测试场景1：不传入任何非锁定参数
            print("\n2. 测试场景1：不传入任何非锁定参数")
            query_data1 = {
                "dynamic_params": {},
                "limit": 100
            }
            
            async with session.post(
                f"{base_url}/api/v1/resource-packages/{package_id}/secure-query", 
                json=query_data1, 
                headers=headers
            ) as response:
                if response.status == 200:
                    result1 = await response.json()
                    print(f"查询成功，生成的SQL: {result1.get('data', {}).get('generated_query')}")
                    print(f"结果数量: {result1.get('data', {}).get('total_count')}")
                else:
                    print(f"查询失败，状态码: {response.status}")
                    text = await response.text()
                    print(f"错误信息: {text}")
            
            # 测试场景2：传入description参数
            print("\n3. 测试场景2：传入description参数")
            query_data2 = {
                "dynamic_params": {
                    "description": "测试描述"
                },
                "limit": 100
            }
            
            async with session.post(
                f"{base_url}/api/v1/resource-packages/{package_id}/secure-query", 
                json=query_data2, 
                headers=headers
            ) as response:
                if response.status == 200:
                    result2 = await response.json()
                    print(f"查询成功，生成的SQL: {result2.get('data', {}).get('generated_query')}")
                    print(f"结果数量: {result2.get('data', {}).get('total_count')}")
                else:
                    print(f"查询失败，状态码: {response.status}")
                    text = await response.text()
                    print(f"错误信息: {text}")
            
            # 测试场景3：传入name和description参数
            print("\n4. 测试场景3：传入name和description参数")
            query_data3 = {
                "dynamic_params": {
                    "name": "测试名称",
                    "description": "测试描述"
                },
                "limit": 100
            }
            
            async with session.post(
                f"{base_url}/api/v1/resource-packages/{package_id}/secure-query", 
                json=query_data3, 
                headers=headers
            ) as response:
                if response.status == 200:
                    result3 = await response.json()
                    print(f"查询成功，生成的SQL: {result3.get('data', {}).get('generated_query')}")
                    print(f"结果数量: {result3.get('data', {}).get('total_count')}")
                else:
                    print(f"查询失败，状态码: {response.status}")
                    text = await response.text()
                    print(f"错误信息: {text}")
            
            print("\n=== API测试完成 ===")
            
        except Exception as e:
            print(f"API测试失败: {e}")
            import traceback
            traceback.print_exc()


async def test_simple_health_check():
    """
    简单的健康检查
    """
    print("=== 健康检查 ===")
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get("http://localhost:8082/api/v1/health") as response:
                if response.status == 200:
                    print("后端服务正常运行")
                else:
                    print(f"后端服务状态异常，状态码: {response.status}")
        except Exception as e:
            print(f"无法连接到后端服务: {e}")


if __name__ == "__main__":
    asyncio.run(test_simple_health_check())
    asyncio.run(test_secure_query_api())