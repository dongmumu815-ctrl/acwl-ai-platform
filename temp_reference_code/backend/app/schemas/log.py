#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志相关Pydantic Schemas

定义API使用日志和数据上传记录相关的响应数据模型。

Author: System
Date: 2024
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum

from .base import BaseQuerySchema


class UploadStatusEnum(str, Enum):
    """
    上传状态枚举
    """
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ApiUsageLogResponse(BaseModel):
    """
    API使用日志响应模型
    
    返回API使用日志信息
    """
    
    id: int = Field(description="日志ID")
    customer_id: int = Field(description="客户ID")
    api_id: int = Field(description="API ID")
    
    # 请求信息
    request_id: str = Field(description="请求唯一标识")
    http_method: str = Field(description="HTTP方法")
    request_url: str = Field(description="请求URL")
    
    # 客户端信息
    client_ip: Optional[str] = Field(None, description="客户端IP地址")
    user_agent: Optional[str] = Field(None, description="用户代理字符串")
    
    # 响应信息
    response_status: int = Field(description="HTTP响应状态码")
    
    # 性能信息
    processing_time: Optional[float] = Field(None, description="处理时间（秒）")
    
    # 错误信息
    error_message: Optional[str] = Field(None, description="错误信息")
    
    # 业务信息
    data_size: Optional[int] = Field(None, description="数据大小（字节）")
    record_count: Optional[int] = Field(None, description="处理记录数")
    
    # 状态标识
    is_success: bool = Field(description="是否成功")
    is_error: bool = Field(description="是否出错")
    
    # 时间戳
    created_at: datetime = Field(description="创建时间")
    
    model_config = ConfigDict(from_attributes=True)


class ApiUsageLogDetailResponse(ApiUsageLogResponse):
    """
    API使用日志详细信息响应模型
    
    包含完整请求和响应数据的日志信息
    """
    
    # 详细请求信息
    request_headers: Optional[Dict[str, Any]] = Field(None, description="请求头信息")
    request_params: Optional[Dict[str, Any]] = Field(None, description="请求参数")
    request_body: Optional[str] = Field(None, description="请求体内容")
    
    # 详细响应信息
    response_headers: Optional[Dict[str, Any]] = Field(None, description="响应头信息")
    
    # 详细错误信息
    error_traceback: Optional[str] = Field(None, description="错误堆栈信息")


class DataUploadResponse(BaseModel):
    """
    数据上传记录响应模型
    
    返回数据上传记录信息
    """
    
    id: int = Field(description="上传记录ID")
    customer_id: int = Field(description="客户ID")
    api_id: int = Field(description="API ID")
    usage_log_id: Optional[int] = Field(None, description="关联的使用日志ID")
    
    # 上传信息
    upload_id: str = Field(description="上传唯一标识")
    batch_id: Optional[str] = Field(None, description="批次标识")
    
    # 文件信息
    original_filename: Optional[str] = Field(None, description="原始文件名")
    file_path: Optional[str] = Field(None, description="文件存储路径")
    file_size: Optional[int] = Field(None, description="文件大小（字节）")
    file_type: Optional[str] = Field(None, description="文件类型")
    
    # 处理状态
    status: UploadStatusEnum = Field(description="处理状态")
    
    # 处理信息
    processed_at: Optional[datetime] = Field(None, description="处理完成时间")
    processing_time: Optional[float] = Field(None, description="处理耗时（秒）")
    record_count: Optional[int] = Field(None, description="记录数量")
    
    # 验证结果
    validation_errors: Optional[List[str]] = Field(None, description="验证错误信息")
    
    # 错误信息
    error_message: Optional[str] = Field(None, description="错误信息")
    
    # 元数据
    metadata: Optional[Dict[str, Any]] = Field(None, description="额外的元数据信息")
    
    # 状态标识
    is_completed: bool = Field(description="是否处理完成")
    is_failed: bool = Field(description="是否处理失败")
    has_validation_errors: bool = Field(description="是否有验证错误")
    
    # 时间戳
    created_at: datetime = Field(description="创建时间")
    updated_at: datetime = Field(description="更新时间")
    
    model_config = ConfigDict(from_attributes=True)


class DataUploadDetailResponse(DataUploadResponse):
    """
    数据上传记录详细信息响应模型
    
    包含数据内容的完整上传记录信息
    """
    
    data_content: Optional[str] = Field(None, description="数据内容（JSON格式）")


class UsageLogQuery(BaseQuerySchema):
    """
    使用日志查询请求模型
    
    查询使用日志时的参数
    """
    
    customer_id: Optional[int] = Field(None, description="客户ID")
    api_id: Optional[int] = Field(None, description="API ID")
    response_status: Optional[int] = Field(None, description="响应状态码")
    client_ip: Optional[str] = Field(None, description="客户端IP")
    
    # 状态过滤
    success_only: Optional[bool] = Field(None, description="只显示成功的请求")
    error_only: Optional[bool] = Field(None, description="只显示错误的请求")
    
    # 性能过滤
    min_processing_time: Optional[float] = Field(None, ge=0, description="最小处理时间")
    max_processing_time: Optional[float] = Field(None, ge=0, description="最大处理时间")
    
    # 日期范围
    start_date: Optional[datetime] = Field(None, description="开始日期")
    end_date: Optional[datetime] = Field(None, description="结束日期")


class DataUploadQuery(BaseQuerySchema):
    """
    数据上传查询请求模型
    
    查询数据上传记录时的参数
    """
    
    customer_id: Optional[int] = Field(None, description="客户ID")
    api_id: Optional[int] = Field(None, description="API ID")
    status: Optional[UploadStatusEnum] = Field(None, description="处理状态")
    batch_id: Optional[str] = Field(None, description="批次ID")
    
    # 文件类型过滤
    file_type: Optional[str] = Field(None, description="文件类型")
    
    # 日期范围
    start_date: Optional[datetime] = Field(None, description="开始日期")
    end_date: Optional[datetime] = Field(None, description="结束日期")


class UsageStatsResponse(BaseModel):
    """
    使用统计响应模型
    
    API使用情况的统计数据
    """
    
    # 基本统计
    total_calls: int = Field(description="总调用次数")
    success_calls: int = Field(description="成功调用次数")
    error_calls: int = Field(description="错误调用次数")
    success_rate: float = Field(description="成功率")
    
    # 性能统计
    avg_processing_time: float = Field(description="平均处理时间（秒）")
    
    # 时间范围
    period_days: int = Field(description="统计周期（天）")
    
    # 生成时间
    generated_at: datetime = Field(default_factory=datetime.utcnow, description="生成时间")


class UploadStatsResponse(BaseModel):
    """
    上传统计响应模型
    
    数据上传情况的统计数据
    """
    
    # 基本统计
    total_uploads: int = Field(description="总上传次数")
    completed_uploads: int = Field(description="完成上传次数")
    failed_uploads: int = Field(description="失败上传次数")
    success_rate: float = Field(description="成功率")
    
    # 数据统计
    total_records: int = Field(description="总记录数")
    total_size: int = Field(description="总数据大小（字节）")
    
    # 时间范围
    period_days: int = Field(description="统计周期（天）")
    
    # 生成时间
    generated_at: datetime = Field(default_factory=datetime.utcnow, description="生成时间")


class DailyStatsResponse(BaseModel):
    """
    每日统计响应模型
    
    按日期统计的使用数据
    """
    
    date: str = Field(description="日期（YYYY-MM-DD）")
    total_calls: int = Field(description="总调用次数")
    success_calls: int = Field(description="成功调用次数")
    error_calls: int = Field(description="错误调用次数")
    unique_ips: int = Field(description="唯一IP数")
    total_uploads: int = Field(description="总上传次数")
    total_records: int = Field(description="总记录数")


class HourlyStatsResponse(BaseModel):
    """
    每小时统计响应模型
    
    按小时统计的使用数据
    """
    
    hour: int = Field(ge=0, le=23, description="小时（0-23）")
    total_calls: int = Field(description="总调用次数")
    success_calls: int = Field(description="成功调用次数")
    error_calls: int = Field(description="错误调用次数")
    avg_processing_time: float = Field(description="平均处理时间")


class TopApiStatsResponse(BaseModel):
    """
    热门API统计响应模型
    
    使用频率最高的API统计
    """
    
    api_id: int = Field(description="API ID")
    api_name: str = Field(description="API名称")
    customer_name: str = Field(description="客户名称")
    total_calls: int = Field(description="总调用次数")
    success_rate: float = Field(description="成功率")
    avg_processing_time: float = Field(description="平均处理时间")


class ErrorAnalysisResponse(BaseModel):
    """
    错误分析响应模型
    
    错误情况的分析数据
    """
    
    error_type: str = Field(description="错误类型")
    error_count: int = Field(description="错误次数")
    error_rate: float = Field(description="错误率")
    sample_message: Optional[str] = Field(None, description="示例错误信息")
    first_occurred: datetime = Field(description="首次出现时间")
    last_occurred: datetime = Field(description="最后出现时间")


class PerformanceAnalysisResponse(BaseModel):
    """
    性能分析响应模型
    
    API性能分析数据
    """
    
    api_id: int = Field(description="API ID")
    api_name: str = Field(description="API名称")
    
    # 响应时间统计
    avg_response_time: float = Field(description="平均响应时间（秒）")
    min_response_time: float = Field(description="最小响应时间（秒）")
    max_response_time: float = Field(description="最大响应时间（秒）")
    p95_response_time: float = Field(description="95%响应时间（秒）")
    p99_response_time: float = Field(description="99%响应时间（秒）")
    
    # 调用统计
    total_calls: int = Field(description="总调用次数")
    slow_calls: int = Field(description="慢请求次数（>2秒）")
    slow_call_rate: float = Field(description="慢请求率")
    
    # 时间范围
    analysis_period: str = Field(description="分析周期")


class LogExportRequest(BaseModel):
    """
    日志导出请求模型
    
    导出日志数据时的请求参数
    """
    
    # 过滤条件
    customer_id: Optional[int] = Field(None, description="客户ID")
    api_id: Optional[int] = Field(None, description="API ID")
    start_date: datetime = Field(description="开始日期")
    end_date: datetime = Field(description="结束日期")
    
    # 导出选项
    export_format: str = Field(default="csv", description="导出格式：csv, json, xlsx")
    include_request_data: bool = Field(default=False, description="是否包含请求数据")
    include_response_data: bool = Field(default=False, description="是否包含响应数据")
    
    # 限制
    max_records: int = Field(default=10000, ge=1, le=100000, description="最大记录数")


class LogExportResponse(BaseModel):
    """
    日志导出响应模型
    
    导出任务的响应信息
    """
    
    export_id: str = Field(description="导出任务ID")
    status: str = Field(description="导出状态")
    file_url: Optional[str] = Field(None, description="下载链接")
    record_count: int = Field(description="导出记录数")
    file_size: Optional[int] = Field(None, description="文件大小（字节）")
    
    created_at: datetime = Field(default_factory=datetime.utcnow, description="创建时间")
    completed_at: Optional[datetime] = Field(None, description="完成时间")
    expires_at: Optional[datetime] = Field(None, description="过期时间")


if __name__ == "__main__":
    # 测试日志schemas
    print("日志Schemas定义完成")
    
    # 测试统计响应
    stats_data = {
        "total_calls": 1000,
        "success_calls": 950,
        "error_calls": 50,
        "success_rate": 0.95,
        "avg_processing_time": 0.25,
        "period_days": 30
    }
    
    try:
        usage_stats = UsageStatsResponse(**stats_data)
        print(f"使用统计验证成功: 成功率 {usage_stats.success_rate:.2%}")
    except Exception as e:
        print(f"使用统计验证失败: {e}")
    
    print("\n日志Schemas测试完成")