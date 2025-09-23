#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试修复后的搜索API功能
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

def test_search_api():
    """
    测试搜索API功能
    """
    token = get_auth_token()
    if not token:
        return
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # 测试搜索请求
    search_data = {
        "page": 1,
        "size": 20,
        "sort_by": "created_at",
        "sort_order": "desc"
    }
    
    print(f"\n🔍 测试搜索API...")
    print(f"请求数据: {json.dumps(search_data, indent=2)}")
    
    try:
        response = requests.post(
            "http://localhost:8082/api/v1/resource-packages/search",
            json=search_data,
            headers=headers
        )
        
        print(f"\n响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 搜索API测试成功!")
            print(f"总数: {result.get('total', 0)}")
            print(f"当前页: {result.get('page', 1)}")
            print(f"每页大小: {result.get('size', 20)}")
            print(f"总页数: {result.get('pages', 0)}")
            
            items = result.get('items', [])
            print(f"返回的资源包数量: {len(items)}")
            
            if items:
                print(f"\n前3个资源包:")
                for i, item in enumerate(items[:3]):
                    print(f"  {i+1}. ID: {item.get('id')}, 名称: {item.get('name')}")
                    print(f"     类型: {item.get('type')}, 创建时间: {item.get('created_at')}")
        else:
            print(f"❌ 搜索API测试失败")
            print(f"错误响应: {response.text}")
            
    except Exception as e:
        print(f"❌ 测试异常: {str(e)}")

if __name__ == "__main__":
    test_search_api()