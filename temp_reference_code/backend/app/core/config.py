#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
应用配置管理模块

使用Pydantic Settings管理应用配置，支持从环境变量和.env文件读取配置。
提供类型安全的配置访问和验证。

Author: System
Date: 2024
"""

from typing import List, Optional
from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings
from functools import lru_cache
import os


class Settings(BaseSettings):
    """
    应用配置类
    
    使用Pydantic BaseSettings自动从环境变量读取配置
    支持类型验证和默认值设置
    """
    
    # 应用基本配置
    APP_NAME: str = "自定义接口管理系统"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    API_PREFIX: str = "/api/v1"
    CUSTOM_API_PREFIX: str = "/api/custom"
    
    # 服务器配置
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 1
    
    # 数据库配置
    DB_HOST: str = "10.20.1.200"
    DB_PORT: int = 3306
    DB_USER: str = "root"
    DB_PASSWORD: str = "2wsx1QAZaczt"
    DB_NAME: str = "acwl_api_system"
    DB_CHARSET: str = "utf8mb4"
    
    # Redis配置
    REDIS_HOST: str = "10.20.1.200"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = "1qaz2WSXaczt"
    REDIS_DB: int = 0
    
    # JWT配置
    SECRET_KEY: str = "your-super-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 修改为1440分钟（一天）
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # 文件上传配置
    UPLOAD_DIR: str = "./uploads"
    TEMP_DIR: str = "./temp"
    MAX_UPLOAD_SIZE: int = 10485760  # 10MB
    ALLOWED_EXTENSIONS: List[str] = ["jpg", "jpeg", "png", "gif", "pdf", "doc", "docx", "xls", "xlsx", "txt", "csv", "json"]
    
    # 日志配置
    LOG_LEVEL: str = "DEBUG"
    LOG_FILE: str = "./logs/app.log"
    LOG_ROTATION: str = "10 MB"  # 改为按大小轮转，避免时间轮转的文件锁定问题
    LOG_RETENTION: str = "30 days"
    
    # CORS配置
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8080"]
    ALLOWED_METHODS: List[str] = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    ALLOWED_HEADERS: List[str] = ["*"]
    
    # iframe嵌入配置
    IFRAME_ENABLED: bool = True  # 是否允许iframe嵌入
    IFRAME_ALLOWED_ORIGINS: List[str] = ["*"]  # 允许嵌入的父页面域名，"*"表示允许所有
    X_FRAME_OPTIONS: str = "SAMEORIGIN"  # X-Frame-Options头部值: DENY, SAMEORIGIN, ALLOW-FROM
    CSP_FRAME_ANCESTORS: str = "*"  # Content-Security-Policy frame-ancestors指令
    
    # 邮件配置
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_TLS: bool = True
    FROM_EMAIL: Optional[str] = None
    
    # Celery配置
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"
    
    # 监控配置
    METRICS_ENABLED: bool = True
    METRICS_PORT: int = 9090
    
    # 系统默认配置
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100
    DEFAULT_RATE_LIMIT: int = 100  # 每分钟请求数
    MAX_API_PER_CUSTOMER: int = 10
    SESSION_TIMEOUT: int = 7200  # 会话超时时间（秒）
    
    # Doris配置
    DORIS_ENABLED: bool = True  # 是否启用Doris存储访问日志
    DORIS_HOST: str = "10.20.1.201"
    DORIS_HTTP_PORT: int = 8030  # FE HTTP端口
    DORIS_BE_HTTP_PORT: int = 8040  # BE HTTP端口（用于Stream Load）
    DORIS_QUERY_PORT: int = 9030  # FE查询端口
    DORIS_USER: str = "root"
    DORIS_PASSWORD: str = "2wsx1QAZaczt"
    DORIS_DATABASE: str = "cepiec-logs"
    DORIS_ACCESS_LOG_TABLE: str = "api_access_logs"
    DORIS_BATCH_SIZE: int = 100  # 批量插入大小
    DORIS_FLUSH_INTERVAL: int = 30  # 刷新间隔（秒）
    
    # MinIO配置
    MINIO_ENDPOINT: str = "10.20.1.200:9000"  # MinIO服务地址
    MINIO_ACCESS_KEY: str = "acwl"  # MinIO访问密钥
    MINIO_SECRET_KEY: str = "1qaz2WSXaczt"  # MinIO秘密密钥
    MINIO_SECURE: bool = False  # 是否使用HTTPS
    MINIO_BUCKET_NAME: str = "cepiec-read-data"  # 存储桶名称
    MINIO_REGION: str = "us-east-1"  # 区域设置

        # API请求数据大小限制
    MAX_REQUEST_BODY_SIZE: int = 600 * 1024 * 1024  # 600MB，考虑加密后数据膨胀
    MAX_ENCRYPTED_DATA_SIZE: int = 500 * 1024 * 1024  # 500MB，加密前原始数据
    MAX_BATCH_RECORDS: int = 10000  # 单批次最大记录数
    
    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, v):
        """
        验证密钥安全性
        
        确保在生产环境中使用安全的密钥
        """
        if len(v) < 32:
            raise ValueError("SECRET_KEY长度至少需要32个字符")
        if v == "your-super-secret-key-change-in-production":
            # 在生产环境中（DEBUG=False）必须更改默认密钥
            # 这里我们假设如果使用默认密钥，则为开发环境
            import os
            debug_mode = os.getenv("DEBUG", "True").lower() in ("true", "1", "yes")
            if not debug_mode:
                raise ValueError("生产环境必须更改默认SECRET_KEY")
        return v
    
    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v) -> List[str]:
        """
        解析CORS允许的源地址
        
        将逗号分隔的字符串转换为列表
        """
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        elif isinstance(v, list):
            return v
        return []
    
    @field_validator("ALLOWED_METHODS", mode="before")
    @classmethod
    def parse_cors_methods(cls, v) -> List[str]:
        """
        解析CORS允许的HTTP方法
        
        将逗号分隔的字符串转换为列表
        """
        if isinstance(v, str):
            return [method.strip().upper() for method in v.split(",") if method.strip()]
        elif isinstance(v, list):
            return [method.upper() for method in v]
        return []
    
    @field_validator("ALLOWED_HEADERS", mode="before")
    @classmethod
    def parse_cors_headers(cls, v) -> List[str]:
        """
        解析CORS允许的请求头
        
        将逗号分隔的字符串转换为列表
        """
        if isinstance(v, str):
            if v == "*":
                return ["*"]
            return [header.strip() for header in v.split(",") if header.strip()]
        elif isinstance(v, list):
            return v
        return []
    
    @field_validator("ALLOWED_EXTENSIONS", mode="before")
    @classmethod
    def parse_allowed_extensions(cls, v) -> List[str]:
        """
        解析允许上传的文件扩展名
        
        将逗号分隔的字符串转换为列表
        """
        if isinstance(v, str):
            return [ext.strip().lower() for ext in v.split(",") if ext.strip()]
        elif isinstance(v, list):
            return [ext.lower() for ext in v]
        return []
    
    @property
    def DATABASE_URL(self) -> str:
        """
        构建数据库连接URL
        
        返回完整的MySQL连接字符串
        """
        return (
            f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
            f"?charset={self.DB_CHARSET}"
        )
    
    @property
    def REDIS_URL(self) -> str:
        """
        构建Redis连接URL
        
        返回完整的Redis连接字符串
        """
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
    
    @property
    def DORIS_HTTP_URL(self) -> str:
        """
        构建Doris FE HTTP连接URL
        
        返回完整的Doris FE HTTP连接字符串
        """
        return f"http://{self.DORIS_HOST}:{self.DORIS_HTTP_PORT}"
    
    @property
    def DORIS_BE_HTTP_URL(self) -> str:
        """
        构建Doris BE HTTP连接URL
        
        返回完整的Doris BE HTTP连接字符串，用于Stream Load
        """
        return f"http://{self.DORIS_HOST}:{self.DORIS_BE_HTTP_PORT}"
    
    @property
    def DORIS_JDBC_URL(self) -> str:
        """
        构建Doris JDBC连接URL
        
        返回完整的Doris JDBC连接字符串，用于查询
        """
        return f"jdbc:mysql://{self.DORIS_HOST}:{self.DORIS_QUERY_PORT}/{self.DORIS_DATABASE}"
    
    @property
    def UPLOAD_PATH(self) -> str:
        """
        获取上传文件的绝对路径
        
        确保上传目录存在
        """
        upload_path = os.path.abspath(self.UPLOAD_DIR)
        os.makedirs(upload_path, exist_ok=True)
        return upload_path
    
    @property
    def TEMP_PATH(self) -> str:
        """
        获取临时文件的绝对路径
        
        确保临时目录存在
        """
        temp_path = os.path.abspath(self.TEMP_DIR)
        os.makedirs(temp_path, exist_ok=True)
        return temp_path
    
    @property
    def LOG_PATH(self) -> str:
        """
        获取日志文件的绝对路径
        
        确保日志目录存在
        """
        log_path = os.path.abspath(os.path.dirname(self.LOG_FILE))
        os.makedirs(log_path, exist_ok=True)
        return os.path.abspath(self.LOG_FILE)
    
    def is_email_configured(self) -> bool:
        """
        检查邮件配置是否完整
        
        返回邮件功能是否可用
        """
        return all([
            self.SMTP_HOST,
            self.SMTP_USER,
            self.SMTP_PASSWORD,
            self.FROM_EMAIL
        ])
    
    def get_allowed_file_extensions(self) -> set:
        """
        获取允许上传的文件扩展名集合
        
        返回小写的扩展名集合，便于快速查找
        """
        if isinstance(self.ALLOWED_EXTENSIONS, list):
            return set(ext.lower() for ext in self.ALLOWED_EXTENSIONS)
        return set()
    
    class Config:
        """
        Pydantic配置类
        
        指定环境变量文件和编码
        """
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """
    获取应用配置实例
    
    使用LRU缓存确保配置单例，提高性能
    
    Returns:
        Settings: 配置实例
    """
    return Settings()


# 全局配置实例
settings = get_settings()


# 配置验证函数
def validate_settings():
    """
    验证配置的完整性和正确性
    
    在应用启动时调用，确保关键配置正确
    """
    errors = []
    
    # 验证数据库配置
    if not settings.DB_HOST or not settings.DB_NAME:
        errors.append("数据库配置不完整")
    
    # 验证密钥配置
    if len(settings.SECRET_KEY) < 32:
        errors.append("SECRET_KEY长度不足")
    
    # 验证上传目录
    try:
        os.makedirs(settings.UPLOAD_PATH, exist_ok=True)
    except Exception as e:
        errors.append(f"无法创建上传目录: {e}")
    
    # 验证日志目录
    try:
        os.makedirs(os.path.dirname(settings.LOG_PATH), exist_ok=True)
    except Exception as e:
        errors.append(f"无法创建日志目录: {e}")
    
    if errors:
        raise ValueError(f"配置验证失败: {'; '.join(errors)}")


if __name__ == "__main__":
    # 测试配置
    print(f"应用名称: {settings.APP_NAME}")
    print(f"数据库URL: {settings.DATABASE_URL}")
    print(f"Redis URL: {settings.REDIS_URL}")
    print(f"上传路径: {settings.UPLOAD_PATH}")
    print(f"日志路径: {settings.LOG_PATH}")
    print(f"邮件配置: {settings.is_email_configured()}")
    print(f"允许的文件扩展名: {settings.get_allowed_file_extensions()}")
    
    # 验证配置
    try:
        validate_settings()
        print("✅ 配置验证通过")
    except ValueError as e:
        print(f"❌ 配置验证失败: {e}")