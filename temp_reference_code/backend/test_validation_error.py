#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试验证异常的错误码
"""

import requests
import json

def get_customer_token():
    """
    获取客户认证token
    """
    try:
        login_data = {
            "app_id": "APP_O0T142KF",
            "app_secret": "6cd4e93d85a97495a5fe9e228bff89bd411efd671392f8753695135db9e52266"
        }
        
        response = requests.post("http://localhost:8000/api/v1/auth/login", json=login_data)
        if response.status_code == 200:
            result = response.json()
            return result.get("access_token")
        else:
            print(f"获取token失败: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"获取token异常: {e}")
        return None

def test_validation_error():
    """
    测试验证异常的错误码
    """
    # 获取有效token
    token = get_customer_token()
    if not token:
        print("无法获取有效token，跳过测试")
        return
    
    print(f"获取到token: {token[:20]}...")
    
    # 测试缺少必填字段的验证异常
    print("\n=== 测试验证异常（缺少必填字段） ===")
    try:
        url = "http://localhost:8000/api/v1/test22333"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        }
        # 发送缺少必填字段'test'的请求
        data = {"wrong_field": "data"}
        
        response = requests.post(url, headers=headers, json=data)
        print(f"状态码: {response.status_code}")
        print(f"响应内容: {response.text}")
        
        if response.status_code >= 400:
            response_data = response.json()
            code = response_data.get('code')
            print(f"错误码类型: {type(code)}")
            print(f"错误码值: {code}")
            print(f"是否为数字: {isinstance(code, int)}")
            
            # 检查是否为400错误码
            if response.status_code == 400:
                print("✅ 验证异常正确返回400状态码")
            else:
                print(f"❌ 验证异常返回了{response.status_code}状态码，应该是400")
                
    except Exception as e:
        print(f"请求异常: {e}")

if __name__ == "__main__":
    test_validation_error()