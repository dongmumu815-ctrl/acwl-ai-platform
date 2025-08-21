#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据源相关的Pydantic模式
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any, TYPE_CHECKING
from datetime import datetime, date
from enum import Enum

from app.models.datasource import DatasourceType, DatasourceStatus, TestResult, PermissionType

# if TYPE_CHECKING:
#     from app.schemas.auth import UserResponse


class DatasourceBase(BaseModel):
    """数据源基础模式"""
    name: str = Field(..., description="数据源名称", max_length=100)
    description: Optional[str] = Field(None, description="数据源描述")
    datasource_type: DatasourceType = Field(..., description="数据源类型")
    host: str = Field(..., description="主机地址", max_length=255)
    port: int = Field(..., description="端口号", ge=1, le=65535)
    database_name: Optional[str] = Field(None, description="数据库名称", max_length=100)
    username: Optional[str] = Field(None, description="用户名", max_length=100)
    password: Optional[str] = Field(None, description="密码", max_length=255)
    connection_params: Optional[Dict[str, Any]] = Field(None, description="连接参数")
    pool_config: Optional[Dict[str, Any]] = Field(None, description="连接池配置")
    is_enabled: bool = Field(True, description="是否启用")

    @validator('port')
    def validate_port(cls, v, values):
        """验证端口号"""
        datasource_type = values.get('datasource_type')
        if datasource_type:
            # 根据数据源类型验证默认端口
            default_ports = {
                DatasourceType.MYSQL: 3306,
                DatasourceType.DORIS: 9030,
                DatasourceType.ORACLE: 1521,
                DatasourceType.POSTGRESQL: 5432,
                DatasourceType.SQLSERVER: 1433,
                DatasourceType.CLICKHOUSE: 9000,
                DatasourceType.MONGODB: 27017,
                DatasourceType.REDIS: 6379,
                DatasourceType.ELASTICSEARCH: 9200,
            }
            # 如果端口为0，使用默认端口
            if v == 0 and datasource_type in default_ports:
                return default_ports[datasource_type]
        return v

    @validator('connection_params')
    def validate_connection_params(cls, v, values):
        """验证连接参数"""
        if v is None:
            return {}
        return v

    @validator('pool_config')
    def validate_pool_config(cls, v, values):
        """验证连接池配置"""
        if v is None:
            # 返回默认连接池配置
            return {
                "pool_size": 5,
                "max_overflow": 10,
                "pool_timeout": 30,
                "pool_recycle": 3600
            }
        return v


class DatasourceCreate(DatasourceBase):
    """创建数据源模式"""
    pass


class DatasourceUpdate(BaseModel):
    """更新数据源模式"""
    name: Optional[str] = Field(None, description="数据源名称", max_length=100)
    description: Optional[str] = Field(None, description="数据源描述")
    host: Optional[str] = Field(None, description="主机地址", max_length=255)
    port: Optional[int] = Field(None, description="端口号", ge=1, le=65535)
    database_name: Optional[str] = Field(None, description="数据库名称", max_length=100)
    username: Optional[str] = Field(None, description="用户名", max_length=100)
    password: Optional[str] = Field(None, description="密码", max_length=255)
    connection_params: Optional[Dict[str, Any]] = Field(None, description="连接参数")
    pool_config: Optional[Dict[str, Any]] = Field(None, description="连接池配置")
    is_enabled: Optional[bool] = Field(None, description="是否启用")


class DatasourceResponse(DatasourceBase):
    """数据源响应模式"""
    id: int = Field(..., description="数据源ID")
    status: DatasourceStatus = Field(..., description="数据源状态")
    last_test_time: Optional[datetime] = Field(None, description="最后测试时间")
    last_test_result: Optional[str] = Field(None, description="最后测试结果")
    created_by: Optional[int] = Field(None, description="创建者ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    # 隐藏敏感信息
    password: Optional[str] = Field(None, description="密码（隐藏）")
    
    class Config:
        from_attributes = True
        
    @validator('password', pre=True, always=True)
    def hide_password(cls, v):
        """隐藏密码"""
        if v:
            return "***"
        return None


class DatasourceListResponse(BaseModel):
    """数据源列表响应模式"""
    items: List[DatasourceResponse] = Field(..., description="数据源列表")
    total: int = Field(..., description="总数量")
    page: int = Field(..., description="当前页码")
    size: int = Field(..., description="每页大小")
    pages: int = Field(..., description="总页数")


class DatasourceTestRequest(BaseModel):
    """数据源测试请求模式"""
    timeout: Optional[int] = Field(10, description="超时时间（秒）", ge=1, le=300)
    test_query: Optional[str] = Field(None, description="测试查询语句")


class DatasourceTestResponse(BaseModel):
    """数据源测试响应模式"""
    success: bool = Field(..., description="测试是否成功")
    response_time: Optional[int] = Field(None, description="响应时间（毫秒）")
    message: str = Field(..., description="测试结果消息")
    error_details: Optional[str] = Field(None, description="错误详情")
    test_time: datetime = Field(..., description="测试时间")
    connection_info: Optional[Dict[str, Any]] = Field(None, description="连接信息")


class DatasourceTestLogResponse(BaseModel):
    """数据源测试日志响应模式"""
    id: int = Field(..., description="日志ID")
    datasource_id: int = Field(..., description="数据源ID")
    test_time: datetime = Field(..., description="测试时间")
    test_result: TestResult = Field(..., description="测试结果")
    response_time: Optional[int] = Field(None, description="响应时间（毫秒）")
    error_message: Optional[str] = Field(None, description="错误信息")
    test_details: Optional[Dict[str, Any]] = Field(None, description="测试详情")
    tested_by: Optional[int] = Field(None, description="测试者ID")
    
    class Config:
        from_attributes = True


# 临时注释掉这个类来测试
# class DatasourceUsageStatsResponse(BaseModel):
#     """数据源使用统计响应模式"""
#     id: int = Field(..., description="统计ID")
#     datasource_id: int = Field(..., description="数据源ID")
#     date: date = Field(..., description="统计日期")
#     connection_count: int = Field(..., description="连接次数")
#     query_count: int = Field(..., description="查询次数")
#     total_response_time: int = Field(..., description="总响应时间（毫秒）")
#     error_count: int = Field(..., description="错误次数")
#     average_response_time: float = Field(..., description="平均响应时间（毫秒）")
#     
#     class Config:
#         from_attributes = True


class DatasourcePermissionCreate(BaseModel):
    """创建数据源权限模式"""
    user_id: int = Field(..., description="用户ID")
    permission_type: PermissionType = Field(..., description="权限类型")
    expires_at: Optional[datetime] = Field(None, description="过期时间")


class DatasourcePermissionUpdate(BaseModel):
    """更新数据源权限模式"""
    permission_type: Optional[PermissionType] = Field(None, description="权限类型")
    expires_at: Optional[datetime] = Field(None, description="过期时间")
    is_active: Optional[bool] = Field(None, description="是否激活")


class DatasourcePermissionResponse(BaseModel):
    """数据源权限响应模式"""
    id: int = Field(..., description="权限ID")
    datasource_id: int = Field(..., description="数据源ID")
    user_id: int = Field(..., description="用户ID")
    permission_type: PermissionType = Field(..., description="权限类型")
    granted_by: Optional[int] = Field(None, description="授权者ID")
    granted_at: datetime = Field(..., description="授权时间")
    expires_at: Optional[datetime] = Field(None, description="过期时间")
    is_active: bool = Field(..., description="是否激活")
    is_expired: bool = Field(..., description="是否已过期")
    
    class Config:
        from_attributes = True


class DatasourceTemplateResponse(BaseModel):
    """数据源模板响应模式"""
    id: int = Field(..., description="模板ID")
    name: str = Field(..., description="模板名称")
    description: Optional[str] = Field(None, description="模板描述")
    datasource_type: DatasourceType = Field(..., description="数据源类型")
    default_port: Optional[int] = Field(None, description="默认端口")
    default_params: Optional[Dict[str, Any]] = Field(None, description="默认连接参数")
    connection_url_template: Optional[str] = Field(None, description="连接URL模板")
    driver_class: Optional[str] = Field(None, description="驱动类名")
    validation_query: Optional[str] = Field(None, description="验证查询语句")
    is_system: bool = Field(..., description="是否系统模板")
    created_by: Optional[int] = Field(None, description="创建者ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    class Config:
        from_attributes = True


class DatasourceFilter(BaseModel):
    """数据源筛选模式"""
    search: Optional[str] = Field(None, description="搜索关键词")
    datasource_type: Optional[DatasourceType] = Field(None, description="数据源类型")
    status: Optional[DatasourceStatus] = Field(None, description="数据源状态")
    is_enabled: Optional[bool] = Field(None, description="是否启用")
    created_by: Optional[int] = Field(None, description="创建者ID")


class DatasourceStats(BaseModel):
    """数据源统计模式"""
    total_count: int = Field(..., description="总数量")
    active_count: int = Field(..., description="激活数量")
    inactive_count: int = Field(..., description="未激活数量")
    error_count: int = Field(..., description="错误数量")
    type_distribution: Dict[str, int] = Field(..., description="类型分布")
    recent_test_success_rate: float = Field(..., description="最近测试成功率")


class DatasourceConnectionInfo(BaseModel):
    """数据源连接信息模式"""
    datasource_id: int = Field(..., description="数据源ID")
    connection_url: str = Field(..., description="连接URL（隐藏敏感信息）")
    driver_info: Optional[Dict[str, Any]] = Field(None, description="驱动信息")
    server_info: Optional[Dict[str, Any]] = Field(None, description="服务器信息")
    database_info: Optional[Dict[str, Any]] = Field(None, description="数据库信息")


class DatasourceQueryRequest(BaseModel):
    """数据源查询请求模式"""
    query: str = Field(..., description="查询语句", max_length=10000)
    limit: Optional[int] = Field(100, description="结果限制", ge=1, le=1000)
    timeout: Optional[int] = Field(30, description="超时时间（秒）", ge=1, le=300)


class DatasourceQueryResponse(BaseModel):
    """数据源查询响应模式"""
    success: bool = Field(..., description="查询是否成功")
    columns: Optional[List[str]] = Field(None, description="列名列表")
    data: Optional[List[List[Any]]] = Field(None, description="查询结果数据")
    row_count: int = Field(..., description="结果行数")
    execution_time: int = Field(..., description="执行时间（毫秒）")
    message: str = Field(..., description="执行消息")
    error_details: Optional[str] = Field(None, description="错误详情")