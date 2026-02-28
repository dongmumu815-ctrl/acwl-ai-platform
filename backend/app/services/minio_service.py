# -*- coding: utf-8 -*-
"""
MinIO对象存储服务模块

提供MinIO对象存储的高级操作功能，包括：
- 分片上传和下载
- 断点续传
- 文件压缩和解压
- 模型文件管理

Author: System
Date: 2024
"""

import os
import json
import zipfile
import tempfile
import hashlib
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple, AsyncGenerator
from pathlib import Path
from io import BytesIO
import asyncio
import aiofiles

from minio import Minio
from minio.error import S3Error
from loguru import logger

from app.core.config import settings


class MinIOService:
    """
    MinIO对象存储服务类
    
    提供MinIO对象存储的高级操作功能
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
        self.logger.info(f"目标存储桶: {settings.MINIO_BUCKET_NAME}")
        
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
        self.chunk_size = settings.MINIO_CHUNK_SIZE
        self.max_retries = settings.MINIO_MAX_RETRIES
        self.timeout = settings.MINIO_TIMEOUT
        
        # 确保存储桶存在
        try:
            self._ensure_bucket_exists()
        except Exception as e:
            self.logger.warning(f"MinIO初始化警告: 无法连接到MinIO服务器或存储桶不可用. 错误: {e}")
            # 不抛出异常，允许应用启动

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

    def _calculate_file_hash(self, file_path: str) -> str:
        """计算文件的MD5哈希值"""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    def upload_json_data(self, data: Dict[str, Any], object_path: str) -> str:
        """
        直接上传JSON数据到MinIO (同步方法)
        
        Args:
            data: JSON数据字典
            object_path: MinIO对象路径
            
        Returns:
            str: MinIO对象路径
        """
        try:
            json_bytes = json.dumps(data, ensure_ascii=False).encode('utf-8')
            data_stream = BytesIO(json_bytes)
            
            self.logger.info(f"📤 正在上传JSON配置到: {object_path}")
            
            self.client.put_object(
                self.bucket_name,
                object_path,
                data_stream,
                len(json_bytes),
                content_type='application/json'
            )
            
            self.logger.info(f"✅ JSON配置上传成功: {object_path}")
            return object_path
            
        except Exception as e:
            self.logger.error(f"JSON配置上传失败: {str(e)}")
            raise

    async def upload_model_file(
        self,
        file_path: str,
        model_name: str,
        model_version: str,
        filename: str,
        progress_callback: Optional[callable] = None
    ) -> str:
        """
        上传模型文件到MinIO，支持分片上传和断点续传
        
        Args:
            file_path: 本地文件路径
            model_name: 模型名称
            model_version: 模型版本
            filename: 文件名
            progress_callback: 进度回调函数
            
        Returns:
            str: MinIO中的对象路径
        """
        try:
            # 构建MinIO对象路径
            object_path = f"models/{model_name}-{model_version}/{filename}"
            
            self.logger.info(f"📁 准备上传模型文件到MinIO")
            self.logger.info(f"   本地文件: {file_path}")
            self.logger.info(f"   存储桶: {self.bucket_name}")
            self.logger.info(f"   对象路径: {object_path}")
            self.logger.info(f"   模型: {model_name} v{model_version}")
            
            # 获取文件大小
            file_size = os.path.getsize(file_path)
            self.logger.info(f"   文件大小: {file_size / (1024*1024):.2f} MB")
            
            # 计算文件哈希
            file_hash = self._calculate_file_hash(file_path)
            self.logger.info(f"   文件哈希: {file_hash}")
            
            # 检查是否已存在相同文件
            try:
                existing_obj = self.client.stat_object(self.bucket_name, object_path)
                existing_etag = existing_obj.etag.strip('"')
                if existing_etag == file_hash:
                    self.logger.info("✅ 文件已存在且内容相同，跳过上传")
                    return object_path
            except S3Error:
                # 文件不存在，继续上传
                pass
            
            # 判断是否使用分片上传
            if file_size > self.chunk_size:
                return await self._upload_large_file(
                    file_path, object_path, file_size, progress_callback
                )
            else:
                return await self._upload_small_file(
                    file_path, object_path, progress_callback
                )
                
        except Exception as e:
            self.logger.error(f"MinIO文件上传失败: {str(e)}")
            raise Exception(f"MinIO文件上传失败: {str(e)}")

    async def _upload_small_file(
        self,
        file_path: str,
        object_path: str,
        progress_callback: Optional[callable] = None
    ) -> str:
        """上传小文件"""
        try:
            self.logger.info(f"🚀 开始上传小文件...")
            
            # 直接上传文件
            self.client.fput_object(
                bucket_name=self.bucket_name,
                object_name=object_path,
                file_path=file_path
            )
            
            if progress_callback:
                progress_callback(100)
            
            self.logger.info(f"✅ 小文件上传成功!")
            return object_path
            
        except Exception as e:
            self.logger.error(f"小文件上传失败: {str(e)}")
            raise

    async def _upload_large_file(
        self,
        file_path: str,
        object_path: str,
        file_size: int,
        progress_callback: Optional[callable] = None
    ) -> str:
        """分片上传大文件"""
        try:
            self.logger.info(f"🚀 开始分片上传大文件...")
            
            # 初始化分片上传
            upload_id = self.client._create_multipart_upload(
                self.bucket_name, object_path, {}
            )
            
            parts = []
            uploaded_size = 0
            part_number = 1
            
            with open(file_path, 'rb') as file:
                while True:
                    chunk = file.read(self.chunk_size)
                    if not chunk:
                        break
                    
                    # 上传分片
                    for retry in range(self.max_retries):
                        try:
                            chunk_stream = BytesIO(chunk)
                            etag = self.client._upload_part(
                                self.bucket_name,
                                object_path,
                                upload_id,
                                part_number,
                                chunk_stream,
                                len(chunk)
                            )
                            
                            parts.append({
                                'PartNumber': part_number,
                                'ETag': etag
                            })
                            
                            uploaded_size += len(chunk)
                            progress = int((uploaded_size / file_size) * 100)
                            
                            if progress_callback:
                                progress_callback(progress)
                            
                            self.logger.info(f"   分片 {part_number} 上传成功 ({progress}%)")
                            break
                            
                        except Exception as e:
                            if retry == self.max_retries - 1:
                                # 取消分片上传
                                self.client._abort_multipart_upload(
                                    self.bucket_name, object_path, upload_id
                                )
                                raise e
                            self.logger.warning(f"分片 {part_number} 上传失败，重试 {retry + 1}/{self.max_retries}")
                            await asyncio.sleep(1)
                    
                    part_number += 1
            
            # 完成分片上传
            self.client._complete_multipart_upload(
                self.bucket_name, object_path, upload_id, parts
            )
            
            self.logger.info(f"✅ 分片上传完成! 总分片数: {len(parts)}")
            return object_path
            
        except Exception as e:
            self.logger.error(f"分片上传失败: {str(e)}")
            raise

    async def download_and_compress_model(
        self,
        object_path: str,
        model_name: str,
        model_version: str,
        progress_callback: Optional[callable] = None
    ) -> str:
        """
        下载模型文件到/tmp，压缩成zip后上传到MinIO
        
        Args:
            object_path: MinIO中的对象路径
            model_name: 模型名称
            model_version: 模型版本
            progress_callback: 进度回调函数
            
        Returns:
            str: 压缩文件在MinIO中的路径
        """
        temp_dir = None
        try:
            self.logger.info(f"📥 开始下载并压缩模型文件")
            self.logger.info(f"   源对象路径: {object_path}")
            self.logger.info(f"   模型: {model_name} v{model_version}")
            
            # 创建临时目录
            temp_dir = tempfile.mkdtemp(prefix=f"model_{model_name}_{model_version}_")
            self.logger.info(f"   临时目录: {temp_dir}")
            
            # 下载文件到临时目录
            filename = os.path.basename(object_path)
            temp_file_path = os.path.join(temp_dir, filename)
            
            await self._download_file_with_progress(
                object_path, temp_file_path, progress_callback, 0, 50
            )
            
            # 压缩文件
            zip_filename = f"{model_name}-{model_version}.zip"
            zip_path = os.path.join(temp_dir, zip_filename)
            
            self.logger.info(f"🗜️ 开始压缩文件...")
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                zipf.write(temp_file_path, filename)
            
            zip_size = os.path.getsize(zip_path)
            self.logger.info(f"   压缩完成，文件大小: {zip_size / (1024*1024):.2f} MB")
            
            if progress_callback:
                progress_callback(60)
            
            # 上传压缩文件到MinIO
            compressed_object_path = f"models/{model_name}-{model_version}/compressed/{zip_filename}"
            
            await self._upload_file_with_progress(
                zip_path, compressed_object_path, progress_callback, 60, 100
            )
            
            self.logger.info(f"✅ 模型下载压缩上传完成!")
            self.logger.info(f"   压缩文件路径: {compressed_object_path}")
            
            return compressed_object_path
            
        except Exception as e:
            self.logger.error(f"模型下载压缩失败: {str(e)}")
            raise Exception(f"模型下载压缩失败: {str(e)}")
        finally:
            # 清理临时文件
            if temp_dir and os.path.exists(temp_dir):
                try:
                    import shutil
                    shutil.rmtree(temp_dir)
                    self.logger.info(f"🧹 已清理临时目录: {temp_dir}")
                except Exception as e:
                    self.logger.warning(f"清理临时目录失败: {e}")

    async def _download_file_with_progress(
        self,
        object_path: str,
        local_path: str,
        progress_callback: Optional[callable] = None,
        progress_start: int = 0,
        progress_end: int = 100
    ):
        """带进度的文件下载"""
        try:
            self.logger.info(f"📥 开始下载文件: {object_path}")
            
            # 获取文件信息
            obj_stat = self.client.stat_object(self.bucket_name, object_path)
            file_size = obj_stat.size
            
            # 判断是否使用分片下载
            if file_size > self.chunk_size:
                await self._download_large_file(
                    object_path, local_path, file_size, 
                    progress_callback, progress_start, progress_end
                )
            else:
                await self._download_small_file(
                    object_path, local_path,
                    progress_callback, progress_start, progress_end
                )
                
        except Exception as e:
            self.logger.error(f"文件下载失败: {str(e)}")
            raise

    async def _download_small_file(
        self,
        object_path: str,
        local_path: str,
        progress_callback: Optional[callable] = None,
        progress_start: int = 0,
        progress_end: int = 100
    ):
        """下载小文件"""
        try:
            self.client.fget_object(self.bucket_name, object_path, local_path)
            
            if progress_callback:
                progress_callback(progress_end)
            
            self.logger.info(f"✅ 小文件下载成功: {local_path}")
            
        except Exception as e:
            self.logger.error(f"小文件下载失败: {str(e)}")
            raise

    async def _download_large_file(
        self,
        object_path: str,
        local_path: str,
        file_size: int,
        progress_callback: Optional[callable] = None,
        progress_start: int = 0,
        progress_end: int = 100
    ):
        """分片下载大文件"""
        try:
            self.logger.info(f"📥 开始分片下载大文件...")
            
            downloaded_size = 0
            
            with open(local_path, 'wb') as local_file:
                while downloaded_size < file_size:
                    # 计算当前分片的范围
                    start_byte = downloaded_size
                    end_byte = min(downloaded_size + self.chunk_size - 1, file_size - 1)
                    
                    # 下载分片
                    for retry in range(self.max_retries):
                        try:
                            response = self.client.get_object(
                                self.bucket_name,
                                object_path,
                                offset=start_byte,
                                length=end_byte - start_byte + 1
                            )
                            
                            chunk_data = response.read()
                            local_file.write(chunk_data)
                            
                            downloaded_size += len(chunk_data)
                            progress = progress_start + int(
                                ((downloaded_size / file_size) * (progress_end - progress_start))
                            )
                            
                            if progress_callback:
                                progress_callback(progress)
                            
                            self.logger.info(f"   下载进度: {progress}%")
                            
                            response.close()
                            response.release_conn()
                            break
                            
                        except Exception as e:
                            if retry == self.max_retries - 1:
                                raise e
                            self.logger.warning(f"分片下载失败，重试 {retry + 1}/{self.max_retries}")
                            await asyncio.sleep(1)
            
            self.logger.info(f"✅ 分片下载完成: {local_path}")
            
        except Exception as e:
            self.logger.error(f"分片下载失败: {str(e)}")
            raise

    async def _upload_file_with_progress(
        self,
        local_path: str,
        object_path: str,
        progress_callback: Optional[callable] = None,
        progress_start: int = 0,
        progress_end: int = 100
    ):
        """带进度的文件上传"""
        try:
            file_size = os.path.getsize(local_path)
            
            if file_size > self.chunk_size:
                await self._upload_large_file_with_progress(
                    local_path, object_path, file_size,
                    progress_callback, progress_start, progress_end
                )
            else:
                self.client.fput_object(self.bucket_name, object_path, local_path)
                if progress_callback:
                    progress_callback(progress_end)
                    
        except Exception as e:
            self.logger.error(f"文件上传失败: {str(e)}")
            raise

    async def _upload_large_file_with_progress(
        self,
        local_path: str,
        object_path: str,
        file_size: int,
        progress_callback: Optional[callable] = None,
        progress_start: int = 0,
        progress_end: int = 100
    ):
        """带进度的大文件分片上传"""
        try:
            upload_id = self.client._create_multipart_upload(
                self.bucket_name, object_path, {}
            )
            
            parts = []
            uploaded_size = 0
            part_number = 1
            
            with open(local_path, 'rb') as file:
                while True:
                    chunk = file.read(self.chunk_size)
                    if not chunk:
                        break
                    
                    chunk_stream = BytesIO(chunk)
                    etag = self.client._upload_part(
                        self.bucket_name,
                        object_path,
                        upload_id,
                        part_number,
                        chunk_stream,
                        len(chunk)
                    )
                    
                    parts.append({
                        'PartNumber': part_number,
                        'ETag': etag
                    })
                    
                    uploaded_size += len(chunk)
                    progress = progress_start + int(
                        ((uploaded_size / file_size) * (progress_end - progress_start))
                    )
                    
                    if progress_callback:
                        progress_callback(progress)
                    
                    part_number += 1
            
            self.client._complete_multipart_upload(
                self.bucket_name, object_path, upload_id, parts
            )
            
        except Exception as e:
            self.logger.error(f"大文件上传失败: {str(e)}")
            raise

    def delete_object(self, object_path: str) -> bool:
        """删除MinIO对象"""
        try:
            self.client.remove_object(self.bucket_name, object_path)
            self.logger.info(f"✅ 已删除MinIO对象: {object_path}")
            return True
        except Exception as e:
            self.logger.error(f"删除MinIO对象失败: {str(e)}")
            return False

    def get_object_url(self, object_path: str) -> str:
        """获取对象的MinIO URL"""
        return f"minio://{settings.MINIO_ENDPOINT}/{self.bucket_name}/{object_path}"

    def list_objects(self, prefix: str = "") -> List[Dict[str, Any]]:
        """列出对象"""
        try:
            objects = self.client.list_objects(
                self.bucket_name, prefix=prefix, recursive=True
            )
            
            result = []
            for obj in objects:
                result.append({
                    "name": obj.object_name,
                    "size": obj.size,
                    "last_modified": obj.last_modified,
                    "etag": obj.etag
                })
            
            return result
            
        except Exception as e:
            self.logger.error(f"列出对象失败: {str(e)}")
            return []


# 创建全局MinIO服务实例
minio_service = MinIOService()