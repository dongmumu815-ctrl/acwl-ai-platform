#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agent聊天API测试
测试与Agent的聊天功能
"""

import requests
import json

def test_agent_chat():
    """
    测试Agent聊天API
    """
    base_url = "http://localhost:8082"
    
    # 1. 先登录获取token
    login_url = f"{base_url}/api/v1/auth/login/json"
    login_data = {
        "username": "admin",
        "password": "123456"
    }
    
    print("正在登录...")
    try:
        login_response = requests.post(login_url, json=login_data)
        print(f"登录响应状态码: {login_response.status_code}")
        
        if login_response.status_code == 200:
            login_result = login_response.json()
            token = login_result.get("access_token")
            print(f"登录成功，获取到token: {token[:20]}...")
        else:
            print(f"登录失败: {login_response.text}")
            return False
    except Exception as e:
        print(f"登录请求异常: {str(e)}")
        return False
    
    # 2. 测试Agent聊天
    agent_id = 32  # 使用Agent ID 32
    chat_url = f"{base_url}/api/v1/agents/{agent_id}/chat"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    chat_data = {
        "message": "你好，请简单回复一下",
        "enable_memory": False
    }
    
    print(f"\n正在测试Agent {agent_id}聊天...")
    try:
        chat_response = requests.post(chat_url, headers=headers, json=chat_data)
        print(f"聊天响应状态码: {chat_response.status_code}")
        print(f"响应头: {dict(chat_response.headers)}")
        
        if chat_response.status_code == 200:
            chat_result = chat_response.json()
            print(f"聊天成功!")
            print(f"响应内容: {json.dumps(chat_result, indent=2, ensure_ascii=False)}")
            return True
        else:
            print(f"聊天失败: {chat_response.text}")
            return False
            
    except Exception as e:
        print(f"聊天请求异常: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Agent聊天API测试开始")
    print("=" * 50)
    
    success = test_agent_chat()
    
    print("\n" + "=" * 50)
    if success:
        print("测试成功! 🎉")
    else:
        print("测试失败! 😞")