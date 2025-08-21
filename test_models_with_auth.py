#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试带认证的模型API调用
"""

import requests
import json


def get_auth_token():
    """获取认证token"""
    base_url = "http://127.0.0.1:8000"
    
    login_data = {
        "username": "newuser",
        "password": "newpass123"
    }
    
    try:
        headers = {"Content-Type": "application/json"}
        response = requests.post(f"{base_url}/api/v1/auth/login/json", 
                               json=login_data, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            return data.get("access_token")
        else:
            print(f"登录失败: {response.text}")
            return None
            
    except Exception as e:
        print(f"登录异常: {e}")
        return None


def test_models_api_with_auth():
    """测试带认证的模型API"""
    
    print("🔐 获取认证token...")
    token = get_auth_token()
    
    if not token:
        print("❌ 无法获取认证token，测试终止")
        return
    
    print(f"✅ 成功获取token: {token[:30]}...")
    
    base_url = "http://127.0.0.1:8000"
    headers = {"Authorization": f"Bearer {token}"}
    
    print("\n📋 测试模型API调用...")
    
    try:
        # 测试基本的模型列表API
        response = requests.get(f"{base_url}/api/v1/models/", headers=headers)
        print(f"\n状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n🎉 模型API调用成功!")
            print(f"响应数据结构:")
            print(f"  - total: {data.get('total')}")
            print(f"  - page: {data.get('page')}")
            print(f"  - size: {data.get('size')}")
            print(f"  - items: {len(data.get('items', []))} 个项目")
            
            items = data.get('items', [])
            if items:
                print(f"\n📝 模型详情:")
                for i, item in enumerate(items, 1):
                    print(f"  {i}. 名称: {item.get('name')}")
                    print(f"     版本: {item.get('version')}")
                    print(f"     类型: {item.get('model_type')}")
                    print(f"     状态: {'活跃' if item.get('is_active') else '非活跃'}")
                    print(f"     ID: {item.get('id')}")
                    print(f"     创建时间: {item.get('created_at')}")
                    print()
            else:
                print(f"\n⚠️  模型列表为空")
                
            # 测试分页参数
            print(f"\n🔄 测试分页参数...")
            response = requests.get(f"{base_url}/api/v1/models/?page=1&size=5", headers=headers)
            if response.status_code == 200:
                page_data = response.json()
                print(f"分页测试成功: 总数={page_data.get('total')}, 页码={page_data.get('page')}, 大小={page_data.get('size')}")
            else:
                print(f"分页测试失败: {response.text}")
                
        else:
            print(f"❌ 模型API调用失败")
            print(f"状态码: {response.status_code}")
            print(f"响应内容: {response.text}")
            
    except Exception as e:
        print(f"❌ API调用异常: {e}")


def test_other_apis():
    """测试其他API端点"""
    
    print("\n🔍 测试其他API端点...")
    
    token = get_auth_token()
    if not token:
        return
        
    base_url = "http://127.0.0.1:8000"
    headers = {"Authorization": f"Bearer {token}"}
    
    # 测试用户信息API
    try:
        response = requests.get(f"{base_url}/api/v1/auth/me", headers=headers)
        print(f"\n👤 用户信息API: {response.status_code}")
        if response.status_code == 200:
            user_data = response.json()
            print(f"  用户: {user_data.get('username')} ({user_data.get('email')})")
            print(f"  角色: {user_data.get('role')}")
        else:
            print(f"  失败: {response.text}")
    except Exception as e:
        print(f"  异常: {e}")
    
    # 测试部署API
    try:
        response = requests.get(f"{base_url}/api/v1/deployments/", headers=headers)
        print(f"\n🚀 部署API: {response.status_code}")
        if response.status_code == 200:
            deploy_data = response.json()
            print(f"  部署总数: {deploy_data.get('total', 0)}")
        else:
            print(f"  失败: {response.text}")
    except Exception as e:
        print(f"  异常: {e}")
    
    # 测试服务器API
    try:
        response = requests.get(f"{base_url}/api/v1/servers/", headers=headers)
        print(f"\n🖥️  服务器API: {response.status_code}")
        if response.status_code == 200:
            server_data = response.json()
            print(f"  服务器总数: {server_data.get('total', 0)}")
        else:
            print(f"  失败: {response.text}")
    except Exception as e:
        print(f"  异常: {e}")


if __name__ == "__main__":
    print("🚀 开始测试带认证的模型API...")
    print("=" * 60)
    
    test_models_api_with_auth()
    test_other_apis()
    
    print("\n" + "=" * 60)
    print("✅ 测试完成!")