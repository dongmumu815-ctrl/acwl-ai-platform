#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
性能计时测试脚本

测试API处理各个环节的计时功能
"""

import requests
import json
import time
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_api_performance():
    """
    测试API性能计时功能
    """
    print("=== API性能计时测试 ===")
    
    # API配置
    base_url = "http://localhost:8000"
    api_code = "test_api"
    batch_id = f"test_batch_{int(time.time())}"
    
    # 测试数据
    test_data = {
        "name": "测试用户",
        "age": 25,
        "email": "test@example.com"
    }
    
    # 请求头
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer test_token_123"
    }
    
    print(f"测试URL: {base_url}/api/v1/custom/3/{api_code}")
    print(f"批次ID: {batch_id}")
    print(f"测试数据: {json.dumps(test_data, ensure_ascii=False)}")
    
    try:
        # 发送请求
        start_time = time.time()
        response = requests.post(
            f"{base_url}/api/v1/custom/3/{api_code}",
            json=test_data,
            headers=headers,
            timeout=30
        )
        end_time = time.time()
        
        request_time = (end_time - start_time) * 1000
        print(f"\n请求总耗时: {request_time:.2f}ms")
        print(f"响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"响应内容: {json.dumps(result, ensure_ascii=False, indent=2)}")
            print("✅ API调用成功")
        else:
            print(f"❌ API调用失败: {response.text}")
            
    except requests.exceptions.Timeout:
        print("❌ 请求超时")
    except requests.exceptions.ConnectionError:
        print("❌ 连接失败，请确保API服务正在运行")
    except Exception as e:
        print(f"❌ 请求异常: {str(e)}")

def test_batch_api_performance():
    """
    测试批量API性能计时功能
    """
    print("\n=== 批量API性能计时测试 ===")
    
    # API配置
    base_url = "http://localhost:8000"
    api_code = "test_api"
    batch_id = f"batch_{int(time.time())}"
    
    # 批量测试数据
    test_data = {
        "data": [
            {"name": "用户1", "age": 25, "email": "user1@example.com"},
            {"name": "用户2", "age": 30, "email": "user2@example.com"},
            {"name": "用户3", "age": 35, "email": "user3@example.com"}
        ]
    }
    
    # 请求头
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer test_token_123"
    }
    
    print(f"测试URL: {base_url}/api/v1/custom/3/{batch_id}/{api_code}")
    print(f"批次数据量: {len(test_data['data'])}条")
    
    try:
        # 发送批量请求
        start_time = time.time()
        response = requests.post(
            f"{base_url}/api/v1/custom/3/{batch_id}/{api_code}",
            json=test_data,
            headers=headers,
            timeout=30
        )
        end_time = time.time()
        
        request_time = (end_time - start_time) * 1000
        print(f"\n批量请求总耗时: {request_time:.2f}ms")
        print(f"响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"响应内容: {json.dumps(result, ensure_ascii=False, indent=2)}")
            print("✅ 批量API调用成功")
        else:
            print(f"❌ 批量API调用失败: {response.text}")
            
    except requests.exceptions.Timeout:
        print("❌ 批量请求超时")
    except requests.exceptions.ConnectionError:
        print("❌ 连接失败，请确保API服务正在运行")
    except Exception as e:
        print(f"❌ 批量请求异常: {str(e)}")

def main():
    """
    主函数
    """
    print("开始API性能计时测试...")
    print("注意：请确保API服务正在运行 (python main.py)")
    print("测试完成后，请查看API服务的日志输出，观察各环节的计时信息")
    
    # 等待用户确认
    input("\n按回车键开始测试...")
    
    # 测试单条API
    test_api_performance()
    
    # 等待一下
    time.sleep(2)
    
    # 测试批量API
    test_batch_api_performance()
    
    print("\n=== 测试完成 ===")
    print("请查看API服务的控制台输出，观察以下计时信息:")
    print("- [API处理] 各环节的详细计时")
    print("- [单条数据处理] 数据库操作计时")
    print("- [批量数据处理] 批量处理计时")
    print("- 总处理时间和性能警告")

if __name__ == "__main__":
    main()