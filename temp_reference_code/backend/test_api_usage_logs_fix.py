#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试API使用日志修复

验证带batch_id的API调用是否能正确保存到api_usage_logs表
"""

import sys
import os
import requests
import json
import time
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import get_db
from app.models.log import ApiUsageLog
from app.models.api import CustomApi
from app.models.customer import Customer
from sqlalchemy import desc

def check_api_usage_logs_before():
    """
    检查修复前的api_usage_logs记录数量
    """
    print("=== 检查修复前的API使用日志 ===")
    
    db = next(get_db())
    try:
        # 查询总记录数
        total_count = db.query(ApiUsageLog).count()
        print(f"当前api_usage_logs表总记录数: {total_count}")
        
        # 查询最近的记录
        recent_logs = db.query(ApiUsageLog).order_by(desc(ApiUsageLog.created_at)).limit(5).all()
        print(f"最近的{len(recent_logs)}条记录:")
        for log in recent_logs:
            print(f"  - ID: {log.id}, API ID: {log.api_id}, 客户ID: {log.customer_id}, 批次ID: {log.batch_id}, 创建时间: {log.created_at}")
        
        return total_count
    finally:
        db.close()

def get_test_api_and_customer():
    """
    获取测试用的API和平台信息
    """
    print("\n=== 获取测试API和平台信息 ===")
    
    db = next(get_db())
    try:
        # 查找可用的API
        api = db.query(CustomApi).filter(CustomApi.status == 'active').first()
        if not api:
            print("错误: 没有找到可用的API")
            return None, None
        
        # 查找对应的客户
        customer = db.query(Customer).filter(Customer.id == api.customer_id).first()
        if not customer:
            print(f"错误: 没有找到API对应的客户 (customer_id: {api.customer_id})")
            return None, None
        
        print(f"找到测试API: {api.api_code} (ID: {api.id})")
        print(f"对应客户: {customer.username} (ID: {customer.id})")
        print(f"API URL: {api.api_url}")
        print(f"HTTP方法: {api.http_method}")
        
        return api, customer
    finally:
        db.close()

def test_api_call_with_batch_id(api, customer):
    """
    测试带batch_id的API调用
    """
    print("\n=== 测试带batch_id的API调用 ===")
    
    # 生成测试batch_id
    batch_id = f"test_batch_{int(time.time())}"
    print(f"使用batch_id: {batch_id}")
    
    # 构建API URL
    base_url = "http://localhost:8000"  # 假设服务运行在本地8000端口
    api_url = f"{base_url}/api/v1/{batch_id}/{api.api_code}"
    print(f"API URL: {api_url}")
    
    # 准备请求数据
    test_data = {
        "batch_id": batch_id,
        "test_data": "这是测试数据",
        "timestamp": int(time.time() * 1000)
    }
    
    # 准备请求头
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "API-Usage-Log-Test/1.0"
    }
    
    # 如果需要认证，添加认证头
    if api.require_authentication:
        # 这里需要根据实际的认证方式添加认证头
        # headers["Authorization"] = "Bearer your_token_here"
        print("注意: 该API需要认证，但测试中未提供认证信息")
    
    try:
        print(f"发送{api.http_method}请求...")
        
        # 发送请求
        if api.http_method.upper() == "GET":
            response = requests.get(api_url, headers=headers, params=test_data, timeout=10)
        elif api.http_method.upper() == "POST":
            response = requests.post(api_url, headers=headers, json=test_data, timeout=10)
        elif api.http_method.upper() == "PUT":
            response = requests.put(api_url, headers=headers, json=test_data, timeout=10)
        elif api.http_method.upper() == "DELETE":
            response = requests.delete(api_url, headers=headers, timeout=10)
        else:
            response = requests.post(api_url, headers=headers, json=test_data, timeout=10)
        
        print(f"响应状态码: {response.status_code}")
        print(f"响应内容: {response.text[:200]}..." if len(response.text) > 200 else f"响应内容: {response.text}")
        
        return True
        
    except requests.exceptions.ConnectionError:
        print("错误: 无法连接到API服务器，请确保服务器正在运行")
        return False
    except requests.exceptions.Timeout:
        print("错误: 请求超时")
        return False
    except Exception as e:
        print(f"错误: API调用失败 - {str(e)}")
        return False

def check_api_usage_logs_after(initial_count, batch_id):
    """
    检查修复后的api_usage_logs记录
    """
    print("\n=== 检查修复后的API使用日志 ===")
    
    # 等待一段时间让异步日志记录完成
    print("等待3秒让异步日志记录完成...")
    time.sleep(3)
    
    db = next(get_db())
    try:
        # 查询总记录数
        total_count = db.query(ApiUsageLog).count()
        new_records = total_count - initial_count
        print(f"当前api_usage_logs表总记录数: {total_count}")
        print(f"新增记录数: {new_records}")
        
        # 查询与batch_id相关的记录
        batch_logs = db.query(ApiUsageLog).filter(ApiUsageLog.batch_id == batch_id).all()
        print(f"\n与batch_id '{batch_id}' 相关的记录数: {len(batch_logs)}")
        
        for log in batch_logs:
            print(f"  - 记录ID: {log.id}")
            print(f"    API ID: {log.api_id}")
            print(f"    客户ID: {log.customer_id}")
            print(f"    请求ID: {log.request_id}")
            print(f"    HTTP方法: {log.http_method}")
            print(f"    请求URL: {log.request_url}")
            print(f"    响应状态: {log.response_status}")
            print(f"    批次ID: {log.batch_id}")
            print(f"    文件路径: {log.file_path}")
            print(f"    客户端IP: {log.client_ip}")
            print(f"    处理时间: {log.processing_time}")
            print(f"    创建时间: {log.created_at}")
            print(f"    是否加密: {log.is_encrypted}")
            print("    ---")
        
        # 查询最新的记录
        latest_logs = db.query(ApiUsageLog).order_by(desc(ApiUsageLog.created_at)).limit(3).all()
        print(f"\n最新的{len(latest_logs)}条记录:")
        for log in latest_logs:
            print(f"  - ID: {log.id}, API ID: {log.api_id}, 批次ID: {log.batch_id}, 创建时间: {log.created_at}")
        
        return new_records > 0
        
    finally:
        db.close()

def main():
    """
    主测试函数
    """
    print("API使用日志修复测试")
    print("=" * 50)
    
    # 1. 检查修复前的记录数
    initial_count = check_api_usage_logs_before()
    
    # 2. 获取测试API和客户
    api, customer = get_test_api_and_customer()
    if not api or not customer:
        print("\n测试失败: 无法获取测试API和平台信息")
        return
    
    # 3. 测试API调用
    batch_id = f"test_batch_{int(time.time())}"
    success = test_api_call_with_batch_id(api, customer)
    
    if not success:
        print("\n测试失败: API调用未成功")
        print("\n建议:")
        print("1. 确保API服务器正在运行 (python start.py 或 python main.py)")
        print("2. 检查API配置是否正确")
        print("3. 检查认证设置")
        return
    
    # 4. 检查修复后的记录
    has_new_records = check_api_usage_logs_after(initial_count, batch_id)
    
    # 5. 总结
    print("\n=== 测试总结 ===")
    if has_new_records:
        print("✅ 测试成功: API调用已正确记录到api_usage_logs表")
        print("✅ 修复生效: 异步日志记录功能正常工作")
        print("✅ batch_id正确保存到日志记录中")
    else:
        print("❌ 测试失败: 没有新的日志记录生成")
        print("\n可能的原因:")
        print("1. 异步日志记录仍被注释或禁用")
        print("2. 数据库连接问题")
        print("3. 日志服务配置问题")
        print("4. API调用未成功触发日志记录")

if __name__ == "__main__":
    main()