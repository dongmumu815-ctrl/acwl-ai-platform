#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通用的Pydantic模式
"""

from pydantic import BaseModel, Field
from typing import List, TypeVar, Generic, Optional, Any, Dict
from datetime import datetime

T = TypeVar('T')


class PaginatedResponse(BaseModel, Generic[T]):
    """分页响应模式"""
    items: List[T] = Field(..., description="数据项列表")
    total: int = Field(..., description="总数量")
    page: int = Field(..., description="当前页码")
    size: int = Field(..., description="每页数量")
    pages: int = Field(..., description="总页数")
    
    @property
    def has_next(self) -> bool:
        """是否有下一页"""
        return self.page < self.pages
    
    @property
    def has_prev(self) -> bool:
        """是否有上一页"""
        return self.page > 1


class ResponseModel(BaseModel, Generic[T]):
    """通用响应模式"""
    success: bool = Field(True, description="是否成功")
    message: str = Field("", description="响应消息")
    data: Optional[T] = Field(None, description="响应数据")
    timestamp: datetime = Field(default_factory=datetime.now, description="响应时间")


# 为了向后兼容，创建一个非泛型版本的别名
class SimpleResponseModel(BaseModel):
    """简单响应模式（非泛型版本）"""
    success: bool = Field(True, description="是否成功")
    message: str = Field("", description="响应消息")
    data: Optional[Any] = Field(None, description="响应数据")
    timestamp: datetime = Field(default_factory=datetime.now, description="响应时间")


class ErrorResponse(BaseModel):
    """错误响应模式"""
    error: str = Field(..., description="错误代码")
    message: str = Field(..., description="错误消息")
    detail: Optional[Any] = Field(None, description="错误详情")
    timestamp: datetime = Field(default_factory=datetime.now, description="错误时间")


class IDResponse(BaseModel):
    """ID响应模式"""
    id: int = Field(..., description="资源ID")
    message: str = Field("操作成功", description="响应消息")


class StatusResponse(BaseModel):
    """状态响应模式"""
    status: str = Field(..., description="状态")
    message: str = Field("", description="状态消息")
    data: Optional[Dict[str, Any]] = Field(None, description="状态数据")


class FileUploadResponse(BaseModel):
    """文件上传响应模式"""
    filename: str = Field(..., description="文件名")
    file_path: str = Field(..., description="文件路径")
    file_size: int = Field(..., description="文件大小(字节)")
    content_type: str = Field(..., description="文件类型")
    upload_time: datetime = Field(default_factory=datetime.now, description="上传时间")


class HealthCheckResponse(BaseModel):
    """健康检查响应模式"""
    status: str = Field(..., description="健康状态")
    timestamp: float = Field(..., description="检查时间戳")
    service: str = Field("ACWL-AI", description="服务名称")
    version: str = Field(..., description="服务版本")
    components: Optional[Dict[str, Any]] = Field(None, description="组件状态")


class MetricsResponse(BaseModel):
    """指标响应模式"""
    timestamp: datetime = Field(default_factory=datetime.now, description="指标时间")
    metrics: Dict[str, Any] = Field(..., description="指标数据")


class BulkOperationResponse(BaseModel):
    """批量操作响应模式"""
    total: int = Field(..., description="总数量")
    success: int = Field(..., description="成功数量")
    failed: int = Field(..., description="失败数量")
    errors: List[str] = Field(default_factory=list, description="错误列表")
    message: str = Field("", description="操作消息")


class SearchRequest(BaseModel):
    """搜索请求模式"""
    query: str = Field(..., min_length=1, description="搜索关键词")
    page: int = Field(1, ge=1, description="页码")
    size: int = Field(20, ge=1, le=100, description="每页数量")
    filters: Optional[Dict[str, Any]] = Field(None, description="筛选条件")
    sort_by: Optional[str] = Field(None, description="排序字段")
    sort_order: Optional[str] = Field("desc", pattern=r"^(asc|desc)$", description="排序方向")


class ConfigUpdateRequest(BaseModel):
    """配置更新请求模式"""
    config: Dict[str, Any] = Field(..., description="配置数据")
    merge: bool = Field(True, description="是否合并现有配置")
    validate: bool = Field(True, description="是否验证配置")