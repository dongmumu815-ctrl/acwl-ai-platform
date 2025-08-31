#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模型相关的Pydantic Schema
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

from app.models.model import ModelType
from app.schemas.common import PaginatedResponse


# ============================================
# 基础Schema
# ============================================

class ModelBase(BaseModel):
    """模型基础Schema"""
    name: str = Field(..., min_length=1, max_length=100, description="模型名称")
    version: str = Field(..., min_length=1, max_length=50, description="模型版本")
    description: Optional[str] = Field(None, description="模型描述")
    base_model: Optional[str] = Field(None, max_length=100, description="基础模型名称")
    model_type: ModelType = Field(..., description="模型类型")
    model_size: Optional[int] = Field(None, ge=0, description="模型大小(字节)")
    parameters: Optional[int] = Field(None, ge=0, description="参数量")
    framework: Optional[str] = Field(None, max_length=50, description="框架，如PyTorch、TensorFlow等")
    quantization: Optional[str] = Field(None, max_length=20, description="量化类型，如FP16、INT8等")
    source_url: Optional[str] = Field(None, description="模型下载地址")
    local_path: Optional[str] = Field(None, description="本地存储路径")
    is_active: bool = Field(True, description="是否激活")


class ModelCreate(ModelBase):
    """创建模型Schema"""
    pass


class ModelUpdate(BaseModel):
    """更新模型Schema"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="模型名称")
    version: Optional[str] = Field(None, min_length=1, max_length=50, description="模型版本")
    description: Optional[str] = Field(None, description="模型描述")
    base_model: Optional[str] = Field(None, max_length=100, description="基础模型名称")
    model_type: Optional[ModelType] = Field(None, description="模型类型")
    model_size: Optional[int] = Field(None, ge=0, description="模型大小(字节)")
    parameters: Optional[int] = Field(None, ge=0, description="参数量")
    framework: Optional[str] = Field(None, max_length=50, description="框架，如PyTorch、TensorFlow等")
    quantization: Optional[str] = Field(None, max_length=20, description="量化类型，如FP16、INT8等")
    source_url: Optional[str] = Field(None, description="模型下载地址")
    local_path: Optional[str] = Field(None, description="本地存储路径")
    is_active: Optional[bool] = Field(None, description="是否激活")


class ModelInDB(ModelBase):
    """数据库中的模型Schema"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    created_at: datetime
    updated_at: datetime


class ModelResponse(ModelInDB):
    """模型响应Schema"""
    pass


class ModelListResponse(PaginatedResponse):
    """模型列表响应Schema"""
    data: List[ModelResponse]


# ============================================
# Agent配置专用Schema
# ============================================

class ModelForAgent(BaseModel):
    """用于Agent配置的模型Schema"""
    label: str = Field(..., description="显示标签")
    value: str = Field(..., description="模型值")
    model_id: int = Field(..., description="模型ID")
    description: Optional[str] = Field(None, description="模型描述")


class ModelStatsResponse(BaseModel):
    """模型统计响应Schema"""
    total_count: int = Field(..., description="总数量")
    active_count: int = Field(..., description="激活数量")
    total_size: int = Field(..., description="总大小(字节)")
    by_type: Dict[str, int] = Field(..., description="按类型统计")
    by_framework: Dict[str, int] = Field(..., description="按框架统计")