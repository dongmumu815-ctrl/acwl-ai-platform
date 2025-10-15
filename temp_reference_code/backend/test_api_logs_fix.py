#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试API日志序列化修复

验证管理员API日志查询接口是否正常工作
"""

import requests
import json
from datetime import datetime

def test_api_logs_serialization():
    """
    测试API日志序列化修复
    """
    print("🔍 测试API日志序列化修复...")
    print("=" * 60)
    
    # API基础URL
    base_url = "http://localhost:8000"
    
    # 管理员登录
    login_url = f"{base_url}/api/v1/admin/login"
    login_data = {
        "username": "admin",
        "password": "admin123"
    }
    
    try:
        print("📝 正在登录管理员账户...")
        login_response = requests.post(login_url, json=login_data)
        
        if login_response.status_code != 200:
            print(f"❌ 登录失败: {login_response.status_code}")
            print(f"响应内容: {login_response.text}")
            return
        
        login_result = login_response.json()
        access_token = login_result["access_token"]
        print(f"✅ 登录成功，获取到访问令牌")
        
        # 设置请求头
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        # 测试API日志查询
        api_id = 3  # 使用API ID 3进行测试
        logs_url = f"{base_url}/api/v1/admin/apis/{api_id}/logs?page=1&size=20"
        
        print(f"\n📊 正在查询API {api_id} 的调用日志...")
        logs_response = requests.get(logs_url, headers=headers)
        
        print(f"响应状态码: {logs_response.status_code}")
        
        if logs_response.status_code == 200:
            print("✅ API日志查询成功！")
            
            try:
                logs_data = logs_response.json()
                print(f"\n📋 响应数据结构:")
                print(f"  - success: {logs_data.get('success')}")
                print(f"  - message: {logs_data.get('message')}")
                print(f"  - data 类型: {type(logs_data.get('data'))}")
                print(f"  - data 长度: {len(logs_data.get('data', []))}")
                
                if logs_data.get('data'):
                    first_log = logs_data['data'][0]
                    print(f"\n📝 第一条日志示例:")
                    print(f"  - ID: {first_log.get('id')}")
                    print(f"  - API ID: {first_log.get('api_id')}")
                    print(f"  - 客户ID: {first_log.get('customer_id')}")
                    print(f"  - HTTP方法: {first_log.get('http_method')}")
                    print(f"  - 响应状态: {first_log.get('response_status')}")
                    print(f"  - 是否成功: {first_log.get('is_success')}")
                    print(f"  - 创建时间: {first_log.get('created_at')}")
                
                pagination = logs_data.get('pagination', {})
                print(f"\n📄 分页信息:")
                print(f"  - 当前页: {pagination.get('page')}")
                print(f"  - 每页大小: {pagination.get('size')}")
                print(f"  - 总数: {pagination.get('total')}")
                print(f"  - 总页数: {pagination.get('pages')}")
                
            except json.JSONDecodeError as e:
                print(f"❌ JSON解析失败: {e}")
                print(f"响应内容: {logs_response.text[:500]}...")
                
        else:
            print(f"❌ API日志查询失败: {logs_response.status_code}")
            print(f"响应内容: {logs_response.text}")
            
            if logs_response.status_code == 500:
                print("\n🔍 这可能是序列化错误，检查响应内容中是否包含序列化相关错误信息")
        
        print(f"\n✅ 测试完成 - {datetime.now()}")
        
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到服务器，请确保服务器正在运行")
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")

if __name__ == "__main__":
    test_api_logs_serialization()