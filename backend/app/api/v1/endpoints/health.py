#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
健康检查API端点
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import time
import psutil
from typing import Dict, Any

from app.core.database import get_db
from app.core.config import settings

router = APIRouter()


@router.get("/", summary="基础健康检查")
async def health_check() -> Dict[str, Any]:
    """基础健康检查"""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "service": "ACWL-AI",
        "version": settings.VERSION
    }


@router.get("/detailed", summary="详细健康检查")
async def detailed_health_check(db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    """详细健康检查，包括数据库连接状态"""
    
    # 检查数据库连接
    db_status = "healthy"
    db_error = None
    try:
        result = await db.execute(text("SELECT 1"))
        await result.fetchone()
    except Exception as e:
        db_status = "unhealthy"
        db_error = str(e)
    
    # 获取系统资源信息
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    return {
        "status": "healthy" if db_status == "healthy" else "unhealthy",
        "timestamp": time.time(),
        "service": "ACWL-AI",
        "version": settings.VERSION,
        "components": {
            "database": {
                "status": db_status,
                "error": db_error
            },
            "system": {
                "cpu_percent": cpu_percent,
                "memory": {
                    "total": memory.total,
                    "available": memory.available,
                    "percent": memory.percent
                },
                "disk": {
                    "total": disk.total,
                    "free": disk.free,
                    "percent": (disk.used / disk.total) * 100
                }
            }
        }
    }


@router.get("/readiness", summary="就绪检查")
async def readiness_check(db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    """就绪检查，用于Kubernetes等容器编排"""
    
    try:
        # 检查数据库连接
        result = await db.execute(text("SELECT 1"))
        await result.fetchone()
        
        return {
            "status": "ready",
            "timestamp": time.time()
        }
    except Exception as e:
        return {
            "status": "not_ready",
            "timestamp": time.time(),
            "error": str(e)
        }


@router.get("/liveness", summary="存活检查")
async def liveness_check() -> Dict[str, Any]:
    """存活检查，用于Kubernetes等容器编排"""
    return {
        "status": "alive",
        "timestamp": time.time()
    }