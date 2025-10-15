#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gunicorn配置文件

生产环境的Gunicorn服务器配置
提供优化的性能和安全设置

Author: System
Date: 2024
"""

import multiprocessing
import os
from pathlib import Path

# 基础配置
bind = "0.0.0.0:8080"  # 绑定地址和端口
backlog = 2048  # 等待连接的最大数量

# Worker配置
workers = multiprocessing.cpu_count() * 2 + 1  # 工作进程数：CPU核心数 * 2 + 1
worker_class = "uvicorn.workers.UvicornWorker"  # 使用Uvicorn worker类
worker_connections = 1000  # 每个worker的最大并发连接数
max_requests = 1000  # 每个worker处理的最大请求数后重启
max_requests_jitter = 50  # 重启抖动，避免所有worker同时重启

# 超时配置
timeout = 30  # worker超时时间（秒）
keepalive = 2  # Keep-Alive连接保持时间（秒）
graceful_timeout = 30  # 优雅关闭超时时间（秒）

# 性能优化
preload_app = True  # 预加载应用，提高启动速度和内存使用效率
reuse_port = True  # 启用端口重用（Linux/macOS）

# 日志配置
accesslog = "-"  # 访问日志输出到stdout
errorlog = "-"   # 错误日志输出到stderr
loglevel = "info"  # 日志级别：debug, info, warning, error, critical
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# 进程管理
pidfile = "/tmp/gunicorn.pid"  # PID文件路径
user = None  # 运行用户（生产环境建议设置为非root用户）
group = None  # 运行组
tmp_upload_dir = None  # 临时上传目录

# 安全配置
limit_request_line = 4094  # HTTP请求行的最大大小
limit_request_fields = 100  # HTTP请求头字段的最大数量
limit_request_field_size = 8190  # HTTP请求头字段的最大大小

# SSL配置（如果需要HTTPS）
# keyfile = "/path/to/keyfile"
# certfile = "/path/to/certfile"
# ssl_version = ssl.PROTOCOL_TLS
# ciphers = "TLSv1"

# 环境变量
raw_env = [
    'PYTHONPATH=/app',
]

# 钩子函数
def on_starting(server):
    """
    服务器启动时调用
    """
    server.log.info("🚀 Gunicorn服务器正在启动...")
    server.log.info(f"📍 监听地址: {bind}")
    server.log.info(f"👥 工作进程数: {workers}")
    server.log.info(f"🔧 Worker类型: {worker_class}")


def on_reload(server):
    """
    服务器重载时调用
    """
    server.log.info("🔄 Gunicorn服务器正在重载...")


def when_ready(server):
    """
    服务器准备就绪时调用
    """
    server.log.info("✅ Gunicorn服务器启动完成!")
    server.log.info(f"🌐 服务地址: http://localhost:8080")
    server.log.info(f"📖 API文档: http://localhost:8080/docs")


def on_exit(server):
    """
    服务器退出时调用
    """
    server.log.info("🛑 Gunicorn服务器正在关闭...")


def worker_int(worker):
    """
    Worker进程收到SIGINT信号时调用
    """
    worker.log.info(f"🔄 Worker {worker.pid} 收到中断信号")


def pre_fork(server, worker):
    """
    Worker进程fork之前调用
    """
    server.log.info(f"👶 正在创建Worker进程 {worker.age}")


def post_fork(server, worker):
    """
    Worker进程fork之后调用
    """
    server.log.info(f"✅ Worker进程 {worker.pid} 创建完成")


def post_worker_init(worker):
    """
    Worker进程初始化完成后调用
    """
    worker.log.info(f"🎯 Worker {worker.pid} 初始化完成")


def worker_abort(worker):
    """
    Worker进程异常退出时调用
    """
    worker.log.error(f"💥 Worker {worker.pid} 异常退出")


# 开发环境配置覆盖
if os.getenv('ENVIRONMENT') == 'development':
    # 开发环境使用更少的worker和更详细的日志
    workers = 1
    loglevel = "debug"
    reload = True
    preload_app = False


# 生产环境优化
if os.getenv('ENVIRONMENT') == 'production':
    # 生产环境优化配置
    workers = multiprocessing.cpu_count() * 2 + 1
    max_requests = 2000
    max_requests_jitter = 100
    preload_app = True
    
    # 生产环境建议设置用户和组
    # user = "www-data"
    # group = "www-data"