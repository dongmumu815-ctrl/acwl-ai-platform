#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
资源类型管理相关 Pydantic 模式
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime


class ResourceTypeBase(BaseModel):
    """资源类型基础模式"""
    name: str = Field(..., description="类型名称", max_length=255)
    describe: Optional[str] = Field(None, description="字段描述", max_length=255)
    # 元数据：前端以多个字段对象的列表保存
    metadata: Optional[List[Dict[str, Any]]] = Field(None, description="字段管理(JSON)")


class ResourceTypeCreate(ResourceTypeBase):
    """创建资源类型模式"""
    pass


class ResourceTypeUpdate(BaseModel):
    """更新资源类型模式"""
    name: Optional[str] = Field(None, description="类型名称", max_length=255)
    describe: Optional[str] = Field(None, description="字段描述", max_length=255)
    metadata: Optional[List[Dict[str, Any]]] = Field(None, description="字段管理(JSON)")


class ResourceTypeResponse(ResourceTypeBase):
    """资源类型响应模式"""
    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="ID")
    create_time: Optional[datetime] = Field(None, description="创建时间")
    update_time: Optional[datetime] = Field(None, description="更新时间")


class ResourceTypeListResponse(BaseModel):
    """资源类型列表响应模式"""
    items: List[ResourceTypeResponse] = Field(..., description="列表")
    total: int = Field(..., description="总数")
    page: int = Field(..., description="页码")
    size: int = Field(..., description="每页大小")
    pages: int = Field(..., description="总页数")