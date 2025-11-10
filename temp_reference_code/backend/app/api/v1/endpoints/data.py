#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据上传接口

实现数据上传功能，包括：
1. 数据加密验证
2. 本地磁盘存储
3. 数据库记录创建
4. 批次管理

Author: System
Date: 2024
"""

import os
import json
import uuid
import time
import hashlib
import hmac
import base64
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

from fastapi import APIRouter, Depends, HTTPException, status, Header, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from app.core.database import get_db
from app.core.config import settings
from app.models.customer import Customer
from app.services.auth import JWTService
from app.core.exceptions import ValidationException
from app.core.business_codes import BusinessException, BusinessCode, BusinessResponse

router = APIRouter()

# 数据上传请求模型
class DataUploadRequest(BaseModel):
    """
    数据上传请求模型
    
    客户端上传数据时的请求参数
    """
    timestamp: int = Field(..., description="当前时间戳（秒）")
    nonce: str = Field(..., min_length=8, max_length=16, description="随机字符串")
    data: str = Field(..., description="加密后的业务数据（Base64编码）")
    iv: str = Field(..., description="初始化向量（Base64编码）")
    signature: Optional[str] = Field(None, description="数据签名值")
    needread: bool = Field(True, description="是否需要读取确认")

# 数据上传响应模型
class DataUploadResponse(BaseModel):
    """
    数据上传响应模型
    
    数据上传成功后的响应
    """
    code: int = Field(200, description="响应码")
    message: str = Field("数据上传成功", description="响应消息")
    upload_id: Optional[str] = Field(None, description="上传记录ID")
    batch_id: Optional[str] = Field(None, description="批次ID")

# Redis客户端（用于获取data_key）
try:
    import redis
    redis_client = redis.Redis.from_url(settings.REDIS_URL)
except ImportError:
    redis_client = None

# 内存存储（Redis不可用时的备选方案）
nonce_store = {}
data_key_store = {}

def get_current_customer(authorization: str = Header(...)) -> Dict[str, Any]:
    """
    获取当前认证的平台信息
    
    Args:
        authorization: Authorization头
        
    Returns:
        Dict[str, Any]: 平台信息
        
    Raises:
        HTTPException: 认证失败时抛出异常
    """
    try:
        # 解析Bearer Token
        if not authorization.startswith("Bearer "):
            raise BusinessException(
                code=BusinessCode.TOKEN_MISSING,
                message="无效的Authorization头格式"
            )
        
        token = authorization.split(" ")[1]
        
        # 验证JWT Token
        jwt_service = JWTService()
        payload = jwt_service.decode_token(token)
        
        return {
            "customer_id": payload.get("customer_id"),
            "app_id": payload.get("app_id")
        }
        
    except Exception as e:
        raise BusinessException(
            code=BusinessCode.TOKEN_INVALID,
            message="Token无效或已过期"
        )

def get_data_key(customer_id: int) -> Optional[str]:
    """
    获取客户的数据加密密钥
    
    Args:
        customer_id: 客户ID
        
    Returns:
        Optional[str]: 数据密钥，如果不存在返回None
    """
    if redis_client:
        try:
            data_key = redis_client.get(f"data_key:{customer_id}")
            if data_key:
                return data_key.decode('utf-8')
        except Exception:
            pass
    
    return data_key_store.get(customer_id)

def verify_signature(data_key: str, encrypted_data: str, signature: str) -> bool:
    """
    验证数据签名
    
    Args:
        data_key: 数据密钥
        encrypted_data: 加密数据
        signature: 签名值
        
    Returns:
        bool: 签名是否有效
    """
    try:
        expected_signature = hmac.new(
            data_key.encode('utf-8'),
            encrypted_data.encode('utf-8'),
            hashlib.sha256
        ).hexdigest().upper()
        
        return signature.upper() == expected_signature
    except Exception:
        return False

def encrypt_data(data_key: str, plaintext: str) -> Dict[str, str]:
    """
    使用AES-256-GCM加密数据
    
    Args:
        data_key: 数据密钥（Base64编码）
        plaintext: 明文数据
        
    Returns:
        Dict[str, str]: 包含加密数据和IV的字典
        
    Raises:
        Exception: 加密失败时抛出异常
    """
    try:
        # 解码data_key（假设是Base64编码）
        key = base64.b64decode(data_key)
        
        # 生成随机IV
        iv = os.urandom(12)  # GCM模式推荐12字节IV
        
        # 创建AES-GCM加密器
        cipher = AES.new(key, AES.MODE_GCM, nonce=iv)
        
        # 加密数据
        ciphertext, tag = cipher.encrypt_and_digest(plaintext.encode('utf-8'))
        
        # 将密文和认证标签合并
        encrypted_data = ciphertext + tag
        
        return {
            "data": base64.b64encode(encrypted_data).decode('utf-8'),
            "iv": base64.b64encode(iv).decode('utf-8')
        }
        
    except Exception as e:
        raise Exception(f"数据加密失败: {str(e)}")

def decrypt_data(data_key: str, encrypted_data: str, iv: str) -> Dict[str, Any]:
    """
    解密数据
    
    Args:
        data_key: 数据密钥（Base64编码）
        encrypted_data: 加密数据（Base64编码，包含密文+认证标签）
        iv: 初始化向量（Base64编码）
        
    Returns:
        Dict[str, Any]: 解密后的数据
        
    Raises:
        Exception: 解密失败时抛出异常
    """
    try:
        # 解码Base64
        key = base64.b64decode(data_key)
        encrypted_bytes = base64.b64decode(encrypted_data)
        iv_bytes = base64.b64decode(iv)
        print("*"*50)
        # 分离密文和认证标签（GCM模式下，最后16字节是认证标签）
        ciphertext = encrypted_bytes[:-16]
        tag = encrypted_bytes[-16:]
        
        # AES-GCM解密
        cipher = AES.new(key, AES.MODE_GCM, nonce=iv_bytes)
        plaintext = cipher.decrypt_and_verify(ciphertext, tag)
        print("*"*50)
        # 解析JSON数据
        return json.loads(plaintext.decode('utf-8'))
        
    except Exception as e:
        raise Exception(f"数据解密失败: {str(e)}")

def save_data_to_disk(batch_id: str, upload_id: str, data: Dict[str, Any]) -> str:
    """
    将数据保存到本地磁盘
    
    Args:
        batch_id: 批次ID
        upload_id: 上传ID
        data: 要保存的数据
        
    Returns:
        str: 文件路径
    """
    try:
        # 创建存储目录结构
        storage_dir = Path(settings.UPLOAD_PATH) / "data" / batch_id
        storage_dir.mkdir(parents=True, exist_ok=True)
        
        # 生成文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{upload_id}_{timestamp}.json"
        file_path = storage_dir / filename
        
        # 保存数据到文件
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump({
                "upload_id": upload_id,
                "batch_id": batch_id,
                "timestamp": datetime.now().isoformat(),
                "data": data
            }, f, ensure_ascii=False, indent=2)
        
        return str(file_path)
        
    except Exception as e:
        raise Exception(f"数据保存失败: {str(e)}")

def check_nonce_exists(nonce: str) -> bool:
    """
    检查nonce是否已使用（防重放攻击）
    
    Args:
        nonce: 随机字符串
        
    Returns:
        bool: True表示已使用
    """
    if redis_client:
        try:
            return redis_client.exists(f"upload_nonce:{nonce}")
        except Exception:
            pass
    
    # 清理过期的nonce
    current_time = time.time()
    expired_keys = [k for k, v in nonce_store.items() if v < current_time]
    for key in expired_keys:
        del nonce_store[key]
    
    return nonce in nonce_store

def store_nonce(nonce: str, ttl: int = 600):
    """
    存储nonce值
    
    Args:
        nonce: 随机字符串
        ttl: 过期时间（秒）
    """
    if redis_client:
        try:
            redis_client.setex(f"upload_nonce:{nonce}", ttl, "1")
        except Exception:
            nonce_store[nonce] = time.time() + ttl
    else:
        nonce_store[nonce] = time.time() + ttl

@router.post("/{batch_id}", response_model=DataUploadResponse, summary="上传数据")
async def upload_data(
    batch_id: str,
    upload_request: DataUploadRequest,
    authorization: str = Header(..., alias="Authorization"),
    x_data_encrypted: str = Header("true", alias="X-Data-Encrypted"),
    x_data_signature: Optional[str] = Header(None, alias="X-Data-Signature"),
    db: Session = Depends(get_db)
) -> DataUploadResponse:
    """
    上传数据到指定批次
    
    实现数据上传流程：
    1. 验证访问令牌
    2. 时间窗口校验
    3. 防重放攻击检查
    4. 数据解密和验证
    5. 本地磁盘存储
    6. 数据库记录创建
    
    Args:
        batch_id: 批次ID
        upload_request: 上传请求数据
        authorization: 认证头
        x_data_encrypted: 数据是否加密
        x_data_signature: 数据签名
        db: 数据库会话
        
    Returns:
        DataUploadResponse: 上传响应
        
    Raises:
        HTTPException: 上传失败时抛出异常
    """
    try:
        # 1. 验证访问令牌
        customer_info = get_current_customer(authorization)
        customer_id = customer_info["customer_id"]
        
        # 2. 验证客户状态
        customer = db.query(Customer).filter(
            Customer.id == customer_id,
            Customer.status == True
        ).first()
        
        if not customer:
            raise BusinessException(
                code=BusinessCode.USER_NOT_FOUND,
                message="客户账户无效或已停用"
            )
        
        # 3. 时间窗口校验
        current_timestamp = int(time.time())
        time_diff = abs(current_timestamp - upload_request.timestamp)
        
        if time_diff > 300:  # 5分钟时间窗口
            raise BusinessException(
                code=BusinessCode.VALIDATION_ERROR,
                message="时间戳超出允许窗口"
            )
        
        # 4. 防重放攻击校验
        if check_nonce_exists(upload_request.nonce):
            raise BusinessException(
                code=BusinessCode.VALIDATION_ERROR,
                message="请求已被重放（nonce已使用）"
            )
        
        # 5. 获取数据密钥
        data_key = get_data_key(customer_id)
        if not data_key:
            raise BusinessException(
                code=BusinessCode.TOKEN_INVALID,
                message="数据密钥不存在，请重新认证"
            )
        
        # 6. 验证数据签名（如果提供）
        if upload_request.signature or x_data_signature:
            signature = upload_request.signature or x_data_signature
            if not verify_signature(data_key, upload_request.data, signature):
                raise BusinessException(
                    code=BusinessCode.VALIDATION_ERROR,
                    message="数据签名验证失败"
                )
        
        # 7. 解密数据
        try:
            decrypted_data = decrypt_data(
                data_key,
                upload_request.data,
                upload_request.iv
            )
        except Exception as e:
            raise BusinessException(
                code=BusinessCode.VALIDATION_ERROR,
                message=f"数据解密失败: {str(e)}"
            )
        
        # 8. 生成上传ID
        upload_id = str(uuid.uuid4())
        
        # 9. 保存数据到本地磁盘
        try:
            file_path = save_data_to_disk(batch_id, upload_id, decrypted_data)
        except Exception as e:
            raise BusinessException(
                code=BusinessCode.INTERNAL_ERROR,
                message=f"数据保存失败: {str(e)}"
            )
        
        # 10. 记录API调用日志到api_usage_logs表
        from app.services.log import log_service
        try:
            # 准备请求和响应数据
            request_data = {
                "timestamp": upload_request.timestamp,
                "nonce": upload_request.nonce,
                "data_size": len(upload_request.data),
                "iv": upload_request.iv,
                "signature": upload_request.signature,
                "needread": upload_request.needread
            }
            
            response_data = {
                "code": 200,
                "message": "数据上传成功",
                "upload_id": upload_id,
                "batch_id": batch_id,
                "file_size": os.path.getsize(file_path),
                "file_path": file_path
            }
            
            # 记录到api_usage_logs表
            log_service.log_api_call(
                db,
                customer_id=customer_id,
                api_id=1,  # 数据上传API的固定ID
                request_method="POST",
                request_url=f"/api/v1/data/{batch_id}",
                request_headers=None,
                request_body=request_data,
                response_status=200,
                response_headers=None,
                response_time=0.0,  # 这里可以计算实际响应时间
                ip_address=None,  # 可以从request中获取
                user_agent=None,  # 可以从request中获取
                error_message=None,
                error_details=None,
                batch_id=batch_id
            )
            
        except Exception as e:
            # 日志记录失败不影响主业务流程
            print(f"API日志记录失败: {str(e)}")
        
        # 11. 存储nonce，防止重放
        store_nonce(upload_request.nonce)
        
        return DataUploadResponse(
            code=200,
            message="数据上传成功",
            upload_id=upload_id,
            batch_id=batch_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        # 在调试模式下显示详细错误信息
        import traceback
        error_detail = f"内部服务器错误: {str(e)}"
        if settings.DEBUG:
            error_detail += f"\n详细错误: {traceback.format_exc()}"
        
        raise BusinessException(
            code=BusinessCode.INTERNAL_ERROR,
            message=error_detail
        )



@router.get("/{batch_id}/status", summary="查询批次状态")
async def get_batch_status(
    batch_id: str,
    authorization: str = Header(..., alias="Authorization"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    查询批次的上传状态
    
    Args:
        batch_id: 批次ID
        authorization: 认证头
        db: 数据库会话
        
    Returns:
        Dict[str, Any]: 批次状态信息
    """
    try:
        # 验证访问令牌
        customer_info = get_current_customer(authorization)
        customer_id = customer_info["customer_id"]
        
        # 从api_usage_logs表查询批次信息
        from app.models.log import ApiUsageLog
        from sqlalchemy import func
        
        batch_logs = db.query(ApiUsageLog).filter(
            ApiUsageLog.batch_id == batch_id,
            ApiUsageLog.customer_id == customer_id
        ).all()
        
        if not batch_logs:
            raise BusinessException(
                code=BusinessCode.RESOURCE_NOT_FOUND,
                message="批次不存在"
            )
        
        # 统计批次信息
        total_uploads = len(batch_logs)
        successful_uploads = len([log for log in batch_logs if log.response_status == 200])
        failed_uploads = total_uploads - successful_uploads
        
        # 获取最早和最晚的上传时间
        first_upload = min(batch_logs, key=lambda x: x.created_at)
        last_upload = max(batch_logs, key=lambda x: x.created_at)
        
        return {
            "batch_id": batch_id,
            "batch_name": f"批次_{batch_id[:8]}",
            "description": "数据上传批次",
            "status": "completed" if failed_uploads == 0 else "partial",
            "total_count": total_uploads,
            "successful_count": successful_uploads,
            "failed_count": failed_uploads,
            "first_upload_time": first_upload.created_at.isoformat() if first_upload else None,
            "last_upload_time": last_upload.created_at.isoformat() if last_upload else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise BusinessException(
            code=BusinessCode.INTERNAL_ERROR,
            message="查询批次状态失败"
        )