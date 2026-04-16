#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据集相关的Pydantic模型
"""

from typing import Optional, List, Any, Dict
from datetime import datetime
from pydantic import BaseModel, Field, validator
from enum import Enum


class DatasetType(str, Enum):
    """数据集类型枚举"""
    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    TABULAR = "tabular"
    MULTIMODAL = "multimodal"


class DatasetStatus(str, Enum):
    """数据集状态枚举"""
    PENDING = "pending"
    PROCESSING = "processing"
    READY = "ready"
    ERROR = "error"


class DatasetBase(BaseModel):
    """数据集基础模型"""
    name: str = Field(..., min_length=1, max_length=100, description="数据集名称")
    description: Optional[str] = Field(None, description="数据集描述")
    dataset_type: DatasetType = Field(..., description="数据集类型")
    format: Optional[str] = Field(None, max_length=50, description="数据格式")
    is_public: bool = Field(False, description="是否公开")
    tags: Optional[List[str]] = Field(default_factory=list, description="标签列表")

    @validator('dataset_type', 'status', pre=True, check_fields=False)
    def parse_enums(cls, v):
        if v is None:
            return v
        if hasattr(v, 'value'):
            return v.value.lower()
        if isinstance(v, str):
            return v.lower()
        return v
        
    @validator('tags', pre=True)
    def parse_tags(cls, v):
        if v is None:
            return []
        if isinstance(v, str):
            try:
                import json
                parsed = json.loads(v)
                if isinstance(parsed, list):
                    return parsed
            except Exception:
                pass
            return [v]
        return v


class DatasetCreate(DatasetBase):
    """创建数据集请求模型"""
    pass


class DatasetUpdate(BaseModel):
    """更新数据集请求模型"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="数据集名称")
    description: Optional[str] = Field(None, description="数据集描述")
    dataset_type: Optional[DatasetType] = Field(None, description="数据集类型")
    format: Optional[str] = Field(None, max_length=50, description="数据格式")
    is_public: Optional[bool] = Field(None, description="是否公开")
    tags: Optional[List[str]] = Field(None, description="标签列表")
    status: Optional[DatasetStatus] = Field(None, description="数据集状态")

    @validator('dataset_type', 'status', pre=True, check_fields=False)
    def parse_enums(cls, v):
        if v is None:
            return v
        if hasattr(v, 'value'):
            return v.value.lower()
        if isinstance(v, str):
            return v.lower()
        return v


class DatasetUpload(BaseModel):
    """数据集上传配置模型"""
    name: str = Field(..., min_length=1, max_length=100, description="数据集名称")
    description: Optional[str] = Field(None, description="数据集描述")
    dataset_type: DatasetType = Field(..., description="数据集类型")
    format: Optional[str] = Field(None, max_length=50, description="数据格式")
    tags: Optional[List[str]] = Field(default_factory=list, description="标签列表")
    processing_options: Optional[Dict[str, Any]] = Field(
        default_factory=dict, 
        description="处理选项"
    )

    @validator('dataset_type', 'status', pre=True, check_fields=False)
    def parse_enums(cls, v):
        if v is None:
            return v
        if hasattr(v, 'value'):
            return v.value.lower()
        if isinstance(v, str):
            return v.lower()
        return v


class DatasetStats(BaseModel):
    """数据集统计信息模型"""
    total: int = Field(..., description="总数据集数量")
    total_samples: int = Field(..., description="总样本数量")
    total_size: int = Field(..., description="总存储大小")
    processing: int = Field(..., description="处理中的数据集数量")
    by_type: Dict[str, int] = Field(..., description="按类型分组的统计")
    by_status: Dict[str, int] = Field(..., description="按状态分组的统计")


class DatasetPreview(BaseModel):
    """数据集预览模型"""
    samples: List[Any] = Field(..., description="预览样本")
    total_count: int = Field(..., description="总样本数量")
    sample_fields: Optional[List[str]] = Field(None, description="样本字段列表")


class DatasetResponse(DatasetBase):
    """数据集响应模型"""
    id: int = Field(..., description="数据集ID")
    size: Optional[int] = Field(None, description="数据集大小(字节)")
    record_count: Optional[int] = Field(None, description="记录数量")
    storage_path: Optional[str] = Field(None, description="存储路径")
    status: DatasetStatus = Field(..., description="数据集状态")
    preview: Optional[List[Any]] = Field(None, description="预览数据")
    created_by: Optional[int] = Field(None, description="创建者ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    class Config:
        from_attributes = True


class DatasetListResponse(BaseModel):
    """数据集列表响应模型"""
    items: List[DatasetResponse] = Field(..., description="数据集列表")
    total: int = Field(..., description="总数量")
    page: int = Field(..., description="当前页码")
    size: int = Field(..., description="每页大小")
    pages: int = Field(..., description="总页数")


class DatasetFilter(BaseModel):
    """数据集筛选模型"""
    search: Optional[str] = Field(None, description="搜索关键词")
    dataset_type: Optional[DatasetType] = Field(None, description="数据集类型")
    status: Optional[DatasetStatus] = Field(None, description="数据集状态")
    is_public: Optional[bool] = Field(None, description="是否公开")
    created_by: Optional[int] = Field(None, description="创建者ID")
    tags: Optional[List[str]] = Field(None, description="标签筛选")
    sort_by: Optional[str] = Field("created_at", description="排序字段")
    sort_order: Optional[str] = Field("desc", description="排序方向")
    page: int = Field(1, ge=1, description="页码")
    size: int = Field(20, ge=1, le=100, description="每页大小")

    @validator('dataset_type', 'status', pre=True, check_fields=False)
    def parse_enums(cls, v):
        if v is None:
            return v
        if hasattr(v, 'value'):
            return v.value.lower()
        if isinstance(v, str):
            return v.lower()
        return v