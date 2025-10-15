#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ACWL AI Backend Main Application
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from app.api.v1.api import api_router
from app.api.v1.multi_database import router as multi_db_router
from app.core.config import settings
from app.core.database import init_db, close_db
from app.core.multi_db_manager import get_multi_db_manager
from app.core.exceptions import ACWLException
import logging

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理
    
    在应用启动时初始化数据库和多数据库管理器，
    在关闭时清理所有资源
    """
    # 启动时初始化数据库（添加错误处理）
    try:
        await init_db()
        logger.info("主数据库初始化成功")
    except Exception as e:
        logger.warning(f"主数据库初始化失败，应用将继续启动: {e}")
        logger.info("应用将使用多数据库功能，主数据库功能可能不可用")
    
    # 初始化多数据库管理器
    try:
        multi_db_manager = await get_multi_db_manager()
        logger.info("多数据库管理器初始化成功")
    except Exception as e:
        logger.error(f"多数据库管理器初始化失败: {e}")
    
    yield
    
    # 关闭时清理资源
    try:
        await close_db()
        logger.info("主数据库连接已关闭")
    except Exception as e:
        logger.warning(f"关闭主数据库连接失败: {e}")
    
    # 关闭多数据库连接
    try:
        multi_db_manager = await get_multi_db_manager()
        await multi_db_manager.close_all()
        logger.info("多数据库连接已关闭")
    except Exception as e:
        logger.error(f"关闭多数据库连接失败: {e}")

app = FastAPI(
    title="ACWL AI Backend",
    description="ACWL AI Platform Backend API",
    version="1.0.0",
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    lifespan=lifespan
)


@app.exception_handler(ACWLException)
async def acwl_exception_handler(request: Request, exc: ACWLException):
    """
    处理自定义ACWL异常
    
    Args:
        request: FastAPI请求对象
        exc: ACWL自定义异常
    
    Returns:
        JSONResponse: 格式化的错误响应
    """
    logger.error(f"ACWL异常: {exc.message} - 状态码: {exc.status_code} - 错误代码: {exc.error_code}")
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.error_code,
            "message": exc.message,
            "detail": exc.detail
        }
    )

# Set up CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix=settings.API_V1_PREFIX)

# 包含多数据库管理路由
app.include_router(
    multi_db_router, 
    prefix=f"{settings.API_V1_PREFIX}/multi-db",
    tags=["多数据库管理"]
)

@app.get("/")
async def root():
    return {"message": "ACWL AI Backend API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3005)