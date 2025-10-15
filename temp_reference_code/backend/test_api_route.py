#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试自定义API路由

用于验证API路由是否正常工作的脚本
"""

import requests
import json

def test_api_route():
    """
    测试自定义API路由
    """
    # 测试URL
    base_url = "http://localhost:8000"
    api_code = "test22333"
    
    # 测试不同的路径
    test_urls = [
        f"{base_url}/api/v1/{api_code}",  # 新添加的v1路由
        f"{base_url}/api/custom/{api_code}"  # 原始的custom路由
    ]
    
    for url in test_urls:
        print(f"\n测试URL: {url}")
        print("-" * 50)
        
        try:
            # 发送POST请求
            response = requests.post(
                url,
                json={"test": "data"},
                timeout=10
            )
            
            print(f"状态码: {response.status_code}")
            print(f"响应头: {dict(response.headers)}")
            
            if response.status_code == 200:
                print(f"✅ 成功: {response.text}")
            elif response.status_code == 404:
                print(f"❌ 404错误: 路由未找到")
            elif response.status_code == 500:
                print(f"❌ 500错误: 服务器内部错误")
                print(f"响应内容: {response.text}")
            else:
                print(f"⚠️  其他状态码: {response.status_code}")
                print(f"响应内容: {response.text}")
                
        except requests.exceptions.ConnectionError:
            print("❌ 连接错误: 服务器可能未启动")
        except requests.exceptions.Timeout:
            print("❌ 超时错误: 请求超时")
        except Exception as e:
            print(f"❌ 其他错误: {e}")

if __name__ == "__main__":
    print("测试自定义API路由")
    print("=" * 50)
    test_api_route()