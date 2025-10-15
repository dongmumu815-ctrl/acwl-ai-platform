#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 logout API 接口

验证新添加的 logout 接口是否正常工作
"""

import requests
import json
import sys

def test_logout_api():
    """
    测试 logout API 接口
    
    测试流程：
    1. 先进行登录获取 token
    2. 使用 token 调用 logout 接口
    3. 验证响应结果
    """
    base_url = "http://localhost:3005/api/v1"
    
    print("🚀 开始测试 logout API 接口")
    print("=" * 50)
    
    # 步骤1: 登录获取 token
    print("🔐 步骤1: 登录获取访问令牌...")
    
    login_data = {
        "username": "admin",
        "password": "admin123"
    }
    
    try:
        login_response = requests.post(
            f"{base_url}/auth/login/json",
            json=login_data,
            timeout=10
        )
        
        print(f"登录状态码: {login_response.status_code}")
        
        if login_response.status_code == 200:
            login_result = login_response.json()
            if login_result.get('success') and 'data' in login_result:
                token = login_result['data'].get('access_token')
                print(f"✅ 登录成功，获取到token: {token[:20]}...")
            else:
                print("❌ 登录失败：响应格式不正确")
                print(f"响应: {login_result}")
                return False
        else:
            print(f"❌ 登录失败: {login_response.status_code}")
            print(f"错误: {login_response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 登录请求失败: {e}")
        return False
    
    # 步骤2: 测试 logout 接口
    print("\n🚪 步骤2: 测试 logout 接口...")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        logout_response = requests.post(
            f"{base_url}/auth/logout",
            headers=headers,
            timeout=10
        )
        
        print(f"Logout 状态码: {logout_response.status_code}")
        
        if logout_response.status_code == 200:
            logout_result = logout_response.json()
            print(f"✅ Logout 成功!")
            print(f"响应内容: {json.dumps(logout_result, indent=2, ensure_ascii=False)}")
            return True
        else:
            print(f"❌ Logout 失败: {logout_response.status_code}")
            print(f"错误: {logout_response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Logout 请求失败: {e}")
        return False

def test_logout_without_token():
    """
    测试没有 token 的情况下调用 logout 接口
    """
    base_url = "http://localhost:3005/api/v1"
    
    print("\n🔒 测试无 token 访问 logout 接口...")
    
    try:
        logout_response = requests.post(
            f"{base_url}/auth/logout",
            timeout=10
        )
        
        print(f"无token访问状态码: {logout_response.status_code}")
        
        if logout_response.status_code == 401:
            print("✅ 正确返回 401 未授权错误")
            return True
        else:
            print(f"⚠️  预期返回 401，实际返回: {logout_response.status_code}")
            print(f"响应: {logout_response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return False

if __name__ == "__main__":
    print("测试 Logout API 接口")
    print("=" * 50)
    
    # 测试正常的 logout 流程
    success1 = test_logout_api()
    
    # 测试无 token 的情况
    success2 = test_logout_without_token()
    
    print("\n" + "=" * 50)
    if success1 and success2:
        print("🎉 所有测试通过!")
        sys.exit(0)
    else:
        print("❌ 部分测试失败!")
        sys.exit(1)