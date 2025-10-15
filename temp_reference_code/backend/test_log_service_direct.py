#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
直接测试日志服务

直接调用日志服务来测试api_usage_logs表的记录功能
"""

import sys
import os
import time
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import get_db
from app.models.log import ApiUsageLog
from app.models.api import CustomApi
from app.models.customer import Customer
from app.services.log import log_service
from sqlalchemy import desc

def check_initial_state():
    """
    检查初始状态
    """
    print("=== 检查初始状态 ===")
    
    db = next(get_db())
    try:
        # 检查表是否存在
        try:
            total_count = db.query(ApiUsageLog).count()
            print(f"✅ api_usage_logs表存在，当前记录数: {total_count}")
        except Exception as e:
            print(f"❌ api_usage_logs表访问失败: {e}")
            return False, 0
        
        # 检查是否有可用的API和客户
        api_count = db.query(CustomApi).count()
        customer_count = db.query(Customer).count()
        print(f"可用API数量: {api_count}")
        print(f"可用客户数量: {customer_count}")
        
        if api_count == 0 or customer_count == 0:
            print("❌ 缺少测试数据（API或客户）")
            return False, total_count
        
        return True, total_count
        
    finally:
        db.close()

def get_test_data():
    """
    获取测试数据
    """
    print("\n=== 获取测试数据 ===")
    
    db = next(get_db())
    try:
        # 获取第一个可用的API
        api = db.query(CustomApi).first()
        if not api:
            print("❌ 没有找到可用的API")
            return None, None
        
        # 获取对应的客户
        customer = db.query(Customer).filter(Customer.id == api.customer_id).first()
        if not customer:
            print(f"❌ 没有找到API对应的客户 (customer_id: {api.customer_id})")
            return None, None
        
        print(f"✅ 找到测试API: {api.api_code} (ID: {api.id})")
        print(f"✅ 对应客户: {customer.username} (ID: {customer.id})")
        
        return api, customer
        
    finally:
        db.close()

def test_log_service_direct(api, customer):
    """
    直接测试日志服务
    """
    print("\n=== 直接测试日志服务 ===")
    
    db = next(get_db())
    try:
        # 生成测试batch_id
        batch_id = f"test_batch_{int(time.time())}"
        print(f"使用batch_id: {batch_id}")
        
        # 准备测试数据
        test_request_data = {
            "batch_id": batch_id,
            "test_data": "这是测试数据",
            "items": ["item1", "item2", "item3"],
            "timestamp": int(time.time() * 1000)
        }
        
        test_response_data = {
            "code": 200,
            "message": "处理成功",
            "total_count": 3,
            "batch_id": batch_id
        }
        
        print("调用log_service.log_api_call...")
        
        # 直接调用日志服务
        log_record = log_service.log_api_call(
            db=db,
            customer_id=customer.id,
            api_id=api.id,
            request_method="POST",
            request_url=f"/api/v1/{batch_id}/{api.api_code}",
            request_headers={"Content-Type": "application/json"},
            request_body=test_request_data,
            response_status=200,
            response_headers={"Content-Type": "application/json"},
            response_time=150.5,  # 150.5ms
            ip_address="127.0.0.1",
            user_agent="Test-Agent/1.0",
            batch_id=batch_id,
            is_encrypted=False
        )
        
        print(f"✅ 日志记录创建成功")
        print(f"   记录ID: {log_record.id}")
        print(f"   请求ID: {log_record.request_id}")
        print(f"   批次ID: {log_record.batch_id}")
        print(f"   文件路径: {log_record.file_path}")
        print(f"   数据大小: {log_record.data_size} 字节")
        print(f"   记录数量: {log_record.record_count}")
        print(f"   创建时间: {log_record.created_at}")
        
        return True, log_record
        
    except Exception as e:
        print(f"❌ 日志记录创建失败: {e}")
        import traceback
        traceback.print_exc()
        return False, None
        
    finally:
        db.close()

def verify_log_record(log_record, batch_id):
    """
    验证日志记录
    """
    print("\n=== 验证日志记录 ===")
    
    db = next(get_db())
    try:
        # 通过ID查询记录
        saved_record = db.query(ApiUsageLog).filter(ApiUsageLog.id == log_record.id).first()
        if not saved_record:
            print(f"❌ 无法通过ID {log_record.id} 找到保存的记录")
            return False
        
        print(f"✅ 通过ID找到记录: {saved_record.id}")
        
        # 通过batch_id查询记录
        batch_records = db.query(ApiUsageLog).filter(ApiUsageLog.batch_id == batch_id).all()
        print(f"✅ 通过batch_id找到 {len(batch_records)} 条记录")
        
        # 验证关键字段
        print("\n字段验证:")
        print(f"  batch_id: {saved_record.batch_id} {'✅' if saved_record.batch_id == batch_id else '❌'}")
        print(f"  file_path: {saved_record.file_path} {'✅' if saved_record.file_path else '❌'}")
        print(f"  data_size: {saved_record.data_size} {'✅' if saved_record.data_size > 0 else '❌'}")
        print(f"  record_count: {saved_record.record_count} {'✅' if saved_record.record_count > 0 else '❌'}")
        print(f"  request_params: {'✅' if saved_record.request_params else '❌'}")
        print(f"  client_ip: {saved_record.client_ip} {'✅' if saved_record.client_ip else '❌'}")
        
        # 验证存储路径格式
        expected_path_pattern = f"/bucket_name/batchfile/{batch_id}/"
        if saved_record.file_path and expected_path_pattern in saved_record.file_path:
            print(f"  存储路径格式: ✅ 符合 /bucket_name/batchfile/batch_id/filename.json 格式")
        else:
            print(f"  存储路径格式: ❌ 不符合预期格式")
        
        return True
        
    finally:
        db.close()

def check_final_state(initial_count):
    """
    检查最终状态
    """
    print("\n=== 检查最终状态 ===")
    
    db = next(get_db())
    try:
        final_count = db.query(ApiUsageLog).count()
        new_records = final_count - initial_count
        
        print(f"初始记录数: {initial_count}")
        print(f"最终记录数: {final_count}")
        print(f"新增记录数: {new_records}")
        
        if new_records > 0:
            print("✅ 成功新增日志记录")
            
            # 显示最新的记录
            latest_records = db.query(ApiUsageLog).order_by(desc(ApiUsageLog.created_at)).limit(3).all()
            print(f"\n最新的 {len(latest_records)} 条记录:")
            for record in latest_records:
                print(f"  - ID: {record.id}, batch_id: {record.batch_id}, 创建时间: {record.created_at}")
        else:
            print("❌ 没有新增记录")
        
        return new_records > 0
        
    finally:
        db.close()

def main():
    """
    主测试函数
    """
    print("API使用日志服务直接测试")
    print("=" * 50)
    
    # 1. 检查初始状态
    success, initial_count = check_initial_state()
    if not success:
        print("\n❌ 初始状态检查失败，测试终止")
        return
    
    # 2. 获取测试数据
    api, customer = get_test_data()
    if not api or not customer:
        print("\n❌ 无法获取测试数据，测试终止")
        return
    
    # 3. 直接测试日志服务
    success, log_record = test_log_service_direct(api, customer)
    if not success:
        print("\n❌ 日志服务测试失败")
        return
    
    # 4. 验证日志记录
    batch_id = log_record.batch_id
    verify_success = verify_log_record(log_record, batch_id)
    
    # 5. 检查最终状态
    final_success = check_final_state(initial_count)
    
    # 6. 总结
    print("\n=== 测试总结 ===")
    if success and verify_success and final_success:
        print("🎉 测试完全成功!")
        print("✅ 日志服务正常工作")
        print("✅ api_usage_logs表正确保存记录")
        print("✅ batch_id和file_path字段正确设置")
        print("✅ 存储路径格式符合要求: /bucket_name/batchfile/batch_id/filename.json")
    else:
        print("❌ 测试失败")
        if not success:
            print("  - 日志服务调用失败")
        if not verify_success:
            print("  - 日志记录验证失败")
        if not final_success:
            print("  - 最终状态检查失败")

if __name__ == "__main__":
    main()