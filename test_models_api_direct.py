#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
直接测试模型API接口
"""

import requests
import json


def test_models_api_with_requests():
    """使用requests库测试模型API接口"""
    
    base_url = "http://127.0.0.1:8000"
    
    # 测试根路径
    print("测试根路径...")
    try:
        response = requests.get(f"{base_url}/")
        print(f"状态码: {response.status_code}")
        print(f"响应内容: {response.text}")
    except Exception as e:
        print(f"请求失败: {e}")
    
    # 测试健康检查接口
    print("\n测试健康检查接口...")
    try:
        response = requests.get(f"{base_url}/health")
        print(f"状态码: {response.status_code}")
        print(f"响应内容: {response.text}")
    except Exception as e:
        print(f"请求失败: {e}")
    
    # 测试API健康检查接口
    print("\n测试API健康检查接口...")
    try:
        response = requests.get(f"{base_url}/api/v1/health/")
        print(f"状态码: {response.status_code}")
        print(f"响应内容: {response.text}")
    except Exception as e:
        print(f"请求失败: {e}")
    
    # 测试不带认证的模型API请求
    print("\n测试不带认证的模型API请求...")
    try:
        response = requests.get(f"{base_url}/api/v1/models/")
        print(f"状态码: {response.status_code}")
        print(f"响应内容: {response.text[:500]}...")
    except Exception as e:
        print(f"请求失败: {e}")
    
    # 测试带分页参数的请求
    print("\n测试带分页参数的模型API请求...")
    try:
        params = {"page": 1, "size": 20}
        response = requests.get(f"{base_url}/api/v1/models/", params=params)
        print(f"状态码: {response.status_code}")
        print(f"响应内容: {response.text[:500]}...")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"\n解析后的响应数据:")
                print(f"总数: {data.get('total', 'N/A')}")
                print(f"页码: {data.get('page', 'N/A')}")
                print(f"每页大小: {data.get('size', 'N/A')}")
                print(f"项目数量: {len(data.get('items', []))}")
                
                if data.get('items'):
                    print("\n前3个模型:")
                    for i, item in enumerate(data['items'][:3]):
                        print(f"  {i+1}. {item.get('name')}:{item.get('version')} (Type: {item.get('model_type')})")
                else:
                    print("\n响应中没有模型数据")
            except json.JSONDecodeError as e:
                print(f"JSON解析失败: {e}")
    except Exception as e:
        print(f"请求失败: {e}")
    
    # 测试不同的URL格式
    print("\n测试不同的URL格式...")
    urls_to_test = [
        f"{base_url}/api/v1/models",  # 不带斜杠
        f"{base_url}/api/v1/models/?params[page]=1&params[size]=20",  # 前端实际使用的格式
    ]
    
    for url in urls_to_test:
        try:
            print(f"\n测试URL: {url}")
            response = requests.get(url)
            print(f"状态码: {response.status_code}")
            print(f"响应内容: {response.text[:200]}...")
        except Exception as e:
            print(f"请求失败: {e}")


if __name__ == "__main__":
    print("开始测试模型API接口...")
    print("注意：请确保后端服务器正在运行 (python -m uvicorn backend.app.main:app --reload)")
    test_models_api_with_requests()