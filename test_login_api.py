#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试登录和模型API调用
"""

import requests
import json


def test_login_and_models_api():
    """测试登录和模型API调用"""
    
    base_url = "http://127.0.0.1:8000"
    
    print("测试用户登录和模型API调用...")
    
    # 使用刚才注册的用户登录
    login_data = {
        "username": "newuser",
        "password": "newpass123"
    }
    
    try:
        # JSON格式登录
        headers = {"Content-Type": "application/json"}
        response = requests.post(f"{base_url}/api/v1/auth/login/json", 
                               json=login_data, headers=headers)
        print(f"\n登录状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            access_token = data.get("access_token")
            user_info = data.get("user")
            
            print(f"登录成功!")
            print(f"  Token: {access_token[:50]}...")
            print(f"  用户: {user_info.get('username')} ({user_info.get('email')})")
            print(f"  角色: {user_info.get('role')}")
            print(f"  用户ID: {user_info.get('id')}")
            
            # 使用token测试模型API
            print("\n使用token测试模型API...")
            auth_headers = {"Authorization": f"Bearer {access_token}"}
            
            # 测试不带参数的请求
            response = requests.get(f"{base_url}/api/v1/models/", headers=auth_headers)
            print(f"\n模型API状态码: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"\n✅ 模型API调用成功!")
                print(f"  总数: {data.get('total', 'N/A')}")
                print(f"  页码: {data.get('page', 'N/A')}")
                print(f"  每页大小: {data.get('size', 'N/A')}")
                print(f"  项目数量: {len(data.get('items', []))}")
                
                if data.get('items'):
                    print("\n📋 模型列表:")
                    for i, item in enumerate(data['items']):
                        print(f"  {i+1}. {item.get('name')}:{item.get('version')} ")
                        print(f"      类型: {item.get('model_type')}, 状态: {'活跃' if item.get('is_active') else '非活跃'}")
                        print(f"      创建时间: {item.get('created_at')}")
                        print()
                else:
                    print("\n⚠️  没有找到模型数据")
                    
                # 测试带分页参数的请求
                print("\n测试带分页参数的模型API...")
                response = requests.get(f"{base_url}/api/v1/models/?page=1&size=10", headers=auth_headers)
                print(f"分页API状态码: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"分页API成功: 总数={data.get('total')}, 页码={data.get('page')}, 大小={data.get('size')}")
                else:
                    print(f"分页API失败: {response.text}")
                    
            else:
                print(f"❌ 模型API调用失败: {response.text}")
                
        else:
            print(f"❌ 登录失败: {response.text}")
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")


def test_form_login():
    """测试表单格式登录"""
    
    base_url = "http://127.0.0.1:8000"
    
    print("\n\n测试表单格式登录...")
    
    # 表单格式登录
    login_data = {
        "username": "newuser",
        "password": "newpass123"
    }
    
    try:
        response = requests.post(f"{base_url}/api/v1/auth/login", data=login_data)
        print(f"表单登录状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            access_token = data.get("access_token")
            
            print(f"表单登录成功!")
            print(f"  Token: {access_token[:50]}...")
            print(f"  Token类型: {data.get('token_type')}")
            print(f"  过期时间: {data.get('expires_in')}秒")
            
        else:
            print(f"表单登录失败: {response.text}")
            
    except Exception as e:
        print(f"表单登录测试失败: {e}")


if __name__ == "__main__":
    print("🚀 开始测试登录和模型API...")
    print("注意：请确保后端服务器正在运行")
    print("=" * 50)
    
    test_login_and_models_api()
    test_form_login()
    
    print("\n" + "=" * 50)
    print("✅ 测试完成!")