#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试API使用日志记录功能
验证修复后的日志记录是否正常工作
"""

import sys
import os
import json
import requests
import time
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import get_db
from app.services.api import ApiService
from app.services.customer import CustomerService
from app.services.log import LogService
from app.models.log import ApiUsageLog
from sqlalchemy.orm import Session

def test_api_usage_logs():
    """
    测试API使用日志记录功能
    """
    print("=== 测试API使用日志记录功能 ===")
    
    # 获取数据库会话
    db_generator = get_db()
    db: Session = next(db_generator)
    
    try:
        # 初始化服务
        api_service = ApiService()
        customer_service = CustomerService()
        log_service = LogService()
        
        # 1. 检查修复前的日志记录数量
        initial_count = db.query(ApiUsageLog).count()
        print(f"修复前日志记录数量: {initial_count}")
        
        # 2. 获取测试数据
        # 获取第一个可用的API
        api_config = api_service.get_first_available_api(db)
        if not api_config:
            print("❌ 没有找到可用的API配置")
            return False
            
        print(f"使用API: {api_config.api_code} (ID: {api_config.id})")
        
        # 获取第一个可用的客户
        customer = customer_service.get_first_available_customer(db)
        if not customer:
            print("❌ 没有找到可用的客户")
            return False
            
        print(f"使用客户: {customer.name} (ID: {customer.id})")
        
        # 3. 直接调用日志服务测试
        print("\n=== 直接调用日志服务测试 ===")
        
        test_batch_id = f"test_batch_{int(time.time())}"
        test_request_data = {
            "test_field": "test_value",
            "batch_id": test_batch_id,
            "timestamp": int(time.time())
        }
        test_response_data = {
            "status": "success",
            "message": "测试成功",
            "data": ["item1", "item2", "item3"]
        }
        
        # 调用日志记录方法
        log_record = log_service.log_api_call(
            db=db,
            customer_id=customer.id,
            api_id=api_config.id,
            request_method="POST",
            request_url=f"/api/v1/{test_batch_id}/{api_config.api_code}",
            request_headers={"Content-Type": "application/json", "User-Agent": "TestClient/1.0"},
            request_body=test_request_data,
            response_status=200,
            response_headers={"Content-Type": "application/json"},
            response_body=test_response_data,
            response_time=150.5,  # 150.5ms
            ip_address="127.0.0.1",
            user_agent="TestClient/1.0",
            error_message=None,
            error_details=None,
            batch_id=test_batch_id,
            timestamp=int(time.time()),
            nonce="test_nonce_123",
            encrypted_data=None,
            iv=None,
            signature="test_signature_456",
            needread=False,
            is_encrypted=False
        )
        
        print(f"✅ 日志记录创建成功: {log_record.request_id}")
        
        # 4. 验证日志记录的字段
        print("\n=== 验证日志记录字段 ===")
        
        # 刷新对象以获取最新数据
        db.refresh(log_record)
        
        # 检查关键字段
        checks = [
            ("customer_id", log_record.customer_id, customer.id),
            ("api_id", log_record.api_id, api_config.id),
            ("batch_id", log_record.batch_id, test_batch_id),
            ("response_status", log_record.response_status, 200),
            ("processing_time", float(log_record.processing_time), 0.1505),
            ("client_ip", log_record.client_ip, "127.0.0.1"),
            ("is_success", log_record.is_success, True),
        ]
        
        for field_name, actual, expected in checks:
            if actual == expected:
                print(f"✅ {field_name}: {actual}")
            else:
                print(f"❌ {field_name}: 期望 {expected}, 实际 {actual}")
        
        # 检查JSON字段
        if log_record.request_params:
            request_params = json.loads(log_record.request_params)
            print(f"✅ request_params: {request_params}")
        else:
            print("❌ request_params 为空")
            
        if log_record.response_body:
            response_body = json.loads(log_record.response_body)
            print(f"✅ response_body: {response_body}")
        else:
            print("❌ response_body 为空")
            
        # 检查文件路径
        if log_record.file_path:
            print(f"✅ file_path: {log_record.file_path}")
        else:
            print("❌ file_path 为空")
            
        # 检查数据大小和记录数
        print(f"✅ data_size: {log_record.data_size} bytes")
        print(f"✅ record_count: {log_record.record_count}")
        
        # 5. 检查最终的日志记录数量
        final_count = db.query(ApiUsageLog).count()
        print(f"\n修复后日志记录数量: {final_count}")
        print(f"新增日志记录: {final_count - initial_count}")
        
        if final_count > initial_count:
            print("✅ 日志记录功能正常工作")
            return True
        else:
            print("❌ 日志记录功能异常")
            return False
            
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

def test_api_endpoint():
    """
    测试实际的API端点调用
    """
    print("\n=== 测试实际API端点调用 ===")
    
    try:
        # 测试API端点
        base_url = "http://localhost:8000"
        test_batch_id = f"test_batch_{int(time.time())}"
        api_code = "test_api"  # 假设存在这个API
        
        url = f"{base_url}/api/v1/{test_batch_id}/{api_code}"
        
        test_data = {
            "test_field": "test_value",
            "batch_id": test_batch_id,
            "items": ["item1", "item2", "item3"]
        }
        
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "TestClient/1.0"
        }
        
        print(f"调用API: {url}")
        print(f"请求数据: {json.dumps(test_data, indent=2)}")
        
        # 发送请求
        response = requests.post(url, json=test_data, headers=headers, timeout=10)
        
        print(f"响应状态码: {response.status_code}")
        print(f"响应内容: {response.text[:200]}...")
        
        # 等待一段时间让异步日志记录完成
        time.sleep(2)
        
        # 检查日志是否记录
        db_generator = get_db()
        db: Session = next(db_generator)
        
        try:
            # 查找最近的日志记录
            recent_log = db.query(ApiUsageLog).filter(
                ApiUsageLog.batch_id == test_batch_id
            ).first()
            
            if recent_log:
                print(f"✅ 找到对应的日志记录: {recent_log.request_id}")
                print(f"   batch_id: {recent_log.batch_id}")
                print(f"   response_status: {recent_log.response_status}")
                return True
            else:
                print(f"❌ 未找到batch_id为 {test_batch_id} 的日志记录")
                return False
                
        finally:
            db.close()
            
    except requests.exceptions.RequestException as e:
        print(f"❌ API请求失败: {e}")
        print("   这可能是因为服务器未运行，但不影响日志服务本身的功能")
        return False
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
        return False

if __name__ == "__main__":
    print("开始测试API使用日志记录功能...")
    print(f"测试时间: {datetime.now()}")
    
    # 测试日志服务
    log_service_result = test_api_usage_logs()
    
    # 测试API端点（可选）
    api_endpoint_result = test_api_endpoint()
    
    print("\n=== 测试结果汇总 ===")
    print(f"日志服务测试: {'✅ 通过' if log_service_result else '❌ 失败'}")
    print(f"API端点测试: {'✅ 通过' if api_endpoint_result else '❌ 失败'}")
    
    if log_service_result:
        print("\n🎉 API使用日志记录功能修复成功！")
        print("现在API调用应该能够正确保存到api_usage_logs表中。")
    else:
        print("\n❌ API使用日志记录功能仍有问题，需要进一步检查。")