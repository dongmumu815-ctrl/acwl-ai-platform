#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自定义异常模块

定义应用中使用的各种自定义异常类。
提供统一的异常处理和错误码管理。

Author: System
Date: 2024
"""

from typing import Any, Dict, Optional
from fastapi import HTTPException, status


class CustomException(Exception):
    """
    自定义异常基类
    
    所有业务异常的基类，提供统一的异常处理接口。
    按照API文档规范，返回数字错误码。
    """
    
    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_code: Optional[int] = None,  # 改为可选的数字类型
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        # 如果没有提供error_code，则使用HTTP状态码作为错误码
        self.error_code = error_code if error_code is not None else status_code
        self.details = details or {}
        super().__init__(self.message)


class ValidationException(CustomException):
    """
    数据验证异常
    
    用于数据验证失败的情况
    """
    
    def __init__(self, message: str, field: str = None, details: Dict[str, Any] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            # 移除字符串错误码，使用默认的数字错误码
            details=details or {}
        )
        if field:
            self.details["field"] = field


class AuthenticationException(CustomException):
    """
    认证异常
    
    用于用户认证失败的情况
    """
    
    def __init__(self, message: str = "认证失败", details: Dict[str, Any] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            # 移除字符串错误码，使用默认的数字错误码
            details=details or {}
        )


class AuthorizationException(CustomException):
    """
    授权异常
    
    用于用户权限不足的情况
    """
    
    def __init__(self, message: str = "权限不足", details: Dict[str, Any] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            # 移除字符串错误码，使用默认的数字错误码
            details=details or {}
        )


class NotFoundException(CustomException):
    """
    资源未找到异常
    
    用于请求的资源不存在的情况
    """
    
    def __init__(self, message: str = "资源未找到", resource_type: str = None, resource_id: str = None):
        details = {}
        if resource_type:
            details["resource_type"] = resource_type
        if resource_id:
            details["resource_id"] = resource_id
        
        super().__init__(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            # 移除字符串错误码，使用默认的数字错误码
            details=details
        )


class ConflictException(CustomException):
    """
    资源冲突异常
    
    用于资源已存在或状态冲突的情况
    """
    
    def __init__(self, message: str = "资源冲突", details: Dict[str, Any] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_409_CONFLICT,
            # 移除字符串错误码，使用默认的数字错误码
            details=details or {}
        )


class BusinessException(CustomException):
    """
    业务逻辑异常
    
    用于业务规则违反的情况
    """
    
    def __init__(self, message: str, error_code: Optional[int] = None, details: Dict[str, Any] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code=error_code,  # 现在接受数字错误码或None
            details=details or {}
        )


class DatabaseException(CustomException):
    """
    数据库操作异常
    
    用于数据库操作失败的情况
    """
    
    def __init__(self, message: str = "数据库操作失败", details: Dict[str, Any] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            # 移除字符串错误码，使用默认的数字错误码
            details=details or {}
        )


class ExternalServiceException(CustomException):
    """
    外部服务异常
    
    用于调用外部服务失败的情况
    """
    
    def __init__(self, message: str = "外部服务调用失败", service_name: str = None, details: Dict[str, Any] = None):
        exception_details = details or {}
        if service_name:
            exception_details["service_name"] = service_name
        
        super().__init__(
            message=message,
            status_code=status.HTTP_502_BAD_GATEWAY,
            # 移除字符串错误码，使用默认的数字错误码
            details=exception_details
        )


class RateLimitException(CustomException):
    """
    频率限制异常
    
    用于请求频率超过限制的情况
    """
    
    def __init__(self, message: str = "请求频率超过限制", retry_after: int = None, details: Dict[str, Any] = None):
        exception_details = details or {}
        if retry_after:
            exception_details["retry_after"] = retry_after
        
        super().__init__(
            message=message,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            # 移除字符串错误码，使用默认的数字错误码
            details=exception_details
        )


class FileUploadException(CustomException):
    """
    文件上传异常
    
    用于文件上传失败的情况
    """
    
    def __init__(self, message: str = "文件上传失败", filename: str = None, details: Dict[str, Any] = None):
        exception_details = details or {}
        if filename:
            exception_details["filename"] = filename
        
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            # 移除字符串错误码，使用默认的数字错误码
            details=exception_details
        )


class ConfigurationException(CustomException):
    """
    配置异常
    
    用于系统配置错误的情况
    """
    
    def __init__(self, message: str = "系统配置错误", config_key: str = None, details: Dict[str, Any] = None):
        exception_details = details or {}
        if config_key:
            exception_details["config_key"] = config_key
        
        super().__init__(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            # 移除字符串错误码，使用默认的数字错误码
            details=exception_details
        )


# 特定业务异常类

class CustomerException(BusinessException):
    """
    客户相关异常
    """
    pass


class CustomerNotFound(NotFoundException):
    """
    客户未找到异常
    """
    
    def __init__(self, customer_id: str = None):
        super().__init__(
            message="客户不存在",
            resource_type="customer",
            resource_id=customer_id
        )


class CustomerAlreadyExists(ConflictException):
    """
    客户已存在异常
    """
    
    def __init__(self, identifier: str = None):
        details = {}
        if identifier:
            details["identifier"] = identifier
        
        super().__init__(
            message="客户已存在",
            details=details
        )


class ApiException(BusinessException):
    """
    API相关异常
    """
    pass


class ApiNotFound(NotFoundException):
    """
    API未找到异常
    """
    
    def __init__(self, api_id: str = None, api_code: str = None):
        details = {}
        if api_code:
            details["api_code"] = api_code
        
        super().__init__(
            message="API接口不存在",
            resource_type="api",
            resource_id=api_id
        )
        self.details.update(details)


class ApiDisabled(BusinessException):
    """
    API已禁用异常
    """
    
    def __init__(self, api_code: str = None):
        details = {}
        if api_code:
            details["api_code"] = api_code
        
        super().__init__(
            message="API接口已禁用",
            # 移除字符串错误码，使用默认的数字错误码
            details=details
        )


class InvalidApiData(ValidationException):
    """
    API数据无效异常
    """
    
    def __init__(self, message: str, field: str = None, validation_errors: list = None):
        details = {}
        if validation_errors:
            details["validation_errors"] = validation_errors
        
        super().__init__(
            message=message,
            field=field,
            details=details
        )


class SessionException(AuthenticationException):
    """
    会话相关异常
    """
    pass


class SessionExpired(SessionException):
    """
    会话过期异常
    """
    
    def __init__(self):
        super().__init__(message="会话已过期，请重新登录")


class InvalidSession(SessionException):
    """
    无效会话异常
    """
    
    def __init__(self):
        super().__init__(message="无效的会话令牌")


# 异常工厂函数

def create_validation_error(field: str, message: str, value: Any = None) -> ValidationException:
    """
    创建验证错误异常
    
    Args:
        field: 字段名
        message: 错误消息
        value: 字段值
    
    Returns:
        ValidationException: 验证异常实例
    """
    details = {"field": field}
    if value is not None:
        details["value"] = str(value)
    
    return ValidationException(
        message=f"{field}: {message}",
        field=field,
        details=details
    )


def create_not_found_error(resource_type: str, identifier: str) -> NotFoundException:
    """
    创建资源未找到异常
    
    Args:
        resource_type: 资源类型
        identifier: 资源标识符
    
    Returns:
        NotFoundException: 未找到异常实例
    """
    return NotFoundException(
        message=f"{resource_type}不存在",
        resource_type=resource_type,
        resource_id=identifier
    )


def create_conflict_error(resource_type: str, identifier: str) -> ConflictException:
    """
    创建资源冲突异常
    
    Args:
        resource_type: 资源类型
        identifier: 资源标识符
    
    Returns:
        ConflictException: 冲突异常实例
    """
    return ConflictException(
        message=f"{resource_type}已存在",
        details={
            "resource_type": resource_type,
            "identifier": identifier
        }
    )


if __name__ == "__main__":
    # 测试异常类
    try:
        raise CustomerNotFound("123")
    except CustomerNotFound as e:
        print(f"异常消息: {e.message}")
        print(f"状态码: {e.status_code}")
        print(f"错误码: {e.error_code}")
        print(f"详情: {e.details}")
    
    try:
        raise InvalidApiData("数据格式错误", "email", ["邮箱格式不正确"])
    except InvalidApiData as e:
        print(f"\n验证异常: {e.message}")
        print(f"详情: {e.details}")
    
    print("\n异常类测试完成")