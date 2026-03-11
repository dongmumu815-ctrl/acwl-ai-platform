#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置管理模块
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List, Optional
import os
from pathlib import Path


class Settings(BaseSettings):
    """应用配置类"""
    
    # 基础配置
    PROJECT_NAME: str = "ACWL-AI"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "企业级AI大模型管理和部署平台"
    
    # 服务器配置
    HOST: str = Field(default="0.0.0.0", description="服务器主机")
    PORT: int = Field(default=8082, description="服务器端口")
    DEBUG: bool = Field(default=False, description="调试模式")
    ENVIRONMENT: str = Field(default="production", description="运行环境")
    
    # 安全配置
    SECRET_KEY: str = Field(default="acwl-ai-secret-key-change-in-production", description="密钥")
    ALGORITHM: str = Field(default="HS256", description="JWT算法")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=1440, description="访问令牌过期时间(分钟)")
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=30, description="刷新令牌过期时间(天)")
    
    # CORS配置
    ALLOWED_HOSTS: List[str] = Field(default=["*"], description="允许的主机")
    
    # 数据库配置
    # DB_HOST: str = Field(default="10.20.1.200", description="数据库主机")
    DB_HOST: str = Field(default="10.20.1.200", description="数据库主机")
    DB_PORT: int = Field(default=3306, description="数据库端口")
    DB_USER: str = Field(default="root", description="数据库用户")
    DB_PASSWORD: str = Field(default="2wsx1QAZaczt", description="数据库密码")
    # DB_PASSWORD: str = Field(default="12345678", description="数据库密码")
    DB_NAME: str = Field(default="acwl-ai-data", description="数据库名称")
    DB_CHARSET: str = Field(default="utf8mb4", description="数据库字符集")
    
    # Doris配置（用于数据上传日志展示）
    DORIS_HOST: str = Field(default=os.getenv("DORIS_HOST", "10.20.1.201"), description="Doris主机")
    DORIS_PORT: int = Field(default=int(os.getenv("DORIS_PORT", "9030")), description="Doris查询端口")
    DORIS_USER: str = Field(default=os.getenv("DORIS_USER", "root"), description="Doris用户")
    DORIS_PASSWORD: str = Field(default=os.getenv("DORIS_PWD", "2wsx1QAZaczt"), description="Doris密码")
    DORIS_DATABASE: str = Field(default=os.getenv("DORIS_DB", "cepiec-logs"), description="Doris数据库")
    
    # Redis配置
    REDIS_HOST: str = Field(default="10.20.1.200", description="Redis主机")
    REDIS_PORT: int = Field(default=6379, description="Redis端口")
    REDIS_PASSWORD: Optional[str] = Field(default=None, description="Redis密码")
    REDIS_DB: int = Field(default=0, description="Redis数据库")
    
    # Celery配置
    CELERY_BROKER_URL: str = Field(default="redis://10.20.1.200:6379/1", description="Celery代理URL")
    CELERY_RESULT_BACKEND: str = Field(default="redis://10.20.1.200:6379/2", description="Celery结果后端")
    
    # 文件存储配置
    UPLOAD_DIR: str = Field(default="uploads", description="上传目录")
    MAX_FILE_SIZE: int = Field(default=100 * 1024 * 1024, description="最大文件大小(字节)")
    ALLOWED_FILE_TYPES: List[str] = Field(
        default=[".txt", ".pdf", ".docx", ".json", ".csv", ".jsonl"],
        description="允许的文件类型"
    )
    
    # 模型存储配置
    MODEL_STORAGE_DIR: str = Field(default="models", description="模型存储目录")
    DATASET_STORAGE_DIR: str = Field(default="datasets", description="数据集存储目录")
    
    # 日志配置
    LOG_LEVEL: str = Field(default="INFO", description="日志级别")
    LOG_FILE: str = Field(default="logs/acwl-ai.log", description="日志文件")
    LOG_ROTATION: str = Field(default="1 day", description="日志轮转")
    LOG_RETENTION: str = Field(default="30 days", description="日志保留")
    
    # API配置
    API_V1_PREFIX: str = Field(default="/api/v1", description="API v1前缀")
    
    # 分页配置
    DEFAULT_PAGE_SIZE: int = Field(default=20, description="默认分页大小")
    MAX_PAGE_SIZE: int = Field(default=100, description="最大分页大小")
    
    # 缓存配置
    CACHE_TTL: int = Field(default=3600, description="缓存TTL(秒)")
    
    # GPU监控配置
    ENABLE_GPU_MONITORING: bool = Field(default=True, description="启用GPU监控")
    GPU_MEMORY_THRESHOLD: float = Field(default=0.9, description="GPU内存阈值")
    
    # 部署配置
    DEFAULT_DEPLOYMENT_TIMEOUT: int = Field(default=300, description="默认部署超时时间(秒)")
    MAX_CONCURRENT_DEPLOYMENTS: int = Field(default=5, description="最大并发部署数")
    
    # MinIO对象存储配置
    MINIO_ENDPOINT: str = Field(default="10.20.1.200:9000", description="MinIO服务地址")
    MINIO_ACCESS_KEY: str = Field(default="acwl", description="MinIO访问密钥")
    MINIO_SECRET_KEY: str = Field(default="1qaz2WSXaczt", description="MinIO秘密密钥")
    MINIO_SECURE: bool = Field(default=False, description="是否使用HTTPS")
    MINIO_BUCKET_NAME: str = Field(default="cepiec-read-data", description="存储桶名称")
    MINIO_REGION: str = Field(default="us-east-1", description="区域设置")
    
    # MinIO分片上传配置
    MINIO_CHUNK_SIZE: int = Field(default=64 * 1024 * 1024, description="分片大小(64MB)")
    MINIO_MAX_RETRIES: int = Field(default=3, description="最大重试次数")
    MINIO_TIMEOUT: int = Field(default=300, description="超时时间(秒)")
    
    @property
    def database_url(self) -> str:
        """获取数据库连接URL"""
        return (
            f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
            f"?charset={self.DB_CHARSET}"
        )
    
    @property
    def redis_url(self) -> str:
        """获取Redis连接URL"""
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
    
    def create_directories(self):
        """创建必要的目录"""
        directories = [
            self.UPLOAD_DIR,
            self.MODEL_STORAGE_DIR,
            self.DATASET_STORAGE_DIR,
            Path(self.LOG_FILE).parent
        ]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# 创建全局配置实例
settings = Settings()

# 创建必要的目录
settings.create_directories()