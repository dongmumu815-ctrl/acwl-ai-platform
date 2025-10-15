#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试API调用过程

检查API调用过程中的详细信息，特别是customer_id的传递
"""

import requests
import json
from datetime import datetime

def debug_api_call():
    """
    调试API调用过程
    """
    base_url = "http://localhost:8000"
    
    print("=" * 80)
    print("调试API调用过程")
    print("=" * 80)
    
    # 1. 客户登录获取token
    print("\n1. 客户登录获取token...")
    login_data = {
        "app_id": "APP_RA5T1GAG",
        "app_secret": "06c697d0e51067293215e8e601028a51a82266d22f8fdeda0812b5a015fcabf9"
    }
    
    try:
        login_response = requests.post(
            f"{base_url}/api/v1/auth/login",
            json=login_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"   登录响应状态码: {login_response.status_code}")
        print(f"   登录响应内容: {login_response.text}")
        
        if login_response.status_code == 200:
            login_result = login_response.json()
            token = login_result["access_token"]
            customer_info = login_result["customer"]
            print(f"   ✅ 登录成功!")
            print(f"   Token: {token[:50]}...")
            print(f"   客户ID: {customer_info['id']}")
            print(f"   客户名称: {customer_info['name']}")
        else:
            print(f"   ❌ 登录失败: {login_response.text}")
            return
            
    except Exception as e:
        print(f"   ❌ 登录异常: {str(e)}")
        return
    
    # 2. 调用自定义API（带认证）
    print("\n2. 调用自定义API（带认证）...")
    
    batch_id = f"debug_batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    print(f"   Authorization: Bearer {token[:20]}...")
    print(f"   Batch ID: {batch_id}")
    
    api_data = {
        "test": "debug_test_value",
        "batch_id": batch_id
    }
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    
    try:
        api_response = requests.post(
            f"{base_url}/api/v1/test22333",
            json=api_data,
            headers=headers
        )
        
        print(f"   API响应状态码: {api_response.status_code}")
        print(f"   API响应内容: {api_response.text}")
        
        if api_response.status_code == 200:
            api_result = api_response.json()
            print(f"   ✅ API调用成功!")
            print(f"   响应数据: {json.dumps(api_result, indent=2, ensure_ascii=False)}")
            
            # 检查响应中是否包含upload_id
            if "upload_id" in api_result:
                print(f"   📝 数据上传ID: {api_result['upload_id']}")
            else:
                print(f"   ⚠️  响应中没有upload_id，可能数据未保存")
                
        else:
            print(f"   ❌ API调用失败: {api_response.text}")
            
    except Exception as e:
        print(f"   ❌ API调用异常: {str(e)}")
    
    print("\n" + "=" * 80)
    print("调试完成")
    print("=" * 80)

if __name__ == "__main__":
    debug_api_call()