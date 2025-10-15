#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速启动脚本

一键启动生产环境服务器，监听8080端口
使用Gunicorn + Uvicorn workers组合，提供最佳性能

Usage:
    python start.py

Author: System
Date: 2024
"""

import os
import sys
import subprocess
from pathlib import Path


def main():
    """
    主启动函数
    
    快速启动生产环境服务器，使用优化的配置
    """
    print("🚀 启动CEPIEC API生产服务器...")
    print("📍 服务地址: http://localhost:8080")
    print("📖 API文档: http://localhost:8080/docs")
    print("🛑 按 Ctrl+C 停止服务器")
    print("=" * 50)
    
    # 确保在正确的目录下运行
    backend_dir = Path(__file__).parent.absolute()
    os.chdir(backend_dir)
    
    # 检查必要文件
    if not (backend_dir / "main.py").exists():
        print("❌ 错误: 找不到main.py文件")
        sys.exit(1)
    
    # 检查Gunicorn是否安装
    try:
        import gunicorn
        print(f"✅ Gunicorn {gunicorn.__version__} 已就绪")
    except ImportError:
        print("❌ 错误: Gunicorn未安装")
        print("请运行: pip install gunicorn")
        sys.exit(1)
    
    # 构建启动命令 - 在Windows环境下使用python -m gunicorn
    cmd = [
        sys.executable, "-m", "gunicorn",
        "--bind", "0.0.0.0:8080",  # 绑定8080端口
        "--workers", "4",  # 4个工作进程
        "--worker-class", "uvicorn.workers.UvicornWorker",  # 使用Uvicorn worker
        "--worker-connections", "1000",  # 每个worker最大连接数
        "--max-requests", "1000",  # 每个worker处理请求数后重启
        "--max-requests-jitter", "100",  # 重启抖动
        "--timeout", "30",  # 请求超时
        "--keepalive", "2",  # Keep-alive时间
        "--preload-app",  # 预加载应用
        "--access-logfile", "-",  # 访问日志到stdout
        "--error-logfile", "-",  # 错误日志到stderr
        "--log-level", "info",  # 日志级别
        "main:app"  # 应用模块
    ]
    
    try:
        # 启动服务器
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\n🛑 服务器已停止")
    except subprocess.CalledProcessError as e:
        print(f"❌ 启动失败: {e}")
        sys.exit(1)
    except FileNotFoundError:
        print("❌ 错误: 找不到gunicorn命令")
        print("请确保已安装: pip install gunicorn")
        sys.exit(1)


if __name__ == "__main__":
    main()