#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API相关Pydantic Schemas

定义自定义API和字段相关的请求和响应数据模型。

Author: System
Date: 2024
"""

from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field, field_validator, ConfigDict
from enum import Enum

from .base import BaseQueryParams, BaseListResponse


class HttpMethodEnum(str, Enum):
    """HTTP方法枚举"""
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"


class ResponseFormatEnum(str, Enum):
    """响应格式枚举"""
    JSON = "JSON"
    XML = "XML"
    CSV = "CSV"
    TEXT = "TEXT"


class FieldTypeEnum(str, Enum):
    """字段类型枚举"""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    DATE = "date"
    DATETIME = "datetime"
    TEXT = "text"
    EMAIL = "email"
    URL = "url"
    JSON = "json"
    FILE = "file"


class CustomApiBase(BaseModel):
    """
    自定义API基础模型
    
    包含API的基本信息字段
    """
    
    api_name: str = Field(..., min_length=1, max_length=100, description="API名称")
    api_code: str = Field(..., min_length=3, max_length=50, description="API代码")
    api_description: Optional[str] = Field(None, max_length=1000, description="API描述")
    http_method: HttpMethodEnum = Field(default=HttpMethodEnum.POST, description="HTTP方法")
    response_format: ResponseFormatEnum = Field(default=ResponseFormatEnum.JSON, description="响应格式")
    
    @field_validator('api_code')
    @classmethod
    def validate_api_code(cls, v):
        """验证API代码格式"""
        import re
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('API代码只能包含字母、数字、下划线和连字符')
        return v.lower()


class CustomApiCopy(BaseModel):
    """
    自定义API复制请求模型
    
    复制API到其他客户时的请求数据
    """
    
    target_customer_id: int = Field(..., description="目标客户ID")
    new_api_code: str = Field(..., min_length=3, max_length=50, description="新的API代码")
    new_api_name: Optional[str] = Field(None, min_length=1, max_length=100, description="新的API名称（可选）")
    
    @field_validator('new_api_code')
    @classmethod
    def validate_api_code(cls, v):
        """验证API代码格式"""
        import re
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('API代码只能包含字母、数字、下划线和连字符')
        return v.lower()


class CustomApiCreate(CustomApiBase):
    """
    自定义API创建请求模型
    
    创建新API时的请求数据
    """
    
    customer_id: int = Field(..., description="客户ID")
    status: bool = Field(default=True, description="状态：True-开放，False-停用")
    rate_limit: Optional[int] = Field(None, ge=1, le=10000, description="频率限制（每分钟）")
    require_authentication: bool = Field(default=True, description="是否需要认证")
    link_read_id: Optional[Union[str, int]] = Field(None, description="链接其他系统的ID")
    
    @field_validator('link_read_id')
    @classmethod
    def validate_link_read_id(cls, v):
        """验证并转换link_read_id为字符串"""
        if v is not None:
            # 将数字转换为字符串，限制长度为50字符
            str_value = str(v)
            if len(str_value) > 50:
                raise ValueError('link_read_id长度不能超过50字符')
            return str_value
        return v


class CustomApiUpdate(BaseModel):
    """
    自定义API更新请求模型
    
    更新API信息时的请求数据
    """
    
    api_name: Optional[str] = Field(None, min_length=1, max_length=100, description="API名称")
    api_code: Optional[str] = Field(None, min_length=1, max_length=50, description="API代码")
    api_description: Optional[str] = Field(None, max_length=1000, description="API描述")
    http_method: Optional[HttpMethodEnum] = Field(None, description="HTTP方法")
    response_format: Optional[ResponseFormatEnum] = Field(None, description="响应格式")
    status: Optional[bool] = Field(None, description="状态")
    rate_limit: Optional[int] = Field(None, ge=1, le=10000, description="频率限制")
    require_authentication: Optional[bool] = Field(None, description="是否需要认证")
    customer_id: Optional[int] = Field(None, description="客户ID（仅管理员可更改）")
    link_read_id: Optional[Union[str, int]] = Field(None, description="链接其他系统的ID")


class CustomApiResponse(CustomApiBase):
    """
    自定义API响应模型
    
    返回API信息时的数据结构
    """
    
    id: int = Field(description="API ID")
    customer_id: int = Field(description="客户ID")
    status: bool = Field(description="状态")
    rate_limit: Optional[int] = Field(description="频率限制")
    require_authentication: bool = Field(description="是否需要认证")
    link_read_id: Optional[str] = Field(None, description="链接其他系统的ID")
    
    # 统计信息
    total_calls: int = Field(default=0, description="总调用次数")
    last_called_at: Optional[datetime] = Field(None, description="最后调用时间")
    
    # URL信息
    api_url: str = Field(description="API URL路径")
    
    # 时间戳
    created_at: datetime = Field(description="创建时间")
    updated_at: datetime = Field(description="更新时间")
    
    model_config = ConfigDict(from_attributes=True)


class ApiQuery(BaseQueryParams):
    """
    API查询请求模型
    
    查询API列表时的参数
    """
    
    customer_id: Optional[int] = Field(None, description="客户ID")
    status: Optional[bool] = Field(None, description="状态")
    http_method: Optional[HttpMethodEnum] = Field(None, description="HTTP方法")
    api_name: Optional[str] = Field(None, description="API名称（模糊搜索）")
    
    # 日期范围
    created_after: Optional[datetime] = Field(None, description="创建时间起始")
    created_before: Optional[datetime] = Field(None, description="创建时间结束")


# ==================== API字段相关Schema ====================

class ApiFieldBase(BaseModel):
    """
    API字段基础模型
    
    包含字段的基本信息
    """
    
    field_name: str = Field(..., min_length=1, max_length=50, description="字段名称")
    field_label: Optional[str] = Field(None, min_length=1, max_length=100, description="字段标签")
    field_type: FieldTypeEnum = Field(..., description="字段类型")
    is_required: bool = Field(default=False, description="是否必填")
    default_value: Optional[str] = Field(None, description="默认值")
    max_length: Optional[int] = Field(None, description="最大长度")
    min_length: Optional[int] = Field(None, description="最小长度")
    max_value: Optional[float] = Field(None, description="最大值")
    min_value: Optional[float] = Field(None, description="最小值")
    allowed_values: Optional[str] = Field(None, description="允许的值列表")
    validation_regex: Optional[str] = Field(None, max_length=500, description="验证正则表达式")
    validation_message: Optional[str] = Field(None, max_length=200, description="验证失败提示")
    sort_order: int = Field(default=0, description="排序顺序")
    description: Optional[str] = Field(None, description="字段描述")
    
    @field_validator('field_label')
    @classmethod
    def validate_field_label(cls, v, info):
        """
        验证字段标签，如果为空则使用字段名称作为默认值
        
        Args:
            v: 字段标签值
            info: 验证上下文信息
            
        Returns:
            str: 验证后的字段标签
        """
        if not v and info.data.get('field_name'):
            return info.data['field_name']
        return v


class ApiFieldCreate(ApiFieldBase):
    """
    API字段创建请求模型
    
    创建新字段时的请求数据
    """
    pass


class ApiFieldUpdate(BaseModel):
    """
    API字段更新请求模型
    
    更新字段时的请求数据，所有字段都是可选的
    """
    
    field_name: Optional[str] = Field(None, min_length=1, max_length=50, description="字段名称")
    field_label: Optional[str] = Field(None, max_length=100, description="字段标签")
    field_type: Optional[FieldTypeEnum] = Field(None, description="字段类型")
    is_required: Optional[bool] = Field(None, description="是否必填")
    default_value: Optional[str] = Field(None, description="默认值")
    max_length: Optional[int] = Field(None, description="最大长度")
    min_length: Optional[int] = Field(None, description="最小长度")
    max_value: Optional[float] = Field(None, description="最大值")
    min_value: Optional[float] = Field(None, description="最小值")
    allowed_values: Optional[str] = Field(None, description="允许的值列表")
    validation_regex: Optional[str] = Field(None, max_length=500, description="验证正则表达式")
    validation_message: Optional[str] = Field(None, max_length=200, description="验证失败提示")
    sort_order: Optional[int] = Field(None, description="排序顺序")
    description: Optional[str] = Field(None, description="字段描述")


class ApiFieldResponse(ApiFieldBase):
    """
    API字段响应模型
    
    返回字段信息时的数据模型
    """
    
    id: int = Field(..., description="字段ID")
    api_id: int = Field(..., description="API ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    model_config = ConfigDict(from_attributes=True)