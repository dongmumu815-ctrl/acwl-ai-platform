#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试模型API是否正常工作
"""

import requests
import json

def login_and_get_token():
    """
    登录并获取访问令牌
    """
    login_url = "http://localhost:8000/api/v1/auth/login/json"
    login_data = {
        "email": "admin@acwl.ai",
        "password": "password"
    }
    
    print("正在登录获取访问令牌...")
    response = requests.post(login_url, json=login_data)
    
    if response.status_code == 200:
        data = response.json()
        token = data.get("access_token")
        print("✅ 登录成功!")
        return token
    else:
        print(f"❌ 登录失败: {response.status_code}")
        print(f"错误信息: {response.text}")
        return None

def test_models_api():
    """
    测试模型API接口
    """
    try:
        # 先登录获取token
        token = login_and_get_token()
        if not token:
            return
        
        # 测试获取模型列表
        url = "http://localhost:8000/api/v1/models/"
        params = {"page": 1, "size": 20}
        headers = {"Authorization": f"Bearer {token}"}
        
        print(f"\n正在测试模型API: {url}")
        print(f"请求参数: {params}")
        
        response = requests.get(url, params=params, headers=headers)
        
        print(f"响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ 模型API测试成功!")
            print(f"总数: {data.get('total', 0)}")
            print(f"返回模型数量: {len(data.get('items', []))}")
            
            # 显示前几个模型的信息
            for i, model in enumerate(data.get('items', [])[:3]):
                print(f"模型 {i+1}: {model.get('name')} ({model.get('model_type')})")
        else:
            print(f"❌ 模型API测试失败: {response.status_code}")
            print(f"错误信息: {response.text}")
            
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {str(e)}")

if __name__ == "__main__":
    test_models_api()