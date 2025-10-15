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

from .base import BaseCreateSchema, BaseUpdateSchema, BaseQuerySchema


class HttpMethodEnum(str, Enum):
    """
    HTTP方法枚举
    """
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"


class ResponseFormatEnum(str, Enum):
    """
    响应格式枚举
    """
    JSON = "JSON"
    XML = "XML"
    TEXT = "TEXT"


class FieldTypeEnum(str, Enum):
    """
    字段类型枚举
    """
    STRING = "string"
    INTEGER = "int"
    FLOAT = "float"
    BOOLEAN = "boolean"
    DATE = "date"
    DATETIME = "datetime"
    JSON = "json"
    FILE = "file"


class CustomApiBase(BaseModel):
    """
    自定义API基础模型
    
    API的基本字段定义
    """
    
    api_name: str = Field(..., min_length=1, max_length=100, description="API名称")
    api_code: str = Field(..., min_length=1, max_length=50, description="API代码")
    api_description: Optional[str] = Field(None, max_length=1000, description="API描述")
    http_method: HttpMethodEnum = Field(default=HttpMethodEnum.POST, description="HTTP方法")
    response_format: ResponseFormatEnum = Field(default=ResponseFormatEnum.JSON, description="响应格式")
    
    @field_validator('api_code')
    @classmethod
    def validate_api_code(cls, v):
        # 验证API代码格式：必须以字母开头，只允许字母、数字、下划线和连字符，长度3-50字符
        import re
        if not re.match(r'^[a-zA-Z][a-zA-Z0-9_-]{2,49}$', v):
            raise ValueError('API代码必须以字母开头，只能包含字母、数字、下划线和连字符，长度3-50字符')
        return v.lower()


class CustomApiCreate(CustomApiBase, BaseCreateSchema):
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
    
    # 字段定义
    fields: List['ApiFieldCreate'] = Field(default_factory=list, description="字段定义列表")


class CustomApiUpdate(BaseUpdateSchema):
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
    
    @field_validator('api_code')
    @classmethod
    def validate_api_code(cls, v):
        """验证API代码格式"""
        if v is not None:
            import re
            if not re.match(r'^[a-zA-Z][a-zA-Z0-9_-]{2,49}$', v):
                raise ValueError('API代码必须以字母开头，只能包含字母、数字、下划线和连字符，长度3-50字符')
            return v.lower()
        return v


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
        import re
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('API代码只能包含字母、数字、下划线和连字符')
        return v.lower()


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


class CustomApiDetailResponse(CustomApiResponse):
    """
    自定义API详细信息响应模型
    
    包含字段定义的完整API信息
    """
    
    fields: List['ApiFieldResponse'] = Field(default_factory=list, description="字段定义列表")
    
    # 使用统计
    today_calls: int = Field(default=0, description="今日调用次数")
    this_month_calls: int = Field(default=0, description="本月调用次数")
    success_rate: float = Field(default=0.0, description="成功率")


class ApiFieldBase(BaseModel):
    """
    API字段基础模型
    
    字段的基本属性定义
    """
    
    field_name: str = Field(..., min_length=1, max_length=50, description="字段名称")
    field_label: str = Field(..., min_length=1, max_length=100, description="字段标签")
    field_type: FieldTypeEnum = Field(..., description="字段类型")
    is_required: bool = Field(default=False, description="是否必填")
    default_value: Optional[str] = Field(None, description="默认值")
    description: Optional[str] = Field(None, max_length=500, description="字段描述")
    
    @field_validator('field_name')
    @classmethod
    def validate_field_name(cls, v):
        # 验证字段名格式：只允许字母、数字和下划线，且以字母开头
        import re
        if not re.match(r'^[a-zA-Z][a-zA-Z0-9_]*$', v):
            raise ValueError('字段名必须以字母开头，只能包含字母、数字和下划线')
        return v.lower()


class ApiFieldCreate(ApiFieldBase, BaseCreateSchema):
    """
    API字段创建请求模型
    
    创建新字段时的请求数据
    """
    
    # 验证规则
    max_length: Optional[int] = Field(None, ge=1, description="最大长度（字符串类型）")
    min_length: Optional[int] = Field(None, ge=0, description="最小长度（字符串类型）")
    max_value: Optional[float] = Field(None, description="最大值（数值类型）")
    min_value: Optional[float] = Field(None, description="最小值（数值类型）")
    allowed_values: Optional[List[str]] = Field(None, description="允许的值列表")
    validation_regex: Optional[str] = Field(None, max_length=500, description="验证正则表达式")
    validation_message: Optional[str] = Field(None, max_length=200, description="验证失败提示")
    
    # 排序
    sort_order: int = Field(default=0, description="排序顺序")
    
    @field_validator('min_length')
    @classmethod
    def validate_min_length(cls, v):
        return v
    
    @field_validator('max_length')
    @classmethod
    def validate_max_length(cls, v):
        return v
    
    @field_validator('min_value')
    @classmethod
    def validate_min_value(cls, v):
        return v
    
    @field_validator('max_value')
    @classmethod
    def validate_max_value(cls, v):
        return v
    
    @field_validator('validation_regex')
    @classmethod
    def validate_regex(cls, v):
        if v:
            import re
            try:
                re.compile(v)
            except re.error:
                raise ValueError('正则表达式格式不正确')
        return v


class ApiFieldUpdate(BaseUpdateSchema):
    """
    API字段更新请求模型
    
    更新字段信息时的请求数据
    """
    
    field_name: Optional[str] = Field(None, min_length=1, max_length=50, description="字段名称")
    field_label: Optional[str] = Field(None, min_length=1, max_length=100, description="字段标签")
    field_type: Optional[FieldTypeEnum] = Field(None, description="字段类型")
    is_required: Optional[bool] = Field(None, description="是否必填")
    default_value: Optional[str] = Field(None, description="默认值")
    description: Optional[str] = Field(None, max_length=500, description="字段描述")
    
    # 验证规则
    max_length: Optional[int] = Field(None, ge=1, description="最大长度")
    min_length: Optional[int] = Field(None, ge=0, description="最小长度")
    max_value: Optional[float] = Field(None, description="最大值")
    min_value: Optional[float] = Field(None, description="最小值")
    allowed_values: Optional[List[str]] = Field(None, description="允许的值列表")
    validation_regex: Optional[str] = Field(None, max_length=500, description="验证正则表达式")
    validation_message: Optional[str] = Field(None, max_length=200, description="验证失败提示")
    
    sort_order: Optional[int] = Field(None, description="排序顺序")
    
    @field_validator('field_name')
    @classmethod
    def validate_field_name(cls, v):
        if v is not None:
            # 验证字段名格式：只允许字母、数字和下划线，且以字母开头
            import re
            if not re.match(r'^[a-zA-Z][a-zA-Z0-9_]*$', v):
                raise ValueError('字段名必须以字母开头，只能包含字母、数字和下划线')
            return v.lower()
        return v


class ApiFieldResponse(ApiFieldBase):
    """
    API字段响应模型
    
    返回字段信息时的数据结构
    """
    
    id: int = Field(description="字段ID")
    api_id: int = Field(description="API ID")
    
    # 验证规则
    max_length: Optional[int] = Field(description="最大长度")
    min_length: Optional[int] = Field(description="最小长度")
    max_value: Optional[float] = Field(description="最大值")
    min_value: Optional[float] = Field(description="最小值")
    allowed_values: Optional[List[str]] = Field(description="允许的值列表")
    validation_regex: Optional[str] = Field(description="验证正则表达式")
    validation_message: Optional[str] = Field(description="验证失败提示")
    
    sort_order: int = Field(description="排序顺序")
    
    # 时间戳
    created_at: datetime = Field(description="创建时间")
    updated_at: datetime = Field(description="更新时间")
    
    model_config = ConfigDict(from_attributes=True)


class ApiQuery(BaseQuerySchema):
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


class ApiDataSubmission(BaseModel):
    """
    API数据提交请求模型
    
    通过自定义API提交数据时的请求结构
    """
    
    data: Dict[str, Any] = Field(..., description="提交的数据")
    batch_id: Optional[str] = Field(None, description="批次ID（用于批量提交）")
    metadata: Optional[Dict[str, Any]] = Field(None, description="元数据")


class ApiDataResponse(BaseModel):
    """
    API数据提交响应模型
    
    数据提交成功后的响应
    """
    
    upload_id: str = Field(description="上传ID")
    status: str = Field(description="处理状态")
    message: str = Field(description="响应消息")
    
    # 验证结果
    validation_passed: bool = Field(description="验证是否通过")
    validation_errors: List[str] = Field(default_factory=list, description="验证错误列表")
    
    # 处理信息
    record_count: Optional[int] = Field(None, description="记录数量")
    processing_time: Optional[float] = Field(None, description="处理时间（秒）")
    
    # 时间戳
    submitted_at: datetime = Field(default_factory=datetime.utcnow, description="提交时间")


class ApiStatsResponse(BaseModel):
    """
    API统计信息响应模型
    
    API的各种统计数据
    """
    
    api_id: int = Field(description="API ID")
    
    # 调用统计
    total_calls: int = Field(description="总调用次数")
    success_calls: int = Field(description="成功调用次数")
    failed_calls: int = Field(description="失败调用次数")
    success_rate: float = Field(description="成功率")
    
    # 时间统计
    today_calls: int = Field(description="今日调用次数")
    this_week_calls: int = Field(description="本周调用次数")
    this_month_calls: int = Field(description="本月调用次数")
    
    # 性能统计
    avg_processing_time: float = Field(description="平均处理时间（秒）")
    
    # 数据统计
    total_uploads: int = Field(description="总上传次数")
    total_records: int = Field(description="总记录数")
    
    # 时间范围
    stats_period: str = Field(description="统计周期")
    generated_at: datetime = Field(default_factory=datetime.utcnow, description="生成时间")


class ApiBatchOperationRequest(BaseModel):
    """
    API批量操作请求模型
    
    批量操作API时的请求
    """
    
    api_ids: List[int] = Field(..., min_items=1, max_items=50, description="API ID列表")
    operation: str = Field(..., description="操作类型：enable, disable, delete")
    
    @field_validator('operation')
    @classmethod
    def validate_operation(cls, v):
        allowed_operations = {'enable', 'disable', 'delete'}
        if v not in allowed_operations:
            raise ValueError(f'操作类型必须是以下之一: {allowed_operations}')
        return v


class ApiFieldBatchUpdateRequest(BaseModel):
    """
    API字段批量更新请求模型
    
    批量更新字段排序等信息
    """
    
    field_updates: List[Dict[str, Any]] = Field(
        ..., 
        min_items=1, 
        description="字段更新列表，每项包含field_id和更新字段"
    )
    
    @field_validator('field_updates')
    @classmethod
    def validate_field_updates(cls, v):
        for update in v:
            if 'field_id' not in update:
                raise ValueError('每个更新项必须包含field_id')
            if not isinstance(update['field_id'], int):
                raise ValueError('field_id必须是整数')
        return v


# 更新前向引用
CustomApiCreate.model_rebuild()
CustomApiDetailResponse.model_rebuild()


if __name__ == "__main__":
    # 测试API schemas
    import logging
    logger = logging.getLogger(__name__)
    logger.info("API Schemas定义完成")
    
    # 测试API创建请求
    api_data = {
        "customer_id": 1,
        "api_name": "用户数据上传",
        "api_code": "user_data_upload",
        "api_description": "用于上传用户数据的API接口",
        "http_method": "POST",
        "fields": [
            {
                "field_name": "username",
                "field_label": "用户名",
                "field_type": "string",
                "is_required": True,
                "max_length": 50,
                "sort_order": 1
            },
            {
                "field_name": "age",
                "field_label": "年龄",
                "field_type": "int",
                "is_required": False,
                "min_value": 0,
                "max_value": 150,
                "sort_order": 2
            }
        ]
    }
    
    try:
        api_create = CustomApiCreate(**api_data)
        logger.info(f"API创建请求验证成功: {api_create.api_name}")
        logger.info(f"包含 {len(api_create.fields)} 个字段定义")
    except Exception as e:
        logger.error(f"API创建请求验证失败: {e}")
    
    logger.info("API Schemas测试完成")