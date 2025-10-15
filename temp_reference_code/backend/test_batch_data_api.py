#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试批次数据接口
"""

import requests
import json

# 配置
BASE_URL = "http://localhost:8000"
API_ENDPOINT = "/api/v1/batch"
BATCH_ID = "erp-2025-014"  # 使用用户报错中的批次ID

def test_batch_data_api():
    """
    测试批次数据接口
    """
    print("=== 测试批次数据接口 ===")
    
    # 构建请求URL
    url = f"{BASE_URL}{API_ENDPOINT}/{BATCH_ID}/data"
    
    # 请求头（需要认证）
    headers = {
        "Authorization": "Bearer test_token",  # 这里需要有效的token
        "Content-Type": "application/json"
    }
    
    # 请求参数
    params = {
        "page": 1,
        "size": 20
    }
    
    print(f"请求URL: {url}")
    print(f"请求参数: {params}")
    
    try:
        # 发送GET请求
        response = requests.get(url, headers=headers, params=params, timeout=10)
        
        print(f"响应状态码: {response.status_code}")
        print(f"响应头: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ 接口调用成功")
            print(f"响应数据: {json.dumps(data, indent=2, ensure_ascii=False)}")
        else:
            print("❌ 接口调用失败")
            print(f"错误响应: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ 请求异常: {e}")
    except Exception as e:
        print(f"❌ 其他异常: {e}")

if __name__ == "__main__":
    test_batch_data_api()