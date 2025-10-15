#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统管理相关Pydantic Schemas

定义管理员用户和系统配置相关的数据模型。

Author: System
Date: 2024
"""

from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field, EmailStr, validator, ConfigDict, computed_field
from enum import Enum

from .base import BaseCreateSchema, BaseUpdateSchema, BaseQuerySchema


class AdminRoleEnum(str, Enum):
    """
    管理员角色枚举
    """
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    OPERATOR = "operator"
    VIEWER = "viewer"


class AdminStatusEnum(str, Enum):
    """
    管理员状态枚举
    """
    ACTIVE = "active"
    INACTIVE = "inactive"
    LOCKED = "locked"
    SUSPENDED = "suspended"


class ConfigTypeEnum(str, Enum):
    """
    配置类型枚举
    """
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    JSON = "json"
    LIST = "list"


class AdminUserBase(BaseModel):
    """
    管理员用户基础模型
    
    包含管理员的基本信息
    """
    
    username: str = Field(min_length=3, max_length=50, description="用户名")
    email: EmailStr = Field(description="邮箱地址")
    real_name: str = Field(min_length=2, max_length=100, description="真实姓名")
    phone: Optional[str] = Field(None, max_length=20, description="手机号码")
    department: Optional[str] = Field(None, max_length=100, description="部门")
    description: Optional[str] = Field(None, max_length=500, description="描述信息")
    
    @validator('username')
    def validate_username(cls, v):
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('用户名只能包含字母、数字、下划线和连字符')
        return v
    
    @validator('phone')
    def validate_phone(cls, v):
        if v and not v.replace('+', '').replace('-', '').replace(' ', '').isdigit():
            raise ValueError('手机号码格式不正确')
        return v


class AdminUserCreate(AdminUserBase, BaseCreateSchema):
    """
    创建管理员用户请求模型
    
    创建新管理员时的请求数据
    """
    
    password: str = Field(min_length=8, max_length=128, description="密码")
    confirm_password: str = Field(description="确认密码")
    is_superuser: bool = Field(default=False, description="是否超级管理员")
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('密码长度至少8位')
        if not any(c.isupper() for c in v):
            raise ValueError('密码必须包含至少一个大写字母')
        if not any(c.islower() for c in v):
            raise ValueError('密码必须包含至少一个小写字母')
        if not any(c.isdigit() for c in v):
            raise ValueError('密码必须包含至少一个数字')
        return v
    
    @validator('confirm_password')
    def validate_confirm_password(cls, v, values):
        if 'password' in values and v != values['password']:
            raise ValueError('两次输入的密码不一致')
        return v


class AdminUserUpdate(BaseUpdateSchema):
    """
    更新管理员用户请求模型
    
    更新管理员信息时的请求数据
    """
    
    email: Optional[EmailStr] = Field(None, description="邮箱地址")
    real_name: Optional[str] = Field(None, min_length=2, max_length=100, description="真实姓名")
    is_superuser: Optional[bool] = Field(None, description="是否超级管理员")
    phone: Optional[str] = Field(None, max_length=20, description="手机号码")
    department: Optional[str] = Field(None, max_length=100, description="部门")
    description: Optional[str] = Field(None, max_length=500, description="描述信息")
    status: Optional[AdminStatusEnum] = Field(None, description="账户状态")
    
    @validator('phone')
    def validate_phone(cls, v):
        if v and not v.replace('+', '').replace('-', '').replace(' ', '').isdigit():
            raise ValueError('手机号码格式不正确')
        return v


class AdminUserResponse(AdminUserBase):
    """
    管理员用户响应模型
    
    返回管理员用户信息
    """
    
    id: int = Field(description="管理员ID")
    is_active: bool = Field(description="是否激活")
    is_superuser: bool = Field(description="是否超级管理员")
    locked_until: Optional[datetime] = Field(None, description="锁定到期时间")
    
    # 登录信息
    last_login_at: Optional[datetime] = Field(None, description="最后登录时间")
    last_login_ip: Optional[str] = Field(None, description="最后登录IP")
    login_count: int = Field(description="登录次数")
    
    # 时间戳
    created_at: datetime = Field(description="创建时间")
    updated_at: datetime = Field(description="更新时间")
    
    @computed_field
    @property
    def is_locked(self) -> bool:
        """
        计算是否锁定
        
        Returns:
            bool: 是否被锁定
        """
        if not self.locked_until:
            return False
        return datetime.utcnow() < self.locked_until
    
    @computed_field
    @property
    def role(self) -> AdminRoleEnum:
        """
        计算管理员角色
        
        Returns:
            AdminRoleEnum: 角色枚举
        """
        if self.is_superuser:
            return AdminRoleEnum.SUPER_ADMIN
        return AdminRoleEnum.ADMIN
    
    @computed_field
    @property
    def status(self) -> AdminStatusEnum:
        """
        计算账户状态
        
        Returns:
            AdminStatusEnum: 状态枚举
        """
        if not self.is_active:
            return AdminStatusEnum.INACTIVE
        elif self.is_locked:
            return AdminStatusEnum.LOCKED
        else:
            return AdminStatusEnum.ACTIVE
    
    model_config = ConfigDict(from_attributes=True)


class AdminUserDetailResponse(AdminUserResponse):
    """
    管理员用户详细信息响应模型
    
    包含完整管理员信息
    """
    
    # 安全信息
    failed_login_count: int = Field(description="失败登录次数")
    locked_at: Optional[datetime] = Field(None, description="锁定时间")
    password_changed_at: Optional[datetime] = Field(None, description="密码修改时间")
    
    # 权限信息
    permissions: List[str] = Field(default_factory=list, description="权限列表")
    
    # 操作记录
    last_activity_at: Optional[datetime] = Field(None, description="最后活动时间")
    last_password_change: Optional[datetime] = Field(None, description="最后密码修改时间")


class AdminUserQuery(BaseQuerySchema):
    """
    管理员用户查询请求模型
    
    查询管理员用户时的参数
    """
    
    username: Optional[str] = Field(None, description="用户名（模糊匹配）")
    email: Optional[str] = Field(None, description="邮箱（模糊匹配）")
    real_name: Optional[str] = Field(None, description="姓名（模糊匹配）")
    role: Optional[AdminRoleEnum] = Field(None, description="角色")
    status: Optional[AdminStatusEnum] = Field(None, description="状态")
    department: Optional[str] = Field(None, description="部门")
    
    # 状态过滤
    active_only: Optional[bool] = Field(None, description="只显示激活用户")
    locked_only: Optional[bool] = Field(None, description="只显示锁定用户")
    
    # 日期范围
    created_after: Optional[datetime] = Field(None, description="创建时间之后")
    created_before: Optional[datetime] = Field(None, description="创建时间之前")
    last_login_after: Optional[datetime] = Field(None, description="最后登录时间之后")
    last_login_before: Optional[datetime] = Field(None, description="最后登录时间之前")


class AdminLoginRequest(BaseModel):
    """
    管理员登录请求模型
    
    管理员登录时的请求数据
    """
    
    username: str = Field(description="用户名或邮箱")
    password: str = Field(description="密码")
    remember_me: bool = Field(default=False, description="记住登录状态")
    captcha: Optional[str] = Field(None, description="验证码")


class AdminLoginResponse(BaseModel):
    """
    管理员登录响应模型
    
    管理员登录成功后的响应数据
    """
    
    access_token: str = Field(description="访问令牌")
    refresh_token: str = Field(description="刷新令牌")
    token_type: str = Field(default="bearer", description="令牌类型")
    expires_in: int = Field(description="令牌有效期（秒）")
    
    # 用户信息
    user_info: AdminUserResponse = Field(description="用户信息")
    
    # 权限信息
    permissions: List[str] = Field(description="权限列表")
    
    # 登录信息
    login_time: datetime = Field(default_factory=datetime.utcnow, description="登录时间")
    session_id: str = Field(description="会话ID")


class PasswordChangeRequest(BaseModel):
    """
    密码修改请求模型
    
    修改密码时的请求数据
    """
    
    current_password: str = Field(description="当前密码")
    new_password: str = Field(min_length=8, max_length=128, description="新密码")
    confirm_password: str = Field(description="确认新密码")
    
    @validator('new_password')
    def validate_new_password(cls, v):
        if len(v) < 8:
            raise ValueError('密码长度至少8位')
        if not any(c.isupper() for c in v):
            raise ValueError('密码必须包含至少一个大写字母')
        if not any(c.islower() for c in v):
            raise ValueError('密码必须包含至少一个小写字母')
        if not any(c.isdigit() for c in v):
            raise ValueError('密码必须包含至少一个数字')
        return v
    
    @validator('confirm_password')
    def validate_confirm_password(cls, v, values):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('两次输入的密码不一致')
        return v


class PasswordResetRequest(BaseModel):
    """
    密码重置请求模型
    
    重置密码时的请求数据
    """
    
    email: EmailStr = Field(description="邮箱地址")
    captcha: Optional[str] = Field(None, description="验证码")


class SystemConfigBase(BaseModel):
    """
    系统配置基础模型
    
    包含系统配置的基本信息
    """
    
    key: str = Field(min_length=1, max_length=100, description="配置键")
    value: str = Field(description="配置值")
    config_type: ConfigTypeEnum = Field(description="配置类型")
    category: str = Field(max_length=50, description="配置分类")
    description: Optional[str] = Field(None, max_length=500, description="配置描述")
    is_public: bool = Field(default=False, description="是否公开（前端可访问）")
    is_required: bool = Field(default=False, description="是否必需")
    
    @validator('key')
    def validate_key(cls, v):
        if not v.replace('_', '').replace('-', '').replace('.', '').isalnum():
            raise ValueError('配置键只能包含字母、数字、下划线、连字符和点号')
        return v


class SystemConfigCreate(SystemConfigBase, BaseCreateSchema):
    """
    创建系统配置请求模型
    
    创建新配置时的请求数据
    """
    
    default_value: Optional[str] = Field(None, description="默认值")
    validation_rule: Optional[str] = Field(None, description="验证规则（正则表达式）")
    allowed_values: Optional[List[str]] = Field(None, description="允许的值列表")


class SystemConfigUpdate(BaseUpdateSchema):
    """
    更新系统配置请求模型
    
    更新配置时的请求数据
    """
    
    value: Optional[str] = Field(None, description="配置值")
    description: Optional[str] = Field(None, max_length=500, description="配置描述")
    is_public: Optional[bool] = Field(None, description="是否公开")
    is_required: Optional[bool] = Field(None, description="是否必需")
    validation_rule: Optional[str] = Field(None, description="验证规则")
    allowed_values: Optional[List[str]] = Field(None, description="允许的值列表")


class SystemConfigResponse(SystemConfigBase):
    """
    系统配置响应模型
    
    返回系统配置信息
    """
    
    id: int = Field(description="配置ID")
    default_value: Optional[str] = Field(None, description="默认值")
    validation_rule: Optional[str] = Field(None, description="验证规则")
    allowed_values: Optional[List[str]] = Field(None, description="允许的值列表")
    
    # 状态信息
    is_active: bool = Field(description="是否激活")
    is_system: bool = Field(description="是否系统配置")
    
    # 时间戳
    created_at: datetime = Field(description="创建时间")
    updated_at: datetime = Field(description="更新时间")
    
    model_config = ConfigDict(from_attributes=True)


class SystemConfigQuery(BaseQuerySchema):
    """
    系统配置查询请求模型
    
    查询系统配置时的参数
    """
    
    key: Optional[str] = Field(None, description="配置键（模糊匹配）")
    category: Optional[str] = Field(None, description="配置分类")
    config_type: Optional[ConfigTypeEnum] = Field(None, description="配置类型")
    keyword: Optional[str] = Field(None, description="搜索关键词（配置键或描述）")
    
    # 状态过滤
    public_only: Optional[bool] = Field(None, description="只显示公开配置")
    required_only: Optional[bool] = Field(None, description="只显示必需配置")
    active_only: Optional[bool] = Field(None, description="只显示激活配置")
    system_only: Optional[bool] = Field(None, description="只显示系统配置")


class ConfigBatchUpdateRequest(BaseModel):
    """
    配置批量更新请求模型
    
    批量更新配置时的请求数据
    """
    
    configs: List[Dict[str, Union[str, int, float, bool]]] = Field(
        description="配置列表，格式：[{\"key\": \"config_key\", \"value\": \"config_value\"}]"
    )
    
    @validator('configs')
    def validate_configs(cls, v):
        if not v:
            raise ValueError('配置列表不能为空')
        
        for config in v:
            if 'key' not in config or 'value' not in config:
                raise ValueError('每个配置必须包含key和value字段')
        
        return v


class SystemStatsResponse(BaseModel):
    """
    系统统计响应模型
    
    系统运行状态的统计数据
    """
    
    # 用户统计
    total_customers: int = Field(description="总客户数")
    active_customers: int = Field(description="活跃客户数")
    total_admins: int = Field(description="总管理员数")
    active_admins: int = Field(description="活跃管理员数")
    
    # API统计
    total_apis: int = Field(description="总API数")
    active_apis: int = Field(description="活跃API数")
    
    # 调用统计
    total_api_calls: int = Field(description="总API调用次数")
    today_api_calls: int = Field(description="今日API调用次数")
    
    # 系统信息
    system_uptime: str = Field(description="系统运行时间")
    database_size: str = Field(description="数据库大小")
    
    # 生成时间
    generated_at: datetime = Field(default_factory=datetime.utcnow, description="生成时间")


class SystemHealthResponse(BaseModel):
    """
    系统健康检查响应模型
    
    系统各组件的健康状态
    """
    
    status: str = Field(description="整体状态：healthy, warning, error")
    
    # 组件状态
    database: Dict[str, Any] = Field(description="数据库状态")
    redis: Dict[str, Any] = Field(description="Redis状态")
    storage: Dict[str, Any] = Field(description="存储状态")
    
    # 性能指标
    response_time: float = Field(description="响应时间（毫秒）")
    memory_usage: float = Field(description="内存使用率")
    cpu_usage: float = Field(description="CPU使用率")
    
    # 检查时间
    checked_at: datetime = Field(default_factory=datetime.utcnow, description="检查时间")


class AuditLogResponse(BaseModel):
    """
    审计日志响应模型
    
    管理员操作的审计记录
    """
    
    id: int = Field(description="日志ID")
    admin_id: int = Field(description="管理员ID")
    admin_username: str = Field(description="管理员用户名")
    
    # 操作信息
    action: str = Field(description="操作类型")
    resource_type: str = Field(description="资源类型")
    resource_id: Optional[str] = Field(None, description="资源ID")
    
    # 详细信息
    description: str = Field(description="操作描述")
    old_values: Optional[Dict[str, Any]] = Field(None, description="修改前的值")
    new_values: Optional[Dict[str, Any]] = Field(None, description="修改后的值")
    
    # 请求信息
    ip_address: Optional[str] = Field(None, description="IP地址")
    user_agent: Optional[str] = Field(None, description="用户代理")
    
    # 结果信息
    is_success: bool = Field(description="是否成功")
    error_message: Optional[str] = Field(None, description="错误信息")
    
    # 时间戳
    created_at: datetime = Field(description="创建时间")
    
    model_config = ConfigDict(from_attributes=True)


if __name__ == "__main__":
    # 测试管理员schemas
    print("管理员Schemas定义完成")
    
    # 测试管理员创建
    admin_data = {
        "username": "admin_test",
        "email": "admin@example.com",
        "real_name": "测试管理员",
        "role": "admin",
        "password": "TestPass123",
        "confirm_password": "TestPass123"
    }
    
    try:
        admin_create = AdminUserCreate(**admin_data)
        print(f"管理员创建验证成功: {admin_create.username}")
    except Exception as e:
        print(f"管理员创建验证失败: {e}")
    
    # 测试系统配置
    config_data = {
        "key": "system.max_upload_size",
        "value": "10485760",
        "config_type": "integer",
        "category": "upload",
        "description": "最大上传文件大小（字节）"
    }
    
    try:
        config_create = SystemConfigCreate(**config_data)
        print(f"系统配置验证成功: {config_create.key}")
    except Exception as e:
        print(f"系统配置验证失败: {e}")
    
    print("\n管理员Schemas测试完成")