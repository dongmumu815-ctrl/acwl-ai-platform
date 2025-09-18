#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试原始API请求
"""

import requests
import json

def test_original_api():
    """测试原始的API请求"""
    try:
        # 获取认证token
        auth_response = requests.post(
            'http://localhost:3005/api/v1/auth/login',
            json={
                'username': 'admin',
                'password': 'admin123'
            }
        )
        
        if auth_response.status_code != 200:
            print(f'认证失败: {auth_response.status_code}')
            print(auth_response.text)
            return
            
        token = auth_response.json()['access_token']
        print('✅ 获取认证token成功')
        
        # 测试原始API请求
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        # 原始请求URL
        url = 'http://localhost:3005/api/v1/datasources/8/schemas/acwl-agents/tables/?_t=1758131146611'
        
        print(f'\n测试原始API请求:')
        print(f'URL: {url}')
        
        response = requests.get(url, headers=headers)
        
        print(f'\n响应状态码: {response.status_code}')
        print(f'响应头: {dict(response.headers)}')
        
        if response.status_code == 200:
            data = response.json()
            print(f'\n✅ API请求成功！')
            print(f'返回的表数量: {len(data)}')
            
            if data:
                print(f'\n前3个表:')
                for i, table in enumerate(data[:3]):
                    print(f'  表{i+1}: {table}')
        else:
            print(f'\n❌ API请求失败')
            print(f'错误响应: {response.text}')
            
    except Exception as e:
        print(f'测试失败: {str(e)}')

if __name__ == "__main__":
    test_original_api()