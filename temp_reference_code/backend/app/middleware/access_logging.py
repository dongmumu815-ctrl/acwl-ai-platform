#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
访问日志中间件

自动记录所有API请求的访问日志，包括详细的请求和响应信息。
支持同时记录到本地文件和Doris数据库。

Author: System
Date: 2024
"""

import time
import uuid
from typing import Callable
from urllib.parse import urlparse

from fastapi import Request, Response
from fastapi.responses import StreamingResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.core.logging import log_api_access
from loguru import logger


class AccessLoggingMiddleware(BaseHTTPMiddleware):
    """
    访问日志中间件
    
    自动记录所有HTTP请求的详细信息
    """
    
    def __init__(self, app: ASGIApp, exclude_paths: list = None):
        """
        初始化访问日志中间件
        
        Args:
            app: ASGI应用实例
            exclude_paths: 排除记录的路径列表
        """
        super().__init__(app)
        self.exclude_paths = exclude_paths or [
            "/health",
            "/metrics",
            "/favicon.ico",
            "/docs",
            "/redoc",
            "/openapi.json"
        ]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        处理请求并记录访问日志
        
        Args:
            request: HTTP请求对象
            call_next: 下一个中间件或路由处理器
        
        Returns:
            Response: HTTP响应对象
        """
        # 检查是否需要排除此路径
        if self._should_exclude_path(request.url.path):
            return await call_next(request)
        
        # 生成请求ID
        request_id = str(uuid.uuid4())
        
        # 记录请求开始时间
        start_time = time.time()
        
        # 获取请求信息
        request_info = await self._extract_request_info(request, request_id)
        
        # 处理请求
        try:
            response = await call_next(request)
            
            # 计算响应时间
            response_time = time.time() - start_time
            
            # 获取响应信息
            response_info = await self._extract_response_info(response)
            
            # 记录访问日志
            await self._log_access(
                request_info=request_info,
                response_info=response_info,
                response_time=response_time
            )
            
            return response
            
        except Exception as e:
            # 计算响应时间
            response_time = time.time() - start_time
            
            # 记录错误访问日志
            await self._log_access(
                request_info=request_info,
                response_info={
                    "status_code": 500,
                    "response_size": 0
                },
                response_time=response_time,
                error_message=str(e)
            )
            
            # 重新抛出异常
            raise e
    
    def _should_exclude_path(self, path: str) -> bool:
        """
        检查路径是否应该被排除
        
        Args:
            path: 请求路径
        
        Returns:
            bool: 是否应该排除
        """
        for exclude_path in self.exclude_paths:
            if path.startswith(exclude_path):
                return True
        return False
    
    async def _extract_request_info(self, request: Request, request_id: str) -> dict:
        """
        提取请求信息
        
        Args:
            request: HTTP请求对象
            request_id: 请求ID
        
        Returns:
            dict: 请求信息字典
        """
        # 获取客户端IP
        client_ip = self._get_client_ip(request)
        
        # 获取用户代理
        user_agent = request.headers.get("user-agent", "")
        
        # 获取引用页面
        referer = request.headers.get("referer", "")
        
        # 获取API密钥（如果存在）
        api_key = request.headers.get("x-api-key") or request.headers.get("authorization")
        if api_key and api_key.startswith("Bearer "):
            api_key = api_key[7:]  # 移除 "Bearer " 前缀
        
        # 获取会话ID
        session_id = request.headers.get("x-session-id") or request.cookies.get("session_id")
        
        # 获取用户ID（从请求状态中，如果已认证）
        user_id = getattr(request.state, "user_id", None)
        
        # 计算请求大小
        request_size = 0
        if hasattr(request, "_body"):
            request_size = len(request._body) if request._body else 0
        else:
            # 尝试从Content-Length头获取
            content_length = request.headers.get("content-length")
            if content_length:
                try:
                    request_size = int(content_length)
                except ValueError:
                    pass
        
        return {
            "request_id": request_id,
            "method": request.method,
            "url": str(request.url),
            "path": request.url.path,
            "query_params": str(request.query_params) if request.query_params else "",
            "client_ip": client_ip,
            "user_agent": user_agent,
            "referer": referer,
            "api_key": api_key,
            "session_id": session_id,
            "user_id": user_id,
            "request_size": request_size
        }
    
    async def _extract_response_info(self, response: Response) -> dict:
        """
        提取响应信息
        
        Args:
            response: HTTP响应对象
        
        Returns:
            dict: 响应信息字典
        """
        # 获取响应大小
        response_size = 0
        
        if hasattr(response, "body") and response.body:
            response_size = len(response.body)
        elif isinstance(response, StreamingResponse):
            # 对于流式响应，无法准确计算大小
            response_size = 0
        else:
            # 尝试从Content-Length头获取
            content_length = response.headers.get("content-length")
            if content_length:
                try:
                    response_size = int(content_length)
                except ValueError:
                    pass
        
        return {
            "status_code": response.status_code,
            "response_size": response_size
        }
    
    def _get_client_ip(self, request: Request) -> str:
        """
        获取客户端真实IP地址
        
        考虑代理和负载均衡器的情况
        
        Args:
            request: HTTP请求对象
        
        Returns:
            str: 客户端IP地址
        """
        # 检查常见的代理头
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            # X-Forwarded-For可能包含多个IP，取第一个
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        forwarded = request.headers.get("x-forwarded")
        if forwarded:
            return forwarded
        
        # 如果没有代理头，使用客户端IP
        if hasattr(request, "client") and request.client:
            return request.client.host
        
        return "unknown"
    
    async def _log_access(self, request_info: dict, response_info: dict,
                         response_time: float, error_message: str = None):
        """
        记录访问日志
        
        Args:
            request_info: 请求信息
            response_info: 响应信息
            response_time: 响应时间
            error_message: 错误信息
        """
        try:
            # 调用日志记录函数
            log_api_access(
                method=request_info["method"],
                url=request_info["url"],
                status_code=response_info["status_code"],
                response_time=response_time,
                client_ip=request_info["client_ip"],
                user_agent=request_info["user_agent"],
                user_id=request_info["user_id"],
                request_size=request_info["request_size"],
                response_size=response_info["response_size"],
                referer=request_info["referer"],
                session_id=request_info["session_id"],
                api_key=request_info["api_key"],
                error_message=error_message
            )
            
        except Exception as e:
            # 记录日志失败不应该影响正常请求处理
            logger.error(f"记录访问日志失败: {e}")


def create_access_logging_middleware(exclude_paths: list = None) -> AccessLoggingMiddleware:
    """
    创建访问日志中间件
    
    Args:
        exclude_paths: 排除记录的路径列表
    
    Returns:
        AccessLoggingMiddleware: 访问日志中间件实例
    """
    return AccessLoggingMiddleware(exclude_paths=exclude_paths)