#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用真实token测试secure query API
验证SQL动态修改功能
"""

import asyncio
import aiohttp
import json


async def test_secure_query_with_token():
    """
    使用真实token测试secure query API
    """
    print("=== 使用真实Token测试Secure Query API ===\n")
    
    # API配置
    base_url = "http://localhost:8082"
    
    # 使用用户提供的token
    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI1IiwiZXhwIjoxNzU4NjUyNDczfQ.Ky0odhETjCv5fEI1brHqBEFD_fwF-PjAlTMaVDjPzf8"
    headers = {"Authorization": f"Bearer {token}"}
    
    async with aiohttp.ClientSession() as session:
        try:
            # 测试secure query接口
            package_id = 4  # 使用ID=4的资源包
            
            # 测试场景1：不传入任何非锁定参数
            print("1. 测试场景1：不传入任何非锁定参数")
            query_data1 = {
                "dynamic_params": {},
                "limit": 100
            }
            
            async with session.post(
                f"{base_url}/api/v1/resource-packages/{package_id}/secure-query", 
                json=query_data1, 
                headers=headers
            ) as response:
                print(f"状态码: {response.status}")
                if response.status == 200:
                    result1 = await response.json()
                    print(f"✅ 查询成功")
                    print(f"生成的SQL: {result1.get('data', {}).get('generated_query', '未找到')}")
                    print(f"结果数量: {result1.get('data', {}).get('total_count', 0)}")
                else:
                    text = await response.text()
                    print(f"❌ 查询失败: {text}")
            
            # 测试场景2：传入description参数
            print("\n2. 测试场景2：传入description参数")
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
                print(f"状态码: {response.status}")
                if response.status == 200:
                    result2 = await response.json()
                    print(f"✅ 查询成功")
                    print(f"生成的SQL: {result2.get('data', {}).get('generated_query', '未找到')}")
                    print(f"结果数量: {result2.get('data', {}).get('total_count', 0)}")
                else:
                    text = await response.text()
                    print(f"❌ 查询失败: {text}")
            
            # 测试场景3：传入name和description参数
            print("\n3. 测试场景3：传入name和description参数")
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
                print(f"状态码: {response.status}")
                if response.status == 200:
                    result3 = await response.json()
                    print(f"✅ 查询成功")
                    print(f"生成的SQL: {result3.get('data', {}).get('generated_query', '未找到')}")
                    print(f"结果数量: {result3.get('data', {}).get('total_count', 0)}")
                else:
                    text = await response.text()
                    print(f"❌ 查询失败: {text}")
            
            # 测试场景4：传入空字符串参数（应该被过滤掉）
            print("\n4. 测试场景4：传入空字符串参数")
            query_data4 = {
                "dynamic_params": {
                    "name": "",
                    "description": "有效描述"
                },
                "limit": 100
            }
            
            async with session.post(
                f"{base_url}/api/v1/resource-packages/{package_id}/secure-query", 
                json=query_data4, 
                headers=headers
            ) as response:
                print(f"状态码: {response.status}")
                if response.status == 200:
                    result4 = await response.json()
                    print(f"✅ 查询成功")
                    print(f"生成的SQL: {result4.get('data', {}).get('generated_query', '未找到')}")
                    print(f"结果数量: {result4.get('data', {}).get('total_count', 0)}")
                else:
                    text = await response.text()
                    print(f"❌ 查询失败: {text}")
            
            # 测试场景5：尝试传入锁定字段的值（应该被忽略）
            print("\n5. 测试场景5：尝试传入锁定字段的值")
            query_data5 = {
                "dynamic_params": {
                    "node_type": "user_input_value",  # 这个应该被忽略
                    "description": "测试描述"
                },
                "limit": 100
            }
            
            async with session.post(
                f"{base_url}/api/v1/resource-packages/{package_id}/secure-query", 
                json=query_data5, 
                headers=headers
            ) as response:
                print(f"状态码: {response.status}")
                if response.status == 200:
                    result5 = await response.json()
                    print(f"✅ 查询成功")
                    print(f"生成的SQL: {result5.get('data', {}).get('generated_query', '未找到')}")
                    print(f"结果数量: {result5.get('data', {}).get('total_count', 0)}")
                else:
                    text = await response.text()
                    print(f"❌ 查询失败: {text}")
            
            print("\n=== 测试完成 ===")
            
        except Exception as e:
            print(f"测试失败: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_secure_query_with_token())