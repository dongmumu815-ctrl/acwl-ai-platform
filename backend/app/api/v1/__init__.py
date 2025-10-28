#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API v1 模块初始化
"""

from fastapi import APIRouter
from . import multi_database
from .endpoints import user_operation_logs

# 创建API v1路由器
api_router = APIRouter()

# 包含多数据库路由
api_router.include_router(
    multi_database.router,
    prefix="/multi-db",
    tags=["多数据库管理"]
)

# 包含用户操作日志路由
api_router.include_router(
    user_operation_logs.router,
    prefix="/user-operation-logs",
    tags=["用户操作日志"]
)