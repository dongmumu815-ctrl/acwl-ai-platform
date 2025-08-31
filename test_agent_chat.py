#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试Agent聊天API
"""

import requests
import json

def test_agent_chat():
    """测试Agent聊天功能"""
    base_url = "http://localhost:8082"
    
    # 1. 登录获取token
    login_data = {
        "username": "admin",
        "password": "admin123"
    }
    
    try:
        login_response = requests.post(
            f"{base_url}/api/v1/auth/login",
            json=login_data,
            headers={"Content-Type": "application/json"}
        )
        
        if login_response.status_code != 200:
            print(f"登录失败: {login_response.status_code}")
            print(f"响应: {login_response.text}")
            return
            
        token_data = login_response.json()
        access_token = token_data.get("access_token")
        
        if not access_token:
            print("未获取到访问令牌")
            return
            
        print(f"登录成功，获取到token: {access_token[:20]}...")
        
        # 2. 测试Agent聊天
        chat_data = {
            "message": "测试消息",
            "session_id": "test_session_123"
        }
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}"
        }
        
        chat_response = requests.post(
            f"{base_url}/api/v1/agents/32/chat",
            json=chat_data,
            headers=headers
        )
        
        print(f"聊天API状态码: {chat_response.status_code}")
        print(f"聊天API响应: {chat_response.text}")
        
        if chat_response.status_code == 200:
            result = chat_response.json()
            print("\n聊天成功!")
            print(f"消息: {result.get('message', 'N/A')}")
            print(f"处理时间: {result.get('processing_time', 'N/A')}ms")
        else:
            print(f"\n聊天失败: {chat_response.status_code}")
            
    except Exception as e:
        print(f"测试过程中发生错误: {str(e)}")

if __name__ == "__main__":
    test_agent_chat()