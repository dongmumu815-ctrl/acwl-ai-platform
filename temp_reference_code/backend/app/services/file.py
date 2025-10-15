#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件服务模块

提供文件上传、下载、管理等功能。

Author: System
Date: 2024
"""

import os
import uuid
import hashlib
import mimetypes
import uuid
from typing import Optional, List, Dict, Any, BinaryIO, Tuple
from pathlib import Path
from datetime import datetime, timedelta
import shutil
from PIL import Image
# import magic  # 移除 magic 库依赖，使用标准库 mimetypes 替代

from app.core.config import settings
from app.core.exceptions import (
    ValidationException,
    BusinessException,
    NotFoundException,
    AuthorizationException
)
from app.schemas.base import FileUploadResponse


class FileService:
    """
    文件服务
    
    提供文件上传、下载、管理等功能
    """
    
    def __init__(self):
        self.logger = self._get_logger()
        self.upload_dir = Path(settings.UPLOAD_PATH)
        self.temp_dir = Path(settings.TEMP_PATH)
        self.max_file_size = settings.MAX_UPLOAD_SIZE
        self.allowed_extensions = settings.ALLOWED_EXTENSIONS
        self.image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
        
        # 确保目录存在
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_logger(self):
        import logging
        return logging.getLogger(self.__class__.__name__)
    
    def upload_file(
        self,
        file: BinaryIO,
        filename: str,
        customer_id: Optional[int] = None,
        category: str = "general",
        max_size: Optional[int] = None,
        allowed_types: Optional[List[str]] = None
    ) -> FileUploadResponse:
        """
        上传文件
        
        Args:
            file: 文件对象
            filename: 原始文件名
            customer_id: 客户ID
            category: 文件分类
            max_size: 最大文件大小（字节）
            allowed_types: 允许的文件类型
            
        Returns:
            文件上传响应
            
        Raises:
            ValidationException: 文件验证失败
            BusinessException: 业务规则验证失败
        """
        # 验证文件
        self._validate_file(file, filename, max_size, allowed_types)
        
        # 生成文件信息
        file_ext = Path(filename).suffix.lower()
        file_id = str(uuid.uuid4())
        new_filename = f"{file_id}{file_ext}"
        
        # 确定存储路径
        if customer_id:
            storage_dir = self.upload_dir / "customers" / str(customer_id) / category
        else:
            storage_dir = self.upload_dir / "system" / category
        
        storage_dir.mkdir(parents=True, exist_ok=True)
        file_path = storage_dir / new_filename
        
        # 保存文件
        file.seek(0)
        with open(file_path, 'wb') as f:
            shutil.copyfileobj(file, f)
        
        # 获取文件信息
        file_size = file_path.stat().st_size
        file_hash = self._calculate_file_hash(file_path)
        mime_type = self._get_mime_type(file_path)
        
        # 处理图片文件
        image_info = None
        if file_ext in self.image_extensions:
            image_info = self._get_image_info(file_path)
        
        # 生成访问URL
        relative_path = file_path.relative_to(self.upload_dir)
        file_url = f"/files/{relative_path.as_posix()}"
        
        self.logger.info(f"Uploaded file: {filename} -> {file_path}")
        
        return FileUploadResponse(
            file_id=file_id,
            filename=filename,
            original_filename=filename,
            file_path=str(file_path),
            file_url=file_url,
            file_size=file_size,
            file_hash=file_hash,
            mime_type=mime_type,
            category=category,
            customer_id=customer_id,
            image_info=image_info,
            upload_time=datetime.utcnow()
        )
    
    def upload_temp_file(
        self,
        file: BinaryIO,
        filename: str,
        expires_in: int = 3600
    ) -> FileUploadResponse:
        """
        上传临时文件
        
        Args:
            file: 文件对象
            filename: 原始文件名
            expires_in: 过期时间（秒）
            
        Returns:
            文件上传响应
        """
        # 生成临时文件信息
        file_ext = Path(filename).suffix.lower()
        file_id = str(uuid.uuid4())
        temp_filename = f"{file_id}{file_ext}"
        temp_path = self.temp_dir / temp_filename
        
        # 保存临时文件
        file.seek(0)
        with open(temp_path, 'wb') as f:
            shutil.copyfileobj(file, f)
        
        # 获取文件信息
        file_size = temp_path.stat().st_size
        file_hash = self._calculate_file_hash(temp_path)
        mime_type = self._get_mime_type(temp_path)
        
        # 生成访问URL
        file_url = f"/temp/{temp_filename}"
        
        # 设置过期时间
        expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
        
        self.logger.info(f"Uploaded temp file: {filename} -> {temp_path}")
        
        return FileUploadResponse(
            file_id=file_id,
            filename=temp_filename,
            original_filename=filename,
            file_path=str(temp_path),
            file_url=file_url,
            file_size=file_size,
            file_hash=file_hash,
            mime_type=mime_type,
            category="temp",
            is_temp=True,
            expires_at=expires_at,
            upload_time=datetime.utcnow()
        )
    
    def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """
        获取文件信息
        
        Args:
            file_path: 文件路径
            
        Returns:
            文件信息字典
            
        Raises:
            NotFoundException: 文件不存在
        """
        path = Path(file_path)
        
        if not path.exists():
            raise NotFoundException(f"文件不存在: {file_path}")
        
        stat = path.stat()
        file_hash = self._calculate_file_hash(path)
        mime_type = self._get_mime_type(path)
        
        info = {
            "filename": path.name,
            "file_size": stat.st_size,
            "file_hash": file_hash,
            "mime_type": mime_type,
            "created_time": datetime.fromtimestamp(stat.st_ctime),
            "modified_time": datetime.fromtimestamp(stat.st_mtime),
            "is_file": path.is_file(),
            "is_dir": path.is_dir()
        }
        
        # 如果是图片文件，添加图片信息
        if path.suffix.lower() in self.image_extensions:
            image_info = self._get_image_info(path)
            if image_info:
                info["image_info"] = image_info
        
        return info
    
    def delete_file(self, file_path: str) -> bool:
        """
        删除文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            是否删除成功
        """
        try:
            path = Path(file_path)
            if path.exists():
                if path.is_file():
                    path.unlink()
                elif path.is_dir():
                    shutil.rmtree(path)
                
                self.logger.info(f"Deleted file: {file_path}")
                return True
            else:
                self.logger.warning(f"File not found for deletion: {file_path}")
                return False
        except Exception as e:
            self.logger.error(f"Failed to delete file {file_path}: {e}")
            return False
    
    def move_file(self, src_path: str, dst_path: str) -> bool:
        """
        移动文件
        
        Args:
            src_path: 源路径
            dst_path: 目标路径
            
        Returns:
            是否移动成功
        """
        try:
            src = Path(src_path)
            dst = Path(dst_path)
            
            if not src.exists():
                raise NotFoundException(f"源文件不存在: {src_path}")
            
            # 确保目标目录存在
            dst.parent.mkdir(parents=True, exist_ok=True)
            
            # 移动文件
            shutil.move(str(src), str(dst))
            
            self.logger.info(f"Moved file: {src_path} -> {dst_path}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to move file {src_path} to {dst_path}: {e}")
            return False
    
    def copy_file(self, src_path: str, dst_path: str) -> bool:
        """
        复制文件
        
        Args:
            src_path: 源路径
            dst_path: 目标路径
            
        Returns:
            是否复制成功
        """
        try:
            src = Path(src_path)
            dst = Path(dst_path)
            
            if not src.exists():
                raise NotFoundException(f"源文件不存在: {src_path}")
            
            # 确保目标目录存在
            dst.parent.mkdir(parents=True, exist_ok=True)
            
            # 复制文件
            if src.is_file():
                shutil.copy2(str(src), str(dst))
            elif src.is_dir():
                shutil.copytree(str(src), str(dst))
            
            self.logger.info(f"Copied file: {src_path} -> {dst_path}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to copy file {src_path} to {dst_path}: {e}")
            return False
    
    def list_files(
        self,
        directory: str,
        pattern: Optional[str] = None,
        recursive: bool = False
    ) -> List[Dict[str, Any]]:
        """
        列出目录中的文件
        
        Args:
            directory: 目录路径
            pattern: 文件名模式
            recursive: 是否递归
            
        Returns:
            文件信息列表
        """
        dir_path = Path(directory)
        
        if not dir_path.exists() or not dir_path.is_dir():
            return []
        
        files = []
        
        if recursive:
            if pattern:
                paths = dir_path.rglob(pattern)
            else:
                paths = dir_path.rglob("*")
        else:
            if pattern:
                paths = dir_path.glob(pattern)
            else:
                paths = dir_path.iterdir()
        
        for path in paths:
            if path.is_file():
                try:
                    file_info = self.get_file_info(str(path))
                    file_info["relative_path"] = str(path.relative_to(dir_path))
                    files.append(file_info)
                except Exception as e:
                    self.logger.warning(f"Failed to get info for file {path}: {e}")
        
        return sorted(files, key=lambda x: x["filename"])
    
    def clean_temp_files(self, max_age_hours: int = 24) -> int:
        """
        清理临时文件
        
        Args:
            max_age_hours: 最大保留时间（小时）
            
        Returns:
            清理的文件数量
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
        cleaned_count = 0
        
        for file_path in self.temp_dir.iterdir():
            if file_path.is_file():
                try:
                    # 检查文件修改时间
                    mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                    if mtime < cutoff_time:
                        file_path.unlink()
                        cleaned_count += 1
                        self.logger.debug(f"Cleaned temp file: {file_path}")
                except Exception as e:
                    self.logger.warning(f"Failed to clean temp file {file_path}: {e}")
        
        self.logger.info(f"Cleaned {cleaned_count} temp files")
        return cleaned_count
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """
        获取存储统计信息
        
        Returns:
            存储统计信息
        """
        stats = {
            "upload_dir": str(self.upload_dir),
            "temp_dir": str(self.temp_dir),
            "total_files": 0,
            "total_size": 0,
            "temp_files": 0,
            "temp_size": 0,
            "categories": {}
        }
        
        # 统计上传目录
        if self.upload_dir.exists():
            for file_path in self.upload_dir.rglob("*"):
                if file_path.is_file():
                    try:
                        file_size = file_path.stat().st_size
                        stats["total_files"] += 1
                        stats["total_size"] += file_size
                        
                        # 按分类统计
                        relative_path = file_path.relative_to(self.upload_dir)
                        category = str(relative_path.parts[0]) if relative_path.parts else "unknown"
                        
                        if category not in stats["categories"]:
                            stats["categories"][category] = {"files": 0, "size": 0}
                        
                        stats["categories"][category]["files"] += 1
                        stats["categories"][category]["size"] += file_size
                    except Exception as e:
                        self.logger.warning(f"Failed to stat file {file_path}: {e}")
        
        # 统计临时目录
        if self.temp_dir.exists():
            for file_path in self.temp_dir.iterdir():
                if file_path.is_file():
                    try:
                        file_size = file_path.stat().st_size
                        stats["temp_files"] += 1
                        stats["temp_size"] += file_size
                    except Exception as e:
                        self.logger.warning(f"Failed to stat temp file {file_path}: {e}")
        
        return stats
    
    def _validate_file(
        self,
        file: BinaryIO,
        filename: str,
        max_size: Optional[int] = None,
        allowed_types: Optional[List[str]] = None
    ) -> None:
        """
        验证文件
        
        Args:
            file: 文件对象
            filename: 文件名
            max_size: 最大文件大小
            allowed_types: 允许的文件类型
            
        Raises:
            ValidationException: 验证失败
        """
        # 检查文件名
        if not filename or len(filename.strip()) == 0:
            raise ValidationException("文件名不能为空")
        
        # 检查文件扩展名
        file_ext = Path(filename).suffix.lower()
        allowed_exts = allowed_types or self.allowed_extensions
        
        if allowed_exts and file_ext not in allowed_exts:
            raise ValidationException(f"不支持的文件类型: {file_ext}")
        
        # 检查文件大小
        file.seek(0, 2)  # 移动到文件末尾
        file_size = file.tell()
        file.seek(0)  # 重置到文件开头
        
        max_allowed_size = max_size or self.max_file_size
        if file_size > max_allowed_size:
            raise ValidationException(f"文件大小超过限制: {file_size} > {max_allowed_size}")
        
        if file_size == 0:
            raise ValidationException("文件不能为空")
        
        # 基本文件内容检查（不使用 magic 库）
        try:
            file_content = file.read(1024)  # 读取前1KB
            file.seek(0)  # 重置到文件开头
            
            # 简单的文件头检查（可选）
            if len(file_content) == 0:
                raise ValidationException("文件内容为空")
                
        except Exception as e:
            self.logger.warning(f"File content validation failed: {e}")
            # 不阻止上传，只记录警告
    
    def _is_compatible_mime_type(self, detected: str, expected: str) -> bool:
        """
        检查MIME类型是否兼容
        
        Args:
            detected: 检测到的MIME类型
            expected: 期望的MIME类型
            
        Returns:
            是否兼容
        """
        # 定义兼容的MIME类型映射
        compatible_types = {
            "image/jpeg": ["image/jpg"],
            "image/jpg": ["image/jpeg"],
            "text/plain": ["text/x-python", "text/x-script.python"],
            "application/json": ["text/plain"],
            "application/xml": ["text/xml", "text/plain"],
        }
        
        if detected == expected:
            return True
        
        return detected in compatible_types.get(expected, [])
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """
        计算文件哈希值
        
        Args:
            file_path: 文件路径
            
        Returns:
            文件MD5哈希值
        """
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def _get_mime_type(self, file_path: Path) -> str:
        """
        获取文件MIME类型
        
        Args:
            file_path: 文件路径
            
        Returns:
            MIME类型
        """
        # 使用标准库 mimetypes 基于扩展名猜测MIME类型
        mime_type, _ = mimetypes.guess_type(str(file_path))
        return mime_type or "application/octet-stream"
    
    def _get_image_info(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """
        获取图片信息
        
        Args:
            file_path: 图片文件路径
            
        Returns:
            图片信息字典或None
        """
        try:
            with Image.open(file_path) as img:
                return {
                    "width": img.width,
                    "height": img.height,
                    "format": img.format,
                    "mode": img.mode,
                    "has_transparency": img.mode in ("RGBA", "LA") or "transparency" in img.info
                }
        except Exception as e:
            self.logger.warning(f"Failed to get image info for {file_path}: {e}")
            return None
    
    def create_thumbnail(
        self,
        image_path: str,
        thumbnail_path: str,
        size: Tuple[int, int] = (200, 200),
        quality: int = 85
    ) -> bool:
        """
        创建缩略图
        
        Args:
            image_path: 原图路径
            thumbnail_path: 缩略图路径
            size: 缩略图尺寸
            quality: 图片质量
            
        Returns:
            是否创建成功
        """
        try:
            with Image.open(image_path) as img:
                # 保持宽高比
                img.thumbnail(size, Image.Resampling.LANCZOS)
                
                # 确保目标目录存在
                Path(thumbnail_path).parent.mkdir(parents=True, exist_ok=True)
                
                # 保存缩略图
                if img.format == "PNG" and img.mode == "RGBA":
                    img.save(thumbnail_path, "PNG", optimize=True)
                else:
                    # 转换为RGB模式以支持JPEG
                    if img.mode != "RGB":
                        img = img.convert("RGB")
                    img.save(thumbnail_path, "JPEG", quality=quality, optimize=True)
                
                self.logger.info(f"Created thumbnail: {image_path} -> {thumbnail_path}")
                return True
        except Exception as e:
            self.logger.error(f"Failed to create thumbnail for {image_path}: {e}")
            return False


class UploadService:
    """
    文件上传服务
    
    提供文件上传的高级功能和管理
    """
    
    def __init__(self):
        self.file_service = FileService()
        self.logger = self._get_logger()
    
    def _get_logger(self):
        import logging
        return logging.getLogger(self.__class__.__name__)
    
    def upload_with_validation(
        self,
        file: BinaryIO,
        filename: str,
        customer_id: Optional[int] = None,
        category: str = "general",
        validate_content: bool = True
    ) -> FileUploadResponse:
        """
        带验证的文件上传
        
        Args:
            file: 文件对象
            filename: 原始文件名
            customer_id: 客户ID
            category: 文件分类
            validate_content: 是否验证文件内容
            
        Returns:
            文件上传响应
        """
        try:
            # 使用 FileService 进行上传
            result = self.file_service.upload_file(
                file=file,
                filename=filename,
                customer_id=customer_id,
                category=category
            )
            
            self.logger.info(f"Successfully uploaded file: {filename}")
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to upload file {filename}: {e}")
            raise
    
    def batch_upload(
        self,
        files: List[Tuple[BinaryIO, str]],
        customer_id: Optional[int] = None,
        category: str = "general"
    ) -> List[FileUploadResponse]:
        """
        批量文件上传
        
        Args:
            files: 文件列表，每个元素为 (文件对象, 文件名) 元组
            customer_id: 客户ID
            category: 文件分类
            
        Returns:
            上传结果列表
        """
        results = []
        
        for file, filename in files:
            try:
                result = self.upload_with_validation(
                    file=file,
                    filename=filename,
                    customer_id=customer_id,
                    category=category
                )
                results.append(result)
            except Exception as e:
                self.logger.error(f"Failed to upload file {filename} in batch: {e}")
                # 继续处理其他文件
                continue
        
        return results


# 全局服务实例
file_service = FileService()
upload_service = UploadService()


if __name__ == "__main__":
    print("文件服务定义完成")