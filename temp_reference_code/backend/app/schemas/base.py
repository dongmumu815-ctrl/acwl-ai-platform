#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基础Pydantic Schemas

定义通用的响应模型和基础数据结构。

Author: System
Date: 2024
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Generic, TypeVar
from pydantic import BaseModel, Field, ConfigDict

# 泛型类型变量
T = TypeVar('T')


class BaseResponse(BaseModel):
    """
    基础响应模型
    
    所有API响应的基础结构
    """
    
    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={
            datetime: lambda v: v.isoformat() if v else None
        }
    )
    
    success: bool = Field(default=True, description="请求是否成功")
    message: str = Field(default="操作成功", description="响应消息")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="响应时间戳")


class SuccessResponse(BaseResponse, Generic[T]):
    """
    成功响应模型
    
    包含数据的成功响应
    """
    
    data: Optional[T] = Field(default=None, description="响应数据")


class ErrorResponse(BaseResponse):
    """
    错误响应模型
    
    错误情况下的响应结构
    """
    
    success: bool = Field(default=False, description="请求是否成功")
    error_code: Optional[str] = Field(default=None, description="错误代码")
    error_details: Optional[Dict[str, Any]] = Field(default=None, description="错误详情")
    trace_id: Optional[str] = Field(default=None, description="追踪ID")


class ValidationErrorResponse(ErrorResponse):
    """
    验证错误响应模型
    
    字段验证失败时的响应结构
    """
    
    validation_errors: List[Dict[str, Any]] = Field(default_factory=list, description="验证错误列表")


class PaginationInfo(BaseModel):
    """
    分页信息模型
    
    分页查询的元数据
    """
    
    page: int = Field(ge=1, description="当前页码")
    size: int = Field(ge=1, le=100, description="每页大小")
    total: int = Field(ge=0, description="总记录数")
    pages: int = Field(ge=0, description="总页数")
    has_next: bool = Field(description="是否有下一页")
    has_prev: bool = Field(description="是否有上一页")
    
    @classmethod
    def create(cls, page: int, size: int, total: int) -> 'PaginationInfo':
        """
        创建分页信息
        
        Args:
            page: 当前页码
            size: 每页大小
            total: 总记录数
        
        Returns:
            PaginationInfo: 分页信息实例
        """
        pages = (total + size - 1) // size if total > 0 else 0
        
        return cls(
            page=page,
            size=size,
            total=total,
            pages=pages,
            has_next=page < pages,
            has_prev=page > 1
        )


class PaginatedResponse(BaseResponse, Generic[T]):
    """
    分页响应模型
    
    包含分页数据的响应结构
    """
    
    data: List[T] = Field(default_factory=list, description="数据列表")
    pagination: PaginationInfo = Field(description="分页信息")


class IdResponse(BaseModel):
    """
    ID响应模型
    
    返回创建或更新后的资源ID
    """
    
    id: int = Field(description="资源ID")


class StatusResponse(BaseModel):
    """
    状态响应模型
    
    返回操作状态
    """
    
    status: str = Field(description="状态")
    affected_count: Optional[int] = Field(default=None, description="影响的记录数")


class HealthCheckResponse(BaseModel):
    """
    健康检查响应模型
    
    系统健康状态检查
    """
    
    status: str = Field(description="系统状态")
    version: str = Field(description="系统版本")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="检查时间")
    services: Dict[str, str] = Field(default_factory=dict, description="服务状态")
    uptime: Optional[float] = Field(default=None, description="运行时间（秒）")


class BaseCreateSchema(BaseModel):
    """
    基础创建Schema
    
    所有创建请求的基础结构
    """
    
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True
    )


class BaseUpdateSchema(BaseModel):
    """
    基础更新Schema
    
    所有更新请求的基础结构
    """
    
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True
    )


class BaseQuerySchema(BaseModel):
    """
    基础查询Schema
    
    所有查询请求的基础结构
    """
    
    page: int = Field(default=1, ge=1, description="页码")
    size: int = Field(default=20, ge=1, le=100, description="每页大小")
    sort_by: Optional[str] = Field(default=None, description="排序字段")
    sort_order: Optional[str] = Field(default="desc", pattern="^(asc|desc)$", description="排序方向")
    search: Optional[str] = Field(default=None, min_length=1, max_length=100, description="搜索关键词")


class DateRangeSchema(BaseModel):
    """
    日期范围Schema
    
    用于日期范围查询
    """
    
    start_date: Optional[datetime] = Field(default=None, description="开始日期")
    end_date: Optional[datetime] = Field(default=None, description="结束日期")
    
    def model_validate(cls, values):
        """
        验证日期范围
        """
        start_date = values.get('start_date')
        end_date = values.get('end_date')
        
        if start_date and end_date and start_date > end_date:
            raise ValueError('开始日期不能晚于结束日期')
        
        return values


class FileUploadResponse(BaseModel):
    """
    文件上传响应模型
    
    文件上传成功后的响应
    """
    
    filename: str = Field(description="文件名")
    file_path: str = Field(description="文件路径")
    file_size: int = Field(description="文件大小")
    file_type: str = Field(description="文件类型")
    upload_id: str = Field(description="上传ID")
    uploaded_at: datetime = Field(default_factory=datetime.utcnow, description="上传时间")


class BulkOperationRequest(BaseModel):
    """
    批量操作请求模型
    
    批量操作的通用请求结构
    """
    
    ids: List[int] = Field(min_items=1, max_items=1000, description="ID列表")
    operation: str = Field(description="操作类型")
    parameters: Optional[Dict[str, Any]] = Field(default=None, description="操作参数")


class BulkOperationResponse(BaseModel):
    """
    批量操作响应模型
    
    批量操作的结果
    """
    
    total_count: int = Field(description="总数量")
    success_count: int = Field(description="成功数量")
    failed_count: int = Field(description="失败数量")
    errors: List[Dict[str, Any]] = Field(default_factory=list, description="错误列表")


if __name__ == "__main__":
    # 测试基础schemas
    print("基础Schemas定义完成")
    
    # 测试分页信息创建
    pagination = PaginationInfo.create(page=2, size=10, total=95)
    print(f"分页信息: 第{pagination.page}页，共{pagination.pages}页，总计{pagination.total}条")
    print(f"有下一页: {pagination.has_next}，有上一页: {pagination.has_prev}")
    
    print("\n基础Schemas测试完成")