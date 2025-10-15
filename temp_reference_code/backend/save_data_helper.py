#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据保存辅助模块

提供数据保存功能，参考 data.py 中的 save_data_to_disk 函数实现
将数据保存到本地磁盘并返回保存路径

Author: System
Date: 2025
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from app.core.config import settings


def save_data_to_disk(
    customer_id: str,
    batch_id: str, 
    upload_id: str, 
    data: Dict[str, Any],
    custom_dir: Optional[str] = None
) -> str:
    """
    将数据保存到本地磁盘
    
    参考 /d:/works/codes/cepiec-api-data/backend/app/api/v1/endpoints/data.py#L244-261
    的实现，保存数据到指定目录结构中
    
    Args:
        customer_id: 客户ID，用于创建目录结构
        batch_id: 批次ID，用于创建目录结构
        upload_id: 上传ID，用于生成文件名
        data: 要保存的数据字典
        custom_dir: 自定义保存目录，如果不指定则使用默认的 UPLOAD_PATH/data
        
    Returns:
        str: 保存文件的完整路径
        
    Raises:
        Exception: 数据保存失败时抛出异常
    """
    try:
        # 确定存储根目录
        if custom_dir:
            storage_root = Path(custom_dir)
        else:
            storage_root = Path(settings.UPLOAD_PATH) / "data"
        
        # 创建存储目录结构：根目录/data/customer_id/batch_id/
        storage_dir = storage_root / customer_id / batch_id
        storage_dir.mkdir(parents=True, exist_ok=True)
        
        # 生成文件名：upload_id_时间戳.json
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{upload_id}_{timestamp}.json"
        file_path = storage_dir / filename
        
        # 保存数据到文件
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump({
                "customer_id": customer_id,
                "upload_id": upload_id,
                "batch_id": batch_id,
                "timestamp": datetime.now().isoformat(),
                "data": data
            }, f, ensure_ascii=False, indent=2)
        
        # 返回文件的绝对路径
        return str(file_path.absolute())
        
    except Exception as e:
        raise Exception(f"数据保存失败: {str(e)}")


def save_simple_data(
    data: Dict[str, Any],
    filename: Optional[str] = None,
    directory: Optional[str] = None
) -> str:
    """
    简化版数据保存函数
    
    直接保存数据到指定目录，不需要batch_id和upload_id
    
    Args:
        data: 要保存的数据字典
        filename: 文件名，如果不指定则自动生成
        directory: 保存目录，如果不指定则使用默认目录
        
    Returns:
        str: 保存文件的完整路径
        
    Raises:
        Exception: 数据保存失败时抛出异常
    """
    try:
        # 确定保存目录
        if directory:
            save_dir = Path(directory)
        else:
            save_dir = Path(settings.UPLOAD_PATH) / "data" / "simple"
        
        # 创建目录
        save_dir.mkdir(parents=True, exist_ok=True)
        
        # 生成文件名
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]  # 包含毫秒
            filename = f"data_{timestamp}.json"
        
        # 确保文件名以.json结尾
        if not filename.endswith('.json'):
            filename += '.json'
        
        file_path = save_dir / filename
        
        # 保存数据到文件
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "data": data
            }, f, ensure_ascii=False, indent=2)
        
        # 返回文件的绝对路径
        return str(file_path.absolute())
        
    except Exception as e:
        raise Exception(f"数据保存失败: {str(e)}")


def get_data_from_file(file_path: str) -> Dict[str, Any]:
    """
    从文件中读取数据
    
    Args:
        file_path: 文件路径
        
    Returns:
        Dict[str, Any]: 读取的数据
        
    Raises:
        Exception: 文件读取失败时抛出异常
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        raise Exception(f"数据读取失败: {str(e)}")


if __name__ == "__main__":
    # 测试代码
    print("数据保存辅助模块测试")
    
    # 测试数据
    test_data = {
        "name": "测试数据",
        "value": 123,
        "items": ["item1", "item2", "item3"],
        "nested": {
            "key1": "value1",
            "key2": "value2"
        }
    }
    
    try:
        # 测试完整版保存
        print("\n=== 测试完整版数据保存 ===")
        customer_id = "customer_001"
        batch_id = "test_batch_001"
        upload_id = "test_upload_001"
        
        file_path = save_data_to_disk(customer_id, batch_id, upload_id, test_data)
        print(f"数据已保存到: {file_path}")
        
        # 验证文件是否存在
        if os.path.exists(file_path):
            print("✅ 文件保存成功")
            
            # 读取并验证数据
            saved_data = get_data_from_file(file_path)
            print(f"读取的数据: {saved_data}")
        else:
            print("❌ 文件保存失败")
        
        # 测试简化版保存
        print("\n=== 测试简化版数据保存 ===")
        simple_path = save_simple_data(test_data, "test_simple.json")
        print(f"简化版数据已保存到: {simple_path}")
        
        if os.path.exists(simple_path):
            print("✅ 简化版文件保存成功")
        else:
            print("❌ 简化版文件保存失败")
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")