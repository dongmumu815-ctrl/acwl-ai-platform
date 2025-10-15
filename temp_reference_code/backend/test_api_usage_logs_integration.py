#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API使用日志集成测试脚本

测试MinIO数据保存后的api_usage_logs表记录功能
"""

import os
import sys
import json
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.config import settings
from app.core.database import get_db
from app.models.log import ApiUsageLog
from app.models.api import CustomApi
from app.models.customer import Customer
from sqlalchemy.orm import Session

def test_api_usage_logs():
    """
    测试api_usage_logs表中的记录
    """
    print("\n=== API使用日志集成测试 ===")
    print(f"当前时间: {datetime.now()}")
    
    # 获取数据库会话
    db: Session = next(get_db())
    
    try:
        # 1. 查询最近的使用日志记录
        print("\n1. 查询最近的使用日志记录...")
        recent_logs = db.query(ApiUsageLog).order_by(ApiUsageLog.created_at.desc()).limit(5).all()
        
        if recent_logs:
            print(f"找到 {len(recent_logs)} 条最近的使用日志记录:")
            for log in recent_logs:
                print(f"  - ID: {log.id}")
                print(f"    请求ID: {log.request_id}")
                print(f"    批次ID: {log.batch_id}")
                print(f"    客户ID: {log.customer_id}")
                print(f"    API ID: {log.api_id}")
                print(f"    文件路径: {log.file_path}")
                print(f"    数据大小: {log.data_size} bytes")
                print(f"    响应状态: {log.response_status}")
                print(f"    记录数量: {log.record_count}")
                print(f"    处理时间: {log.processing_time}s")
                print(f"    创建时间: {log.created_at}")
                print(f"    HTTP方法: {log.http_method}")
                print(f"    请求URL: {log.request_url}")
                print(f"    客户端IP: {log.client_ip}")
                print(f"    用户代理: {log.user_agent}")
                print()
        else:
            print("  没有找到使用日志记录")
        
        # 2. 查询批量处理的记录
        print("\n2. 查询批量处理的记录...")
        batch_logs = db.query(ApiUsageLog).filter(
            ApiUsageLog.batch_id.isnot(None),
            ApiUsageLog.file_path.isnot(None)
        ).order_by(ApiUsageLog.created_at.desc()).limit(3).all()
        
        if batch_logs:
            print(f"找到 {len(batch_logs)} 条批量处理记录:")
            for log in batch_logs:
                print(f"  - 请求ID: {log.request_id}")
                print(f"    批次ID: {log.batch_id}")
                print(f"    存储路径: {log.file_path}")
                print(f"    响应状态: {log.response_status}")
                print(f"    处理时间: {log.processing_time}s")
                print(f"    记录数量: {log.record_count}")
                print()
        else:
            print("  没有找到批量处理记录")
        
        # 3. 查询特定存储路径格式的记录
        print("\n3. 查询MinIO存储路径格式的记录...")
        minio_logs = db.query(ApiUsageLog).filter(
            ApiUsageLog.file_path.like('%/batchfile/%')
        ).order_by(ApiUsageLog.created_at.desc()).limit(3).all()
        
        if minio_logs:
            print(f"找到 {len(minio_logs)} 条MinIO存储记录:")
            for log in minio_logs:
                print(f"  - 请求ID: {log.request_id}")
                print(f"    存储路径: {log.file_path}")
                print(f"    数据大小: {log.data_size} bytes")
                print(f"    记录数量: {log.record_count}")
                print()
        else:
            print("  没有找到MinIO存储记录")
        
        # 4. 统计信息
        print("\n4. 统计信息...")
        total_logs = db.query(ApiUsageLog).count()
        success_logs = db.query(ApiUsageLog).filter(ApiUsageLog.response_status == 200).count()
        batch_count = db.query(ApiUsageLog).filter(ApiUsageLog.batch_id.isnot(None)).count()
        file_storage_count = db.query(ApiUsageLog).filter(ApiUsageLog.file_path.isnot(None)).count()
        
        print(f"  总日志记录数: {total_logs}")
        print(f"  成功响应记录数: {success_logs}")
        print(f"  批量处理记录数: {batch_count}")
        print(f"  文件存储记录数: {file_storage_count}")
        
        # 5. 查询关联的API和客户信息
        print("\n5. 查询关联信息...")
        if recent_logs:
            log = recent_logs[0]
            
            # 查询关联的API
            api = db.query(CustomApi).filter(CustomApi.id == log.api_id).first()
            if api:
                print(f"  关联API: {api.api_code} - {api.api_name}")
            
            # 查询关联的客户
            customer = db.query(Customer).filter(Customer.id == log.customer_id).first()
            if customer:
                print(f"  关联客户: {customer.customer_name}")
        
        print("\n✅ API使用日志集成测试完成!")
        
    except Exception as e:
        print(f"\n❌ 数据库测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()

def test_storage_path_format():
    """
    测试存储路径格式
    """
    print("\n=== 存储路径格式测试 ===")
    
    # 模拟存储路径构建
    bucket_name = settings.MINIO_BUCKET_NAME
    batch_id = "test-batch-123"
    filename = "API001_req-456_20241201120000.json"
    
    storage_path = f"/{bucket_name}/batchfile/{batch_id}/{filename}"
    
    print(f"存储路径配置:")
    print(f"  存储桶: {bucket_name}")
    print(f"  批次ID: {batch_id}")
    print(f"  文件名: {filename}")
    print(f"  存储路径: {storage_path}")
    
    # 验证路径格式
    expected_format = f"/{bucket_name}/batchfile/"
    if storage_path.startswith(expected_format):
        print("✅ 存储路径格式正确")
    else:
        print("❌ 存储路径格式错误")
    
    # 解析路径组件
    path_parts = storage_path.strip('/').split('/')
    if len(path_parts) >= 4:
        print(f"\n路径组件解析:")
        print(f"  存储桶: {path_parts[0]}")
        print(f"  目录类型: {path_parts[1]}")
        print(f"  批次ID: {path_parts[2]}")
        print(f"  文件名: {path_parts[3]}")
    
def test_api_usage_log_fields():
    """
    测试ApiUsageLog模型字段
    """
    print("\n=== ApiUsageLog模型字段测试 ===")
    
    # 检查必要字段
    required_fields = [
        'customer_id', 'api_id', 'request_id', 'http_method', 
        'request_url', 'response_status', 'file_path', 'batch_id',
        'data_size', 'record_count', 'processing_time'
    ]
    
    from app.models.log import ApiUsageLog
    model_columns = [column.name for column in ApiUsageLog.__table__.columns]
    
    print(f"模型字段检查:")
    for field in required_fields:
        if field in model_columns:
            print(f"  ✅ {field}: 存在")
        else:
            print(f"  ❌ {field}: 缺失")
    
    print(f"\n模型总字段数: {len(model_columns)}")
    print(f"检查字段数: {len(required_fields)}")

if __name__ == "__main__":
    print("API使用日志集成测试脚本")
    print("=" * 50)
    
    # 显示当前配置
    print(f"数据库URL: {settings.DATABASE_URL}")
    print(f"MinIO端点: {settings.MINIO_ENDPOINT}")
    print(f"MinIO存储桶: {settings.MINIO_BUCKET_NAME}")
    
    # 运行测试
    test_storage_path_format()
    test_api_usage_log_fields()
    test_api_usage_logs()
    
    print("\n测试完成!")