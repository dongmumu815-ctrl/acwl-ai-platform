#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基础Schema定义
"""

from pydantic import BaseModel, Field
from typing import Optional


class BaseQueryParams(BaseModel):
    """基础查询参数Schema"""
    page: int = Field(1, ge=1, description="页码")
    size: int = Field(10, ge=1, le=100, description="每页大小")
    search: Optional[str] = Field(None, description="搜索关键词")
    sort_by: Optional[str] = Field(None, description="排序字段")
    sort_order: Optional[str] = Field("asc", pattern="^(asc|desc)$", description="排序方向")


class BaseListResponse(BaseModel):
    """基础列表响应Schema"""
    total: int = Field(..., description="总数")
    page: int = Field(..., description="当前页")
    size: int = Field(..., description="每页大小")
    pages: int = Field(..., description="总页数")