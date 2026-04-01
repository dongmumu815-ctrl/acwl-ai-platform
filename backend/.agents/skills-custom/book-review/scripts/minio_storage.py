import io
import os
from datetime import datetime
from typing import Optional

try:
    from minio import Minio
    from minio.error import S3Error
    MINIO_AVAILABLE = True
except ImportError:
    MINIO_AVAILABLE = False

from config import MINIO_ENDPOINT, MINIO_ACCESS_KEY, MINIO_SECRET_KEY, MINIO_BUCKET_NAME, MINIO_FOLDER


class MinioStorage:
    """MinIO 对象存储工具，用于上传审读报告"""

    def __init__(self):
        if not MINIO_AVAILABLE:
            raise ImportError("minio 库未安装，请执行: pip install minio")
        self.client = Minio(
            MINIO_ENDPOINT,
            access_key=MINIO_ACCESS_KEY,
            secret_key=MINIO_SECRET_KEY,
            secure=False
        )
        self.bucket = MINIO_BUCKET_NAME
        self.folder = MINIO_FOLDER
        self._ensure_bucket()

    def _ensure_bucket(self):
        """确保 bucket 存在"""
        try:
            if not self.client.bucket_exists(self.bucket):
                self.client.make_bucket(self.bucket)
                print(f"已创建 MinIO bucket: {self.bucket}")
        except S3Error as e:
            print(f"MinIO bucket 检查失败: {e}")
            raise

    def upload_report(self, filename: str, content: str) -> str:
        """
        上传报告内容到 MinIO。
        返回对象路径（folder/filename）。
        """
        object_name = f"{self.folder}/{filename}"
        data = content.encode("utf-8")
        self.client.put_object(
            self.bucket,
            object_name,
            io.BytesIO(data),
            length=len(data),
            content_type="text/markdown; charset=utf-8"
        )
        return object_name

    def get_report_url(self, object_name: str, expires_days: int = 7) -> str:
        """
        获取报告的预签名下载 URL（默认有效期7天）。
        """
        from datetime import timedelta
        url = self.client.presigned_get_object(
            self.bucket,
            object_name,
            expires=timedelta(days=expires_days)
        )
        return url


# 全局单例
_storage: Optional[MinioStorage] = None


def get_minio_storage() -> MinioStorage:
    global _storage
    if _storage is None:
        _storage = MinioStorage()
    return _storage
