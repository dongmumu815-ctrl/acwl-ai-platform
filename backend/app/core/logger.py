#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志配置模块

提供统一的日志配置和记录器
"""

import logging
import sys
from pathlib import Path
from typing import Optional


def setup_logger(
    name: str = "acwl",
    level: str = "INFO",
    log_file: Optional[str] = None,
    format_string: Optional[str] = None
) -> logging.Logger:
    """
    设置日志记录器
    
    Args:
        name: 记录器名称
        level: 日志级别
        log_file: 日志文件路径
        format_string: 日志格式字符串
        
    Returns:
        配置好的日志记录器
    """
    if format_string is None:
        format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # 创建记录器
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # 清除现有的处理器，确保不重复添加
    if logger.handlers:
        logger.handlers.clear()
    
    # 创建格式化器
    formatter = logging.Formatter(format_string)
    
    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, level.upper()))
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 确保立即输出
    console_handler.flush = sys.stdout.flush
    
    # 文件处理器（如果指定了日志文件）
    if log_file:
        # 确保日志目录存在
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(getattr(logging, level.upper()))
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


# 创建默认的日志记录器
logger = setup_logger(
    name="acwl",
    level="INFO",
    log_file="logs/app.log"
)

# 为不同模块创建专用记录器
executor_logger = setup_logger(
    name="acwl.executor",
    level="INFO",
    log_file="logs/executor.log"
)

scheduler_logger = setup_logger(
    name="acwl.scheduler",
    level="INFO",
    log_file="logs/scheduler.log"
)

cluster_logger = setup_logger(
    name="acwl.cluster",
    level="INFO",
    log_file="logs/cluster.log"
)


def get_logger(name: str = "acwl") -> logging.Logger:
    """
    获取指定名称的日志记录器
    
    Args:
        name: 记录器名称
        
    Returns:
        日志记录器
    """
    return logging.getLogger(name)