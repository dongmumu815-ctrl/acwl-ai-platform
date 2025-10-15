#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化的批次列表接口测试

直接测试 GET /api/v1/batch/ 接口
"""

import requests
import json

# 测试配置
BASE_URL = "http://localhost:8000"
API_URL = f"{BASE_URL}/api/v1"

# 测试Token
TEST_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI2IiwidHlwZSI6ImN1c3RvbWVyIiwiZXhwIjoxNzUzMTY0MDc1LCJpYXQiOjE3NTMwNzc2NzUsImp0aSI6InlOUm9GZWpobkZJR3p6YlB4QkF4ejVfTkRrdWl2Um5pSXhhOGxUQXBJWUUiLCJjdXN0b21lcl9pZCI6NiwiYXBwX2lkIjoidGVzdF9hcHBfMDAxIn0.r1if0CDb9ANFCd2_VVA1Q_k59YmTLrKOSqPu1oM8QoQ"

def test_batch_list():
    """
    测试批次列表接口
    """
    print("=== 测试批次列表接口 ===")
    
    # 构建请求
    url = f"{API_URL}/batch/"
    headers = {
        "Authorization": f"Bearer {TEST_TOKEN}",
        "Content-Type": "application/json"
    }
    
    params = {
        "page": 1,
        "size": 20
    }
    
    print(f"请求URL: {url}")
    print(f"请求参数: {params}")
    print(f"请求头: {json.dumps(headers, indent=2)}")
    
    try:
        response = requests.get(url, headers=headers, params=params)
        
        print(f"\n响应状态码: {response.status_code}")
        print(f"响应头: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ 请求成功!")
            print(f"响应数据: {json.dumps(data, indent=2, ensure_ascii=False)}")
            
            # 检查数据结构
            if 'total' in data and 'items' in data:
                print(f"\n📊 数据统计:")
                print(f"   总数: {data['total']}")
                print(f"   当前页: {data['page']}")
                print(f"   页大小: {data['size']}")
                print(f"   项目数: {len(data['items'])}")
                
                if data['items']:
                    print(f"\n📋 批次列表:")
                    for i, item in enumerate(data['items']):
                        print(f"   {i+1}. {item.get('batch_id')} - {item.get('batch_name')} ({item.get('status')})")
                else:
                    print(f"\n⚠️ 没有找到批次数据")
            else:
                print(f"\n❌ 响应数据格式异常")
                
        else:
            print(f"\n❌ 请求失败: {response.status_code}")
            print(f"错误信息: {response.text}")
            
    except Exception as e:
        print(f"\n❌ 请求异常: {e}")

def test_token_validation():
    """
    测试Token验证
    """
    print("\n=== 测试Token验证 ===")
    
    # 测试一个简单的认证接口
    url = f"{API_URL}/batch/test_batch_123"
    headers = {
        "Authorization": f"Bearer {TEST_TOKEN}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers)
        print(f"Token验证测试 - 状态码: {response.status_code}")
        if response.status_code != 401:
            print(f"✅ Token验证通过")
        else:
            print(f"❌ Token验证失败: {response.text}")
    except Exception as e:
        print(f"❌ Token验证异常: {e}")

if __name__ == "__main__":
    print("批次列表接口简化测试")
    print(f"Token: {TEST_TOKEN[:50]}...")
    
    test_token_validation()
    test_batch_list()
    
    print("\n测试完成！")