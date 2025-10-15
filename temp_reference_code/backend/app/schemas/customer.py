#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
客户相关Pydantic Schemas

定义客户管理相关的API请求和响应数据模型。

Author: System
Date: 2024
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, EmailStr, validator, ConfigDict

from .base import BaseCreateSchema, BaseUpdateSchema, BaseQuerySchema


class CustomerBase(BaseModel):
    """
    客户基础模型
    
    客户的基本字段定义
    """
    
    name: str = Field(..., min_length=1, max_length=100, description="客户名称")
    email: EmailStr = Field(..., description="客户邮箱")
    phone: Optional[str] = Field(None, max_length=20, description="联系电话")
    company: Optional[str] = Field(None, max_length=200, description="公司名称")
    link_read_id: Optional[str] = Field(None, max_length=50, description="关联系统ID")


class CustomerCreate(CustomerBase, BaseCreateSchema):
    """
    客户创建请求模型
    
    创建新客户时的请求数据
    """
    
    # 可选的初始配置
    status: str = Field(default="active", description="状态：active-启用，inactive-禁用")
    rate_limit: Optional[int] = Field(default=None, ge=1, le=10000, description="频率限制（每分钟）")
    max_apis: Optional[int] = Field(default=None, ge=1, le=100, description="最大API数量")
    
    @validator('phone')
    def validate_phone(cls, v):
        if v and not v.replace('-', '').replace(' ', '').replace('+', '').isdigit():
            raise ValueError('电话号码格式不正确')
        return v


class CustomerUpdate(BaseUpdateSchema):
    """
    客户更新请求模型
    
    更新客户信息时的请求数据
    """
    
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="客户名称")
    email: Optional[EmailStr] = Field(None, description="客户邮箱")
    phone: Optional[str] = Field(None, max_length=20, description="联系电话")
    company: Optional[str] = Field(None, max_length=200, description="公司名称")
    link_read_id: Optional[str] = Field(None, max_length=50, description="关联系统ID")
    status: Optional[str] = Field(None, description="状态：active-启用，inactive-禁用")
    rate_limit: Optional[int] = Field(None, ge=1, le=10000, description="频率限制（每分钟）")
    max_apis: Optional[int] = Field(None, ge=1, le=100, description="最大API数量")
    
    @validator('phone')
    def validate_phone(cls, v):
        if v and not v.replace('-', '').replace(' ', '').replace('+', '').isdigit():
            raise ValueError('电话号码格式不正确')
        return v


class CustomerResponse(CustomerBase):
    """
    客户响应模型
    
    返回客户信息时的数据结构
    """
    
    id: int = Field(description="客户ID")
    app_id: str = Field(description="应用ID")
    status: str = Field(description="状态")
    rate_limit: Optional[int] = Field(description="频率限制（每分钟）")
    max_apis: Optional[int] = Field(description="最大API数量")
    
    # 统计信息
    api_count: int = Field(default=0, description="API数量")
    total_calls: int = Field(default=0, description="总调用次数")
    last_called_at: Optional[datetime] = Field(None, description="最后调用时间")
    
    # 时间戳
    created_at: datetime = Field(description="创建时间")
    updated_at: datetime = Field(description="更新时间")
    
    model_config = ConfigDict(from_attributes=True)


class CustomerDetailResponse(CustomerResponse):
    """
    客户详细信息响应模型
    
    包含更多详细信息的客户数据
    """
    
    app_secret: str = Field(description="应用密钥")
    
    # 会话统计
    active_sessions: int = Field(default=0, description="活跃会话数")
    
    # 使用统计
    today_calls: int = Field(default=0, description="今日调用次数")
    this_month_calls: int = Field(default=0, description="本月调用次数")
    
    # API列表（可选）
    apis: Optional[List[dict]] = Field(None, description="API列表")


class CustomerQuery(BaseQuerySchema):
    """
    客户查询请求模型
    
    查询客户列表时的参数
    """
    
    name: Optional[str] = Field(None, description="客户名称（模糊搜索）")
    email: Optional[str] = Field(None, description="客户邮箱（模糊搜索）")
    company: Optional[str] = Field(None, description="公司名称（模糊搜索）")
    status: Optional[str] = Field(None, description="状态")
    link_read_id: Optional[str] = Field(None, description="关联系统ID")
    
    # 日期范围
    created_after: Optional[datetime] = Field(None, description="创建时间起始")
    created_before: Optional[datetime] = Field(None, description="创建时间结束")


class CustomerLoginRequest(BaseModel):
    """
    客户登录请求模型
    
    客户系统登录时的请求数据
    """
    
    app_id: str = Field(..., min_length=1, description="应用ID")
    app_secret: str = Field(..., min_length=1, description="应用密钥")
    
    # 可选的客户端信息
    client_info: Optional[dict] = Field(None, description="客户端信息")


class CustomerLoginResponse(BaseModel):
    """
    客户登录响应模型
    
    登录成功后的响应数据
    """
    
    access_token: str = Field(description="访问令牌")
    token_type: str = Field(default="bearer", description="令牌类型")
    expires_in: int = Field(description="过期时间（秒）")
    
    # 客户信息
    customer: CustomerResponse = Field(description="客户信息")
    
    # 会话信息
    session_id: str = Field(description="会话ID")


class CustomerSessionResponse(BaseModel):
    """
    客户会话响应模型
    
    客户会话信息
    """
    
    id: int = Field(description="会话ID")
    customer_id: int = Field(description="客户ID")
    session_token: str = Field(description="会话令牌")
    is_active: bool = Field(description="是否活跃")
    
    # 会话详情
    client_ip: Optional[str] = Field(None, description="客户端IP")
    user_agent: Optional[str] = Field(None, description="用户代理")
    client_info: Optional[dict] = Field(None, description="客户端信息")
    
    # 时间信息
    created_at: datetime = Field(description="创建时间")
    last_accessed_at: datetime = Field(description="最后访问时间")
    expires_at: datetime = Field(description="过期时间")
    
    model_config = ConfigDict(from_attributes=True)


class CustomerStatsResponse(BaseModel):
    """
    客户统计信息响应模型
    
    客户的各种统计数据
    """
    
    customer_id: int = Field(description="客户ID")
    
    # API统计
    total_apis: int = Field(description="总API数量")
    active_apis: int = Field(description="活跃API数量")
    
    # 调用统计
    total_calls: int = Field(description="总调用次数")
    success_calls: int = Field(description="成功调用次数")
    failed_calls: int = Field(description="失败调用次数")
    success_rate: float = Field(description="成功率")
    
    # 时间统计
    today_calls: int = Field(description="今日调用次数")
    this_week_calls: int = Field(description="本周调用次数")
    this_month_calls: int = Field(description="本月调用次数")
    
    # 数据统计
    total_uploads: int = Field(description="总上传次数")
    total_records: int = Field(description="总记录数")
    total_data_size: int = Field(description="总数据大小（字节）")
    
    # 时间范围
    stats_period: str = Field(description="统计周期")
    generated_at: datetime = Field(default_factory=datetime.utcnow, description="生成时间")


class CustomerSecretResetRequest(BaseModel):
    """
    客户密钥重置请求模型
    
    重置客户应用密钥时的请求
    """
    
    reason: Optional[str] = Field(None, max_length=200, description="重置原因")


class CustomerSecretResetResponse(BaseModel):
    """
    客户密钥重置响应模型
    
    密钥重置成功后的响应
    """
    
    app_secret: str = Field(description="新的应用密钥")
    reset_at: datetime = Field(default_factory=datetime.utcnow, description="重置时间")
    
    # 警告信息
    warning: str = Field(
        default="请妥善保管新密钥，旧密钥将在24小时后失效",
        description="警告信息"
    )


class CustomerBatchUpdateRequest(BaseModel):
    """
    客户批量更新请求模型
    
    批量更新客户状态时的请求
    """
    
    customer_ids: List[int] = Field(..., min_items=1, max_items=100, description="客户ID列表")
    updates: dict = Field(..., description="更新字段")
    
    @validator('updates')
    def validate_updates(cls, v):
        allowed_fields = {'is_active', 'rate_limit', 'max_apis', 'description'}
        if not set(v.keys()).issubset(allowed_fields):
            raise ValueError(f'只允许更新以下字段: {allowed_fields}')
        return v


if __name__ == "__main__":
    # 测试客户schemas
    print("客户Schemas定义完成")
    
    # 测试客户创建请求
    customer_data = {
        "company_name": "测试公司",
        "contact_name": "张三",
        "contact_email": "zhangsan@test.com",
        "contact_phone": "13800138000",
        "description": "这是一个测试客户"
    }
    
    try:
        customer_create = CustomerCreate(**customer_data)
        print(f"客户创建请求验证成功: {customer_create.company_name}")
    except Exception as e:
        print(f"客户创建请求验证失败: {e}")
    
    print("\n客户Schemas测试完成")