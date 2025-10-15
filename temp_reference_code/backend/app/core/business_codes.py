#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
业务状态码定义

统一的业务状态码，用于替代HTTP状态码作为业务错误标识

Author: System
Date: 2024
"""

from enum import Enum
from typing import Dict, Any


class BusinessCode(Enum):
    """业务状态码枚举"""
    
    # 成功状态
    SUCCESS = (0, "success")
    
    # 认证相关错误 (1000-1999)
    PARAM_ERROR = (1001, "参数缺失或格式错误")
    SIGNATURE_FAILED = (1002, "签名验证失败")
    TIMESTAMP_OUT_OF_WINDOW = (1003, "请求时间戳不在允许窗口")
    NONCE_REPLAY_ATTACK = (1004, "请求已被重放（nonce已使用）")
    APPID_INVALID = (1005, "appid无效或未授权")
    TOKEN_INVALID = (1006, "Token无效或已过期")
    TOKEN_MISSING = (1007, "缺少认证令牌")
    ACCESS_DENIED = (1008, "访问权限不足")
    CUSTOMER_DISABLED = (1009, "客户账户已停用")
    
    # 数据相关错误 (2000-2999)
    DATA_DECRYPT_FAILED = (2001, "数据解密失败")
    DATA_SIGNATURE_MISMATCH = (2002, "数据签名不匹配")
    DATA_VALIDATION_FAILED = (2003, "数据验证失败")
    DATA_PARSING_FAILED = (2004, "数据解析失败")
    DATA_KEY_NOT_FOUND = (2005, "数据密钥不存在")
    
    # 批次相关错误 (3000-3999)
    BATCH_NOT_FOUND = (3001, "批次不存在")
    BATCH_ALREADY_COMPLETED = (3002, "批次已完成")
    BATCH_STATUS_INVALID = (3003, "批次状态无效")
    BATCH_NO_PENDING_DATA = (3004, "批次中没有待处理的数据")
    BATCH_PROCESSING_FAILED = (3005, "批次处理失败")
    BATCH_ACCESS_DENIED = (3006, "批次访问权限不足")
    BATCH_ALREADY_EXISTS = (3007, "批次已存在")
    DATA_NOT_FOUND = (3008, "数据不存在")
    DATA_IS_PENDING = (3009, "数据已在处理中")
    
    # API相关错误 (4000-4999)
    API_NOT_FOUND = (4001, "API不存在")
    API_DISABLED = (4002, "API已停用")
    API_METHOD_NOT_ALLOWED = (4003, "HTTP方法不允许")
    API_ACCESS_DENIED = (4004, "API访问权限不足")
    API_CODE_INVALID = (4005, "API代码无效")
    
    # 系统错误 (5000-5999)
    INTERNAL_ERROR = (5000, "内部服务器错误")
    DATABASE_ERROR = (5001, "数据库错误")
    REDIS_ERROR = (5002, "缓存服务错误")
    REQUEST_TOO_LARGE = (5003, "请求数据过大")
    
    def __init__(self, code: int, message: str):
        self.code = code
        self.message = message


class BusinessResponse:
    """统一业务响应类"""
    
    @staticmethod
    def success(data: Any = None, message: str = None) -> Dict[str, Any]:
        """成功响应"""
        return {
            "code": BusinessCode.SUCCESS.code,
            "message": message if message else BusinessCode.SUCCESS.message,
            "data": data
        }
    
    @staticmethod
    def error(business_code: BusinessCode, detail: str = None) -> Dict[str, Any]:
        """错误响应"""
        message = detail if detail else business_code.message
        return {
            "code": business_code.code,
            "message": message,
            "data": None
        }
    
    @staticmethod
    def custom_error(code: int, message: str) -> Dict[str, Any]:
        """自定义错误响应"""
        return {
            "code": code,
            "message": message,
            "data": None
        }


class BusinessException(Exception):
    """业务异常类"""
    
    def __init__(self, business_code: BusinessCode, detail: str = None):
        self.business_code = business_code
        self.detail = detail
        super().__init__(detail or business_code.message)