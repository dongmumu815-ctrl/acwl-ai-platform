#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
服务器分组 API 模式
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

# 基础模型
class ServerGroupBase(BaseModel):
    name: str = Field(..., description="分组名称")
    description: Optional[str] = Field(None, description="分组描述")

# 创建模型
class ServerGroupCreate(ServerGroupBase):
    pass

# 更新模型
class ServerGroupUpdate(ServerGroupBase):
    name: Optional[str] = Field(None, description="分组名称")

# 响应模型
class ServerGroupResponse(ServerGroupBase):
    id: int = Field(..., description="分组ID")
    created_at: datetime
    updated_at: datetime
    server_count: int = Field(0, description="服务器数量")

    class Config:
        from_attributes = True

# 列表响应
class ServerGroupListResponse(BaseModel):
    total: int
    items: List[ServerGroupResponse]
