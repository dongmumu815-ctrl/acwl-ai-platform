#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试修复后的数据源查询功能
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
            "http://localhost:8082/api/v1/auth/login/json",
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

def test_datasource_query():
    """
    测试数据源8的查询功能，验证是否能正确选择数据库
    """
    url = "http://localhost:8082/api/v1/datasources/8/query"
    
    # 测试查询cpc_agents表（应该在acwl-agents数据库中）
    payload = {
        "query": "SELECT name, description, parent_id FROM cpc_agents ORDER BY id DESC LIMIT 100",
        "limit": 100,
        "timeout": 30
    }
    
    # 获取认证token
    token = get_auth_token()
    if not token:
        print("❌ 无法获取认证token，测试终止")
        return
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    
    print("正在测试修复后的查询功能...")
    print(f"请求URL: {url}")
    print(f"查询SQL: {payload['query']}")
    print("="*50)
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        
        print(f"响应状态码: {response.status_code}")
        print(f"响应头: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print("\n响应内容:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            
            if result.get('success'):
                print("\n✅ 查询成功！修复生效！")
                print(f"返回行数: {result.get('row_count', 0)}")
                print(f"执行时间: {result.get('execution_time', 0)}ms")
                
                if result.get('data'):
                    print("\n前3行数据:")
                    for i, row in enumerate(result['data'][:3]):
                        print(f"  行{i+1}: {row}")
            else:
                print("\n❌ 查询失败:")
                print(f"错误信息: {result.get('message', '未知错误')}")
                print(f"错误详情: {result.get('error_details', '无详情')}")
        else:
            print(f"\n❌ HTTP请求失败: {response.status_code}")
            print(f"响应内容: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("\n❌ 连接失败: 请确保后端服务正在运行 (http://localhost:8082)")
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")

if __name__ == "__main__":
    test_datasource_query()