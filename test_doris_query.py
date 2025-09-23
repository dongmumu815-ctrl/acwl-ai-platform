#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 Doris 查询功能
"""

import requests
import json

def get_auth_token():
    """
    获取管理员认证token
    """
    login_data = {
        "email": "admin@acwl.ai",
        "password": "password"
    }
    
    try:
        response = requests.post(
            "http://localhost:3005/api/v1/auth/login/json",
            json=login_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            token = data.get("access_token")
            print(f"✅ 获取认证token成功: {token[:30]}...")
            return token
        else:
            print(f"❌ 登录失败: {response.text}")
            return None
    except Exception as e:
        print(f"❌ 登录异常: {e}")
        return None

def test_doris_query():
    """
    测试 Doris 数据源查询接口
    """
    # API 基础 URL
    base_url = "http://localhost:3005"
    
    # 测试查询接口
    query_url = f"{base_url}/api/v1/datasources/10/query"
    
    # 测试查询数据
    test_queries = [
        {
            "name": "简单查询测试",
            "query": "SELECT * FROM cpc_dw_publication LIMIT 5",
            "limit": 5,
            "timeout": 30
        },
        {
            "name": "计数查询测试", 
            "query": "SELECT COUNT(*) as total_count FROM cpc_dw_publication",
            "limit": 10,
            "timeout": 30
        },
        {
            "name": "字段查询测试",
            "query": "SELECT id, title, author FROM cpc_dw_publication LIMIT 3",
            "limit": 3,
            "timeout": 30
        }
    ]
    
    # 获取认证token
    token = get_auth_token()
    if not token:
        print("❌ 无法获取认证token，测试终止")
        return
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    
    print("开始测试 Doris 查询功能...")
    print("=" * 60)
    
    for i, test_case in enumerate(test_queries, 1):
        print(f"\n测试 {i}: {test_case['name']}")
        print(f"查询语句: {test_case['query']}")
        print("-" * 40)
        
        try:
            # 发送 POST 请求
            response = requests.post(
                query_url,
                json={
                    "query": test_case["query"],
                    "limit": test_case["limit"],
                    "timeout": test_case["timeout"]
                },
                headers={"Content-Type": "application/json"},
                timeout=60
            )
            
            print(f"状态码: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"响应结果:")
                print(f"  - success: {result.get('success', 'N/A')}")
                print(f"  - message: {result.get('message', 'N/A')}")
                print(f"  - row_count: {result.get('row_count', 'N/A')}")
                print(f"  - execution_time: {result.get('execution_time', 'N/A')}ms")
                
                if result.get('success'):
                    columns = result.get('columns', [])
                    data = result.get('data', [])
                    print(f"  - columns: {columns}")
                    if data:
                        print(f"  - 数据示例 (前2行):")
                        for j, row in enumerate(data[:2]):
                            print(f"    行 {j+1}: {row}")
                    else:
                        print(f"  - 无数据返回")
                else:
                    print(f"  - error_details: {result.get('error_details', 'N/A')}")
            else:
                print(f"请求失败: {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"请求异常: {str(e)}")
        except Exception as e:
            print(f"其他错误: {str(e)}")
    
    print("\n" + "=" * 60)
    print("测试完成")

if __name__ == "__main__":
    test_doris_query()