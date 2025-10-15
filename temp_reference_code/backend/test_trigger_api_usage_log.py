#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试触发API使用日志记录
"""

import os
import sys
import json
import requests
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import get_db
from app.models.log import ApiUsageLog
from app.models.api import CustomApi
from app.models.customer import Customer

def test_api_call():
    """
    测试API调用以触发ApiUsageLog记录
    """
    print("\n=== 测试API调用触发使用日志 ===")
    print(f"当前时间: {datetime.now()}")
    
    # 获取数据库会话
    db = next(get_db())
    
    try:
        # 1. 检查是否有可用的API配置
        print("\n1. 检查可用的API配置...")
        apis = db.query(CustomApi).limit(3).all()
        
        if not apis:
            print("❌ 没有找到可用的API配置")
            return
        
        print(f"找到 {len(apis)} 个API配置:")
        for api in apis:
            print(f"  - API代码: {api.api_code}")
            print(f"    API名称: {api.api_name}")
            print(f"    客户ID: {api.customer_id}")
        
        # 2. 检查是否有可用的客户
        print("\n2. 检查可用的客户...")
        customers = db.query(Customer).limit(3).all()
        
        if not customers:
            print("❌ 没有找到可用的客户")
            return
        
        print(f"找到 {len(customers)} 个客户:")
        for customer in customers:
            print(f"  - 客户ID: {customer.id}")
            print(f"    应用ID: {customer.app_id}")
            print(f"    客户名称: {customer.name}")
        
        # 3. 检查ApiUsageLog记录数量（调用前）
        print("\n3. 检查调用前的记录数量...")
        count_before = db.query(ApiUsageLog).count()
        print(f"调用前记录数: {count_before}")
        
        # 4. 模拟API调用（直接调用服务层方法）
        print("\n4. 模拟API调用...")
        
        # 选择第一个API和客户进行测试
        test_api = apis[0]
        test_customer = customers[0]
        
        print(f"使用API: {test_api.api_code}")
        print(f"使用客户: {test_customer.customer_name} (ID: {test_customer.id})")
        
        # 准备测试数据
        test_data = [
            {"name": "测试数据1", "value": "test1"},
            {"name": "测试数据2", "value": "test2"}
        ]
        
        # 直接调用API服务的批量处理方法
        from app.services.api import ApiService
        api_service = ApiService()
        
        try:
            result = api_service._process_batch_data(
                db=db,
                api_config=test_api,
                data_list=test_data,
                customer_id=test_customer.id,
                batch_id="test-batch-manual",
                request_id="test-req-manual"
            )
            
            print("✅ API调用成功")
            print(f"返回结果: {json.dumps(result, indent=2, ensure_ascii=False)}")
            
        except Exception as api_error:
            print(f"❌ API调用失败: {str(api_error)}")
            import traceback
            traceback.print_exc()
        
        # 5. 检查ApiUsageLog记录数量（调用后）
        print("\n5. 检查调用后的记录数量...")
        count_after = db.query(ApiUsageLog).count()
        print(f"调用后记录数: {count_after}")
        print(f"新增记录数: {count_after - count_before}")
        
        if count_after > count_before:
            print("\n✅ 成功创建了新的使用日志记录!")
            
            # 显示最新的记录
            latest_log = db.query(ApiUsageLog).order_by(ApiUsageLog.created_at.desc()).first()
            if latest_log:
                print("\n最新的使用日志记录:")
                print(f"  ID: {latest_log.id}")
                print(f"  请求ID: {latest_log.request_id}")
                print(f"  批次ID: {latest_log.batch_id}")
                print(f"  客户ID: {latest_log.customer_id}")
                print(f"  API ID: {latest_log.api_id}")
                print(f"  文件路径: {latest_log.file_path}")
                print(f"  响应状态: {latest_log.response_status}")
                print(f"  数据大小: {latest_log.data_size}")
                print(f"  记录数量: {latest_log.record_count}")
                print(f"  创建时间: {latest_log.created_at}")
        else:
            print("\n⚠️  没有创建新的使用日志记录")
            print("\n可能的原因:")
            print("1. API服务中的数据库保存逻辑有问题")
            print("2. 事务回滚了")
            print("3. 异常处理阻止了记录保存")
        
    except Exception as e:
        print(f"\n❌ 测试过程中出现错误: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()

if __name__ == "__main__":
    test_api_call()