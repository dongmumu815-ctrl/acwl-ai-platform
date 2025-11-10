#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库集成测试脚本

测试MinIO数据保存后的数据库记录功能
"""

import os
import sys
import json
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.config import settings
from app.core.database import get_db
from app.models.log import DataUpload
from app.models.api import CustomApi
from app.models.customer import Customer
from sqlalchemy.orm import Session

def test_database_records():
    """
    测试数据库中的上传记录
    """
    print("\n=== 数据库集成测试 ===")
    print(f"当前时间: {datetime.now()}")
    
    # 获取数据库会话
    db: Session = next(get_db())
    
    try:
        # 1. 查询最近的上传记录
        print("\n1. 查询最近的上传记录...")
        recent_uploads = db.query(DataUpload).order_by(DataUpload.created_at.desc()).limit(5).all()
        
        if recent_uploads:
            print(f"找到 {len(recent_uploads)} 条最近的上传记录:")
            for upload in recent_uploads:
                print(f"  - ID: {upload.id}")
                print(f"    Upload ID: {upload.upload_id}")
                print(f"    Batch ID: {upload.batch_id}")
                print(f"    Customer ID: {upload.customer_id}")
                print(f"    API ID: {upload.api_id}")
                print(f"    文件路径: {upload.file_path}")
                print(f"    文件大小: {upload.file_size} bytes")
                print(f"    状态: {upload.status}")
                print(f"    记录数量: {upload.record_count}")
                print(f"    创建时间: {upload.created_at}")
                if upload.meta_data:
                    print(f"    元数据: {json.dumps(upload.meta_data, indent=2, ensure_ascii=False)}")
                print()
        else:
            print("  没有找到上传记录")
        
        # 2. 查询MinIO存储的记录
        print("\n2. 查询MinIO存储的记录...")
        minio_uploads = db.query(DataUpload).filter(
            DataUpload.file_path.like('minio://%')
        ).order_by(DataUpload.created_at.desc()).limit(3).all()
        
        if minio_uploads:
            print(f"找到 {len(minio_uploads)} 条MinIO存储记录:")
            for upload in minio_uploads:
                print(f"  - Upload ID: {upload.upload_id}")
                print(f"    MinIO路径: {upload.file_path}")
                print(f"    状态: {upload.status}")
                print(f"    处理时间: {upload.processing_time}s")
                print()
        else:
            print("  没有找到MinIO存储记录")
        
        # 3. 统计信息
        print("\n3. 统计信息...")
        total_uploads = db.query(DataUpload).count()
        completed_uploads = db.query(DataUpload).filter(DataUpload.status == 'completed').count()
        minio_count = db.query(DataUpload).filter(DataUpload.file_path.like('minio://%')).count()
        
        print(f"  总上传记录数: {total_uploads}")
        print(f"  已完成记录数: {completed_uploads}")
        print(f"  MinIO存储记录数: {minio_count}")
        
        # 4. 查询关联的API和平台信息
        print("\n4. 查询关联信息...")
        if recent_uploads:
            upload = recent_uploads[0]
            
            # 查询关联的API
            api = db.query(CustomApi).filter(CustomApi.id == upload.api_id).first()
            if api:
                print(f"  关联API: {api.api_code} - {api.api_name}")
            
            # 查询关联的客户
            customer = db.query(Customer).filter(Customer.id == upload.customer_id).first()
            if customer:
                print(f"  关联客户: {customer.customer_name}")
        
        print("\n✅ 数据库集成测试完成!")
        
    except Exception as e:
        print(f"\n❌ 数据库测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()

def test_minio_path_format():
    """
    测试MinIO路径格式
    """
    print("\n=== MinIO路径格式测试 ===")
    
    # 模拟MinIO路径构建
    endpoint = settings.MINIO_ENDPOINT
    bucket = settings.MINIO_BUCKET_NAME
    object_path = "batchfile/test-batch-123/API001_req-456_20241201120000.json"
    
    minio_full_path = f"minio://{endpoint}/{bucket}/{object_path}"
    
    print(f"MinIO配置:")
    print(f"  端点: {endpoint}")
    print(f"  存储桶: {bucket}")
    print(f"  对象路径: {object_path}")
    print(f"  完整路径: {minio_full_path}")
    
    # 验证路径格式
    if minio_full_path.startswith('minio://'):
        print("✅ MinIO路径格式正确")
    else:
        print("❌ MinIO路径格式错误")

if __name__ == "__main__":
    print("数据库集成测试脚本")
    print("=" * 50)
    
    # 显示当前配置
    print(f"数据库URL: {settings.DATABASE_URL}")
    print(f"MinIO端点: {settings.MINIO_ENDPOINT}")
    print(f"MinIO存储桶: {settings.MINIO_BUCKET_NAME}")
    
    # 运行测试
    test_minio_path_format()
    test_database_records()
    
    print("\n测试完成!")