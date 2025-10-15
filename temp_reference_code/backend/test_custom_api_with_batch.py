#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试自定义API接口的数据保存功能
包括客户认证和batch_id参数的测试
"""

import requests
import json
import uuid
from datetime import datetime

# 配置
BASE_URL = "http://localhost:8000"
API_ENDPOINT = "/api/v1/test22333"  # 用户提到的测试接口
ADMIN_LOGIN_URL = f"{BASE_URL}/api/v1/admin/login"
CUSTOMER_LOGIN_URL = f"{BASE_URL}/api/v1/auth/login"

def test_custom_api_with_batch():
    """
    测试自定义API接口的数据保存功能
    """
    print("=== 测试自定义API接口数据保存功能 ===")
    
    # 1. 首先获取客户认证token（如果API需要认证）
    print("\n1. 尝试获取客户认证token...")
    
    # 这里需要根据实际的客户认证方式来获取token
    # 假设有一个测试客户，需要根据实际情况调整
    customer_token = None
    
    try:
        # 使用实际的客户凭据
        login_data = {
            "app_id": "APP_O0T142KF",  # 客户ID为1的应用ID
            "app_secret": "6cd4e93d85a97495a5fe9e228bff89bd411efd671392f8753695135db9e52266"  # 对应的应用密钥
        }
        
        response = requests.post(CUSTOMER_LOGIN_URL, json=login_data)
        if response.status_code == 200:
            result = response.json()
            customer_token = result.get("access_token")
            print(f"✅ 获取客户token成功: {customer_token[:20]}...")
        else:
            print(f"⚠️ 客户登录失败: {response.status_code} - {response.text}")
            print("将测试无认证的API调用...")
    except Exception as e:
        print(f"⚠️ 客户登录异常: {e}")
        print("将测试无认证的API调用...")
    
    # 2. 测试不同场景的API调用
    test_cases = [
        {
            "name": "带batch_id的请求（无认证）",
            "data": {
                "batch_id": f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "test": "test_value_1",
                "number_field": 123
            },
            "headers": {"Content-Type": "application/json"},
            "use_auth": False
        },
        {
            "name": "带batch_id的请求（有认证）",
            "data": {
                "batch_id": f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}_auth",
                "test": "test_value_2",
                "number_field": 456
            },
            "headers": {"Content-Type": "application/json"},
            "use_auth": True
        },
        {
            "name": "不带batch_id的请求",
            "data": {
                "test": "test_value_3",
                "number_field": 789
            },
            "headers": {"Content-Type": "application/json"},
            "use_auth": False
        }
    ]
    
    print("\n2. 开始测试不同场景...")
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n--- 测试场景 {i}: {test_case['name']} ---")
        
        headers = test_case["headers"].copy()
        
        # 如果需要认证且有token，添加Authorization头
        if test_case["use_auth"] and customer_token:
            headers["Authorization"] = f"Bearer {customer_token}"
        elif test_case["use_auth"] and not customer_token:
            print("⚠️ 跳过认证测试（无有效token）")
            continue
        
        try:
            print(f"请求数据: {json.dumps(test_case['data'], ensure_ascii=False, indent=2)}")
            
            response = requests.post(
                f"{BASE_URL}{API_ENDPOINT}",
                json=test_case["data"],
                headers=headers
            )
            
            print(f"响应状态码: {response.status_code}")
            print(f"响应内容: {response.text}")
            
            if response.status_code == 200:
                result = response.json()
                print("✅ 请求成功")
                
                # 检查响应中是否包含upload_id（表示数据已保存）
                if "upload_id" in result:
                    print(f"📝 数据已保存，upload_id: {result['upload_id']}")
                if "batch_id" in result:
                    print(f"📦 批次ID: {result['batch_id']}")
            else:
                print(f"❌ 请求失败: {response.status_code}")
                
        except Exception as e:
            print(f"❌ 请求异常: {e}")
    
    print("\n=== 测试完成 ===")
    print("\n💡 提示:")
    print("- 如果API需要认证，请确保有有效的客户凭据")
    print("- 检查数据库中的data_uploads表，确认数据是否正确保存")
    print("- 观察服务器日志，查看详细的处理过程")

def test_api_configuration():
    """
    检查API配置是否存在
    """
    print("\n=== 检查API配置 ===")
    
    try:
        # 尝试获取API配置信息
        response = requests.get(f"{BASE_URL}/api/v1/admin/apis")
        if response.status_code == 200:
            apis = response.json()
            print(f"找到 {len(apis)} 个API配置")
            
            # 查找test22333相关的API
            target_api = None
            for api in apis:
                if "test22333" in api.get("endpoint", ""):
                    target_api = api
                    break
            
            if target_api:
                print(f"✅ 找到目标API: {target_api.get('name', 'N/A')}")
                print(f"   端点: {target_api.get('endpoint', 'N/A')}")
                print(f"   需要认证: {target_api.get('require_authentication', False)}")
                return target_api
            else:
                print("⚠️ 未找到test22333相关的API配置")
        else:
            print(f"❌ 获取API配置失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 检查API配置异常: {e}")
    
    return None

if __name__ == "__main__":
    print("自定义API数据保存功能测试")
    print(f"测试时间: {datetime.now()}")
    print(f"目标API: {API_ENDPOINT}")
    
    # 检查API配置
    api_config = test_api_configuration()
    
    # 执行测试
    test_custom_api_with_batch()