#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
认证鉴权接口

实现客户端认证和密钥获取功能，包括：
1. 签名验证
2. 时间窗口校验
3. 防重放攻击
4. 生成访问令牌和数据密钥

Author: System
Date: 2024
"""

import hashlib
import hmac
import time
import uuid
import base64
from datetime import datetime, timedelta
from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.core.config import settings
from app.models.customer import Customer
from app.services.auth import AuthService, JWTService
from app.services.customer import CustomerSessionService
from app.schemas.customer import CustomerLoginRequest, CustomerLoginResponse
from app.core.exceptions import ValidationException
from app.core.business_codes import BusinessException, BusinessCode, BusinessResponse

router = APIRouter()

# 服务实例
auth_service = AuthService()
jwt_service = JWTService()
customer_session_service = CustomerSessionService()

# 认证请求模型
class AuthRequest(BaseModel):
    """
    认证请求模型
    
    客户端认证时需要提供的参数
    """
    appid: str = Field(..., description="应用唯一标识")
    timestamp: int = Field(..., description="当前时间戳（秒）")
    nonce: str = Field(..., min_length=8, max_length=16, description="随机字符串")
    signature: str = Field(..., description="签名值")

# 简化认证请求模型
class SimpleAuthRequest(BaseModel):
    """
    简化认证请求模型
    
    使用app_id和app_secret进行简单认证
    """
    app_id: str = Field(..., description="应用ID")
    app_secret: str = Field(..., description="应用密钥")

# 认证响应模型
class AuthResponse(BaseModel):
    """
    认证响应模型
    
    认证成功后返回的数据
    """
    access_token: str = Field(description="访问令牌")
    data_key: str = Field(description="数据加密密钥")
    expires_in: int = Field(description="令牌过期时间（秒）")

# Redis客户端（用于存储nonce）
try:
    import redis
    redis_client = redis.Redis.from_url(settings.REDIS_URL)
except ImportError as e:
    print(f"警告: REDIS连接失败: {e}, 请检查配置{settings.REDIS_URL}")
    redis_client = None

# 内存存储（Redis不可用时的备选方案）
nonce_store = {}

def store_nonce(nonce: str, ttl: int = 600):
    """
    存储nonce值，防止重放攻击
    
    Args:
        nonce: 随机字符串
        ttl: 过期时间（秒）
    """
    if redis_client:
        try:
            redis_client.setex(f"nonce:{nonce}", ttl, "1")
        except Exception:
            # Redis失败时使用内存存储
            nonce_store[nonce] = time.time() + ttl
    else:
        nonce_store[nonce] = time.time() + ttl

def check_nonce(nonce: str) -> bool:
    """
    检查nonce是否已使用
    
    Args:
        nonce: 随机字符串
        
    Returns:
        bool: True表示已使用，False表示未使用
    """
    if redis_client:
        try:
            return redis_client.exists(f"nonce:{nonce}")
        except Exception:
            pass
    
    # 清理过期的nonce
    current_time = time.time()
    expired_keys = [k for k, v in nonce_store.items() if v < current_time]
    for key in expired_keys:
        del nonce_store[key]
    
    return nonce in nonce_store

def generate_signature(appid: str, timestamp: int, nonce: str, secret: str) -> str:
    """
    生成签名
    
    Args:
        appid: 应用ID
        timestamp: 时间戳
        nonce: 随机字符串
        secret: 预共享密钥
        
    Returns:
        str: 签名值
    """
    signature_data = f"{appid}{timestamp}{nonce}"
    signature = hmac.new(
        secret.encode('utf-8'),
        signature_data.encode('utf-8'),
        hashlib.sha256
    ).hexdigest().upper()
    return signature

def generate_data_key() -> str:
    """
    生成数据加密密钥
    
    Returns:
        str: Base64编码的AES-256密钥
    """
    # 生成32字节的随机密钥（AES-256）
    key = uuid.uuid4().bytes + uuid.uuid4().bytes
    return base64.b64encode(key).decode('utf-8')

@router.post("/login", response_model=CustomerLoginResponse, summary="客户登录")
async def customer_login(
    login_request: CustomerLoginRequest,
    db: Session = Depends(get_db)
) -> CustomerLoginResponse:
    """
    客户登录接口
    
    使用app_id和app_secret进行简单认证，返回访问令牌
    
    Args:
        login_request: 登录请求参数
        db: 数据库会话
        
    Returns:
        CustomerLoginResponse: 登录响应数据
        
    Raises:
        HTTPException: 认证失败时抛出异常
    """
    try:
        # 使用客户会话服务进行登录
        result = customer_session_service.login_customer(
            db, login_request
        )
        
        # 构造响应
        from app.schemas.customer import CustomerResponse
        customer_dict = result["customer"]
        customer_response = CustomerResponse.model_validate(customer_dict)
        
        return CustomerLoginResponse(
            access_token=result["access_token"],
            token_type=result["token_type"],
            expires_in=result["expires_in"],
            customer=customer_response,
            session_id=result["session_token"]
        )
        
    except ValidationException as e:
        raise BusinessException(
            BusinessCode.AUTH_FAILED,
            str(e)
        )
    except Exception as e:
        import traceback
        print(f"Login error: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        raise BusinessException(
            BusinessCode.INTERNAL_ERROR,
            f"登录失败: {str(e)}"
        )

@router.post("/token", summary="获取访问令牌（签名认证）")
async def get_access_token(
    auth_request: AuthRequest,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    获取访问令牌和数据密钥
    
    实现客户端认证流程：
    1. 验证时间窗口
    2. 防重放攻击检查
    3. 签名验证
    4. 生成访问令牌和数据密钥
    
    Args:
        auth_request: 认证请求参数
        db: 数据库会话
        
    Returns:
        AuthResponse: 认证响应数据
        
    Raises:
        HTTPException: 认证失败时抛出异常
    """
    try:
        # 1. 时间窗口校验
        current_timestamp = int(time.time())
        time_diff = abs(current_timestamp - auth_request.timestamp)
        
        if time_diff > 300:  # 5分钟时间窗口
            raise BusinessException(BusinessCode.TIMESTAMP_OUT_OF_WINDOW)
        
        # 2. 防重放攻击校验
        if check_nonce(auth_request.nonce):
            raise BusinessException(BusinessCode.NONCE_REPLAY_ATTACK)
        
        # 3. 查找平台信息
        customer = db.query(Customer).filter(
            Customer.app_id == auth_request.appid,
            Customer.status == True
        ).first()
        
        if not customer:
            raise BusinessException(BusinessCode.APPID_INVALID)
        
        # 4. 签名验证
        expected_signature = generate_signature(
            auth_request.appid,
            auth_request.timestamp,
            auth_request.nonce,
            customer.app_secret
        )
        
        if auth_request.signature != expected_signature:
            raise BusinessException(BusinessCode.SIGNATURE_FAILED)
        
        # 5. 存储nonce，防止重放
        store_nonce(auth_request.nonce)
        
        # 6. 生成访问令牌
        jwt_service = JWTService()
        access_token = jwt_service.create_access_token(
            subject=customer.id,
            user_type="customer",
            additional_claims={
                "customer_id": customer.id,
                "app_id": customer.app_id
            }
        )
        
        # 7. 生成数据密钥
        data_key = generate_data_key()
        
        # 8. 可选：将data_key存储到Redis中，与access_token关联
        print(f"Data Key111: {data_key}",type(redis_client))
        
        if redis_client:
            try:
                redis_client.setex(
                    f"data_key:{customer.id}",
                    settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
                    data_key
                )
            except Exception:
                print(f"Data redis_client set error: {data_key}",type(redis_client))

        
        # 构造成功响应数据
        response_data = {
            "access_token": access_token,
            "data_key": data_key,
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        }
        
        return BusinessResponse.success(response_data)
        
    except BusinessException:
        raise
    except Exception as e:
        raise BusinessException(BusinessCode.INTERNAL_ERROR)

@router.get("/verify", summary="验证令牌")
async def verify_token(
    token: str,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    验证访问令牌的有效性
    
    Args:
        token: 访问令牌
        db: 数据库会话
        
    Returns:
        Dict[str, Any]: 令牌信息
    """
    try:
        jwt_service = JWTService()
        payload = jwt_service.decode_token(token)
        
        # 验证客户是否仍然有效
        customer = db.query(Customer).filter(
            Customer.id == payload.get("customer_id"),
            Customer.status == True
        ).first()
        
        if not customer:
            raise BusinessException(
                code=BusinessCode.USER_NOT_FOUND,
                message="令牌对应的客户无效"
            )
        
        return {
            "valid": True,
            "customer_id": customer.id,
            "app_id": customer.app_id,
            "expires_at": payload.get("exp")
        }
        
    except Exception as e:
        raise BusinessException(
            code=BusinessCode.TOKEN_INVALID,
            message="令牌无效或已过期"
        )