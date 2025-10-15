#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MinIO集成测试脚本

测试MinIO服务的基本功能，包括数据保存、读取、列表和删除操作。
用于验证MinIO集成是否正常工作。

Usage:
    python test_minio_integration.py
"""

import sys
import os
import json
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.minio_service import minio_service


def test_minio_basic_operations():
    """
    测试MinIO基本操作
    """
    print("=" * 60)
    print("MinIO集成测试开始")
    print("=" * 60)
    
    # 测试数据
    test_batch_id = f"test_batch_{int(datetime.now().timestamp())}"
    test_data = {
        "api_code": "test_api",
        "api_id": 1,
        "request_id": "test_request_001",
        "customer_id": 123,
        "data_list": [
            {"id": 1, "name": "测试数据1", "value": "test_value_1"},
            {"id": 2, "name": "测试数据2", "value": "test_value_2"},
            {"id": 3, "name": "测试数据3", "value": "test_value_3"}
        ],
        "processing_info": {
            "total_count": 3,
            "processed_at": datetime.now().isoformat()
        }
    }
    
    test_filename = "test_data.json"
    
    try:
        # 1. 测试数据保存
        print("\n1. 测试数据保存到MinIO...")
        object_path = minio_service.save_batch_data(test_batch_id, test_data, test_filename)
        print(f"✓ 数据保存成功: {object_path}")
        
        # 2. 测试数据读取
        print("\n2. 测试从MinIO读取数据...")
        retrieved_data = minio_service.get_batch_data(test_batch_id, test_filename)
        print(f"✓ 数据读取成功")
        print(f"  - 批次ID: {retrieved_data.get('batch_id')}")
        print(f"  - 数据记录数: {len(retrieved_data.get('data', {}).get('data_list', []))}")
        
        # 3. 测试文件列表
        print("\n3. 测试批次文件列表...")
        files = minio_service.list_batch_files(test_batch_id)
        print(f"✓ 文件列表获取成功，共 {len(files)} 个文件:")
        for file_info in files:
            print(f"  - {file_info['name']} (大小: {file_info['size']} 字节)")
        
        # 4. 验证数据完整性
        print("\n4. 验证数据完整性...")
        original_data_list = test_data['data_list']
        retrieved_data_list = retrieved_data.get('data', {}).get('data_list', [])
        
        if len(original_data_list) == len(retrieved_data_list):
            print("✓ 数据记录数匹配")
        else:
            print(f"✗ 数据记录数不匹配: 原始 {len(original_data_list)}, 读取 {len(retrieved_data_list)}")
            return False
        
        # 5. 测试数据删除
        print("\n5. 测试数据删除...")
        delete_success = minio_service.delete_batch_data(test_batch_id, test_filename)
        if delete_success:
            print("✓ 数据删除成功")
        else:
            print("✗ 数据删除失败")
            return False
        
        # 6. 验证删除后文件列表
        print("\n6. 验证删除后文件列表...")
        files_after_delete = minio_service.list_batch_files(test_batch_id)
        if len(files_after_delete) == 0:
            print("✓ 文件已成功删除")
        else:
            print(f"✗ 删除后仍有 {len(files_after_delete)} 个文件")
            return False
        
        print("\n" + "=" * 60)
        print("✓ 所有测试通过！MinIO集成正常工作")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"\n✗ 测试失败: {str(e)}")
        print("=" * 60)
        return False


def test_minio_connection():
    """
    测试MinIO连接
    """
    try:
        print("测试MinIO连接...")
        # 尝试列出存储桶
        buckets = minio_service.client.list_buckets()
        print(f"✓ MinIO连接成功，共有 {len(buckets)} 个存储桶")
        for bucket in buckets:
            print(f"  - {bucket.name} (创建时间: {bucket.creation_date})")
        return True
    except Exception as e:
        print(f"✗ MinIO连接失败: {str(e)}")
        return False


def main():
    """
    主函数
    """
    print("MinIO集成测试脚本")
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 测试连接
    if not test_minio_connection():
        print("\n请检查MinIO服务是否正常运行，以及配置是否正确")
        return False
    
    # 测试基本操作
    if not test_minio_basic_operations():
        print("\n基本操作测试失败")
        return False
    
    print("\n🎉 MinIO集成测试全部通过！")
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)