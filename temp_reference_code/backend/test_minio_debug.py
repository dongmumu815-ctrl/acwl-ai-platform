#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MinIO调试测试脚本

用于测试MinIO连接和数据保存功能，输出详细的调试信息
"""

import sys
import os
import json
from datetime import datetime

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 设置环境变量（如果需要）
os.environ.setdefault('PYTHONPATH', os.path.dirname(os.path.abspath(__file__)))

from app.core.config import settings
from app.core.logging import setup_logging
from loguru import logger

def test_minio_connection():
    """
    测试MinIO连接和基本操作
    """
    logger.info("🔧 开始MinIO连接测试...")
    
    try:
        # 导入MinIO服务
        from app.services.minio_service import MinIOService
        
        logger.info("📦 正在创建MinIO服务实例...")
        
        # 创建MinIO服务实例（这里会触发连接和初始化日志）
        minio_service = MinIOService()
        
        logger.info("✅ MinIO服务实例创建成功!")
        
        # 测试数据保存
        logger.info("🧪 开始测试数据保存...")
        
        test_batch_id = f"test_batch_{int(datetime.now().timestamp())}"
        test_data = {
            "test_field_1": "测试数据1",
            "test_field_2": "测试数据2",
            "test_number": 12345,
            "test_array": [1, 2, 3, 4, 5],
            "test_object": {
                "nested_field": "嵌套数据",
                "nested_number": 67890
            }
        }
        
        logger.info(f"   测试批次ID: {test_batch_id}")
        logger.info(f"   测试数据: {json.dumps(test_data, ensure_ascii=False, indent=2)}")
        
        # 保存测试数据
        object_path = minio_service.save_batch_data(
            batch_id=test_batch_id,
            data=test_data,
            filename="debug_test.json"
        )
        
        logger.info(f"🎉 测试数据保存成功!")
        logger.info(f"   对象路径: {object_path}")
        logger.info(f"   存储桶: {settings.MINIO_BUCKET_NAME}")
        logger.info(f"   完整MinIO路径: minio://{settings.MINIO_ENDPOINT}/{settings.MINIO_BUCKET_NAME}/{object_path}")
        
        # 测试数据读取
        logger.info("📖 开始测试数据读取...")
        
        try:
            retrieved_data = minio_service.get_batch_data(test_batch_id, "debug_test.json")
            logger.info(f"✅ 数据读取成功!")
            logger.info(f"   读取的数据: {json.dumps(retrieved_data, ensure_ascii=False, indent=2)}")
        except Exception as read_error:
            logger.error(f"❌ 数据读取失败: {read_error}")
        
        # 测试文件列表
        logger.info("📋 开始测试文件列表...")
        
        try:
            files = minio_service.list_batch_files(test_batch_id)
            logger.info(f"✅ 文件列表获取成功!")
            logger.info(f"   批次 {test_batch_id} 中的文件: {files}")
        except Exception as list_error:
            logger.error(f"❌ 文件列表获取失败: {list_error}")
        
        logger.info("🎊 MinIO测试完成!")
        
    except Exception as e:
        logger.error(f"❌ MinIO测试失败: {e}")
        logger.error(f"   错误类型: {type(e).__name__}")
        logger.error(f"   错误详情: {str(e)}")
        
        # 输出配置信息用于调试
        logger.info("🔍 当前MinIO配置:")
        logger.info(f"   端点: {settings.MINIO_ENDPOINT}")
        logger.info(f"   访问密钥: {settings.MINIO_ACCESS_KEY[:8]}***")
        logger.info(f"   安全连接: {settings.MINIO_SECURE}")
        logger.info(f"   存储桶: {settings.MINIO_BUCKET_NAME}")
        logger.info(f"   区域: {settings.MINIO_REGION}")
        
        raise

def main():
    """
    主函数
    """
    print("=" * 60)
    print("MinIO 调试测试脚本")
    print("=" * 60)
    
    # 设置日志级别为DEBUG，确保所有日志都能显示
    setup_logging("DEBUG")
    
    logger.info("🚀 开始MinIO调试测试...")
    
    try:
        test_minio_connection()
        logger.info("🎉 所有测试完成!")
    except Exception as e:
        logger.error(f"❌ 测试失败: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)