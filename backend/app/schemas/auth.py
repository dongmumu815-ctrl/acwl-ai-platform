#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
认证相关的Pydantic模式
"""

from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
from datetime import datetime


class UserLogin(BaseModel):
    """用户登录模式"""
    username: Optional[str] = Field(None, min_length=3, max_length=50, description="用户名")
    email: Optional[EmailStr] = Field(None, description="邮箱地址")
    password: str = Field(..., min_length=6, max_length=128, description="密码")
    
    @validator('password')
    def validate_username_or_email(cls, v, values):
        username = values.get('username')
        email = values.get('email')
        if not username and not email:
            raise ValueError('用户名或邮箱必须提供其中一个')
        return v


class UserRegister(BaseModel):
    """用户注册模式"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    email: EmailStr = Field(..., description="邮箱地址")
    password: str = Field(..., min_length=6, max_length=128, description="密码")
    confirm_password: str = Field(..., min_length=6, max_length=128, description="确认密码")
    
    @validator('confirm_password')
    def passwords_match(cls, v, values, **kwargs):
        if 'password' in values and v != values['password']:
            raise ValueError('密码不匹配')
        return v
    
    @validator('username')
    def username_alphanumeric(cls, v):
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('用户名只能包含字母、数字、下划线和连字符')
        return v


class UserResponse(BaseModel):
    """用户响应模式"""
    id: int
    username: str
    email: str
    role: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    """用户更新模式"""
    email: Optional[EmailStr] = None
    role: Optional[str] = Field(None, pattern=r'^(admin|user)$')
    
    @validator('role')
    def validate_role(cls, v):
        if v and v not in ['admin', 'user']:
            raise ValueError('角色必须是 admin 或 user')
        return v


class PasswordChange(BaseModel):
    """密码修改模式"""
    current_password: str = Field(..., min_length=6, max_length=128, description="当前密码")
    new_password: str = Field(..., min_length=6, max_length=128, description="新密码")
    confirm_new_password: str = Field(..., min_length=6, max_length=128, description="确认新密码")
    
    @validator('confirm_new_password')
    def passwords_match(cls, v, values, **kwargs):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('新密码不匹配')
        return v


class Token(BaseModel):
    """令牌响应模式"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # 过期时间（秒）


class LoginResponse(BaseModel):
    """登录响应模式"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # 过期时间（秒）
    user: UserResponse


class TokenData(BaseModel):
    """令牌数据模式"""
    user_id: Optional[int] = None
    username: Optional[str] = None
    scopes: list[str] = []