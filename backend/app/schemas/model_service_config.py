#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模型服务配置相关的Pydantic Schema
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal
from enum import Enum

from app.schemas.common import PaginatedResponse
from app.models.model_service_config import ModelServiceProvider


class ModelServiceConfigBase(BaseModel):
    """模型服务配置基础Schema"""
    name: str = Field(..., min_length=1, max_length=100, description="服务配置名称")
    display_name: str = Field(..., min_length=1, max_length=100, description="显示名称")
    provider: ModelServiceProvider = Field(..., description="服务提供商")
    model_type: Optional[str] = Field("chat", description="模型类型")
    model_name: str = Field(..., min_length=1, max_length=100, description="模型名称")
    api_endpoint: Optional[str] = Field(None, max_length=500, description="API端点URL")
    api_key: Optional[str] = Field(None, max_length=500, description="API密钥")
    api_version: Optional[str] = Field(None, max_length=20, description="API版本")
    max_tokens: Optional[int] = Field(4096, ge=1, le=100000, description="最大token数")
    temperature: Optional[Decimal] = Field(0.7, ge=0.0, le=2.0, description="温度参数")
    top_p: Optional[Decimal] = Field(0.9, ge=0.0, le=1.0, description="top_p参数")
    frequency_penalty: Optional[Decimal] = Field(0.0, ge=-2.0, le=2.0, description="频率惩罚")
    presence_penalty: Optional[Decimal] = Field(0.0, ge=-2.0, le=2.0, description="存在惩罚")
    timeout: Optional[int] = Field(30, ge=1, le=300, description="请求超时时间(秒)")
    retry_count: Optional[int] = Field(3, ge=0, le=10, description="重试次数")
    extra_config: Optional[str] = Field(None, description="额外配置(JSON格式)")
    is_active: Optional[bool] = Field(True, description="是否启用")
    is_default: Optional[bool] = Field(False, description="是否为默认配置")
    description: Optional[str] = Field(None, description="配置描述")
    
    @validator('name')
    def validate_name(cls, v):
        """验证配置名称格式"""
        if not v.replace('-', '').replace('_', '').replace('.', '').isalnum():
            raise ValueError('配置名称只能包含字母、数字、连字符、下划线和点')
        return v
    
    @validator('api_endpoint')
    def validate_api_endpoint(cls, v):
        """验证API端点URL格式"""
        if v and not (v.startswith('http://') or v.startswith('https://')):
            raise ValueError('API端点必须是有效的HTTP或HTTPS URL')
        return v


class ModelServiceConfigCreate(ModelServiceConfigBase):
    """创建模型服务配置Schema"""
    pass


class ModelServiceConfigUpdate(BaseModel):
    """更新模型服务配置Schema"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="服务配置名称")
    display_name: Optional[str] = Field(None, min_length=1, max_length=100, description="显示名称")
    provider: Optional[ModelServiceProvider] = Field(None, description="服务提供商")
    model_type: Optional[str] = Field(None, description="模型类型")
    model_name: Optional[str] = Field(None, min_length=1, max_length=100, description="模型名称")
    api_endpoint: Optional[str] = Field(None, max_length=500, description="API端点URL")
    api_key: Optional[str] = Field(None, max_length=500, description="API密钥")
    api_version: Optional[str] = Field(None, max_length=20, description="API版本")
    max_tokens: Optional[int] = Field(None, ge=1, le=100000, description="最大token数")
    temperature: Optional[Decimal] = Field(None, ge=0.0, le=2.0, description="温度参数")
    top_p: Optional[Decimal] = Field(None, ge=0.0, le=1.0, description="top_p参数")
    frequency_penalty: Optional[Decimal] = Field(None, ge=-2.0, le=2.0, description="频率惩罚")
    presence_penalty: Optional[Decimal] = Field(None, ge=-2.0, le=2.0, description="存在惩罚")
    timeout: Optional[int] = Field(None, ge=1, le=300, description="请求超时时间(秒)")
    retry_count: Optional[int] = Field(None, ge=0, le=10, description="重试次数")
    extra_config: Optional[str] = Field(None, description="额外配置(JSON格式)")
    is_active: Optional[bool] = Field(None, description="是否启用")
    is_default: Optional[bool] = Field(None, description="是否为默认配置")
    description: Optional[str] = Field(None, description="配置描述")
    
    @validator('api_endpoint')
    def validate_api_endpoint(cls, v):
        """验证API端点URL格式"""
        if v and not (v.startswith('http://') or v.startswith('https://')):
            raise ValueError('API端点必须是有效的HTTP或HTTPS URL')
        return v


class ModelServiceConfigInDB(ModelServiceConfigBase):
    """数据库中的模型服务配置Schema"""
    model_config = {"from_attributes": True}
    
    id: int
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime


class ModelServiceConfigResponse(ModelServiceConfigInDB):
    """模型服务配置响应Schema"""
    provider_display_name: Optional[str] = Field(None, description="提供商显示名称")
    
    @validator('api_key', pre=True)
    def mask_api_key(cls, v):
        """隐藏API密钥的敏感信息"""
        if v and len(v) > 8:
            return v[:4] + '*' * (len(v) - 8) + v[-4:]
        return v


class ModelServiceConfigListResponse(PaginatedResponse[ModelServiceConfigResponse]):
    """模型服务配置列表响应Schema"""
    pass


class ModelServiceConfigForAgent(BaseModel):
    """用于Agent配置的模型服务配置Schema"""
    label: str = Field(..., description="显示标签")
    value: str = Field(..., description="配置值")
    model_id: int = Field(..., description="模型配置ID")
    description: Optional[str] = Field(None, description="描述")
    provider: str = Field(..., description="服务提供商")
    provider_display_name: str = Field(..., description="提供商显示名称")
    model_name: str = Field(..., description="模型名称")
    is_default: bool = Field(False, description="是否为默认配置")


class ModelServiceConfigStats(BaseModel):
    """
    模型服务配置统计信息
    """
    total_count: int = Field(..., description="总配置数")
    active_count: int = Field(..., description="激活配置数")
    inactive_count: int = Field(..., description="未激活配置数")
    provider_stats: Dict[str, int] = Field(..., description="按提供商统计")
    
    class Config:
        from_attributes = True


class ModelServiceConfigTest(BaseModel):
    """
    模型服务配置测试请求
    支持两种模式：
    1. 使用config_id测试已保存的配置
    2. 直接传递配置参数测试新配置
    """
    # 模式1：使用已保存的配置
    config_id: Optional[int] = Field(None, description="配置ID")
    
    # 模式2：直接传递配置参数
    provider: Optional[str] = Field(None, description="服务提供商")
    model_name: Optional[str] = Field(None, description="模型名称")
    api_endpoint: Optional[str] = Field(None, description="API端点URL")
    api_key: Optional[str] = Field(None, description="API密钥")
    max_tokens: Optional[int] = Field(None, description="最大token数")
    temperature: Optional[float] = Field(None, description="温度参数")
    timeout: Optional[int] = Field(None, description="请求超时时间(秒)")
    headers: Optional[List[Dict[str, str]]] = Field(None, description="请求头")
    extra_params: Optional[Dict[str, Any]] = Field(None, description="额外参数")
    
    # 通用字段
    test_message: str = Field(
        default="Hello, this is a test message.",
        description="测试消息"
    )
    
    class Config:
        from_attributes = True


class ModelServiceConfigTestResult(BaseModel):
    """
    模型服务配置测试结果
    """
    success: bool = Field(..., description="测试是否成功")
    response_time: Optional[float] = Field(None, description="响应时间(秒)")
    response_content: Optional[str] = Field(None, description="响应内容")
    error_message: Optional[str] = Field(None, description="错误信息")
    status_code: Optional[int] = Field(None, description="HTTP状态码")
    
    class Config:
        from_attributes = True