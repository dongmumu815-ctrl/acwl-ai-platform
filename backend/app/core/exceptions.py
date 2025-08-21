#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自定义异常类
"""

from typing import Optional, Any, Dict


class ACWLException(Exception):
    """ACWL平台基础异常类"""
    
    def __init__(
        self,
        message: str,
        status_code: int = 500,
        error_code: str = "INTERNAL_ERROR",
        detail: Optional[Any] = None
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.detail = detail
        super().__init__(self.message)


class ValidationError(ACWLException):
    """验证错误"""
    
    def __init__(self, message: str, detail: Optional[Any] = None):
        super().__init__(
            message=message,
            status_code=400,
            error_code="VALIDATION_ERROR",
            detail=detail
        )


class AuthenticationError(ACWLException):
    """认证错误"""
    
    def __init__(self, message: str = "认证失败", detail: Optional[Any] = None):
        super().__init__(
            message=message,
            status_code=401,
            error_code="AUTHENTICATION_ERROR",
            detail=detail
        )


class AuthorizationError(ACWLException):
    """授权错误"""
    
    def __init__(self, message: str = "权限不足", detail: Optional[Any] = None):
        super().__init__(
            message=message,
            status_code=403,
            error_code="AUTHORIZATION_ERROR",
            detail=detail
        )


class PermissionError(ACWLException):
    """权限错误"""
    
    def __init__(self, message: str = "权限不足", detail: Optional[Any] = None):
        super().__init__(
            message=message,
            status_code=403,
            error_code="PERMISSION_ERROR",
            detail=detail
        )


class NotFoundError(ACWLException):
    """资源未找到错误"""
    
    def __init__(self, message: str = "资源未找到", detail: Optional[Any] = None):
        super().__init__(
            message=message,
            status_code=404,
            error_code="NOT_FOUND_ERROR",
            detail=detail
        )


class ConflictError(ACWLException):
    """冲突错误"""
    
    def __init__(self, message: str = "资源冲突", detail: Optional[Any] = None):
        super().__init__(
            message=message,
            status_code=409,
            error_code="CONFLICT_ERROR",
            detail=detail
        )


class BusinessError(ACWLException):
    """业务逻辑错误"""
    
    def __init__(self, message: str, detail: Optional[Any] = None):
        super().__init__(
            message=message,
            status_code=422,
            error_code="BUSINESS_ERROR",
            detail=detail
        )


class ExternalServiceError(ACWLException):
    """外部服务错误"""
    
    def __init__(self, message: str = "外部服务错误", detail: Optional[Any] = None):
        super().__init__(
            message=message,
            status_code=502,
            error_code="EXTERNAL_SERVICE_ERROR",
            detail=detail
        )


class ResourceLimitError(ACWLException):
    """资源限制错误"""
    
    def __init__(self, message: str = "资源不足", detail: Optional[Any] = None):
        super().__init__(
            message=message,
            status_code=507,
            error_code="RESOURCE_LIMIT_ERROR",
            detail=detail
        )


class ModelError(ACWLException):
    """模型相关错误"""
    
    def __init__(self, message: str, detail: Optional[Any] = None):
        super().__init__(
            message=message,
            status_code=422,
            error_code="MODEL_ERROR",
            detail=detail
        )


class DeploymentError(ACWLException):
    """部署相关错误"""
    
    def __init__(self, message: str, detail: Optional[Any] = None):
        super().__init__(
            message=message,
            status_code=422,
            error_code="DEPLOYMENT_ERROR",
            detail=detail
        )


class GPUError(ACWLException):
    """GPU相关错误"""
    
    def __init__(self, message: str, detail: Optional[Any] = None):
        super().__init__(
            message=message,
            status_code=422,
            error_code="GPU_ERROR",
            detail=detail
        )


class DatasetError(ACWLException):
    """数据集相关错误"""
    
    def __init__(self, message: str, detail: Optional[Any] = None):
        super().__init__(
            message=message,
            status_code=422,
            error_code="DATASET_ERROR",
            detail=detail
        )


class FineTuningError(ACWLException):
    """微调相关错误"""
    
    def __init__(self, message: str, detail: Optional[Any] = None):
        super().__init__(
            message=message,
            status_code=422,
            error_code="FINE_TUNING_ERROR",
            detail=detail
        )