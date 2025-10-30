#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ACWL-AI 大模型管理平台 - 主应用入口
"""

# 清理Python路径，避免导入冲突
import sys
sys.path = [p for p in sys.path if 'fastdatasets' not in p]

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import time
import os

from sqlalchemy import text
from app.core.config import settings
from app.core.database import engine, Base
from app.api.v1.api import api_router
from app.core.exceptions import ACWLException
from loguru import logger
from app.core.middleware.user_operation_logging import UserOperationLoggingMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    logger.info("🚀 ACWL-AI 平台启动中...")
    
    # 创建数据库表
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # 确保用户操作日志表存在
        await conn.execute(text(
            """
            CREATE TABLE IF NOT EXISTS user_operation_logs (
              id BIGINT AUTO_INCREMENT PRIMARY KEY,
              request_id VARCHAR(64),
              user_id BIGINT NULL,
              username VARCHAR(255),
              method VARCHAR(16),
              path TEXT,
              url TEXT,
              status_code INT,
              result_status VARCHAR(32),
              ip_address VARCHAR(64),
              duration_ms INT,
              module VARCHAR(64) COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '业务模块（如 resource、package、api 等）',
              response_status INT DEFAULT NULL COMMENT '响应状态码',
              server_host VARCHAR(128) COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '服务主机名/实例ID',
              user_agent TEXT COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '用户代理信息',
              referer VARCHAR(512) COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '来源页面',
              request_size INT DEFAULT NULL COMMENT '请求体大小（字节）',
              response_size INT DEFAULT NULL COMMENT '响应体大小（字节）',
              session_id VARCHAR(128) COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '会话ID',
              trace_id VARCHAR(128) COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '链路追踪ID',
              created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """
        ))
        await conn.execute(text(
            """
            CREATE TABLE IF NOT EXISTS user_operation_log_details (
              id BIGINT AUTO_INCREMENT PRIMARY KEY,
              log_id BIGINT,
              request_headers TEXT,
              query_params TEXT,
              request_body TEXT,
              response_body TEXT,
              error_message TEXT,
              stack_trace TEXT,
              created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
              CONSTRAINT fk_user_operation_log_details_log
                FOREIGN KEY (log_id) REFERENCES user_operation_logs(id)
                ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """
        ))
    
    logger.info("✅ 数据库初始化完成")
    
    # 启动异步任务服务
    from app.services.async_task_service import async_task_service
    await async_task_service.start()
    logger.info("✅ 异步任务服务启动完成")
    
    logger.info(f"🌐 API文档地址: http://{settings.HOST}:{settings.PORT}/docs")
    
    yield
    
    # 关闭时执行
    logger.info("🛑 ACWL-AI 平台关闭中...")
    
    # 停止异步任务服务
    await async_task_service.stop()
    logger.info("✅ 异步任务服务已停止")
    
    # 关闭MySQL连接池
    from app.core.mysql_pool import mysql_pool_manager
    await mysql_pool_manager.close_all_pools()
    logger.info("✅ MySQL连接池已关闭")
    
    logger.info("🛑 ACWL-AI 平台关闭完成")


# 创建FastAPI应用实例
app = FastAPI(
    title="ACWL-AI 大模型管理平台",
    description="企业级AI大模型管理和部署平台API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 添加用户操作日志中间件
app.add_middleware(UserOperationLoggingMiddleware)

# 可信主机中间件
if settings.ENVIRONMENT == "production":
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.ALLOWED_HOSTS
    )


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """添加请求处理时间头"""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


@app.exception_handler(ACWLException)
async def acwl_exception_handler(request: Request, exc: ACWLException):
    """自定义异常处理器"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.error_code,
            "message": exc.message,
            "detail": exc.detail
        }
    )


@app.get("/", tags=["健康检查"])
async def root():
    """根路径健康检查"""
    return {
        "message": "ACWL-AI 大模型管理平台",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }


@app.get("/health", tags=["健康检查"])
async def health_check():
    """健康检查端点"""
    return {
        "status": "healthy",
        "timestamp": time.time()
    }


# 挂载静态文件服务（前端页面）
# 新版打包 UI（ui），按 /ui 作为基准路径
ui_built_path = os.path.join(os.path.dirname(__file__), "ui")
if os.path.exists(ui_built_path):
    # 挂载静态资源目录（/ui/assets/*）
    assets_path = os.path.join(ui_built_path, "assets")
    if os.path.exists(assets_path):
        app.mount("/ui/assets", StaticFiles(directory=assets_path), name="ui_assets")
        logger.info(f"📁 前端资源已挂载: {assets_path}")

    # 提供 index.html
    @app.get("/ui", include_in_schema=False)
    async def serve_ui_index():
        return FileResponse(os.path.join(ui_built_path, "index.html"))

    # SPA 路由回退：/ui/* 都返回 index.html（资源路径除外）
    @app.get("/ui/{path:path}", include_in_schema=False)
    async def serve_ui_spa(path: str):
        return FileResponse(os.path.join(ui_built_path, "index.html"))

    logger.info(f"📁 前端页面已启用: {ui_built_path}")

# 注册API路由
app.include_router(api_router, prefix="/api/v1")


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info"
    )