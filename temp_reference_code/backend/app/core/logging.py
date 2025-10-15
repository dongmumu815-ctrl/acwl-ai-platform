#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志配置模块

使用loguru库提供结构化日志记录功能。
支持文件轮转、日志级别控制和格式化输出。

Author: System
Date: 2024
"""

import sys
import os
from loguru import logger
from typing import Optional

from app.core.config import settings
from app.core.doris_client import log_api_access_to_doris


def setup_logging(log_level: Optional[str] = None) -> None:
    """
    设置应用日志配置
    
    配置loguru日志记录器，包括控制台输出和文件输出。
    支持日志轮转和保留策略。
    
    Args:
        log_level: 日志级别，如果不指定则使用配置文件中的设置
    """
    # 移除默认处理器
    logger.remove()
    
    # 添加异常处理，确保日志配置失败不会影响应用启动
    try:
        _configure_loggers(log_level)
    except Exception as e:
        # 如果日志配置失败，至少保证控制台输出可用
        logger.add(
            sys.stdout,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
            level="INFO",
            colorize=True
        )
        logger.error(f"日志配置失败，使用简化配置: {e}")


def _configure_loggers(log_level: Optional[str] = None) -> None:
    """
    内部日志配置函数
    
    Args:
        log_level: 日志级别
    """
    
    # 确定日志级别
    level = log_level or settings.LOG_LEVEL
    
    # 控制台日志格式
    console_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    )
    
    # 文件日志格式
    file_format = (
        "{time:YYYY-MM-DD HH:mm:ss.SSS} | "
        "{level: <8} | "
        "{name}:{function}:{line} | "
        "{message}"
    )
    
    # 添加控制台处理器
    logger.add(
        sys.stdout,
        format=console_format,
        level=level,
        colorize=True,
        backtrace=True,
        diagnose=True
    )
    
    # 确保日志目录存在
    log_dir = os.path.dirname(settings.LOG_PATH)
    os.makedirs(log_dir, exist_ok=True)
    
    # 添加文件处理器 - 普通日志
    # 使用enqueue=True避免多进程文件锁定问题
    logger.add(
        settings.LOG_PATH,
        format=file_format,
        level=level,
        rotation=settings.LOG_ROTATION,
        retention=settings.LOG_RETENTION,
        compression="zip",
        backtrace=True,
        diagnose=True,
        encoding="utf-8",
        enqueue=True,  # 启用队列模式，避免文件锁定
        catch=True     # 捕获日志记录过程中的异常
    )
    
    # 添加错误日志文件处理器
    error_log_path = settings.LOG_PATH.replace(".log", "_error.log")
    logger.add(
        error_log_path,
        format=file_format,
        level="ERROR",
        rotation=settings.LOG_ROTATION,
        retention=settings.LOG_RETENTION,
        compression="zip",
        backtrace=True,
        diagnose=True,
        encoding="utf-8",
        enqueue=True,  # 启用队列模式，避免文件锁定
        catch=True     # 捕获日志记录过程中的异常
    )
    
    # 添加访问日志文件处理器
    access_log_path = settings.LOG_PATH.replace(".log", "_access.log")
    logger.add(
        access_log_path,
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {message}",
        level="INFO",
        rotation=settings.LOG_ROTATION,
        retention=settings.LOG_RETENTION,
        compression="zip",
        filter=lambda record: "ACCESS" in record["extra"],
        encoding="utf-8",
        enqueue=True,  # 启用队列模式，避免文件锁定
        catch=True     # 捕获日志记录过程中的异常
    )
    
    logger.info(f"日志系统初始化完成 - 级别: {level}")


def get_logger(name: str):
    """
    获取指定名称的日志记录器
    
    Args:
        name: 日志记录器名称
    
    Returns:
        Logger: loguru日志记录器实例
    """
    return logger.bind(name=name)


def log_api_access(method: str, url: str, status_code: int, 
                  response_time: float, client_ip: str = None,
                  user_agent: str = None, user_id: str = None,
                  request_size: int = None, response_size: int = None,
                  referer: str = None, session_id: str = None,
                  api_key: str = None, error_message: str = None):
    """
    记录API访问日志
    
    同时记录到本地文件和Doris数据库（如果启用）
    
    Args:
        method: HTTP方法
        url: 请求URL
        status_code: 响应状态码
        response_time: 响应时间（秒）
        client_ip: 客户端IP
        user_agent: 用户代理
        user_id: 用户ID
        request_size: 请求大小（字节）
        response_size: 响应大小（字节）
        referer: 引用页面
        session_id: 会话ID
        api_key: API密钥
        error_message: 错误信息
    """
    access_info = {
        "method": method,
        "url": url,
        "status_code": status_code,
        "response_time": f"{response_time:.3f}s",
        "client_ip": client_ip or "unknown",
        "user_agent": user_agent or "unknown",
        "user_id": user_id or "anonymous"
    }
    
    # 构建访问日志消息
    message = (
        f"{method} {url} {status_code} {response_time:.3f}s "
        f"- IP: {client_ip} - User: {user_id or 'anonymous'}"
    )
    
    # 记录到本地文件
    logger.bind(ACCESS=True).info(message)
    
    # 记录到Doris（如果启用）
    try:
        log_api_access_to_doris(
            method=method,
            url=url,
            status_code=status_code,
            response_time=response_time,
            client_ip=client_ip or "unknown",
            user_agent=user_agent,
            user_id=user_id,
            request_size=request_size,
            response_size=response_size,
            referer=referer,
            session_id=session_id,
            api_key=api_key,
            error_message=error_message
        )
    except Exception as e:
        logger.error(f"记录访问日志到Doris失败: {e}")


def log_database_operation(operation: str, table: str, 
                         execution_time: float = None,
                         affected_rows: int = None,
                         error: str = None):
    """
    记录数据库操作日志
    
    Args:
        operation: 操作类型（SELECT, INSERT, UPDATE, DELETE等）
        table: 表名
        execution_time: 执行时间（秒）
        affected_rows: 影响的行数
        error: 错误信息
    """
    if error:
        logger.error(
            f"数据库操作失败 - {operation} {table}: {error}"
        )
    else:
        message = f"数据库操作 - {operation} {table}"
        if execution_time is not None:
            message += f" - 耗时: {execution_time:.3f}s"
        if affected_rows is not None:
            message += f" - 影响行数: {affected_rows}"
        
        logger.info(message)


def log_security_event(event_type: str, description: str, 
                      client_ip: str = None, user_id: str = None,
                      severity: str = "WARNING"):
    """
    记录安全事件日志
    
    Args:
        event_type: 事件类型（LOGIN_FAILED, UNAUTHORIZED_ACCESS等）
        description: 事件描述
        client_ip: 客户端IP
        user_id: 用户ID
        severity: 严重程度（INFO, WARNING, ERROR, CRITICAL）
    """
    message = (
        f"安全事件 [{event_type}] - {description} "
        f"- IP: {client_ip or 'unknown'} "
        f"- User: {user_id or 'unknown'}"
    )
    
    if severity.upper() == "CRITICAL":
        logger.critical(message)
    elif severity.upper() == "ERROR":
        logger.error(message)
    elif severity.upper() == "WARNING":
        logger.warning(message)
    else:
        logger.info(message)


def log_business_operation(operation: str, details: dict = None,
                         user_id: str = None, success: bool = True):
    """
    记录业务操作日志
    
    Args:
        operation: 操作名称
        details: 操作详情字典
        user_id: 操作用户ID
        success: 操作是否成功
    """
    status = "成功" if success else "失败"
    message = f"业务操作 [{operation}] {status} - 用户: {user_id or 'system'}"
    
    if details:
        detail_str = ", ".join([f"{k}: {v}" for k, v in details.items()])
        message += f" - 详情: {detail_str}"
    
    if success:
        logger.info(message)
    else:
        logger.error(message)


class LoggerMixin:
    """
    日志记录器混入类
    
    为其他类提供便捷的日志记录功能
    """
    
    @property
    def logger(self):
        """
        获取当前类的日志记录器
        
        Returns:
            Logger: 绑定了类名的日志记录器
        """
        return logger.bind(name=self.__class__.__name__)
    
    def log_info(self, message: str, **kwargs):
        """记录信息日志"""
        self.logger.info(message, **kwargs)
    
    def log_warning(self, message: str, **kwargs):
        """记录警告日志"""
        self.logger.warning(message, **kwargs)
    
    def log_error(self, message: str, **kwargs):
        """记录错误日志"""
        self.logger.error(message, **kwargs)
    
    def log_debug(self, message: str, **kwargs):
        """记录调试日志"""
        self.logger.debug(message, **kwargs)
    
    def log_critical(self, message: str, **kwargs):
        """记录严重错误日志"""
        self.logger.critical(message, **kwargs)


# 创建专用日志记录器
api_logger = get_logger("API")
db_logger = get_logger("DATABASE")
security_logger = get_logger("SECURITY")
business_logger = get_logger("BUSINESS")


if __name__ == "__main__":
    # 测试日志功能
    setup_logging("DEBUG")
    
    logger.info("这是一条信息日志")
    logger.warning("这是一条警告日志")
    logger.error("这是一条错误日志")
    
    # 测试API访问日志
    log_api_access(
        method="GET",
        url="/api/v1/users",
        status_code=200,
        response_time=0.123,
        client_ip="192.168.1.100",
        user_id="user123"
    )
    
    # 测试数据库操作日志
    log_database_operation(
        operation="SELECT",
        table="users",
        execution_time=0.045,
        affected_rows=10
    )
    
    # 测试安全事件日志
    log_security_event(
        event_type="LOGIN_FAILED",
        description="用户登录失败，密码错误",
        client_ip="192.168.1.100",
        user_id="user123",
        severity="WARNING"
    )
    
    # 测试业务操作日志
    log_business_operation(
        operation="创建用户",
        details={"username": "testuser", "email": "test@example.com"},
        user_id="admin",
        success=True
    )
    
    print("日志测试完成，请查看日志文件")