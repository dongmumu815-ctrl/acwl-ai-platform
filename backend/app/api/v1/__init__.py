#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API v1 模块初始化
"""

from fastapi import APIRouter
from . import multi_database

# 创建API v1路由器
api_router = APIRouter()

# 包含多数据库路由
api_router.include_router(
    multi_database.router,
    prefix="/multi-db",
    tags=["多数据库管理"]
)

# 如果有其他路由模块，也可以在这里包含
# api_router.include_router(other_router, prefix="/other", tags=["其他"])