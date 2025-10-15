#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据保存功能使用示例

展示如何使用 save_data_helper.py 中的函数来保存数据并返回保存路径

Author: System
Date: 2025
"""

import uuid
from datetime import datetime
from save_data_helper import save_data_to_disk, save_simple_data, get_data_from_file


def example_1_basic_usage():
    """
    示例1：基本用法 - 使用批次ID和上传ID保存数据
    """
    print("=== 示例1：基本用法 ===")
    
    # 准备测试数据
    data = {
        "user_id": 12345,
        "username": "张三",
        "email": "zhangsan@example.com",
        "profile": {
            "age": 28,
            "city": "北京",
            "interests": ["编程", "阅读", "旅行"]
        },
        "created_at": datetime.now().isoformat()
    }
    
    # 生成客户ID、批次ID和上传ID
    customer_id = "customer_001"
    batch_id = f"batch_{int(datetime.now().timestamp())}"
    upload_id = str(uuid.uuid4())
    
    try:
        # 保存数据
        file_path = save_data_to_disk(customer_id, batch_id, upload_id, data)
        print(f"✅ 数据保存成功")
        print(f"📁 保存路径: {file_path}")
        
        # 验证数据
        saved_data = get_data_from_file(file_path)
        print(f"📄 保存的数据包含: upload_id, batch_id, timestamp, data")
        print(f"🔍 客户ID: {saved_data['customer_id']}, 原始数据用户名: {saved_data['data']['username']}")
        
        return file_path
        
    except Exception as e:
        print(f"❌ 保存失败: {e}")
        return None


def example_2_simple_usage():
    """
    示例2：简化用法 - 直接保存数据到指定文件
    """
    print("\n=== 示例2：简化用法 ===")
    
    # 准备API响应数据
    api_response = {
        "status": "success",
        "code": 200,
        "message": "数据处理完成",
        "result": {
            "processed_count": 150,
            "success_count": 148,
            "error_count": 2,
            "errors": [
                {"line": 23, "error": "数据格式错误"},
                {"line": 67, "error": "必填字段缺失"}
            ]
        },
        "processing_time": "2.34s"
    }
    
    try:
        # 使用自定义文件名保存
        filename = f"api_response_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        file_path = save_simple_data(api_response, filename)
        
        print(f"✅ API响应数据保存成功")
        print(f"📁 保存路径: {file_path}")
        
        # 读取并验证
        saved_data = get_data_from_file(file_path)
        print(f"📊 处理结果: 成功 {saved_data['data']['result']['success_count']} 条，失败 {saved_data['data']['result']['error_count']} 条")
        
        return file_path
        
    except Exception as e:
        print(f"❌ 保存失败: {e}")
        return None


def example_3_custom_directory():
    """
    示例3：自定义目录 - 保存到指定目录
    """
    print("\n=== 示例3：自定义目录 ===")
    
    # 准备日志数据
    log_data = {
        "level": "INFO",
        "timestamp": datetime.now().isoformat(),
        "module": "data_processor",
        "message": "批量数据处理完成",
        "details": {
            "batch_size": 1000,
            "processing_time": 45.67,
            "memory_usage": "256MB",
            "cpu_usage": "78%"
        }
    }
    
    try:
        # 保存到自定义目录
        custom_dir = "./logs/processed"
        customer_id = "customer_002"
        batch_id = "log_batch_001"
        upload_id = "log_upload_001"
        
        file_path = save_data_to_disk(customer_id, batch_id, upload_id, log_data, custom_dir)
        
        print(f"✅ 日志数据保存成功")
        print(f"📁 保存路径: {file_path}")
        print(f"📂 自定义目录: {custom_dir}")
        
        return file_path
        
    except Exception as e:
        print(f"❌ 保存失败: {e}")
        return None


def example_4_batch_processing():
    """
    示例4：批量处理 - 模拟批量保存多个数据文件
    """
    print("\n=== 示例4：批量处理 ===")
    
    customer_id = "customer_003"
    batch_id = f"batch_{int(datetime.now().timestamp())}"
    saved_files = []
    
    # 模拟处理多个数据项
    for i in range(3):
        data_item = {
            "item_id": i + 1,
            "name": f"数据项_{i + 1}",
            "value": (i + 1) * 100,
            "processed_at": datetime.now().isoformat(),
            "metadata": {
                "source": "batch_processor",
                "version": "1.0",
                "batch_index": i + 1
            }
        }
        
        try:
            upload_id = f"item_{i + 1}_{uuid.uuid4().hex[:8]}"
            file_path = save_data_to_disk(customer_id, batch_id, upload_id, data_item)
            saved_files.append(file_path)
            print(f"✅ 数据项 {i + 1} 保存成功: {file_path}")
            
        except Exception as e:
            print(f"❌ 数据项 {i + 1} 保存失败: {e}")
    
    print(f"\n📊 批量处理完成，共保存 {len(saved_files)} 个文件")
    print(f"📁 批次目录: uploads/data/{customer_id}/{batch_id}/")
    
    return saved_files


def main():
    """
    主函数：运行所有示例
    """
    print("🚀 数据保存功能使用示例")
    print("=" * 50)
    
    # 运行所有示例
    example_1_basic_usage()
    example_2_simple_usage()
    example_3_custom_directory()
    example_4_batch_processing()
    
    print("\n" + "=" * 50)
    print("✅ 所有示例运行完成！")
    print("\n💡 使用说明:")
    print("1. save_data_to_disk(customer_id, batch_id, upload_id, data) - 完整功能，支持客户ID、批次ID和上传ID")
    print("2. save_simple_data() - 简化功能，直接保存数据")
    print("3. get_data_from_file() - 读取保存的数据")
    print("4. 所有函数都返回保存文件的绝对路径")
    print("5. 数据以JSON格式保存，支持中文和复杂数据结构")
    print("6. 目录结构: uploads/data/{customer_id}/{batch_id}/")


if __name__ == "__main__":
    main()