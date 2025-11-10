#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pydantic Schemas包初始化文件

导入并导出所有schemas模块，用于API数据验证和序列化。

Author: System
Date: 2024
"""

# 基础schemas
from .base import (
    BaseResponse,
    SuccessResponse,
    ErrorResponse,
    ValidationErrorResponse,
    PaginationInfo,
    PaginatedResponse,
    IdResponse,
    StatusResponse,
    HealthCheckResponse,
    BaseCreateSchema,
    BaseUpdateSchema,
    BaseQuerySchema,
    DateRangeSchema,
    FileUploadResponse,
    BulkOperationRequest,
    BulkOperationResponse
)

# 平台管理schemas
from .customer import (
    CustomerBase,
    CustomerCreate,
    CustomerUpdate,
    CustomerResponse,
    CustomerDetailResponse,
    CustomerQuery,
    CustomerLoginRequest,
    CustomerLoginResponse,
    CustomerSessionResponse,
    CustomerStatsResponse,
    CustomerSecretResetRequest,
    CustomerSecretResetResponse,
    CustomerBatchUpdateRequest
)

# API定义schemas
from .api import (
    HttpMethodEnum,
    ResponseFormatEnum,
    FieldTypeEnum,
    CustomApiBase,
    CustomApiCreate,
    CustomApiUpdate,
    CustomApiResponse,
    CustomApiDetailResponse,
    ApiQuery,
    ApiFieldBase,
    ApiFieldCreate,
    ApiFieldUpdate,
    ApiFieldResponse,
    ApiDataSubmission,
    ApiDataResponse,
    ApiStatsResponse,
    ApiBatchOperationRequest
)

# 日志记录schemas
from .log import (
    UploadStatusEnum,
    ApiUsageLogResponse,
    ApiUsageLogDetailResponse,
    DataUploadResponse,
    DataUploadDetailResponse,
    UsageLogQuery,
    DataUploadQuery,
    UsageStatsResponse,
    UploadStatsResponse,
    DailyStatsResponse,
    HourlyStatsResponse,
    TopApiStatsResponse,
    ErrorAnalysisResponse,
    PerformanceAnalysisResponse,
    LogExportRequest,
    LogExportResponse
)

# 系统管理schemas
from .admin import (
    AdminRoleEnum,
    AdminStatusEnum,
    ConfigTypeEnum,
    AdminUserBase,
    AdminUserCreate,
    AdminUserUpdate,
    AdminUserResponse,
    AdminUserDetailResponse,
    AdminUserQuery,
    AdminLoginRequest,
    AdminLoginResponse,
    PasswordChangeRequest,
    PasswordResetRequest,
    SystemConfigBase,
    SystemConfigCreate,
    SystemConfigUpdate,
    SystemConfigResponse,
    SystemConfigQuery,
    ConfigBatchUpdateRequest,
    SystemStatsResponse,
    SystemHealthResponse,
    AuditLogResponse
)

# 导出所有schemas
__all__ = [
    # 基础schemas
    "BaseResponse",
    "SuccessResponse", 
    "ErrorResponse",
    "ValidationErrorResponse",
    "PaginationInfo",
    "PaginatedResponse",
    "IdResponse",
    "StatusResponse",
    "HealthCheckResponse",
    "BaseCreateSchema",
    "BaseUpdateSchema",
    "BaseQuerySchema",
    "DateRangeSchema",
    "FileUploadResponse",
    "BulkOperationRequest",
    "BulkOperationResponse",
    
    # 平台管理schemas
    "CustomerBase",
    "CustomerCreate",
    "CustomerUpdate",
    "CustomerResponse",
    "CustomerDetailResponse",
    "CustomerQuery",
    "CustomerLoginRequest",
    "CustomerLoginResponse",
    "CustomerSessionResponse",
    "CustomerStatsResponse",
    "CustomerSecretResetRequest",
    "CustomerSecretResetResponse",
    "CustomerBatchUpdateRequest",
    
    # API定义schemas
    "HttpMethodEnum",
    "ResponseFormatEnum",
    "FieldTypeEnum",
    "CustomApiBase",
    "CustomApiCreate",
    "CustomApiUpdate",
    "CustomApiResponse",
    "CustomApiDetailResponse",
    "ApiQuery",
    "ApiFieldBase",
    "ApiFieldCreate",
    "ApiFieldUpdate",
    "ApiFieldResponse",
    "ApiDataSubmission",
    "ApiDataResponse",
    "ApiStatsResponse",
    "ApiBatchOperationRequest",
    
    # 日志记录schemas
    "UploadStatusEnum",
    "ApiUsageLogResponse",
    "ApiUsageLogDetailResponse",
    "DataUploadResponse",
    "DataUploadDetailResponse",
    "UsageLogQuery",
    "DataUploadQuery",
    "UsageStatsResponse",
    "UploadStatsResponse",
    "DailyStatsResponse",
    "HourlyStatsResponse",
    "TopApiStatsResponse",
    "ErrorAnalysisResponse",
    "PerformanceAnalysisResponse",
    "LogExportRequest",
    "LogExportResponse",
    
    # 系统管理schemas
    "AdminRoleEnum",
    "AdminStatusEnum",
    "ConfigTypeEnum",
    "AdminUserBase",
    "AdminUserCreate",
    "AdminUserUpdate",
    "AdminUserResponse",
    "AdminUserDetailResponse",
    "AdminUserQuery",
    "AdminLoginRequest",
    "AdminLoginResponse",
    "PasswordChangeRequest",
    "PasswordResetRequest",
    "SystemConfigBase",
    "SystemConfigCreate",
    "SystemConfigUpdate",
    "SystemConfigResponse",
    "SystemConfigQuery",
    "ConfigBatchUpdateRequest",
    "SystemStatsResponse",
    "SystemHealthResponse",
    "AuditLogResponse",
]