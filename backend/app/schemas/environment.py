#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
环境管理相关的Pydantic Schema
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime

from app.schemas.common import PaginatedResponse


class EnvironmentBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="环境名称")
    config: Optional[Dict[str, Any]] = Field(default=None, description="环境配置(JSON)")
    description: Optional[str] = Field(default=None, description="环境描述")


class EnvironmentCreate(EnvironmentBase):
    pass


class EnvironmentUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="环境名称")
    config: Optional[Dict[str, Any]] = Field(default=None, description="环境配置(JSON)")
    description: Optional[str] = Field(default=None, description="环境描述")


class EnvironmentInDB(EnvironmentBase):
    model_config = {"from_attributes": True}

    id: int
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime


class EnvironmentResponse(EnvironmentInDB):
    pass


class EnvironmentListResponse(PaginatedResponse[EnvironmentResponse]):
    pass