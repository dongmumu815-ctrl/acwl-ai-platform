#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自定义接口管理系统 - 主入口文件

这是FastAPI应用的主入口点，负责：
1. 初始化FastAPI应用
2. 配置中间件和CORS
3. 注册路由
4. 启动应用服务

Author: System
Date: 2024
"""

import uvicorn
from fastapi import FastAPI, Request, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import time
from loguru import logger

from app.core.config import settings
from app.core.database import engine, Base
from app.api.v1.router import api_router
from app.api.custom.router import custom_api_router
from app.core.logging import setup_logging
from app.core.exceptions import CustomException
from app.core.business_codes import BusinessException, BusinessResponse

# 设置日志 - 使用DEBUG级别显示更多信息
setup_logging("DEBUG")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理
    
    在应用启动时创建数据库表，在关闭时清理资源
    """
    # 启动时执行
    logger.info("🚀 正在启动应用...")
    logger.debug(f"应用名称: {settings.APP_NAME}")
    logger.debug(f"应用版本: {settings.APP_VERSION}")
    logger.debug(f"调试模式: {settings.DEBUG}")
    logger.debug(f"API前缀: {settings.API_PREFIX}")
    logger.debug(f"数据库地址: {settings.DB_HOST}:{settings.DB_PORT}")
    logger.debug(f"Redis地址: {settings.REDIS_HOST}:{settings.REDIS_PORT}")
    
    try:
        # 创建数据库表
        logger.info("📊 正在初始化数据库...")
        Base.metadata.create_all(bind=engine)
        logger.info("✅ 数据库表创建完成")
    except Exception as e:
        logger.error(f"❌ 数据库初始化失败: {e}")
        raise
    
    logger.info("🎉 应用启动完成!")
    yield
    
    # 关闭时执行
    logger.info("🛑 正在关闭应用...")


# 创建FastAPI应用实例
logger.info("🔧 正在创建FastAPI应用实例...")
app = FastAPI(
    title=settings.APP_NAME,
    description="灵活的自定义接口管理系统，支持动态创建和管理客户专用API接口",
    version=settings.APP_VERSION,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan
)
logger.debug(f"FastAPI应用创建完成 - 文档地址: {'/docs' if settings.DEBUG else '已禁用'}")

# 添加CORS中间件
logger.info("🌐 正在配置CORS中间件...")
if settings.ALLOWED_ORIGINS:
    # 如果启用iframe嵌入，需要合并iframe允许的源地址
    cors_origins = settings.ALLOWED_ORIGINS.copy()
    if settings.IFRAME_ENABLED and settings.IFRAME_ALLOWED_ORIGINS:
        # 合并iframe允许的源地址到CORS配置中
        for origin in settings.IFRAME_ALLOWED_ORIGINS:
            if origin not in cors_origins and origin != "*":
                cors_origins.append(origin)
    
    # 如果iframe配置允许所有源，则CORS也允许所有源
    if settings.IFRAME_ENABLED and "*" in settings.IFRAME_ALLOWED_ORIGINS:
        cors_origins = ["*"]
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=settings.ALLOWED_METHODS,
        allow_headers=settings.ALLOWED_HEADERS,
    )
    logger.debug(f"CORS配置完成 - 允许的源: {cors_origins}")
    if settings.IFRAME_ENABLED:
        logger.debug(f"iframe嵌入已启用 - iframe允许的源: {settings.IFRAME_ALLOWED_ORIGINS}")
else:
    logger.warning("⚠️ 未配置CORS允许的源地址")

# 添加可信主机中间件（生产环境安全）
if not settings.DEBUG:
    logger.info("🔒 正在配置可信主机中间件...")
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["localhost", "127.0.0.1", settings.HOST]
    )
    logger.debug("可信主机中间件配置完成")
else:
    logger.debug("调试模式 - 跳过可信主机中间件配置")


@app.middleware("http")
async def request_size_limit_middleware(request: Request, call_next):
    """
    请求大小限制中间件
    
    检查请求体大小，防止过大的请求消耗服务器资源
    """
    # 检查Content-Length头
    content_length = request.headers.get("content-length")
    if content_length:
        try:
            size = int(content_length)
            if size > settings.MAX_REQUEST_BODY_SIZE:
                logger.warning(
                    f"🚫 请求体过大被拒绝 - {request.method} {request.url.path} - "
                    f"大小: {size // 1024 // 1024}MB, 限制: {settings.MAX_REQUEST_BODY_SIZE // 1024 // 1024}MB"
                )
                return JSONResponse(
                    status_code=413,
                    content={
                        "error": True,
                        "message": f"请求体过大，当前{size // 1024 // 1024}MB，最大允许{settings.MAX_REQUEST_BODY_SIZE // 1024 // 1024}MB",
                        "code": 413,
                        "timestamp": int(time.time())
                    }
                )
        except ValueError:
            # Content-Length不是有效数字，继续处理
            pass
    
    return await call_next(request)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """
    添加请求处理时间中间件
    
    记录每个请求的处理时间，用于性能监控
    """
    start_time = time.time()
    
    # 记录请求开始
    client_ip = request.client.host if request.client else "unknown"
    logger.debug(f"📥 {request.method} {request.url.path} - IP: {client_ip}")
    
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    
    # 记录请求完成
    logger.debug(f"📤 {request.method} {request.url.path} - {response.status_code} - {process_time:.3f}s")
    
    # 记录慢请求
    if process_time > 1.0:  # 超过1秒的请求
        logger.warning(
            f"🐌 慢请求检测: {request.method} {request.url} - {process_time:.2f}s"
        )
    
    return response


@app.middleware("http")
async def iframe_security_middleware(request: Request, call_next):
    """
    iframe安全中间件
    
    根据配置设置适当的安全头部以支持或限制iframe嵌入
    """
    response = await call_next(request)
    
    if settings.IFRAME_ENABLED:
        # 如果启用iframe嵌入，设置相应的安全头部
        if settings.X_FRAME_OPTIONS.upper() == "ALLOW-ALL":
            # 不设置X-Frame-Options头部，允许所有域名嵌入
            pass
        elif settings.X_FRAME_OPTIONS.upper() == "SAMEORIGIN":
            response.headers["X-Frame-Options"] = "SAMEORIGIN"
        elif settings.X_FRAME_OPTIONS.upper() == "DENY":
            response.headers["X-Frame-Options"] = "DENY"
        
        # 设置Content-Security-Policy的frame-ancestors指令
        if settings.CSP_FRAME_ANCESTORS == "*":
            # 允许所有域名嵌入
            response.headers["Content-Security-Policy"] = "frame-ancestors *;"
        elif settings.CSP_FRAME_ANCESTORS.upper() == "NONE":
            # 不允许任何域名嵌入
            response.headers["Content-Security-Policy"] = "frame-ancestors 'none';"
        elif settings.CSP_FRAME_ANCESTORS.upper() == "SELF":
            # 只允许同源嵌入
            response.headers["Content-Security-Policy"] = "frame-ancestors 'self';"
        else:
            # 允许指定域名嵌入
            response.headers["Content-Security-Policy"] = f"frame-ancestors {settings.CSP_FRAME_ANCESTORS};"
        
        logger.debug(f"🖼️ iframe安全头部已设置 - X-Frame-Options: {response.headers.get('X-Frame-Options', '未设置')}, CSP: {response.headers.get('Content-Security-Policy', '未设置')}")
    else:
        # 如果禁用iframe嵌入，设置严格的安全头部
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Content-Security-Policy"] = "frame-ancestors 'none';"
        logger.debug("🚫 iframe嵌入已禁用 - 设置了严格的安全头部")
    
    return response


# 异常处理器注册顺序很重要，具体的异常类型要在通用异常类型之前注册

@app.exception_handler(BusinessException)
async def business_exception_handler(request: Request, exc: BusinessException):
    """
    业务异常处理器
    
    统一处理业务异常，返回业务状态码格式
    """
    logger.error(f"业务异常: {exc.business_code.message} - {request.url}")
    return JSONResponse(
        status_code=200,  # HTTP层始终返回200
        content=BusinessResponse.error(exc.business_code, exc.detail)
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    参数验证异常处理器
    
    将参数验证错误转换为业务状态码格式
    """
    from app.core.business_codes import BusinessCode
    logger.warning(f"参数验证失败: {exc.errors()} - {request.url}")
    return JSONResponse(
        status_code=200,  # HTTP层始终返回200
        content=BusinessResponse.error(BusinessCode.PARAM_ERROR)
    )


@app.exception_handler(CustomException)
async def custom_exception_handler(request: Request, exc: CustomException):
    """
    自定义异常处理器
    
    统一处理应用中的自定义异常
    """
    logger.error(f"自定义异常: {exc.message} - {request.url}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "message": exc.message,
            "code": exc.error_code,
            "timestamp": int(time.time())
        }
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """
    HTTP异常处理器
    
    统一处理HTTP异常响应格式，按照API文档规范返回数字错误码
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "message": exc.detail,
            "code": exc.status_code,  # 返回数字错误码，符合API文档规范
            "timestamp": int(time.time())
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """
    通用异常处理器
    
    处理所有未捕获的异常，但要排除已经处理的业务异常
    """
    # 检查是否是业务异常，如果是则重新抛出让业务异常处理器处理
    if isinstance(exc, BusinessException):
        return await business_exception_handler(request, exc)
    
    # 安全地记录异常信息，避免格式化错误
    try:
        logger.error(f"未处理异常: {str(exc)} - {request.url}", exc_info=True)
    except Exception as log_error:
        # 如果日志记录失败，使用更安全的方式
        logger.error("未处理异常发生，详情请查看异常堆栈", exc_info=True)
        logger.error(f"日志记录错误: {str(log_error)}")
    
    return JSONResponse(
        status_code=500,
        content={
            "error": True,
            "message": "服务器内部错误" if not settings.DEBUG else str(exc),
            "code": 500,  # 返回数字错误码，符合API文档规范
            "timestamp": int(time.time())
        }
    )


# 健康检查端点
@app.get("/health")
async def health_check():
    """
    健康检查接口
    
    用于监控系统运行状态
    """
    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "timestamp": int(time.time())
    }


# 系统信息端点
@app.get("/info")
async def system_info():
    """
    系统信息接口
    
    返回系统基本信息（仅在调试模式下可用）
    """
    if not settings.DEBUG:
        raise HTTPException(status_code=404, detail="Not found")
    
    return {
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "debug": settings.DEBUG,
        "database_url": settings.DATABASE_URL.replace(settings.DB_PASSWORD, "***"),
        "redis_url": settings.REDIS_URL,
        "timestamp": int(time.time())
    }


# 注册路由
logger.info("🛣️ 正在注册API路由...")
app.include_router(
    api_router,
    prefix=settings.API_PREFIX,
    tags=["管理接口"]
)
logger.debug(f"✅ 管理接口路由注册完成 - 前缀: {settings.API_PREFIX}")

app.include_router(
    custom_api_router,
    prefix=settings.CUSTOM_API_PREFIX,
    tags=["自定义接口"]
)
logger.debug(f"✅ 自定义接口路由注册完成 - 前缀: {settings.CUSTOM_API_PREFIX}")
logger.info("🎯 所有路由注册完成!")


if __name__ == "__main__":
    """
    直接运行时的入口点
    
    用于开发环境快速启动
    """
    logger.info(f"启动 {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"调试模式: {settings.DEBUG}")
    logger.info(f"监听地址: {settings.HOST}:{settings.PORT}")
    
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        workers=1 if settings.DEBUG else settings.WORKERS,
        log_level=settings.LOG_LEVEL.lower(),
        access_log=True
    )