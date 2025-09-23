#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试资源包API的脚本
使用有效的token来获取资源包详情
"""

import requests
import json

def test_package_api():
    """
    测试资源包API，检查dynamic_conditions字段
    """
    # 使用提供的有效token
    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI1IiwiZXhwIjoxNzU4NjI0OTY4fQ.W1W7RCekbb9Ih-QLiWi7eSth8P9WI9um4wIIAwtqX8E"
    
    # API端点
    url = "http://localhost:3005/api/v1/resource-packages/4"
    
    # 请求头
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        print("正在测试资源包API...")
        print(f"URL: {url}")
        print(f"Token: {token[:50]}...")
        
        # 发送请求
        response = requests.get(url, headers=headers)
        
        print(f"\n响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("\n✅ API请求成功!")
            print(f"响应数据结构:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
            
            # 检查dynamic_conditions字段
            if 'data' in data and 'dynamic_conditions' in data['data']:
                dynamic_conditions = data['data']['dynamic_conditions']
                print(f"\n✅ 找到dynamic_conditions字段:")
                print(json.dumps(dynamic_conditions, indent=2, ensure_ascii=False))
                
                if dynamic_conditions:
                    print(f"\n✅ dynamic_conditions不为空，包含 {len(dynamic_conditions)} 个条件")
                else:
                    print(f"\n⚠️ dynamic_conditions为空")
            else:
                print(f"\n❌ 未找到dynamic_conditions字段")
                if 'data' in data:
                    print(f"可用字段: {list(data['data'].keys())}")
        else:
            print(f"\n❌ API请求失败")
            try:
                error_data = response.json()
                print(f"错误信息: {json.dumps(error_data, indent=2, ensure_ascii=False)}")
            except:
                print(f"错误信息: {response.text}")
                
    except requests.exceptions.ConnectionError:
        print("❌ 连接失败，请确保后端服务正在运行")
    except Exception as e:
        print(f"❌ 请求异常: {str(e)}")

if __name__ == "__main__":
    test_package_api()