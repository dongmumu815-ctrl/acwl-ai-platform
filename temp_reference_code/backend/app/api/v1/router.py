#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API v1 路由配置

数据采集接口 v1 版本的路由配置，包括：
1. 认证鉴权接口
2. 数据上传接口
3. 批次管理接口
4. 结果查询接口

Author: System
Date: 2024
"""

from typing import Optional
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from functools import lru_cache
import time
import logging
import asyncio
import json

from app.core.database import get_db
from app.models.api import CustomApi
from app.services.api import api_field_service, custom_api_service
from app.services.auth import jwt_service, AuthService
from app.core.exceptions import ValidationException, CustomException
from app.core.business_codes import BusinessCode, BusinessResponse, BusinessException
from app.core.logging import logger
from app.core.config import settings
from app.models.batch import DataBatch

# Redis客户端配置
try:
    import redis
    redis_client = redis.Redis.from_url(settings.REDIS_URL)
except ImportError:
    redis_client = None

# 导入各个端点模块
from app.api.v1.endpoints import auth, data, batch, result, results, admin
from app.api.v1.endpoints.data import get_current_customer, decrypt_data, get_data_key
import ipaddress

# 获取日志记录器
logger = logging.getLogger(__name__)

# 常用HTTP方法集合，用于快速查找
WRITE_METHODS = {"POST", "PUT", "PATCH"}

def is_internal_ip(ip_address: str) -> bool:
    """
    检查IP地址是否为内网地址（192.** 或 10.**）
    
    Args:
        ip_address: IP地址字符串
        
    Returns:
        bool: 如果是内网地址返回True，否则返回False
    """
    if not ip_address or ip_address == "unknown":
        return False
        
    try:
        ip = ipaddress.ip_address(ip_address)
        # 检查是否为192.168.0.0/16网段
        if ip in ipaddress.ip_network('192.168.0.0/16'):
            return True
        # 检查是否为10.0.0.0/8网段
        if ip in ipaddress.ip_network('10.0.0.0/8'):
            return True
        return False
    except ValueError:
        # 无效的IP地址
        return False

def get_api_config_with_cache(db: Session, api_code: str) -> Optional[CustomApi]:
    """
    获取API配置（带Redis缓存）
    
    Args:
        db: 数据库会话
        api_code: API代码
        
    Returns:
        CustomApi: API配置对象或None
    """
    cache_key = f"api_config:{api_code}"
    cache_ttl = 300  # 5分钟缓存
    
    # 尝试从Redis缓存获取
    if redis_client:
        try:
            cached_data = redis_client.get(cache_key)
            if cached_data:
                api_data = json.loads(cached_data.decode('utf-8'))
                # 重新构造CustomApi对象
                api_config = CustomApi(**api_data)
                logger.debug(f"Cache hit for API config: {api_code}")
                return api_config
        except Exception as e:
            logger.warning(f"Failed to get API config from cache: {e}")
    
    # 缓存未命中或Redis不可用，查询数据库
    logger.debug(f"Cache miss for API config: {api_code}, querying database")
    api_config = db.query(CustomApi).filter(
        CustomApi.api_code == api_code
    ).first()
    
    # 将结果存入Redis缓存
    if redis_client and api_config:
        try:
            # 将API配置序列化为字典
            api_dict = {
                "id": api_config.id,
                "customer_id": api_config.customer_id,
                "api_name": api_config.api_name,
                "api_code": api_config.api_code,
                "api_description": api_config.api_description,
                "api_url": api_config.api_url,
                "http_method": api_config.http_method,
                "status": api_config.status,
                "rate_limit": api_config.rate_limit,
                "require_authentication": api_config.require_authentication,
                "response_format": api_config.response_format,
                "created_at": api_config.created_at.isoformat() if api_config.created_at else None,
                "updated_at": api_config.updated_at.isoformat() if api_config.updated_at else None
            }
            
            serialized_data = json.dumps(api_dict, ensure_ascii=False)
            redis_client.setex(cache_key, cache_ttl, serialized_data)
            logger.debug(f"Cached API config: {api_code}")
        except Exception as e:
            logger.warning(f"Failed to cache API config for {api_code}: {e}")
    
    return api_config


def invalidate_api_config_cache(api_code: str):
    """
    清除指定API的配置缓存
    
    Args:
        api_code: API代码
    """
    if not redis_client:
        return
    
    try:
        cache_key = f"api_config:{api_code}"
        redis_client.delete(cache_key)
        logger.debug(f"Invalidated cache for API config: {api_code}")
    except Exception as e:
        logger.warning(f"Failed to invalidate cache for API config {api_code}: {e}")

# 创建主路由
api_router = APIRouter()

# 注册子路由
api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["认证鉴权"]
)

api_router.include_router(
    data.router,
    prefix="/data",
    tags=["数据上传"]
)

api_router.include_router(
    batch.router,
    prefix="/batch",
    tags=["批次管理"]
)

api_router.include_router(
    result.router,
    prefix="/result",
    tags=["结果查询"]
)

api_router.include_router(
    results.router,
    prefix="/results",
    tags=["批次结果查询"]
)

api_router.include_router(
    admin.router,
    prefix="/admin",
    tags=["管理后台"]
)

# 服务实例
api_service = custom_api_service
auth_service = AuthService()


# 支持带batch_id的路径参数路由
@api_router.api_route(
    "/{batch_id}/{api_code}",
    methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    summary="带批次ID的动态自定义API",
    tags=["自定义API"]
)
async def handle_custom_api_with_batch_v1(
    batch_id: str,
    api_code: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    处理带批次ID的自定义API请求（v1路径兼容）
    
    根据API代码和批次ID动态处理不同的自定义API请求。
    URL格式: /api/v1/{batch_id}/{api_code}
    
    Args:
        batch_id: 批次标识符（路径参数）
        api_code: API代码（路径参数）
        request: 请求对象
        db: 数据库会话
        
    Returns:
        API响应结果
    """
    return await _handle_custom_api_internal(
        api_code=api_code,
        request=request,
        db=db,
        batch_id_from_path=batch_id
    )


async def _log_api_call_async(
    api_service,
    db: Session,
    api_config,
    ip_address: str,
    request_data: dict,
    response_data: dict,
    is_success: bool,
    batch_id: str = None,
    encryption_params: dict = None,
    file_path: str = None
):
    """
    异步记录API调用日志
    
    Args:
        api_service: API服务实例
        db: 数据库会话（如果为None，则创建独立的数据库会话）
        api_config: API配置对象
        ip_address: 客户端IP地址
        request_data: 请求数据
        response_data: 响应数据
        is_success: 是否成功
        batch_id: 批次ID（可选）
        encryption_params: 加密相关参数（可选）
        file_path: 文件存储路径（可选）
    """
    log_start_time = time.time()
    
    print(f"🚀 [异步日志] 开始异步记录API调用日志...")
    print(f"   API代码: {api_config.api_code if hasattr(api_config, 'api_code') else 'N/A'}")
    print(f"   批次ID: {batch_id}")
    print(f"   文件路径: {file_path}")
    print(f"   是否成功: {is_success}")
    print(f"   IP地址: {ip_address}")
    
    # 如果没有传递数据库会话，创建独立的会话
    if db is None:
        print(f"📊 [异步日志] 创建独立的数据库会话...")
        from app.core.database import get_db
        db_generator = get_db()
        db = next(db_generator)
        should_close_db = True
    else:
        print(f"📊 [异步日志] 使用传入的数据库会话...")
        should_close_db = False
    
    try:
        # 准备加密参数（如果有的话）
        encryption_kwargs = {}
        if encryption_params:
            print(f"🔐 [异步日志] 准备加密参数: {list(encryption_params.keys())}")
            encryption_kwargs.update({
                "timestamp": encryption_params.get("timestamp"),
                "nonce": encryption_params.get("nonce"),
                "encrypted_data": encryption_params.get("encrypted_data"),
                "iv": encryption_params.get("iv"),
                "signature": encryption_params.get("signature"),
                "needread": encryption_params.get("needread"),
                "is_encrypted": encryption_params.get("is_encrypted", False)
            })
        else:
            print(f"🔐 [异步日志] 无加密参数")
        
        print(f"📞 [异步日志] 调用api_service.log_api_call...")
        api_service.log_api_call(
            db=db,
            api_config=api_config,
            ip_address=ip_address,
            request_data=request_data,
            response_data=response_data,
            is_success=is_success,
            batch_id=batch_id,
            file_path=file_path,
            **encryption_kwargs
        )
        print(f"✅ [异步日志] api_service.log_api_call调用成功!")
        log_time = (time.time() - log_start_time) * 1000
        logger.debug(f"API日志记录完成 - api_code: {api_config.api_code}, log_time: {log_time:.2f}ms")
    except Exception as e:
        log_time = (time.time() - log_start_time) * 1000
        print(f"❌ [异步日志] API日志记录失败!")
        print(f"   API代码: {api_config.api_code if hasattr(api_config, 'api_code') else 'N/A'}")
        print(f"   耗时: {log_time:.2f}ms")
        print(f"   错误信息: {str(e)}")
        print(f"   错误类型: {type(e).__name__}")
        import traceback
        print(f"   错误堆栈: {traceback.format_exc()}")
        # 日志记录失败不应影响主业务流程，只记录错误
        logger.error(f"API日志记录失败 - api_code: {api_config.api_code}, log_time: {log_time:.2f}ms, error: {str(e)}")
    finally:
        # 如果创建了独立的数据库会话，需要关闭它
        if should_close_db and db:
            try:
                db.close()
            except Exception as close_error:
                logger.warning(f"关闭数据库会话失败: {close_error}")


# 注释掉这个路由，因为它会与批次管理路由冲突
# 自定义API应该通过 /api/custom/{api_code} 访问
# @api_router.api_route(
#     "/{api_code}",
#     methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
#     summary="动态自定义API",
#     tags=["自定义API"]
# )
# async def handle_custom_api_v1(
#     api_code: str,
#     request: Request,
#     db: Session = Depends(get_db)
# ):
#     """
#     处理自定义API请求（v1路径兼容）
#     
#     根据API代码动态处理不同的自定义API请求。
#     这个路由提供与 /api/custom/{api_code} 相同的功能，
#     但使用 /api/v1/{api_code} 路径以兼容前端测试。
#     
#     Args:
#         api_code: API代码
#         request: 请求对象
#         db: 数据库会话
#         
#     Returns:
#         API响应结果
#     """
#     return await _handle_custom_api_internal(
#         api_code=api_code,
#         request=request,
#         db=db,
#         batch_id_from_path=None
#     )





async def _validate_record_count(data, api_code: str, max_records: int):
    """
    验证批次记录数是否超过限制
    
    Args:
        data: 要验证的数据（list或dict）
        api_code: API代码，用于日志记录
        max_records: 最大记录数限制
        
    Raises:
        BusinessException: 当记录数超过限制时抛出
    """
    record_count = 0
    
    if isinstance(data, list):
        record_count = len(data)
    elif isinstance(data, dict) and 'data' in data and isinstance(data['data'], list):
        record_count = len(data['data'])
    else:
        return  # 不是批次数据，跳过验证
    
    if record_count > max_records:
        logger.warning(
            f"🚫 批次记录数过多被拒绝 - api_code: {api_code}, "
            f"记录数: {record_count}, 限制: {max_records}"
        )
        raise BusinessException(
            BusinessCode.REQUEST_TOO_LARGE,
            f"批次记录数过多，当前{record_count}条，最大允许{max_records}条"
        )


async def _validate_api_config(db: Session, api_code: str, request_method: str) -> CustomApi:
    """
    验证API配置（带Redis缓存优化）
    
    Args:
        db: 数据库会话
        api_code: API代码
        request_method: 请求方法
        
    Returns:
        CustomApi: API配置对象
        
    Raises:
        BusinessException: 当API不存在、已停用或方法不支持时抛出
    """
    # 使用缓存获取API配置
    api_config = get_api_config_with_cache(db, api_code)
    
    if not api_config:
        raise BusinessException(
            BusinessCode.API_NOT_FOUND,
            f"API '{api_code}' 不存在"
        )
    
    if not api_config.status:
        raise BusinessException(
            BusinessCode.API_DISABLED,
            f"API '{api_code}' 已停用"
        )
    
    if request_method != api_config.http_method:
        raise BusinessException(
            BusinessCode.API_METHOD_NOT_ALLOWED,
            f"API '{api_code}' 不支持 {request_method} 方法"
        )
    
    return api_config


async def _handle_authentication(request: Request, api_config: CustomApi, batch_id: str = None) -> Optional[int]:
    """
    处理认证逻辑
    
    Args:
        request: 请求对象
        api_config: API配置
        batch_id: 批次ID（可选）
        
    Returns:
        Optional[int]: 客户ID，如果不需要认证则返回None
        
    Raises:
        BusinessException: 认证失败时抛出
    """
    if not api_config.require_authentication:
        return None
    
    authorization = request.headers.get("Authorization")
    if not authorization:
        raise BusinessException(
            BusinessCode.TOKEN_MISSING,
            "缺少Authorization头"
        )
    
    if not authorization.startswith("Bearer "):
        raise BusinessException(
            BusinessCode.PARAM_ERROR,
            "无效的Authorization头格式"
        )
    
    token = authorization.split(" ")[1]
    try:
        payload = jwt_service.verify_token(token)
        customer_id = payload.get("customer_id")
        
        if not customer_id:
            raise BusinessException(
                BusinessCode.TOKEN_INVALID,
                "Token中缺少客户ID"
            )
        
        # 权限验证
        if api_config.customer_id != customer_id:
            raise BusinessException(
                BusinessCode.ACCESS_DENIED,
                "无权限访问此API"
            )
        
        return customer_id
        
    except BusinessException:
        raise
    except Exception as e:
        logger.warning(f"JWT验证失败: {str(e)}")
        raise BusinessException(
            BusinessCode.TOKEN_INVALID,
            "认证失败"
        )


async def _process_request_data(request: Request, api_code: str) -> tuple[dict, dict]:
    """
    处理请求数据和加密参数
    
    Args:
        request: 请求对象
        api_code: API代码
        
    Returns:
        tuple[dict, dict]: (请求数据, 加密参数)
        
    Raises:
        BusinessException: 数据处理失败时抛出
    """
    # 检测是否为加密请求
    is_encrypted_request = request.headers.get("X-Data-Encrypted") == "true"
    
    # 获取X-Data-Signature头部
    x_data_signature = request.headers.get("X-Data-Signature")
    
    # 初始化加密相关变量
    encryption_params = {
        "timestamp": None,
        "nonce": None,
        "encrypted_data": None,
        "iv": None,
        "signature": None,
        "x_data_signature": x_data_signature,
        "needread": None,
        "is_encrypted": is_encrypted_request
    }
    
    if request.method in WRITE_METHODS:
        try:
            request_data = await request.json()
            
            # 检查原始JSON大小
            import json
            json_size = len(json.dumps(request_data, ensure_ascii=False).encode('utf-8'))
            if json_size > settings.MAX_REQUEST_BODY_SIZE:
                logger.warning(
                    f"🚫 JSON数据过大被拒绝 - api_code: {api_code}, "
                    f"大小: {json_size // 1024 // 1024}MB, 限制: {settings.MAX_REQUEST_BODY_SIZE // 1024 // 1024}MB"
                )
                raise BusinessException(
                    BusinessCode.REQUEST_TOO_LARGE,
                    f"请求数据过大，当前{json_size // 1024 // 1024}MB，最大允许{settings.MAX_REQUEST_BODY_SIZE // 1024 // 1024}MB"
                )
            
            # 如果是加密请求，提取加密参数
            if is_encrypted_request and request_data:
                encryption_params.update({
                    "timestamp": request_data.get("timestamp"),
                    "nonce": request_data.get("nonce"),
                    "encrypted_data": request_data.get("data"),
                    "iv": request_data.get("iv"),
                    "signature": request_data.get("signature"),
                    "needread": request_data.get("needread", False)
                })
                
                # 检查加密数据大小
                encrypted_data = encryption_params.get("encrypted_data")
                if encrypted_data:
                    try:
                        import base64
                        decoded_size = len(base64.b64decode(encrypted_data))
                        if decoded_size > settings.MAX_ENCRYPTED_DATA_SIZE:
                            logger.warning(
                                f"🚫 加密数据过大被拒绝 - api_code: {api_code}, "
                                f"大小: {decoded_size // 1024 // 1024}MB, 限制: {settings.MAX_ENCRYPTED_DATA_SIZE // 1024 // 1024}MB"
                            )
                            raise BusinessException(
                                BusinessCode.REQUEST_TOO_LARGE,
                                f"加密数据过大，当前{decoded_size // 1024 // 1024}MB，最大允许{settings.MAX_ENCRYPTED_DATA_SIZE // 1024 // 1024}MB"
                            )
                    except Exception as decode_error:
                        logger.debug(f"Base64解码失败，将在后续验证中处理: {str(decode_error)}")
                
                # 记录加密请求信息
                logger.info(
                    f"检测到加密请求 - api_code: {api_code}, "
                    f"timestamp: {encryption_params['timestamp']}, "
                    f"nonce: {encryption_params['nonce'][:8] if encryption_params['nonce'] else None}..., "
                    f"needread: {encryption_params['needread']}, "
                    f"json_size: {json_size // 1024}KB"
                )
                
        except BusinessException:
            raise
        except Exception:
            request_data = {}
    else:
        request_data = dict(request.query_params)
    
    return request_data, encryption_params


async def _validate_and_decrypt_data(
    request_data: dict, 
    encryption_params: dict, 
    api_config: CustomApi, 
    customer_id: Optional[int],
    client_ip: str,
    api_code: str,
    db: Session
) -> dict:
    """
    验证和解密请求数据
    
    Args:
        request_data: 请求数据
        encryption_params: 加密参数
        api_config: API配置
        customer_id: 客户ID
        client_ip: 客户端IP
        api_code: API代码
        db: 数据库会话
        
    Returns:
        dict: 验证后的数据
        
    Raises:
        BusinessException: 验证或解密失败时抛出
    """
    is_encrypted_request = encryption_params.get("is_encrypted", False)
    
    if is_encrypted_request and encryption_params.get("encrypted_data"):
        try:
            # 获取数据密钥
            data_key = get_data_key(customer_id)
            if not data_key:
                raise BusinessException(
                    BusinessCode.DATA_KEY_NOT_FOUND,
                    "数据密钥不存在，请重新认证"
                )
            
            # 解密数据
            decrypted_data = decrypt_data(
                data_key, 
                encryption_params["encrypted_data"], 
                encryption_params["iv"]
            )
            
            # 验证批次记录数
            await _validate_record_count(decrypted_data, api_code, settings.MAX_BATCH_RECORDS)
            
            # 使用解密后的数据进行验证
            validated_data = api_field_service.validate_request_data(
                db, api_config.id, decrypted_data
            )
            
            logger.info(
                f"加密数据解密成功 - api_code: {api_code}, "
                f"原始数据类型: {type(decrypted_data)}, "
                f"数据长度: {len(decrypted_data) if isinstance(decrypted_data, (list, dict)) else 'N/A'}"
            )
            
            return validated_data
            
        except BusinessException:
            raise
        except Exception as e:
            logger.error(f"加密数据解密失败 - api_code: {api_code}, error: {str(e)}")
            raise BusinessException(
                BusinessCode.DATA_VALIDATION_FAILED,
                f"数据解密失败: {str(e)}"
            )
    else:
        # 非加密请求，检查是否为内网IP地址
        if not is_internal_ip(client_ip):
            logger.warning(
                f"非加密请求来自非内网IP - api_code: {api_code}, "
                f"client_ip: {client_ip}"
            )
            raise BusinessException(
                BusinessCode.ACCESS_DENIED,
                "非加密请求只允许来自内网地址（192.**或10.**）"
            )
        
        # 验证批次记录数（非加密请求）
        await _validate_record_count(request_data, api_code, settings.MAX_BATCH_RECORDS)
        
        # 非加密请求，直接验证原始数据
        validated_data = api_field_service.validate_request_data(
            db, api_config.id, request_data
        )
        
        return validated_data


async def _handle_custom_api_internal(
    api_code: str,
    request: Request,
    db: Session,
    batch_id_from_path: str = None
):
    """
    内部函数：处理自定义API请求的核心逻辑（重构优化版本）
    
    Args:
        api_code: API代码
        request: 请求对象
        db: 数据库会话
        batch_id_from_path: 从URL路径中获取的batch_id（可选）
        
    Returns:
        API响应结果
    """
    start_time = time.time()
    client_ip = request.client.host if request.client else None
    api_config = None
    request_data = {}
    customer_id = None
    result = None
    exception_occurred = None
    is_success = False
    encryption_params = {}
    # 性能计时器
    timings = {}
    
    try:
        # 1. 验证API配置
        step_start = time.time()
        api_config = await _validate_api_config(db, api_code, request.method)
        api_config_time = (time.time() - step_start) * 1000
        timings['api_config_query'] = api_config_time
        print(f"*** API配置验证耗时: {api_config_time:.2f}ms ***")
        
        # 2. 处理请求数据
        step_start = time.time()
        request_data, encryption_params = await _process_request_data(request, api_code)
        request_parsing_time = (time.time() - step_start) * 1000
        timings['request_data_parsing'] = request_parsing_time
        print(f"*** 请求数据处理耗时: {request_parsing_time:.2f}ms ***")
        
        # 3. 获取batch_id（修复：在获取请求数据后再提取）
        batch_id = batch_id_from_path or request_data.get("batch_id")
        
        # 4. 认证处理
        step_start = time.time()
        customer_id = await _handle_authentication(request, api_config, batch_id)
        auth_time = (time.time() - step_start) * 1000
        timings['authentication'] = auth_time
        print(f"*** 认证处理耗时: {auth_time:.2f}ms ***")
        
        # 4.5. 验证签名（如果提供）
        step_start = time.time()
        x_data_signature = encryption_params.get("x_data_signature")
        request_signature = request_data.get("signature") if isinstance(request_data, dict) else None
        
        if request_signature or x_data_signature:
            from .endpoints.data import verify_signature, get_data_key
            signature = request_signature or x_data_signature
            
            # 获取数据密钥
            data_key = get_data_key(customer_id)
            if not data_key:
                raise BusinessException(
                    BusinessCode.DATA_KEY_NOT_FOUND,
                    "数据密钥不存在，请重新认证"
                )
            
            # 获取要验证的数据
            data_to_verify = encryption_params.get("encrypted_data") or str(request_data)
            print("x_data_signature.encryption_params", encryption_params)
            print("request_data.signature:", request_signature)
            print("request_data.data:", data_to_verify)
            print("$"*60)
            
            if not verify_signature(data_key, data_to_verify, signature):
                signature_time = (time.time() - step_start) * 1000
                timings['signature_verification'] = signature_time
                print(f"*** 签名验证耗时: {signature_time:.2f}ms ***")
                raise BusinessException(
                    BusinessCode.DATA_VALIDATION_FAILED,
                    "数据签名验证失败"
                )
        
        signature_time = (time.time() - step_start) * 1000
        timings['signature_verification'] = signature_time
        print(f"*** 签名验证耗时: {signature_time:.2f}ms ***")
        
        # 5. 数据验证和解密
        step_start = time.time()
        validated_data = await _validate_and_decrypt_data(
             request_data, encryption_params, api_config, customer_id,
             client_ip, api_code, db
         )
        validation_time = (time.time() - step_start) * 1000
        timings['data_validation'] = validation_time
        print(f"*** 数据验证和解密耗时: {validation_time:.2f}ms ***")
        
        # 6. 处理API逻辑
        step_start = time.time()
        api_result = api_field_service.process_custom_api(
            db, api_config, validated_data, customer_id, batch_id
        )
        api_processing_time = (time.time() - step_start) * 1000
        timings['api_processing'] = api_processing_time
        print(f"*** API逻辑处理耗时: {api_processing_time:.2f}ms ***")
        
        # 6.5. 提取文件路径信息（如果有的话）
        file_path = None
        if api_result and isinstance(api_result, dict):
            # 从API处理结果中提取文件路径
            database_record = api_result.get('database_record', {})
            if isinstance(database_record, dict):
                file_path = database_record.get('storage_path')
            # 如果没有从database_record中获取到，尝试从其他字段获取
            if not file_path and api_result.get('object_path'):
                bucket_name = api_result.get('bucket_name', 'cepiec-read-data')
                object_path = api_result.get('object_path')
                file_path = f"/{bucket_name}/{object_path}"
        
        # 7. 构建响应
        step_start = time.time()
        response_data = {
            "code": BusinessCode.SUCCESS.value,
            "message": "处理成功",
            "total_count": api_result["total_count"],
            "batch_id": batch_id,
            "timestamp": int(time.time() * 1000)
        }
        response_building_time = (time.time() - step_start) * 1000
        timings['response_building'] = response_building_time
        print(f"*** 响应构建耗时: {response_building_time:.2f}ms ***")
        
        # 标记成功
        is_success = True
        result = response_data
        
        # 计算总处理时间
        total_time = (time.time() - start_time) * 1000
        timings['total'] = total_time
        
        # 记录详细的性能日志
        logger.info(
            f"API调用完成 - api_code: {api_code}, customer_id: {customer_id}, "
            f"total_time: {total_time:.2f}ms, "
            f"timings: {timings}"
        )
        
        # 如果总时间超过阈值，记录警告
        if total_time > 1000:  # 超过1秒
            logger.warning(
                f"API响应缓慢 - api_code: {api_code}, total_time: {total_time:.2f}ms, "
                f"详细计时: {timings}"
            )
        
        return response_data
        
    except ValidationException as e:
        exception_occurred = e
        total_time = (time.time() - start_time) * 1000
        timings['total'] = total_time
        logger.warning(
            f"API验证失败 - api_code: {api_code}, total_time: {total_time:.2f}ms, "
            f"timings: {timings}, error: {str(e)}"
        )
        raise BusinessException(
            BusinessCode.PARAM_ERROR,
            str(e)
        )
    
    except BusinessException as business_exc:
        exception_occurred = business_exc
        total_time = (time.time() - start_time) * 1000
        timings['total'] = total_time
        logger.info(
            f"API业务异常 - api_code: {api_code}, code: {business_exc.business_code.code}, "
            f"total_time: {total_time:.2f}ms, timings: {timings}"
        )
        raise
    
    except Exception as e:
        exception_occurred = e
        total_time = (time.time() - start_time) * 1000
        timings['total'] = total_time
        
        # 如果是自定义异常，直接抛出
        if isinstance(e, CustomException):
            logger.error(
                f"API自定义异常 - api_code: {api_code}, total_time: {total_time:.2f}ms, "
                f"timings: {timings}, error: {str(e)}"
            )
            raise e
        
        # 其他异常抛出为500错误
        logger.error(
            f"API系统错误 - api_code: {api_code}, total_time: {total_time:.2f}ms, "
            f"timings: {timings}, error: {str(e)}", exc_info=True
        )
        raise BusinessException(
            BusinessCode.INTERNAL_ERROR,
            "服务器内部错误"
        )
    
    finally:
        # 统一处理API调用日志记录（优化：避免重复代码）
        if api_config:
            try:
                # 准备响应数据
                if is_success:
                    response_data = result
                elif exception_occurred:
                    response_data = {"error": str(exception_occurred)}
                else:
                    response_data = {"error": "未知错误"}
                
                # 获取batch_id（确保在finally块中可用）
                batch_id = batch_id_from_path or request_data.get("batch_id") if request_data else None
                
                # 异步记录API调用日志，避免阻塞接口响应
                # 注意：不传递db会话，让异步任务创建独立的数据库连接
                asyncio.create_task(
                    _log_api_call_async(
                        api_service=api_service,
                        db=None,  # 传递None，让异步函数创建独立的数据库会话
                        api_config=api_config,
                        ip_address=client_ip,
                        request_data=request_data,
                        response_data=response_data,
                        is_success=is_success,
                        batch_id=batch_id,
                        encryption_params=encryption_params if encryption_params else {},
                        file_path=file_path  # 传递文件路径信息
                    )
                )
            except Exception as log_error:
                # 日志记录失败不应影响API响应
                logger.warning(f"API调用日志记录失败: {log_error}")