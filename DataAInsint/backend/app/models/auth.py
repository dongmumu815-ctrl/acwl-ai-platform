import os
from pydantic import BaseModel
from typing import Optional

class LoginRequest(BaseModel):
    """登录请求模型"""
    secret_key: str

class LoginResponse(BaseModel):
    """登录响应模型"""
    success: bool
    message: str
    token: Optional[str] = None

class AuthConfig:
    """认证配置"""
    # 从环境变量读取密钥，如果没有设置则使用默认值
    SECRET_KEY = os.getenv("DATAINSIGHT_SECRET_KEY", "DataInsight@2024#Secure!Key")
    # JWT密钥，从环境变量读取
    JWT_SECRET = os.getenv("DATAINSIGHT_JWT_SECRET", "DataInsight-JWT-Secret-Key-2024!@#$%^&*()")
    # Token过期时间（小时）
    TOKEN_EXPIRE_HOURS = int(os.getenv("DATAINSIGHT_TOKEN_EXPIRE_HOURS", "24"))