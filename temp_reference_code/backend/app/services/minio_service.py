# -*- coding: utf-8 -*-
"""
MinIO对象存储服务模块

提供MinIO对象存储的基本操作功能，包括文件上传、下载、删除等。
用于替代本地文件存储，将数据保存到MinIO对象存储中。

Author: System
Date: 2024
"""

import json
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

from minio import Minio
from minio.error import S3Error
from io import BytesIO
from loguru import logger

from app.core.config import settings


class MinIOService:
    """
    MinIO对象存储服务类
    
    提供MinIO对象存储的基本操作功能
    """
    
    def __init__(self):
        """初始化MinIO客户端"""
        self.logger = logger.bind(name=self.__class__.__name__)
        
        # 打印MinIO配置信息
        self.logger.info(f"正在初始化MinIO客户端...")
        self.logger.info(f"MinIO端点: {settings.MINIO_ENDPOINT}")
        self.logger.info(f"MinIO访问密钥: {settings.MINIO_ACCESS_KEY[:8]}***")
        self.logger.info(f"MinIO安全连接: {settings.MINIO_SECURE}")
        self.logger.info(f"MinIO区域: {settings.MINIO_REGION}")
        
        # 创建MinIO客户端
        try:
            self.client = Minio(
                endpoint=settings.MINIO_ENDPOINT,
                access_key=settings.MINIO_ACCESS_KEY,
                secret_key=settings.MINIO_SECRET_KEY,
                secure=settings.MINIO_SECURE,
                region=settings.MINIO_REGION
            )
            self.logger.info("MinIO客户端创建成功!")
        except Exception as e:
            self.logger.error(f"MinIO客户端创建失败: {e}")
            raise
        
        self.bucket_name = settings.MINIO_BUCKET_NAME
        self.logger.info(f"目标存储桶: {self.bucket_name}")
        
        # 确保存储桶存在
        self._ensure_bucket_exists()
    
    def _ensure_bucket_exists(self):
        """确保存储桶存在，如果不存在则创建"""
        try:
            self.logger.info(f"检查存储桶是否存在: {self.bucket_name}")
            bucket_exists = self.client.bucket_exists(self.bucket_name)
            
            if not bucket_exists:
                self.logger.info(f"存储桶不存在，正在创建: {self.bucket_name}")
                self.client.make_bucket(self.bucket_name, location=settings.MINIO_REGION)
                self.logger.info(f"✅ 成功创建MinIO存储桶: {self.bucket_name}")
            else:
                self.logger.info(f"✅ MinIO存储桶已存在: {self.bucket_name}")
                
            # 验证连接
            self.logger.info("正在验证MinIO连接...")
            buckets = list(self.client.list_buckets())
            self.logger.info(f"✅ MinIO连接成功! 可访问的存储桶数量: {len(buckets)}")
            
        except S3Error as e:
            self.logger.error(f"❌ MinIO存储桶操作失败: {e}")
            raise
        except Exception as e:
            self.logger.error(f"❌ MinIO连接验证失败: {e}")
            raise
    
    def save_batch_data(
        self,
        batch_id: str,
        data: Dict[str, Any],
        filename: Optional[str] = None
    ) -> str:
        """
        保存批量数据到MinIO
        
        Args:
            batch_id: 批次ID
            data: 要保存的数据
            filename: 文件名，如果不指定则自动生成
            
        Returns:
            str: MinIO中的对象路径
            
        Raises:
            Exception: 保存失败时抛出异常
        """
        try:
            # 生成文件名
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{timestamp}.json"
            
            # 构建对象路径：batchfile/{batch_id}/文件名.json
            object_path = f"batchfile/{batch_id}/{filename}"
            
            self.logger.info(f"📁 准备保存数据到MinIO")
            self.logger.info(f"   存储桶: {self.bucket_name}")
            self.logger.info(f"   对象路径: {object_path}")
            self.logger.info(f"   批次ID: {batch_id}")
            self.logger.info(f"   文件名: {filename}")
            
            # 准备数据
            save_data = {
                "batch_id": batch_id,
                "timestamp": datetime.now().isoformat(),
                "data": data
            }
            
            # 将数据转换为JSON字符串
            json_data = json.dumps(save_data, ensure_ascii=False, indent=2)
            data_size = len(json_data.encode('utf-8'))
            
            self.logger.info(f"   数据大小: {data_size} 字节")
            
            # 转换为字节流
            data_stream = BytesIO(json_data.encode('utf-8'))
            
            # 上传到MinIO
            self.logger.info(f"🚀 开始上传数据到MinIO...")
            self.client.put_object(
                bucket_name=self.bucket_name,
                object_name=object_path,
                data=data_stream,
                length=data_size,
                content_type='application/json'
            )
            
            self.logger.info(f"✅ 数据已成功保存到MinIO!")
            self.logger.info(f"   完整路径: {self.bucket_name}/{object_path}")
            self.logger.info(f"   访问URL: minio://{settings.MINIO_ENDPOINT}/{self.bucket_name}/{object_path}")
            
            return object_path
            
        except Exception as e:
            self.logger.error(f"MinIO数据保存失败: {str(e)}")
            raise Exception(f"MinIO数据保存失败: {str(e)}")
    
    def get_batch_data(self, batch_id: str, filename: str) -> Dict[str, Any]:
        """
        从MinIO获取批量数据
        
        Args:
            batch_id: 批次ID
            filename: 文件名
            
        Returns:
            Dict[str, Any]: 数据内容
            
        Raises:
            Exception: 获取失败时抛出异常
        """
        try:
            # 构建对象路径
            object_path = f"batchfile/{batch_id}/{filename}"
            
            # 从MinIO获取对象
            response = self.client.get_object(
                bucket_name=self.bucket_name,
                object_name=object_path
            )
            
            # 读取数据
            data = response.read()
            response.close()
            response.release_conn()
            
            # 解析JSON数据
            json_data = json.loads(data.decode('utf-8'))
            
            self.logger.info(f"从MinIO获取数据成功: {self.bucket_name}/{object_path}")
            return json_data
            
        except Exception as e:
            self.logger.error(f"MinIO数据获取失败: {str(e)}")
            raise Exception(f"MinIO数据获取失败: {str(e)}")
    
    def list_batch_files(self, batch_id: str) -> list:
        """
        列出指定批次的所有文件
        
        Args:
            batch_id: 批次ID
            
        Returns:
            list: 文件列表
        """
        try:
            # 构建前缀
            prefix = f"batchfile/{batch_id}/"
            
            # 列出对象
            objects = self.client.list_objects(
                bucket_name=self.bucket_name,
                prefix=prefix,
                recursive=True
            )
            
            files = []
            for obj in objects:
                files.append({
                    "name": obj.object_name,
                    "size": obj.size,
                    "last_modified": obj.last_modified,
                    "etag": obj.etag
                })
            
            self.logger.info(f"列出批次文件成功: {batch_id}, 文件数量: {len(files)}")
            return files
            
        except Exception as e:
            self.logger.error(f"MinIO文件列表获取失败: {str(e)}")
            raise Exception(f"MinIO文件列表获取失败: {str(e)}")
    
    def delete_batch_data(self, batch_id: str, filename: str) -> bool:
        """
        删除指定的批量数据文件
        
        Args:
            batch_id: 批次ID
            filename: 文件名
            
        Returns:
            bool: 删除是否成功
        """
        try:
            # 构建对象路径
            object_path = f"batchfile/{batch_id}/{filename}"
            
            # 删除对象
            self.client.remove_object(
                bucket_name=self.bucket_name,
                object_name=object_path
            )
            
            self.logger.info(f"MinIO数据删除成功: {self.bucket_name}/{object_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"MinIO数据删除失败: {str(e)}")
            return False


# 创建全局MinIO服务实例
minio_service = MinIOService()