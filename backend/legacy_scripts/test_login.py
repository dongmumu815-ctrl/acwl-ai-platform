#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import requests
import json

def test_login():
    """测试登录功能"""
    
    # 服务器URL
    base_url = "http://localhost:8000"
    login_url = f"{base_url}/api/v1/auth/login/json"
    
    # 登录数据
    login_data = {
        "email": "admin@acwl.ai",
        "password": "password"
    }
    
    print("测试登录功能...")
    print(f"URL: {login_url}")
    print(f"数据: {json.dumps(login_data, indent=2)}")
    print("="*50)
    
    try:
        # 发送登录请求
        response = requests.post(
            login_url,
            json=login_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print(f"状态码: {response.status_code}")
        print(f"响应头: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print("\n✅ 登录成功!")
            print(f"访问令牌: {result.get('access_token', 'N/A')[:50]}...")
            print(f"令牌类型: {result.get('token_type', 'N/A')}")
            print(f"过期时间: {result.get('expires_in', 'N/A')} 秒")
            
            user_info = result.get('user', {})
            if user_info:
                print(f"\n用户信息:")
                print(f"  ID: {user_info.get('id')}")
                print(f"  用户名: {user_info.get('username')}")
                print(f"  邮箱: {user_info.get('email')}")
                print(f"  角色: {user_info.get('role')}")
        else:
            print(f"\n❌ 登录失败!")
            try:
                error_detail = response.json()
                print(f"错误详情: {json.dumps(error_detail, indent=2, ensure_ascii=False)}")
            except:
                print(f"错误内容: {response.text}")
                
    except requests.exceptions.ConnectionError:
        print("❌ 连接失败: 服务器可能未启动")
        print("请确保后端服务器正在运行 (python main.py)")
    except requests.exceptions.Timeout:
        print("❌ 请求超时")
    except Exception as e:
        print(f"❌ 请求错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_login()