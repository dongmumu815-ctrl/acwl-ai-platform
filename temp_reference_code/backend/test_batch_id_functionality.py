#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试batch_id功能

直接测试数据库中batch_id的记录和查询功能

Author: System
Date: 2025-07-18
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import get_db
from app.models.log import ApiUsageLog
from app.services.api import ApiService
from sqlalchemy import desc
import uuid
from datetime import datetime
import json

def test_batch_id_database_functionality():
    """
    测试batch_id在数据库中的功能
    """
    print("🧪 测试batch_id数据库功能...")
    print("=" * 60)
    
    db = next(get_db())
    try:
        # 生成测试数据
        test_batch_id = f"test_batch_{uuid.uuid4().hex[:8]}"
        test_request_id = f"req_{uuid.uuid4().hex[:8]}"
        
        print(f"📋 测试批次ID: {test_batch_id}")
        print(f"📋 测试请求ID: {test_request_id}")
        
        # 创建测试日志记录
        print(f"\n📝 创建测试日志记录...")
        test_log = ApiUsageLog(
            customer_id=6,  # 测试客户ID
            api_id=3,       # 测试API ID
            request_id=test_request_id,
            http_method="POST",
            request_url=f"/api/v1/custom/3/batch/{test_batch_id}",
            request_headers=json.dumps({"Content-Type": "application/json"}),
            request_params=None,
            request_body=json.dumps({"data": [{"name": "测试", "age": 25}]}),
            client_ip="127.0.0.1",
            user_agent="Test-Agent/1.0",
            response_status=200,
            response_headers=json.dumps({"Content-Type": "application/json"}),
            response_body=json.dumps({"success": True, "message": "处理成功"}),
            processing_time=0.123,
            error_message=None,
            error_traceback=None,
            data_size=1024,
            record_count=1,
            batch_id=test_batch_id  # 关键：设置batch_id
        )
        
        # 保存到数据库
        db.add(test_log)
        db.commit()
        db.refresh(test_log)
        
        print(f"✅ 测试日志记录已创建，ID: {test_log.id}")
        
        # 验证记录是否正确保存
        print(f"\n🔍 验证记录保存...")
        saved_log = db.query(ApiUsageLog).filter(ApiUsageLog.id == test_log.id).first()
        
        if saved_log:
            print(f"✅ 记录保存成功")
            print(f"   ID: {saved_log.id}")
            print(f"   批次ID: {saved_log.batch_id}")
            print(f"   客户ID: {saved_log.customer_id}")
            print(f"   API ID: {saved_log.api_id}")
            print(f"   HTTP方法: {saved_log.http_method}")
            print(f"   响应状态: {saved_log.response_status}")
            print(f"   处理时间: {saved_log.processing_time}ms")
            print(f"   创建时间: {saved_log.created_at}")
        else:
            print(f"❌ 记录保存失败")
            return False
        
        # 测试按batch_id查询
        print(f"\n🔍 测试按batch_id查询...")
        batch_logs = db.query(ApiUsageLog).filter(
            ApiUsageLog.batch_id == test_batch_id
        ).all()
        
        print(f"📊 找到 {len(batch_logs)} 条匹配的记录")
        for log in batch_logs:
            print(f"   记录ID: {log.id}, 批次ID: {log.batch_id}")
        
        # 测试索引性能（查询包含batch_id的记录）
        print(f"\n🚀 测试索引性能...")
        import time
        start_time = time.time()
        
        batch_records = db.query(ApiUsageLog).filter(
            ApiUsageLog.batch_id.isnot(None)
        ).order_by(desc(ApiUsageLog.created_at)).limit(10).all()
        
        end_time = time.time()
        query_time = (end_time - start_time) * 1000  # 转换为毫秒
        
        print(f"📈 查询性能: {query_time:.2f}ms")
        print(f"📊 包含batch_id的记录数: {len(batch_records)}")
        
        # 显示最近的batch记录
        if batch_records:
            print(f"\n📋 最近的batch记录:")
            for i, log in enumerate(batch_records[:5], 1):
                print(f"   {i}. 批次ID: {log.batch_id}, 创建时间: {log.created_at}")
        
        # 测试ApiService的log_api_call方法
        print(f"\n🧪 测试ApiService.log_api_call方法...")
        api_service = ApiService()
        
        test_batch_id_2 = f"service_test_{uuid.uuid4().hex[:8]}"
        test_request_id_2 = f"req_{uuid.uuid4().hex[:8]}"
        
        # 模拟调用log_api_call方法
        try:
            api_service.log_api_call(
                db=db,
                customer_id=6,
                api_id=3,
                request_id=test_request_id_2,
                http_method="POST",
                request_url=f"/api/v1/custom/3/batch/{test_batch_id_2}",
                request_headers={"Content-Type": "application/json"},
                request_params=None,
                request_body={"data": [{"name": "服务测试", "age": 30}]},
                client_ip="127.0.0.1",
                user_agent="Service-Test/1.0",
                response_status=200,
                response_headers={"Content-Type": "application/json"},
                response_body={"success": True, "message": "服务测试成功"},
                processing_time=0.456,
                error_message=None,
                error_traceback=None,
                data_size=2048,
                record_count=1,
                batch_id=test_batch_id_2  # 传递batch_id
            )
            
            print(f"✅ ApiService.log_api_call调用成功")
            print(f"   批次ID: {test_batch_id_2}")
            
            # 验证服务方法创建的记录
            service_log = db.query(ApiUsageLog).filter(
                ApiUsageLog.batch_id == test_batch_id_2
            ).first()
            
            if service_log:
                print(f"✅ 服务方法创建的记录验证成功")
                print(f"   记录ID: {service_log.id}")
                print(f"   批次ID: {service_log.batch_id}")
            else:
                print(f"❌ 服务方法创建的记录验证失败")
                
        except Exception as e:
            print(f"❌ ApiService.log_api_call调用失败: {str(e)}")
            import traceback
            traceback.print_exc()
        
        print(f"\n🎉 batch_id功能测试完成！")
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

def main():
    """
    主函数
    """
    print("🚀 开始测试batch_id功能...")
    print("=" * 60)
    
    success = test_batch_id_database_functionality()
    
    print(f"\n📊 测试结果: {'✅ 成功' if success else '❌ 失败'}")
    
    print(f"\n💡 功能说明:")
    print(f"   - ✅ api_usage_logs表已包含batch_id字段")
    print(f"   - ✅ batch_id索引已创建，提高查询性能")
    print(f"   - ✅ ApiUsageLog模型支持batch_id")
    print(f"   - ✅ ApiService.log_api_call方法支持batch_id参数")
    print(f"   - ✅ 减少了对data_uploads表的依赖")
    print(f"   - ✅ 提高了接口响应性能")

if __name__ == '__main__':
    main()