#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
管理后台接口

提供系统管理功能，包括：
1. 管理员登录认证
2. 平台管理
3. API管理
4. 系统配置
5. 统计信息
6. 日志查询

Author: System
Date: 2024
"""

from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import ValidationException, NotFoundException
from app.core.business_codes import BusinessException, BusinessCode, BusinessResponse
from app.services.admin import AdminUserService, SystemConfigService, SystemStatsService
from app.services.customer import CustomerService
from app.services.api import custom_api_service, ApiFieldService
from app.services.log import LogService
from app.services.auth import get_current_admin_user, JWTService
from app.services.external_data import DataLink
from app.models.admin import AdminUser
from app.models.customer import Customer
from app.models.api import CustomApi
from app.schemas.admin import (
    AdminLoginRequest,
    AdminLoginResponse,
    AdminUserCreate,
    AdminUserUpdate,
    AdminUserResponse,
    AdminUserDetailResponse,
    AdminUserQuery,
    PasswordChangeRequest,
    SystemConfigCreate,
    SystemConfigUpdate,
    SystemConfigResponse,
    SystemConfigQuery,
    SystemStatsResponse
)
from app.schemas.customer import (
    CustomerResponse,
    CustomerDetailResponse,
    CustomerQuery,
    CustomerCreate,
    CustomerUpdate
)
from app.schemas.api import (
    CustomApiResponse,
    CustomApiDetailResponse,
    ApiQuery,
    CustomApiCreate,
    CustomApiUpdate,
    CustomApiCopy,
    ApiFieldCreate,
    ApiFieldUpdate,
    ApiFieldResponse,
    ApiFieldBatchUpdateRequest
)
from app.schemas.base import (
    BaseResponse,
    SuccessResponse,
    PaginatedResponse,
    PaginationInfo,
    IdResponse
)
from app.schemas.log import ApiUsageLogResponse

router = APIRouter()

# 服务实例
admin_service = AdminUserService()
config_service = SystemConfigService()
stats_service = SystemStatsService()
customer_service = CustomerService()
api_service = custom_api_service
api_field_service = ApiFieldService()
log_service = LogService()


# ==================== 认证相关 ====================

@router.post("/login", response_model=AdminLoginResponse, summary="管理员登录")
async def admin_login(
    login_data: AdminLoginRequest,
    db: Session = Depends(get_db)
):
    """
    管理员登录接口
    
    Args:
        login_data: 登录信息
        db: 数据库会话
        
    Returns:
        登录响应，包含访问令牌和管理员信息
    """
    try:
        result = admin_service.login_admin(db, login_data)
        
        # 构造正确的登录响应
        admin = result["admin"]
        
        # 创建用户信息响应
        user_info = AdminUserResponse.model_validate(admin)
        
        return AdminLoginResponse(
            access_token=result["access_token"],
            refresh_token=result["refresh_token"],
            token_type=result["token_type"],
            expires_in=result["expires_in"],
            user_info=user_info,
            permissions=admin.permissions or [],
            session_id=f"session_{admin.id}_{int(datetime.utcnow().timestamp())}"
        )
    except ValidationException as e:
        raise HTTPException(
            status_code=400,
            detail=f"登录验证失败: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"登录过程中发生错误: {str(e)}"
        )


def _generate_complete_api_documentation(db: Session, api: CustomApi, format: str = "markdown") -> str:
    """
    生成完整的API服务文档
    
    包含认证、数据上传、批次完成和结果查询四个核心接口的文档
    
    Args:
        db: 数据库会话
        api: API对象（用于获取平台信息）
        format: 文档格式（markdown/html/json）
        
    Returns:
        完整的API服务文档内容
    """
    if format == "markdown":
        return _generate_complete_markdown_documentation(api)
    # elif format == "html":
    #     return _generate_complete_html_documentation(api)
    elif format == "json":
        return _generate_complete_json_documentation(api)
    else:
        raise ValueError(f"不支持的文档格式: {format}")


def _generate_complete_markdown_documentation(api: CustomApi) -> str:
    """
    生成完整的Markdown格式API服务文档
    
    Args:
        api: API对象
        
    Returns:
        Markdown文档内容
    """
    doc = []
    
    # 文档标题
    doc.append(f"# 📋 {api.customer.name if api.customer else '客户'}数据采集API服务文档")
    doc.append("")
    doc.append("本文档描述了完整的数据采集API服务，包含认证、数据上传、批次管理和结果查询四个核心功能。")
    doc.append("")
    
    # 目录
    doc.append("## 📑 目录")
    doc.append("")
    doc.append("- [🔐 1. 认证接口](#1-认证接口)")
    doc.append("- [📤 2. 数据上传接口](#2-数据上传接口)")
    doc.append("- [✅ 3. 批次完成接口](#3-批次完成接口)")
    doc.append("- [📥 4. 结果查询接口](#4-结果查询接口)")
    doc.append("- [🔄 5. 完整调用流程](#5-完整调用流程)")
    doc.append("- [📋 6. 业务状态码说明](#6-业务状态码说明)")
    doc.append("- [⚠️ 7. 注意事项](#7-注意事项)")
    doc.append("")
    
    # 1. 认证接口
    doc.append("## 🔐 1. 认证接口")
    doc.append("")
    doc.append("### 接口信息")
    doc.append("- **接口地址**: `/api/v1/auth/token`")
    doc.append("- **请求方法**: `POST`")
    doc.append("- **功能说明**: 获取访问令牌和数据加密密钥")
    doc.append("- **认证方式**: 签名认证")
    doc.append("")
    
    doc.append("### 请求参数")
    doc.append("")
    doc.append("| 字段名 | 类型 | 必填 | 描述 |")
    doc.append("|--------|------|------|------|")
    doc.append("| appid | String | 是 | 应用唯一标识 |")
    doc.append("| timestamp | Long | 是 | 当前时间戳（秒） |")
    doc.append("| nonce | String | 是 | 随机字符串（8-16位） |")
    doc.append("| signature | String | 是 | HMAC-SHA256签名 |")
    doc.append("")
    
    doc.append("### 签名生成规则")
    doc.append("")
    doc.append("```")
    doc.append("signature_data = appid + timestamp + nonce")
    doc.append("signature = HMAC_SHA256(secret, signature_data).hexdigest().upper()")
    doc.append("```")
    doc.append("")
    
    doc.append("### 请求示例")
    doc.append("")
    doc.append("```json")
    doc.append("{")
    doc.append('    "appid": "your_app_id",')
    doc.append('    "timestamp": 1640995200,')
    doc.append('    "nonce": "abc123def456",')
    doc.append('    "signature": "ABCD1234..."')
    doc.append("}")
    doc.append("```")
    doc.append("")
    
    doc.append("### 响应示例")
    doc.append("")
    doc.append("```json")
    doc.append("{")
    doc.append('    "code": 0,')
    doc.append('    "message": "认证成功",')
    doc.append('    "data": {')
    doc.append('        "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",')
    doc.append('        "data_key": "base64_encoded_key",')
    doc.append('        "expires_in": 3600')
    doc.append('    }')
    doc.append("}")
    doc.append("```")
    doc.append("")
    
    # 2. 数据上传接口
    doc.append("## 📤 2. 数据上传接口")
    doc.append("")
    doc.append("### 接口信息")
    doc.append(f"- **接口地址**: `/api/v1/{{batch_id}}/{api.api_code}`")
    doc.append(f"- **请求方法**: `{api.http_method}`")
    doc.append("- **功能说明**: 上传业务数据到指定批次")
    doc.append("- **认证方式**: Bearer Token")
    doc.append("- **数据加密**: 支持AES-256-GCM加密")
    doc.append("- **数据签名**: 支持HMAC-SHA256签名验证")
    doc.append("")
    
    doc.append("### 请求头")
    doc.append("")
    doc.append("| 字段名 | 类型 | 必填 | 描述 |")
    doc.append("|--------|------|------|------|")
    doc.append("| Authorization | String | 是 | Bearer {access_token} |")
    doc.append("| Content-Type | String | 是 | application/json |")
    doc.append("| X-Data-Encrypted | String | 否 | true（启用加密时） |")
    doc.append("| X-Data-Signature | String | 否 | 数据签名（启用签名验证时） |")
    doc.append("")
    
    doc.append("### 路径参数")
    doc.append("")
    doc.append("| 参数名 | 类型 | 必填 | 描述 |")
    doc.append("|--------|------|------|------|")
    doc.append("| batch_id | String | 是 | 批次唯一标识 |")
    doc.append("")
    
    # 添加字段说明（如果API有字段定义）
    if hasattr(api, 'fields') and api.fields:
        doc.append("### 数据字段说明")
        doc.append("")
        doc.append("| 字段名 | 类型 | 必填 | 描述 |")
        doc.append("|--------|------|------|------|")
        for field in api.fields:
            required = "是" if field.is_required else "否"
            doc.append(f"| {field.field_name} | {field.field_type} | {required} | {field.description or '无描述'} |")
        doc.append("")
    
    doc.append("### 数据签名机制")
    doc.append("")
    doc.append("为确保数据完整性和防篡改，系统支持HMAC-SHA256数据签名验证：")
    doc.append("")
    doc.append("#### 签名生成规则")
    doc.append("")
    doc.append("```")
    doc.append("signature = HMAC_SHA256(data_key, encrypted_data).hexdigest().upper()")
    doc.append("```")
    doc.append("")
    doc.append("- **签名密钥**: 使用认证接口返回的`data_key`")
    doc.append("- **签名数据**: 加密后的数据（`data`字段的值）")
    doc.append("- **签名算法**: HMAC-SHA256")
    doc.append("- **签名格式**: 十六进制字符串（大写）")
    doc.append("")
    doc.append("#### 签名传递方式")
    doc.append("")
    doc.append("签名可通过以下两种方式传递（优先级：请求体 > 请求头）：")
    doc.append("")
    doc.append("1. **请求体中的signature字段**")
    doc.append("2. **请求头X-Data-Signature**")
    doc.append("")
    doc.append("#### 服务端验证流程")
    doc.append("")
    doc.append("1. 提取客户的`data_key`")
    doc.append("2. 使用相同规则重新计算签名")
    doc.append("3. 比较计算结果与提供的签名")
    doc.append("4. 签名不匹配时返回错误码2003")
    doc.append("")
    
    doc.append("### 加密请求示例")
    doc.append("")
    doc.append("```json")
    doc.append("{")
    doc.append('    "timestamp": 1640995200,')
    doc.append('    "nonce": "random_string",')
    doc.append('    "data": "base64_encrypted_data",')
    doc.append('    "iv": "base64_iv",')
    doc.append('    "signature": "ABCD1234567890ABCDEF...",')
    doc.append('    "needread": false')
    doc.append("}")
    doc.append("```")
    doc.append("")
    doc.append("### 客户端实现示例（Python）")
    doc.append("")
    doc.append("```python")
    doc.append("import hmac")
    doc.append("import hashlib")
    doc.append("")
    doc.append("def generate_data_signature(data_key: str, encrypted_data: str) -> str:")
    doc.append('    """生成数据签名"""')
    doc.append("    signature = hmac.new(")
    doc.append("        data_key.encode('utf-8'),")
    doc.append("        encrypted_data.encode('utf-8'),")
    doc.append("        hashlib.sha256")
    doc.append("    ).hexdigest().upper()")
    doc.append("    return signature")
    doc.append("```")
    doc.append("")
    
    doc.append("### 响应示例")
    doc.append("")
    doc.append("```json")
    doc.append("{")
    doc.append('    "code": 0,')
    doc.append('    "message": "数据上传成功",')
    doc.append('    "data": {')
    doc.append('        "batch_id": "batch_123",')
    doc.append('        "record_count": 100,')
    doc.append('        "upload_time": "2024-01-01T12:00:00Z"')
    doc.append('    }')
    doc.append("}")
    doc.append("```")
    doc.append("")
    
    # 3. 批次完成接口
    doc.append("## ✅ 3. 批次完成接口")
    doc.append("")
    doc.append("### 接口信息")
    doc.append(f"- **接口地址**: `/api/v1/batch/{api.api_code}/{{batch_id}}/complete`")
    doc.append("- **请求方法**: `POST`")
    doc.append("- **功能说明**: 标记批次数据上传完成，触发后续处理")
    doc.append("- **认证方式**: Bearer Token")
    doc.append("- **数据加密**: 支持AES-256-GCM加密")
    doc.append("- **数据签名**: 支持HMAC-SHA256签名验证")
    doc.append("")
    
    doc.append("### 请求头")
    doc.append("")
    doc.append("| 字段名 | 类型 | 必填 | 描述 |")
    doc.append("|--------|------|------|------|")
    doc.append("| Authorization | String | 是 | Bearer {access_token} |")
    doc.append("| X-Data-Encrypted | String | 是 | true |")
    doc.append("| X-Data-Signature | String | 否 | 数据签名（推荐使用） |")
    doc.append("")
    
    doc.append("### 路径参数")
    doc.append("")
    doc.append("| 参数名 | 类型 | 必填 | 描述 |")
    doc.append("|--------|------|------|------|")
    doc.append("| batch_id | String | 是 | 批次唯一标识 |")
    doc.append("")
    
    doc.append("### 请求体参数")
    doc.append("")
    doc.append("| 字段名 | 类型 | 必填 | 描述 |")
    doc.append("|--------|------|------|------|")
    doc.append("| timestamp | Long | 是 | 当前时间戳（秒） |")
    doc.append("| nonce | String | 是 | 随机字符串（8-16位） |")
    doc.append("| data | String | 是 | AES-GCM加密后的完成数据（Base64编码） |")
    doc.append("| iv | String | 是 | 初始化向量（Base64编码） |")
    doc.append("| signature | String | 否 | 数据签名（HMAC-SHA256） |")
    doc.append("| needread | Boolean | 否 | 是否需要读取确认，默认false |")
    doc.append("")
    
    doc.append("### 完成数据结构（加密前）")
    doc.append("")
    doc.append("```json")
    doc.append("{")
    doc.append('    "callback_url": "http://your-domain.com/callback",')
    doc.append('    "total": 1000,')
    doc.append('    "remark": "批次处理完成"')
    doc.append("}")
    doc.append("```")
    doc.append("")
    doc.append("### 数据签名说明")
    doc.append("")
    doc.append("批次完成接口的签名机制与数据上传接口相同：")
    doc.append("")
    doc.append("- **签名对象**: 加密后的数据（`data`字段值）")
    doc.append("- **签名密钥**: 认证接口返回的`data_key`")
    doc.append("- **签名算法**: HMAC-SHA256")
    doc.append("- **传递方式**: 请求体`signature`字段或请求头`X-Data-Signature`")
    doc.append("")
    
    doc.append("### 请求示例")
    doc.append("")
    doc.append("```json")
    doc.append("{")
    doc.append('    "timestamp": 1640995200,')
    doc.append('    "nonce": "random_string",')
    doc.append('    "data": "encrypted_completion_data",')
    doc.append('    "iv": "base64_iv",')
    doc.append('    "signature": "ABCD1234567890ABCDEF...",')
    doc.append('    "needread": false')
    doc.append("}")
    doc.append("```")
    doc.append("")
    
    doc.append("### 响应示例")
    doc.append("")
    doc.append("```json")
    doc.append("{")
    doc.append('    "code": 0,')
    doc.append('    "message": "批次完成标记成功",')
    doc.append('    "data": {')
    doc.append('        "batch_id": "batch_123",')
    doc.append('        "status": "completed",')
    doc.append('        "completed_at": "2024-01-01T12:00:00Z"')
    doc.append('    }')
    doc.append("}")
    doc.append("```")
    doc.append("")
    
    # 4. 结果查询接口
    doc.append("## 📥 4. 结果查询接口")
    doc.append("")
    doc.append("### 接口信息")
    doc.append(f"- **接口地址**: `/api/v1/results/{api.api_code}/{{batch_id}}`")
    doc.append("- **请求方法**: `GET`")
    doc.append("- **功能说明**: 查询批次处理结果")
    doc.append("- **认证方式**: Bearer Token")
    doc.append("- **数据加密**: 支持AES-256-GCM加密返回")
    doc.append("- **数据签名**: 返回结果包含HMAC-SHA256签名")
    doc.append("")
    
    doc.append("### 请求头")
    doc.append("")
    doc.append("| 字段名 | 类型 | 必填 | 描述 |")
    doc.append("|--------|------|------|------|")
    doc.append("| Authorization | String | 是 | Bearer {access_token} |")
    doc.append("")
    
    doc.append("### 路径参数")
    doc.append("")
    doc.append("| 参数名 | 类型 | 必填 | 描述 |")
    doc.append("|--------|------|------|------|")
    doc.append("| batch_id | String | 是 | 批次唯一标识 |")
    doc.append("")
    
    doc.append("### 响应字段说明")
    doc.append("")
    doc.append("| 字段名 | 类型 | 描述 |")
    doc.append("|--------|------|------|")
    doc.append("| status | String | 批次状态：processing/completed/failed/cancelled |")
    doc.append("| data | String | 加密后的结果数据（Base64编码），仅在completed/failed时返回 |")
    doc.append("| iv | String | 初始化向量（Base64编码），用于解密data字段 |")
    doc.append("| result_sign | String | 结果数据签名（HMAC-SHA256），用于验证数据完整性 |")
    doc.append("")
    
    doc.append("### 结果数据签名机制")
    doc.append("")
    doc.append("服务端在返回处理结果时会生成数据签名，确保结果数据的完整性：")
    doc.append("")
    doc.append("#### 签名生成规则")
    doc.append("")
    doc.append("```")
    doc.append("result_sign = HMAC_SHA256(data_key, encrypted_result_data).hexdigest()")
    doc.append("```")
    doc.append("")
    doc.append("- **签名密钥**: 客户的`data_key`")
    doc.append("- **签名数据**: 加密后的结果数据（`data`字段值）")
    doc.append("- **签名算法**: HMAC-SHA256")
    doc.append("- **签名格式**: 十六进制字符串（小写）")
    doc.append("")
    doc.append("#### 客户端验证示例（Python）")
    doc.append("")
    doc.append("```python")
    doc.append("import hmac")
    doc.append("import hashlib")
    doc.append("")
    doc.append("def verify_result_signature(data_key: str, encrypted_data: str, signature: str) -> bool:")
    doc.append('    """验证结果数据签名"""')
    doc.append("    expected_signature = hmac.new(")
    doc.append("        data_key.encode('utf-8'),")
    doc.append("        encrypted_data.encode('utf-8'),")
    doc.append("        hashlib.sha256")
    doc.append("    ).hexdigest()")
    doc.append("    return hmac.compare_digest(expected_signature, signature)")
    doc.append("```")
    doc.append("")
    
    doc.append("### 响应示例")
    doc.append("")
    doc.append("#### 处理中状态")
    doc.append("")
    doc.append("```json")
    doc.append("{")
    doc.append('    "code": 0,')
    doc.append('    "message": "批次结果查询成功",')
    doc.append('    "data": {')
    doc.append('        "status": "processing",')
    doc.append('        "data": null,')
    doc.append('        "iv": null,')
    doc.append('        "result_sign": null')
    doc.append('    }')
    doc.append("}")
    doc.append("```")
    doc.append("")
    doc.append("#### 处理完成状态")
    doc.append("")
    doc.append("```json")
    doc.append("{")
    doc.append('    "code": 0,')
    doc.append('    "message": "批次结果查询成功",')
    doc.append('    "data": {')
    doc.append('        "status": "completed",')
    doc.append('        "data": "base64_encrypted_result_data",')
    doc.append('        "iv": "base64_initialization_vector",')
    doc.append('        "result_sign": "abcd1234567890abcdef..."')
    doc.append('    }')
    doc.append("}")
    doc.append("```")
    doc.append("")
    
    # 5. 完整调用流程
    doc.append("## 🔄 5. 完整调用流程")
    doc.append("")
    doc.append("### 步骤说明")
    doc.append("")
    doc.append("1. **认证获取令牌**")
    doc.append("   - 调用认证接口获取 `access_token` 和 `data_key`")
    doc.append("   - 保存令牌用于后续接口调用")
    doc.append("")
    doc.append("2. **上传业务数据**")
    doc.append("   - 使用 `data_key` 加密业务数据")
    doc.append("   - 调用数据上传接口，传入 `batch_id`")
    doc.append("   - 可多次调用上传同一批次的不同数据")
    doc.append("")
    doc.append("3. **标记批次完成**")
    doc.append("   - 所有数据上传完成后，调用批次完成接口")
    doc.append("   - 系统开始处理该批次数据")
    doc.append("")
    doc.append("4. **查询处理结果**")
    doc.append("   - 调用结果查询接口获取处理结果")
    doc.append("   - 可轮询查询直到处理完成")
    doc.append("")
    
    doc.append("### 流程图")
    doc.append("")
    doc.append("```")
    doc.append("客户端                    API服务")
    doc.append("  |                         |")
    doc.append("  |-- 1. 认证请求 --------->|")
    doc.append("  |<-- access_token --------|")
    doc.append("  |                         |")
    doc.append("  |-- 2. 上传数据 --------->|")
    doc.append("  |<-- 上传成功 ------------|")
    doc.append("  |                         |")
    doc.append("  |-- 3. 标记完成 --------->|")
    doc.append("  |<-- 完成确认 ------------|")
    doc.append("  |                         |")
    doc.append("  |-- 4. 查询结果 --------->|")
    doc.append("  |<-- 处理结果 ------------|")
    doc.append("```")
    doc.append("")
    
    # 6. 业务状态码说明
    doc.append("## 📋 6. 业务状态码说明")
    doc.append("")
    doc.append("所有接口都使用统一的响应格式，包含业务状态码(code)、消息(message)和数据(data)三个字段：")
    doc.append("")
    doc.append("```json")
    doc.append("{")
    doc.append('    "code": 0,        // 业务状态码，0表示成功')
    doc.append('    "message": "...", // 响应消息')
    doc.append('    "data": {...}     // 响应数据，失败时为null')
    doc.append("}")
    doc.append("```")
    doc.append("")
    doc.append("### 常用状态码")
    doc.append("")
    doc.append("| 状态码 | 说明 | 场景 |")
    doc.append("|--------|------|------|")
    doc.append("| 0 | 成功 | 请求处理成功 |")
    doc.append("| 1001 | 认证失败 | 签名验证失败或凭据无效 |")
    doc.append("| 1006 | Token无效或已过期 | 访问令牌失效 |")
    doc.append("| 1007 | 缺少认证令牌 | 请求头缺少Authorization |")
    doc.append("| 1009 | 客户账户已停用 | 客户状态异常 |")
    doc.append("| 2001 | 数据验证失败 | 请求参数格式错误 |")
    doc.append("| 2002 | 数据解密失败 | 数据密钥错误或数据损坏 |")
    doc.append("| 2003 | 数据签名验证失败 | 数据完整性校验失败 |")
    doc.append("| 3001 | 批次不存在 | 指定的批次ID不存在 |")
    doc.append("| 3002 | 批次状态异常 | 批次已完成或处理中 |")
    doc.append("| 4001 | API不存在 | 指定的API不存在 |")
    doc.append("| 5001 | 内部服务器错误 | 系统内部错误 |")
    doc.append("| 5002 | 数据库操作失败 | 数据保存或查询失败 |")
    doc.append("| 5003 | 请求数据过大 | 上传数据超过限制 |")
    doc.append("")
    doc.append("### 错误响应示例")
    doc.append("")
    doc.append("```json")
    doc.append("{")
    doc.append('    "code": 1006,')
    doc.append('    "message": "Token无效或已过期",')
    doc.append('    "data": null')
    doc.append("}")
    doc.append("```")
    doc.append("")
    
    # 7. 注意事项
    doc.append("## ⚠️ 7. 注意事项")
    doc.append("")
    doc.append("### 安全要求")
    doc.append("- 所有接口调用必须使用HTTPS")
    doc.append("- 签名密钥和数据密钥需妥善保管")
    doc.append("- 建议对敏感数据进行加密传输")
    doc.append("")
    
    doc.append("### 性能建议")
    doc.append("- 单次上传数据量建议不超过10MB")
    doc.append("- 批次记录数建议不超过10000条")
    doc.append("- 合理设置请求超时时间")
    doc.append("")
    
    doc.append("### 错误处理")
    doc.append("- 网络异常时建议重试，最多3次")
    doc.append("- 认证失败时需重新获取令牌")
    doc.append("- 详细错误信息请查看响应中的message字段")
    doc.append("")
    
    # 页脚
    doc.append("---")
    doc.append("")
    doc.append("📝 *本文档由系统自动生成，如有疑问请联系技术支持*")
    doc.append("")
    
    return "\n".join(doc)


def _generate_complete_html_documentation(api: CustomApi) -> str:
    """
    生成完整的HTML格式API服务文档
    
    Args:
        api: API对象
        
    Returns:
        HTML文档内容
    """
    import html
    
    customer_name = html.escape(api.customer.name if api.customer else "客户")
    api_code = html.escape(api.api_code)
    
    html_content = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{customer_name}数据采集API服务文档</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f8f9fa;
        }}
        .container {{
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            padding: 30px;
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #34495e;
            border-bottom: 2px solid #ecf0f1;
            padding-bottom: 8px;
            margin-top: 30px;
        }}
        h3 {{
            color: #2c3e50;
            margin-top: 25px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 12px;
            text-align: left;
        }}
        th {{
            background-color: #f8f9fa;
            font-weight: 600;
        }}
        .endpoint {{
            background: #e8f4fd;
            border-left: 4px solid #3498db;
            padding: 15px;
            margin: 15px 0;
            font-family: monospace;
            font-size: 14px;
        }}
        .method {{
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-weight: bold;
            font-size: 12px;
        }}
        .method-get {{ background: #d4edda; color: #155724; }}
        .method-post {{ background: #cce5ff; color: #004085; }}
        pre {{
            background: #f8f9fa;
            border: 1px solid #e9ecef;
            border-radius: 4px;
            padding: 15px;
            overflow-x: auto;
        }}
        .toc {{
            background: #f8f9fa;
            border-radius: 6px;
            padding: 20px;
            margin: 20px 0;
        }}
        .toc ul {{
            list-style-type: none;
            padding-left: 0;
        }}
        .toc li {{
            margin: 8px 0;
        }}
        .toc a {{
            text-decoration: none;
            color: #3498db;
        }}
        .flow-diagram {{
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 6px;
            padding: 20px;
            font-family: monospace;
            white-space: pre;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📋 {customer_name}数据采集API服务文档</h1>
        
        <p>本文档描述了完整的数据采集API服务，包含认证、数据上传、批次管理和结果查询四个核心功能。</p>
        
        <div class="toc">
            <h2>📑 目录</h2>
            <ul>
                <li><a href="#auth">🔐 1. 认证接口</a></li>
                <li><a href="#upload">📤 2. 数据上传接口</a></li>
                <li><a href="#complete">✅ 3. 批次完成接口</a></li>
                <li><a href="#results">📥 4. 结果查询接口</a></li>
                <li><a href="#flow">🔄 5. 完整调用流程</a></li>
                <li><a href="#notes">⚠️ 6. 注意事项</a></li>
            </ul>
        </div>
        
        <h2 id="auth">🔐 1. 认证接口</h2>
        
        <div class="endpoint">
            <span class="method method-post">POST</span> /api/v1/auth/token
        </div>
        
        <h3>功能说明</h3>
        <p>获取访问令牌和数据加密密钥，用于后续接口调用的身份验证和数据加密。</p>
        
        <h3>请求参数</h3>
        <table>
            <thead>
                <tr>
                    <th>字段名</th>
                    <th>类型</th>
                    <th>必填</th>
                    <th>描述</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>appid</td>
                    <td>String</td>
                    <td>是</td>
                    <td>应用唯一标识</td>
                </tr>
                <tr>
                    <td>timestamp</td>
                    <td>Long</td>
                    <td>是</td>
                    <td>当前时间戳（秒）</td>
                </tr>
                <tr>
                    <td>nonce</td>
                    <td>String</td>
                    <td>是</td>
                    <td>随机字符串（8-16位）</td>
                </tr>
                <tr>
                    <td>signature</td>
                    <td>String</td>
                    <td>是</td>
                    <td>HMAC-SHA256签名</td>
                </tr>
            </tbody>
        </table>
        
        <h3>签名生成规则</h3>
        <pre>signature_data = appid + timestamp + nonce
signature = HMAC_SHA256(secret, signature_data).hexdigest().upper()</pre>
        
        <h2 id="upload">📤 2. 数据上传接口</h2>
        
        <div class="endpoint">
            <span class="method method-post">POST</span> /api/v1/{{batch_id}}/{api_code}
        </div>
        
        <h3>功能说明</h3>
        <p>上传业务数据到指定批次，支持AES-256-GCM加密传输。</p>
        
        <h3>请求头</h3>
        <table>
            <thead>
                <tr>
                    <th>字段名</th>
                    <th>类型</th>
                    <th>必填</th>
                    <th>描述</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>Authorization</td>
                    <td>String</td>
                    <td>是</td>
                    <td>Bearer {{access_token}}</td>
                </tr>
                <tr>
                    <td>Content-Type</td>
                    <td>String</td>
                    <td>是</td>
                    <td>application/json</td>
                </tr>
                <tr>
                    <td>X-Data-Encrypted</td>
                    <td>String</td>
                    <td>否</td>
                    <td>true（启用加密时）</td>
                </tr>
            </tbody>
        </table>
        
        <h2 id="complete">✅ 3. 批次完成接口</h2>
        
        <div class="endpoint">
            <span class="method method-post">POST</span> /api/v1/batch/{api_code}/{{batch_id}}/complete
        </div>
        
        <h3>功能说明</h3>
        <p>标记批次数据上传完成，触发后续数据处理流程。</p>
        
        <h2 id="results">📥 4. 结果查询接口</h2>
        
        <div class="endpoint">
            <span class="method method-get">GET</span> /api/v1/results/{api_code}/{{batch_id}}
        </div>
        
        <h3>功能说明</h3>
        <p>查询批次处理结果，支持加密返回数据。</p>
        
        <h2 id="flow">🔄 5. 完整调用流程</h2>
        
        <div class="flow-diagram">
客户端                    API服务
  |                         |
  |-- 1. 认证请求 --------->|
  |<-- access_token --------|
  |                         |
  |-- 2. 上传数据 --------->|
  |<-- 上传成功 ------------|
  |                         |
  |-- 3. 标记完成 --------->|
  |<-- 完成确认 ------------|
  |                         |
  |-- 4. 查询结果 --------->|
  |<-- 处理结果 ------------|
        </div>
        
        <h2 id="notes">⚠️ 6. 注意事项</h2>
        
        <h3>安全要求</h3>
        <ul>
            <li>所有接口调用必须使用HTTPS</li>
            <li>签名密钥和数据密钥需妥善保管</li>
            <li>建议对敏感数据进行加密传输</li>
        </ul>
        
        <h3>性能建议</h3>
        <ul>
            <li>单次上传数据量建议不超过10MB</li>
            <li>批次记录数建议不超过10000条</li>
            <li>合理设置请求超时时间</li>
        </ul>
        
        <hr>
        <p><em>📝 本文档由系统自动生成，如有疑问请联系技术支持</em></p>
    </div>
</body>
</html>
    """
    
    return html_content


def _generate_complete_json_documentation(api: CustomApi) -> str:
    """
    生成完整的JSON格式API服务文档
    
    Args:
        api: API对象
        
    Returns:
        JSON文档内容
    """
    import json
    
    customer_name = api.customer.name if api.customer else "客户"
    
    openapi_doc = {
        "openapi": "3.0.3",
        "info": {
            "title": f"{customer_name}数据采集API服务",
            "description": "完整的数据采集API服务，包含认证、数据上传、批次管理和结果查询功能",
            "version": "1.0.0",
            "contact": {
                "name": "API支持",
                "email": "support@example.com"
            }
        },
        "servers": [
            {
                "url": "https://your-domain.com/api/v1",
                "description": "生产环境"
            },
            {
                "url": "http://localhost:8000/api/v1",
                "description": "开发环境"
            }
        ],
        "paths": {
            "/auth/token": {
                "post": {
                    "summary": "获取访问令牌",
                    "description": "通过签名认证获取访问令牌和数据加密密钥",
                    "tags": ["认证"],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "required": ["appid", "timestamp", "nonce", "signature"],
                                    "properties": {
                                        "appid": {
                                            "type": "string",
                                            "description": "应用唯一标识"
                                        },
                                        "timestamp": {
                                            "type": "integer",
                                            "description": "当前时间戳（秒）"
                                        },
                                        "nonce": {
                                            "type": "string",
                                            "description": "随机字符串（8-16位）"
                                        },
                                        "signature": {
                                            "type": "string",
                                            "description": "HMAC-SHA256签名"
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "认证成功",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "code": {"type": "integer"},
                                            "message": {"type": "string"},
                                            "data": {
                                                "type": "object",
                                                "properties": {
                                                    "access_token": {"type": "string"},
                                                    "data_key": {"type": "string"},
                                                    "expires_in": {"type": "integer"}
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            f"/{{{"batch_id"}}}/{api.api_code}": {
                api.http_method.lower(): {
                    "summary": "上传业务数据",
                    "description": "上传业务数据到指定批次",
                    "tags": ["数据上传"],
                    "parameters": [
                        {
                            "name": "batch_id",
                            "in": "path",
                            "required": True,
                            "description": "批次唯一标识",
                            "schema": {"type": "string"}
                        }
                    ],
                    "security": [{"bearerAuth": []}],
                    "responses": {
                        "200": {
                            "description": "上传成功",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "code": {"type": "integer"},
                                            "message": {"type": "string"},
                                            "data": {"type": "object"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            f"/batch/{api.api_code}/{{{"batch_id"}}}/complete": {
                "post": {
                    "summary": "标记批次完成",
                    "description": "标记批次数据上传完成，触发后续处理",
                    "tags": ["批次管理"],
                    "parameters": [
                        {
                            "name": "batch_id",
                            "in": "path",
                            "required": True,
                            "description": "批次唯一标识",
                            "schema": {"type": "string"}
                        }
                    ],
                    "security": [{"bearerAuth": []}],
                    "responses": {
                        "200": {
                            "description": "完成标记成功",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "code": {"type": "integer"},
                                            "message": {"type": "string"},
                                            "data": {"type": "object"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            f"/results/{api.api_code}/{{{"batch_id"}}}": {
                "get": {
                    "summary": "查询处理结果",
                    "description": "查询批次处理结果",
                    "tags": ["结果查询"],
                    "parameters": [
                        {
                            "name": "batch_id",
                            "in": "path",
                            "required": True,
                            "description": "批次唯一标识",
                            "schema": {"type": "string"}
                        }
                    ],
                    "security": [{"bearerAuth": []}],
                    "responses": {
                        "200": {
                            "description": "查询成功",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "code": {"type": "integer"},
                                            "message": {"type": "string"},
                                            "data": {
                                                "type": "object",
                                                "properties": {
                                                    "batch_id": {"type": "string"},
                                                    "status": {"type": "string"},
                                                    "total_records": {"type": "integer"},
                                                    "processed_records": {"type": "integer"},
                                                    "success_records": {"type": "integer"},
                                                    "failed_records": {"type": "integer"},
                                                    "results": {"type": "string"},
                                                    "created_at": {"type": "string"},
                                                    "completed_at": {"type": "string"}
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        },
        "components": {
            "securitySchemes": {
                "bearerAuth": {
                    "type": "http",
                    "scheme": "bearer",
                    "bearerFormat": "JWT"
                }
            }
        },
        "tags": [
            {"name": "认证", "description": "身份认证相关接口"},
            {"name": "数据上传", "description": "数据上传相关接口"},
            {"name": "批次管理", "description": "批次管理相关接口"},
            {"name": "结果查询", "description": "结果查询相关接口"}
        ]
    }
    
    return json.dumps(openapi_doc, ensure_ascii=False, indent=2)


@router.post("/logout", response_model=BaseResponse, summary="管理员登出")
async def admin_logout(
    current_admin: AdminUser = Depends(get_current_admin_user)
):
    """
    管理员登出接口
    
    Args:
        current_admin: 当前管理员
        
    Returns:
        操作结果
    """
    return BaseResponse(
        success=True,
        message="登出成功"
    )


@router.get("/profile", response_model=AdminUserDetailResponse, summary="获取管理员信息")
async def get_admin_profile(
    current_admin: AdminUser = Depends(get_current_admin_user)
):
    """
    获取当前管理员信息
    
    Args:
        current_admin: 当前管理员
        
    Returns:
        管理员详细信息
    """
    return AdminUserDetailResponse(
        success=True,
        message="获取成功",
        data=current_admin
    )


@router.put("/profile", response_model=AdminUserResponse, summary="更新管理员信息")
async def update_admin_profile(
    update_data: AdminUserUpdate,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user)
):
    """
    更新当前管理员信息
    
    Args:
        update_data: 更新数据
        db: 数据库会话
        current_admin: 当前管理员
        
    Returns:
        更新后的管理员信息
    """
    try:
        updated_admin = admin_service.update_admin(
            db, current_admin.id, update_data
        )
        return SuccessResponse[AdminUserResponse](
            success=True,
            message="更新成功",
            data=AdminUserResponse.model_validate(updated_admin)
        )
    except ValidationException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/change-password", response_model=BaseResponse, summary="修改密码")
async def change_password(
    password_data: PasswordChangeRequest,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user)
):
    """
    修改管理员密码
    
    Args:
        password_data: 密码修改数据
        db: 数据库会话
        current_admin: 当前管理员
        
    Returns:
        操作结果
    """
    try:
        admin_service.change_password(
            db, current_admin.id, password_data
        )
        return BaseResponse(
            success=True,
            message="密码修改成功"
        )
    except ValidationException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# ==================== 管理员管理 ====================

@router.get("/admins", response_model=PaginatedResponse[AdminUserResponse], summary="获取管理员列表")
async def get_admins(
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    role: Optional[str] = Query(None, description="角色筛选"),
    is_active: Optional[bool] = Query(None, description="状态筛选"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user)
):
    """
    获取管理员列表
    
    Args:
        keyword: 搜索关键词
        role: 角色筛选
        is_active: 状态筛选
        page: 页码
        page_size: 每页数量
        db: 数据库会话
        current_admin: 当前管理员
        
    Returns:
        分页的管理员列表
    """
    admins, pagination = admin_service.search_admins(
        db,
        keyword=keyword,
        role=role,
        is_active=is_active,
        page=page,
        page_size=page_size
    )
    
    return PaginatedResponse[
        AdminUserResponse
    ](
        success=True,
        message="获取成功",
        data=[AdminUserResponse.model_validate(admin) for admin in admins],
        pagination=pagination
    )


@router.post("/admins", response_model=AdminUserResponse, summary="创建管理员")
async def create_admin(
    admin_data: AdminUserCreate,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user)
):
    """
    创建管理员
    
    Args:
        admin_data: 管理员创建数据
        db: 数据库会话
        current_admin: 当前管理员
        
    Returns:
        创建的管理员信息
    """
    try:
        admin = admin_service.create_admin(
            db, admin_data, created_by=current_admin.id
        )
        return SuccessResponse[AdminUserResponse](
            success=True,
            message="创建成功",
            data=AdminUserResponse.model_validate(admin)
        )
    except ValidationException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/admins/{admin_id}", response_model=AdminUserDetailResponse, summary="获取管理员详情")
async def get_admin(
    admin_id: int,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user)
):
    """
    获取管理员详情
    
    Args:
        admin_id: 管理员ID
        db: 数据库会话
        current_admin: 当前管理员
        
    Returns:
        管理员详细信息
    """
    admin = admin_service.get(db, admin_id)
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="管理员不存在"
        )
    
    return SuccessResponse[AdminUserDetailResponse](
        success=True,
        message="获取成功",
        data=AdminUserDetailResponse.model_validate(admin)
    )


@router.put("/admins/{admin_id}", response_model=AdminUserResponse, summary="更新管理员")
async def update_admin(
    admin_id: int,
    update_data: AdminUserUpdate,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user)
):
    """
    更新管理员信息
    
    Args:
        admin_id: 管理员ID
        update_data: 更新数据
        db: 数据库会话
        current_admin: 当前管理员
        
    Returns:
        更新后的管理员信息
    """
    try:
        admin = admin_service.update_admin(db, admin_id, update_data)
        return SuccessResponse[AdminUserResponse](
            success=True,
            message="更新成功",
            data=AdminUserResponse.model_validate(admin)
        )
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ValidationException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/admins/{admin_id}", response_model=BaseResponse, summary="删除管理员")
async def delete_admin(
    admin_id: int,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user)
):
    """
    删除管理员
    
    Args:
        admin_id: 管理员ID
        db: 数据库会话
        current_admin: 当前管理员
        
    Returns:
        操作结果
    """
    if admin_id == current_admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能删除自己"
        )
    
    try:
        admin_service.delete_admin(db, admin_id)
        return BaseResponse(
            success=True,
            message="删除成功"
        )
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


# ==================== 平台管理 ====================

@router.get("/customers", response_model=PaginatedResponse[CustomerResponse], summary="获取客户列表")
async def get_customers(
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    status: Optional[str] = Query(None, description="状态筛选"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user)
):
    """
    获取客户列表
    
    Args:
        keyword: 搜索关键词
        status: 状态筛选
        page: 页码
        page_size: 每页数量
        db: 数据库会话
        current_admin: 当前管理员
        
    Returns:
        分页的客户列表
    """
    customers, pagination = customer_service.search_customers(
        db,
        keyword=keyword,
        status=status,
        page=page,
        page_size=page_size
    )
    
    # 转换客户对象列表
    customer_dicts = [customer_service.customer_to_response_dict(customer) for customer in customers]
    customer_responses = [CustomerResponse.model_validate(customer_dict) for customer_dict in customer_dicts]
    
    return PaginatedResponse[CustomerResponse](
        success=True,
        message="获取成功",
        data=customer_responses,
        pagination=pagination
    )


@router.post("/customers", response_model=SuccessResponse[CustomerResponse], summary="创建客户")
async def create_customer(
    customer_data: CustomerCreate,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user)
):
    """
    创建客户
    
    Args:
        customer_data: 客户创建数据
        db: 数据库会话
        current_admin: 当前管理员
        
    Returns:
        创建的平台信息
    """
    try:
        customer = customer_service.create_customer(db, customer_data)
        # 使用服务方法转换Customer对象
        customer_dict = customer_service.customer_to_response_dict(customer)
        return SuccessResponse[CustomerResponse](
            success=True,
            message="创建成功",
            data=CustomerResponse.model_validate(customer_dict)
        )
    except ValidationException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/customers/{customer_id}", response_model=SuccessResponse[CustomerDetailResponse], summary="获取客户详情")
async def get_customer(
    customer_id: int,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user)
):
    """
    获取客户详情
    
    Args:
        customer_id: 客户ID
        db: 数据库会话
        current_admin: 当前管理员
        
    Returns:
        客户详细信息
    """
    customer = customer_service.get(db, customer_id)
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="客户不存在"
        )
    
    # 使用服务方法转换Customer对象
    customer_dict = customer_service.customer_to_detail_response_dict(customer)
    return SuccessResponse[CustomerDetailResponse](
        success=True,
        message="获取成功",
        data=CustomerDetailResponse.model_validate(customer_dict)
    )


@router.put("/customers/{customer_id}", response_model=SuccessResponse[CustomerResponse], summary="更新客户")
async def update_customer(
    customer_id: int,
    update_data: CustomerUpdate,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user)
):
    """
    更新平台信息
    
    Args:
        customer_id: 客户ID
        update_data: 更新数据
        db: 数据库会话
        current_admin: 当前管理员
        
    Returns:
        更新后的平台信息
    """
    try:
        customer = customer_service.update_customer(db, customer_id, update_data)
        # 使用服务方法转换Customer对象
        customer_dict = customer_service.customer_to_response_dict(customer)
        return SuccessResponse[CustomerResponse](
            success=True,
            message="更新成功",
            data=CustomerResponse.model_validate(customer_dict)
        )
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ValidationException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/customers/{customer_id}", response_model=BaseResponse, summary="删除客户")
async def delete_customer(
    customer_id: int,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user)
):
    """
    删除客户
    
    Args:
        customer_id: 客户ID
        db: 数据库会话
        current_admin: 当前管理员
        
    Returns:
        操作结果
    """
    try:
        customer_service.delete_customer(db, customer_id)
        return BaseResponse(
            success=True,
            message="删除成功"
        )
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post("/customers/{customer_id}/reset-secret", response_model=SuccessResponse, summary="重置客户App Secret")
async def reset_customer_app_secret(
    customer_id: int,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user)
):
    """
    重置客户的App Secret
    
    Args:
        customer_id: 客户ID
        db: 数据库会话
        current_admin: 当前管理员
        
    Returns:
        包含新App Secret的响应
    """
    try:
        customer = customer_service.reset_app_secret(db, customer_id, reset_by=current_admin.id)
        return SuccessResponse(
            success=True,
            message="App Secret重置成功",
            data={
                "app_secret": customer.app_secret,
                "reset_at": customer.secret_reset_at or customer.updated_at
            }
        )
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


# ==================== API管理 ====================

@router.get("/apis", response_model=PaginatedResponse[CustomApiResponse], summary="获取API列表")
async def get_apis(
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    customer_id: Optional[int] = Query(None, description="客户ID筛选"),
    is_active: Optional[bool] = Query(None, description="状态筛选"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user)
):
    """
    获取API列表
    
    Args:
        keyword: 搜索关键词
        customer_id: 客户ID筛选
        is_active: 状态筛选
        page: 页码
        page_size: 每页数量
        db: 数据库会话
        current_admin: 当前管理员
        
    Returns:
        分页的API列表
    """
    apis, pagination = api_service.search_apis(
        db,
        keyword=keyword,
        customer_id=customer_id,
        is_active=is_active,
        page=page,
        page_size=page_size
    )
    
    return PaginatedResponse[CustomApiResponse](
        success=True,
        message="获取成功",
        data=apis,
        pagination=pagination
    )


@router.get("/apis/{api_id}", response_model=SuccessResponse[CustomApiDetailResponse], summary="获取API详情")
async def get_api(
    api_id: int,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user)
):
    """
    获取API详情
    
    Args:
        api_id: API ID
        db: 数据库会话
        current_admin: 当前管理员
        
    Returns:
        API详细信息
    """
    api = api_service.get(db, api_id)
    if not api:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API不存在"
        )
    
    return SuccessResponse(
        success=True,
        message="获取成功",
        data=api
    )


@router.post("/apis", response_model=SuccessResponse[CustomApiDetailResponse], summary="创建API")
async def create_api(
    api_data: CustomApiCreate,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user)
):
    """
    创建新的自定义API
    
    Args:
        api_data: API创建数据
        db: 数据库会话
        current_admin: 当前管理员
        
    Returns:
        创建的API详细信息
    """
    try:
        api = api_service.create_api(
            db, 
            api_data, 
            customer_id=api_data.customer_id,
            created_by=current_admin.id
        )
        return SuccessResponse(
            success=True,
            message="创建成功",
            data=api
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put("/apis/{api_id}", response_model=SuccessResponse[CustomApiDetailResponse], summary="更新API")
async def update_api(
    api_id: int,
    update_data: CustomApiUpdate,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user)
):
    """
    更新API信息
    
    Args:
        api_id: API ID
        update_data: 更新数据
        db: 数据库会话
        current_admin: 当前管理员
        
    Returns:
        更新后的API详细信息
    """
    try:
        api = api_service.update_api(db, api_id, update_data)
        return SuccessResponse(
            success=True,
            message="更新成功",
            data=api
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/apis/{api_id}", response_model=BaseResponse, summary="删除API")
async def delete_api(
    api_id: int,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user)
):
    """
    删除API
    
    Args:
        api_id: API ID
        db: 数据库会话
        current_admin: 当前管理员
        
    Returns:
        操作结果
    """
    try:
        api_service.delete_api(db, api_id)
        return BaseResponse(
            success=True,
            message="删除成功"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.patch("/apis/{api_id}/status", response_model=SuccessResponse[CustomApiDetailResponse], summary="切换API状态")
async def toggle_api_status(
    api_id: int,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user)
):
    """
    切换API启用/禁用状态
    
    Args:
        api_id: API ID
        db: 数据库会话
        current_admin: 当前管理员
        
    Returns:
        更新后的API详细信息
    """
    try:
        api = api_service.toggle_api_status(db, api_id)
        return SuccessResponse(
            success=True,
            message="状态切换成功",
            data=api
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/get_api_link", response_model=SuccessResponse, summary="获取任务类型链接数据")
async def get_api_link(
    current_admin: AdminUser = Depends(get_current_admin_user)
):
    """
    获取任务类型链接数据
    
    从外部数据库获取任务类型配置信息，包括任务ID、菜单名称、类型名称、数据库名和表名
    
    Args:
        current_admin: 当前管理员
        
    Returns:
        包含任务类型数据的响应
    """
    try:
        data_link = DataLink()
        result = data_link.get_link_menu_types()
        
        if not result['success']:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"获取数据失败: {result.get('error', '未知错误')}"
            )
        
        return SuccessResponse(
            success=True,
            message="获取成功",
            data=result['data']
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取任务类型数据失败: {str(e)}"
        )


@router.post("/apis/{api_id}/copy", response_model=SuccessResponse[CustomApiDetailResponse], summary="复制API")
async def copy_api(
    api_id: int,
    copy_data: CustomApiCopy,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user)
):
    """
    复制API到指定客户
    
    Args:
        api_id: 源API ID
        copy_data: 复制配置数据
        db: 数据库会话
        current_admin: 当前管理员
        
    Returns:
        复制后的API详细信息
    """
    try:
        copied_api = api_service.copy_api(
            db,
            source_api_id=api_id,
            target_customer_id=copy_data.target_customer_id,
            new_api_code=copy_data.new_api_code,
            new_api_name=copy_data.new_api_name,
            created_by=current_admin.id
        )
        return SuccessResponse(
            success=True,
            message="API复制成功",
            data=copied_api
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/apis/{api_id}/documentation", summary="生成API文档")
async def generate_api_documentation(
    api_id: int,
    format: str = Query("markdown", regex="^(markdown|html|json)$", description="文档格式：markdown, html, json"),
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user)
):
    """
    自动生成完整的API服务文档
    
    生成包含认证、数据上传、批次完成和结果查询的完整API服务文档，
    支持多种格式输出（Markdown、HTML、JSON）。
    
    Args:
        api_id: API ID（用于获取平台信息和API配置）
        format: 文档格式（markdown/html/json）
        db: 数据库会话
        current_admin: 当前管理员
        
    Returns:
        生成的完整API服务文档内容
    """
    try:
        # 获取API详细信息（用于获取平台信息）
        api = api_service.get_with_fields(db, api_id)
        
        if not api:
            raise BusinessException(
                code=BusinessCode.DATA_NOT_FOUND,
                message="API不存在"
            )
        
        # 生成完整的API服务文档
        documentation = _generate_complete_api_documentation(db, api, format)
        
        return BusinessResponse.success(
            data={
                "api_id": api_id,
                "api_name": api.api_name,
                "customer_name": api.customer.name if api.customer else "未知客户",
                "format": format,
                "documentation": documentation,
                "generated_at": datetime.now().isoformat()
            },
            message="API服务文档生成成功"
        )
    except Exception as e:
        import traceback
        error_detail = f"生成API服务文档失败: {str(e)}"
        print(f"文档生成异常: {traceback.format_exc()}")
        raise BusinessException(
            code=BusinessCode.INTERNAL_ERROR,
            message=error_detail
        )


@router.get("/apis/{api_id}/docs", summary="API文档查看器")
async def view_api_documentation(
    api_id: int,
    token: str = Query(..., description="认证token（必需，用于新窗口访问）"),
    db: Session = Depends(get_db)
):
    """
    提供类似/docs的API文档查看界面
    
    基于生成的OpenAPI JSON文档，提供Swagger UI界面来查看和测试API。
    
    Args:
        api_id: API ID
        token: 认证token（必需，用于新窗口访问）
        db: 数据库会话
        
    Returns:
        Swagger UI HTML页面
    """
    try:
        # 使用URL参数中的token进行认证
        jwt_service = JWTService()
        try:
            payload = jwt_service.verify_token(token)
            admin_id = payload.get("sub")
            if not admin_id:
                raise BusinessException(
                    code=BusinessCode.TOKEN_INVALID,
                    message="无效的认证token"
                )
            # 获取管理员信息
            current_admin = db.query(AdminUser).filter(AdminUser.id == admin_id).first()
            if not current_admin:
                raise BusinessException(
                    code=BusinessCode.USER_NOT_FOUND,
                    message="管理员不存在"
                )
        except Exception as e:
            raise BusinessException(
                code=BusinessCode.AUTH_FAILED,
                message="认证失败，请重新登录"
            )
        # 获取API详细信息
        api = api_service.get_with_fields(db, api_id)
        
        if not api:
            raise BusinessException(
                code=BusinessCode.DATA_NOT_FOUND,
                message="API不存在"
            )
        
        # 生成OpenAPI JSON文档
        openapi_json = _generate_complete_api_documentation(db, api, "json")
        
        # 生成Swagger UI HTML页面
        swagger_html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>{api.customer.name if api.customer else '客户'}数据采集API文档</title>
    <link rel="stylesheet" type="text/css" href="https://unpkg.com/swagger-ui-dist@5.9.0/swagger-ui.css" />
    <style>
        html {{
            box-sizing: border-box;
            overflow: -moz-scrollbars-vertical;
            overflow-y: scroll;
        }}
        *, *:before, *:after {{
            box-sizing: inherit;
        }}
        body {{
            margin:0;
            background: #fafafa;
        }}
        .swagger-ui .topbar {{
            background-color: #2c3e50;
        }}
        .swagger-ui .topbar .download-url-wrapper .select-label {{
            color: #fff;
        }}
        .swagger-ui .info .title {{
            color: #2c3e50;
        }}
        .swagger-ui .scheme-container {{
            background: #fff;
            box-shadow: 0 1px 2px 0 rgba(0,0,0,.15);
        }}
    </style>
</head>
<body>
    <div id="swagger-ui"></div>
    <script src="https://unpkg.com/swagger-ui-dist@5.9.0/swagger-ui-bundle.js"></script>
    <script src="https://unpkg.com/swagger-ui-dist@5.9.0/swagger-ui-standalone-preset.js"></script>
    <script>
        window.onload = function() {{
            const ui = SwaggerUIBundle({{
                spec: {openapi_json},
                dom_id: '#swagger-ui',
                deepLinking: true,
                presets: [
                    SwaggerUIBundle.presets.apis,
                    SwaggerUIStandalonePreset
                ],
                plugins: [
                    SwaggerUIBundle.plugins.DownloadUrl
                ],
                layout: "StandaloneLayout",
                validatorUrl: null,
                tryItOutEnabled: true,
                supportedSubmitMethods: ['get', 'post', 'put', 'delete', 'patch'],
                onComplete: function() {{
                    console.log('Swagger UI 加载完成');
                }},
                requestInterceptor: function(request) {{
                    // 可以在这里添加认证头等
                    console.log('请求拦截:', request);
                    return request;
                }},
                responseInterceptor: function(response) {{
                    console.log('响应拦截:', response);
                    return response;
                }}
            }});
        }};
    </script>
</body>
</html>
        """
        
        return HTMLResponse(content=swagger_html)
        
    except Exception as e:
        import traceback
        error_detail = f"生成API文档查看器失败: {str(e)}"
        print(f"文档查看器生成异常: {traceback.format_exc()}")
        raise BusinessException(
            code=BusinessCode.INTERNAL_ERROR,
            message=error_detail
        )


@router.get("/apis/{api_id}/logs", response_model=PaginatedResponse[ApiUsageLogResponse], summary="获取API调用日志")
async def get_api_logs(
    api_id: int,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user)
):
    """
    获取API调用日志
    
    Args:
        api_id: API ID
        page: 页码
        page_size: 每页数量
        db: 数据库会话
        current_admin: 当前管理员
        
    Returns:
        分页的日志列表
    """
    try:
        logs, pagination = log_service.get_api_logs(
            db, api_id, page=page, page_size=page_size
        )
        
        # 将数据库模型转换为响应模型，并添加平台名称
        log_responses = []
        for log in logs:
            # 获取平台信息
            customer = db.query(Customer).filter(Customer.id == log.customer_id).first()
            customer_name = customer.name if customer else "未知客户"
            
            # 创建响应对象，映射字段名以匹配前端期望
            log_dict = {
                "id": log.id,
                "customer_id": log.customer_id,
                "customer_name": customer_name,  # 前端期望的字段
                "api_id": log.api_id,
                "request_id": log.request_id,
                "request_method": log.http_method,  # 前端期望 request_method
                "http_method": log.http_method,  # 保持兼容性
                "request_path": log.request_url,  # 前端期望 request_path
                "request_url": log.request_url,  # 保持兼容性
                "client_ip": log.client_ip,
                "user_agent": log.user_agent,
                "status_code": log.response_status,  # 前端期望 status_code
                "response_status": log.response_status,  # 保持兼容性
                "response_time": int(log.processing_time * 1000) if log.processing_time else 0,  # 前端期望毫秒单位
                "processing_time": log.processing_time,  # 保持兼容性
                "error_message": log.error_message,
                "data_size": getattr(log, 'data_size', None),
                "record_count": getattr(log, 'record_count', None),
                "is_success": 200 <= log.response_status < 300,
                "is_error": log.response_status >= 400,
                "created_at": log.created_at
            }
            log_responses.append(log_dict)
        
        return PaginatedResponse[ApiUsageLogResponse](
            success=True,
            message="获取成功",
            data=log_responses,
            pagination=pagination
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# ==================== API字段管理 ====================

@router.get("/apis/{api_id}/fields", response_model=PaginatedResponse[ApiFieldResponse], summary="获取API字段列表")
async def get_api_fields(
    api_id: int,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user)
):
    """
    获取指定API的字段列表
    
    Args:
        api_id: API ID
        db: 数据库会话
        current_admin: 当前管理员
        
    Returns:
        API字段列表
    """
    try:
        # 检查API是否存在
        api = api_service.get(db, api_id)
        if not api:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="API不存在"
            )
        
        # 获取字段列表
        fields = api_field_service.get_api_fields(db, api_id, ordered=True)
        
        # 创建分页信息
        pagination = PaginationInfo.create(
            page=1,
            size=max(1, len(fields)),  # 确保size至少为1
            total=len(fields)
        )
        
        return PaginatedResponse[ApiFieldResponse](
            success=True,
            message="获取成功",
            data=fields,
            pagination=pagination
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/apis/{api_id}/fields", response_model=SuccessResponse[ApiFieldResponse], summary="创建API字段")
async def create_api_field(
    api_id: int,
    field_data: ApiFieldCreate,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user)
):
    """
    为指定API创建新字段
    
    Args:
        api_id: API ID
        field_data: 字段创建数据
        db: 数据库会话
        current_admin: 当前管理员
        
    Returns:
        创建的字段信息
    """
    try:
        field = api_field_service.create_field(
            db,
            field_data,
            api_id=api_id,
            created_by=current_admin.id
        )
        return SuccessResponse[ApiFieldResponse](
            success=True,
            message="字段创建成功",
            data=field
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/apis/{api_id}/fields/{field_id}", response_model=SuccessResponse[ApiFieldResponse], summary="获取API字段详情")
async def get_api_field(
    api_id: int,
    field_id: int,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user)
):
    """
    获取指定API字段的详细信息
    
    Args:
        api_id: API ID
        field_id: 字段ID
        db: 数据库会话
        current_admin: 当前管理员
        
    Returns:
        字段详细信息
    """
    try:
        field = api_field_service.get(db, field_id)
        if not field or field.api_id != api_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="字段不存在"
            )
        
        return SuccessResponse[ApiFieldResponse](
            success=True,
            message="获取成功",
            data=field
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put("/apis/{api_id}/fields/{field_id}", response_model=SuccessResponse[ApiFieldResponse], summary="更新API字段")
async def update_api_field(
    api_id: int,
    field_id: int,
    field_data: ApiFieldUpdate,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user)
):
    """
    更新指定API字段
    
    Args:
        api_id: API ID
        field_id: 字段ID
        field_data: 字段更新数据
        db: 数据库会话
        current_admin: 当前管理员
        
    Returns:
        更新后的字段信息
    """
    try:
        # 检查字段是否属于指定API
        field = api_field_service.get(db, field_id)
        if not field or field.api_id != api_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="字段不存在"
            )
        
        updated_field = api_field_service.update_field(
            db,
            field_id,
            field_data,
            updated_by=current_admin.id
        )
        
        return SuccessResponse[ApiFieldResponse](
            success=True,
            message="字段更新成功",
            data=updated_field
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/apis/{api_id}/fields/{field_id}", response_model=BaseResponse, summary="删除API字段")
async def delete_api_field(
    api_id: int,
    field_id: int,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user)
):
    """
    删除指定API字段
    
    Args:
        api_id: API ID
        field_id: 字段ID
        db: 数据库会话
        current_admin: 当前管理员
        
    Returns:
        操作结果
    """
    try:
        # 检查字段是否属于指定API
        field = api_field_service.get(db, field_id)
        if not field or field.api_id != api_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="字段不存在"
            )
        
        api_field_service.delete(db, id=field_id)
        
        return BaseResponse(
            success=True,
            message="字段删除成功"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/apis/{api_id}/fields/batch", response_model=BaseResponse, summary="批量更新API字段")
async def batch_update_api_fields(
    api_id: int,
    batch_data: ApiFieldBatchUpdateRequest,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user)
):
    """
    批量更新API字段（主要用于排序）
    
    Args:
        api_id: API ID
        batch_data: 批量更新数据
        db: 数据库会话
        current_admin: 当前管理员
        
    Returns:
        操作结果
    """
    try:
        # 检查API是否存在
        api = api_service.get(db, api_id)
        if not api:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="API不存在"
            )
        
        # 批量更新字段
        for field_update in batch_data.field_updates:
            field_id = field_update["field_id"]
            update_data = {k: v for k, v in field_update.items() if k != "field_id"}
            
            # 检查字段是否属于指定API
            field = api_field_service.get(db, field_id)
            if field and field.api_id == api_id:
                api_field_service.update(db, db_obj=field, obj_in=update_data)
        
        return BaseResponse(
            success=True,
            message="批量更新成功"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/apis/{api_id}/validate", response_model=BaseResponse, summary="验证API数据")
async def validate_api_data(
    api_id: int,
    data: dict,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user)
):
    """
    根据API字段定义验证提交的数据
    
    Args:
        api_id: API ID
        data: 要验证的数据
        db: 数据库会话
        current_admin: 当前管理员
        
    Returns:
        验证结果
    """
    try:
        # 检查API是否存在
        api = api_service.get(db, api_id)
        if not api:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="API不存在"
            )
        
        # 验证数据
        is_valid, errors = api_field_service.validate_field_data(db, api_id, data)
        
        if is_valid:
            return BaseResponse(
                success=True,
                message="数据验证通过"
            )
        else:
            return BaseResponse(
                success=False,
                message="数据验证失败",
                data={"errors": errors}
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# ==================== 系统配置 ====================

@router.get("/configs", response_model=PaginatedResponse[SystemConfigResponse], summary="获取系统配置列表")
async def get_configs(
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    category: Optional[str] = Query(None, description="分类筛选"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user)
):
    """
    获取系统配置列表
    
    Args:
        keyword: 搜索关键词
        category: 分类筛选
        page: 页码
        page_size: 每页数量
        db: 数据库会话
        current_admin: 当前管理员
        
    Returns:
        分页的配置列表
    """
    query_params = SystemConfigQuery(
        keyword=keyword,
        category=category
    )
    
    configs, pagination = config_service.search_configs(
        db, query_params, page=page, page_size=page_size
    )
    
    return PaginatedResponse[SystemConfigResponse](
        success=True,
        message="获取成功",
        data=configs,
        pagination=pagination
    )


@router.post("/configs", response_model=SystemConfigResponse, summary="创建系统配置")
async def create_config(
    config_data: SystemConfigCreate,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user)
):
    """
    创建系统配置
    
    Args:
        config_data: 配置创建数据
        db: 数据库会话
        current_admin: 当前管理员
        
    Returns:
        创建的配置信息
    """
    try:
        config = config_service.create_config(
            db, config_data, created_by=current_admin.id
        )
        return SystemConfigResponse(
            success=True,
            message="创建成功",
            data=config
        )
    except ValidationException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put("/configs/{config_id}", response_model=SystemConfigResponse, summary="更新系统配置")
async def update_config(
    config_id: int,
    update_data: SystemConfigUpdate,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user)
):
    """
    更新系统配置
    
    Args:
        config_id: 配置ID
        update_data: 更新数据
        db: 数据库会话
        current_admin: 当前管理员
        
    Returns:
        更新后的配置信息
    """
    try:
        config = config_service.update_config(db, config_id, update_data)
        return SystemConfigResponse(
            success=True,
            message="更新成功",
            data=config
        )
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ValidationException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/configs/{config_id}", response_model=BaseResponse, summary="删除系统配置")
async def delete_config(
    config_id: int,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user)
):
    """
    删除系统配置
    
    Args:
        config_id: 配置ID
        db: 数据库会话
        current_admin: 当前管理员
        
    Returns:
        操作结果
    """
    try:
        config_service.delete_config(db, config_id)
        return BaseResponse(
            success=True,
            message="删除成功"
        )
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


# ==================== 批次管理 ====================

@router.get("/batches", response_model=SuccessResponse, summary="获取批次列表")
async def get_admin_batch_list(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    status_filter: Optional[str] = Query(None, description="状态过滤"),
    start_date: Optional[str] = Query(None, description="开始日期"),
    end_date: Optional[str] = Query(None, description="结束日期"),
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user)
):
    """
    管理员获取批次列表
    
    Args:
        page: 页码
        size: 每页数量
        status_filter: 状态过滤
        start_date: 开始日期
        end_date: 结束日期
        db: 数据库会话
        current_admin: 当前管理员
        
    Returns:
        批次列表
    """
    try:
        from app.models.batch import DataBatch
        from sqlalchemy import and_
        from datetime import datetime
        
        # 计算偏移量
        offset = (page - 1) * size
        
        # 构建查询条件
        query_conditions = []
        
        # 日期过滤
        if start_date:
            try:
                start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                query_conditions.append(DataBatch.created_at >= start_dt)
            except ValueError:
                pass
                
        if end_date:
            try:
                end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                query_conditions.append(DataBatch.created_at < end_dt)
            except ValueError:
                pass
                
        # 状态过滤
        if status_filter:
            query_conditions.append(DataBatch.status == status_filter)
            
        # 构建查询
        if query_conditions:
            batch_query = db.query(DataBatch).filter(and_(*query_conditions))
        else:
            batch_query = db.query(DataBatch)
            
        # 获取总数
        total = batch_query.count()
        
        # 获取分页数据
        batches = batch_query.order_by(DataBatch.created_at.desc()).offset(offset).limit(size).all()
        
        # 构建响应数据
        items = []
        for batch in batches:
            # 更新批次统计信息
            batch.update_counts(db)
            
            items.append({
                "id": batch.id,
                "batch_id": batch.batch_id,
                "batch_name": batch.batch_name,
                "description": batch.description,
                "status": batch.status,
                "total_count": batch.total_count,
                "pending_count": batch.pending_count,
                "processing_count": batch.processing_count,
                "completed_count": batch.completed_count,
                "failed_count": batch.failed_count,
                "needread": batch.needread,
                "created_at": batch.created_at,
                "updated_at": batch.updated_at
            })
            
        return SuccessResponse(
            success=True,
            message="获取成功",
            data={
                "items": items,
                "pagination": {
                    "page": page,
                    "size": size,
                    "total": total,
                    "pages": (total + size - 1) // size
                }
            }
        )
        
    except Exception as e:
        logger.error(f"获取批次列表失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取批次列表失败"
        )


@router.get("/batches/{batch_id}", response_model=SuccessResponse, summary="获取批次详情")
async def get_admin_batch_detail(
    batch_id: str,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user)
):
    """
    管理员获取批次详情
    
    Args:
        batch_id: 批次ID
        db: 数据库会话
        current_admin: 当前管理员
        
    Returns:
        批次详情
    """
    try:
        from app.models.batch import DataBatch
        
        # 查询批次信息
        batch = db.query(DataBatch).filter(
            DataBatch.batch_id == batch_id
        ).first()
        
        if not batch:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="批次不存在"
            )
            
        # 更新批次统计信息
        batch.update_counts(db)
        
        return SuccessResponse(
            success=True,
            message="获取成功",
            data={
                "id": batch.id,
                "batch_id": batch.batch_id,
                "batch_name": batch.batch_name,
                "description": batch.description,
                "status": batch.status,
                "total_count": batch.total_count,
                "pending_count": batch.pending_count,
                "processing_count": batch.processing_count,
                "completed_count": batch.completed_count,
                "failed_count": batch.failed_count,
                "needread": batch.needread,
                "created_at": batch.created_at,
                "updated_at": batch.updated_at
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取批次详情失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取批次详情失败"
        )


@router.delete("/batches/{batch_id}", response_model=SuccessResponse, summary="删除批次")
async def delete_admin_batch(
    batch_id: str,
    force: bool = Query(False, description="是否强制删除"),
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user)
):
    """
    管理员删除批次
    
    Args:
        batch_id: 批次ID
        force: 是否强制删除
        db: 数据库会话
        current_admin: 当前管理员
        
    Returns:
        操作结果
    """
    try:
        from app.models.batch import DataBatch
        from app.models.data import DataUpload
        
        # 查询批次信息
        batch = db.query(DataBatch).filter(
            DataBatch.batch_id == batch_id
        ).first()
        
        if not batch:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="批次不存在"
            )
            
        # 检查批次状态
        if batch.status == 'processing' and not force:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="批次正在处理中，请使用强制删除或等待处理完成"
            )
            
        # 查询批次下的所有上传记录
        uploads = db.query(DataUpload).filter(
            DataUpload.batch_id == batch_id
        ).all()
        
        # 删除上传记录
        for upload in uploads:
            db.delete(upload)
            
        # 删除批次记录
        db.delete(batch)
        db.commit()
        
        return SuccessResponse(
            success=True,
            message="删除成功",
            data={"batch_id": batch_id}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除批次失败: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="删除批次失败"
        )


# ==================== 统计信息 ====================

@router.get("/stats", response_model=SuccessResponse[SystemStatsResponse], summary="获取系统统计信息")
async def get_system_stats(
    days: int = Query(30, ge=1, le=365, description="统计天数"),
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user)
):
    """
    获取系统统计信息
    
    Args:
        days: 统计天数
        db: 数据库会话
        current_admin: 当前管理员
        
    Returns:
        系统统计信息
    """
    stats = stats_service.get_system_stats(db, days=days)
    return SuccessResponse[SystemStatsResponse](
        success=True,
        message="获取成功",
        data=stats
    )