#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生产环境启动脚本

使用Gunicorn作为WSGI服务器启动FastAPI应用
适用于生产环境部署

Author: System
Date: 2024
"""

import os
import sys
import subprocess
from pathlib import Path
from loguru import logger


def setup_environment():
    """
    设置环境变量和工作目录
    """
    # 确保在backend目录下运行
    backend_dir = Path(__file__).parent.absolute()
    os.chdir(backend_dir)
    
    # 添加当前目录到Python路径
    if str(backend_dir) not in sys.path:
        sys.path.insert(0, str(backend_dir))
    
    logger.info(f"工作目录: {backend_dir}")
    
    # 检查必要文件
    required_files = ['main.py', 'requirements.txt']
    for file in required_files:
        if not (backend_dir / file).exists():
            logger.error(f"缺少必要文件: {file}")
            sys.exit(1)
    
    # 检查.env文件
    env_file = backend_dir / '.env'
    if not env_file.exists():
        logger.warning("未找到.env文件，将使用默认配置")
        logger.info("建议复制.env.example为.env并配置相应参数")


def check_dependencies():
    """
    检查依赖是否已安装
    """
    try:
        import gunicorn
        logger.info(f"Gunicorn版本: {gunicorn.__version__}")
    except ImportError:
        logger.error("Gunicorn未安装，请运行: pip install -r requirements.txt")
        sys.exit(1)
    
    try:
        import uvicorn
        logger.info(f"Uvicorn版本: {uvicorn.__version__}")
    except ImportError:
        logger.error("Uvicorn未安装，请运行: pip install -r requirements.txt")
        sys.exit(1)


def start_production_server():
    """
    启动生产环境服务器
    
    使用Gunicorn + Uvicorn workers的组合
    提供更好的性能和稳定性
    """
    # Gunicorn配置参数
    gunicorn_config = {
        'bind': '0.0.0.0:8080',  # 绑定到8080端口
        'workers': 4,  # 工作进程数，建议为CPU核心数的2倍
        'worker_class': 'uvicorn.workers.UvicornWorker',  # 使用Uvicorn worker
        'worker_connections': 1000,  # 每个worker的连接数
        'max_requests': 1000,  # 每个worker处理的最大请求数
        'max_requests_jitter': 100,  # 随机抖动，避免所有worker同时重启
        'timeout': 30,  # 请求超时时间
        'keepalive': 2,  # Keep-alive连接时间
        'preload_app': True,  # 预加载应用，提高性能
        'access_logfile': '-',  # 访问日志输出到stdout
        'error_logfile': '-',  # 错误日志输出到stderr
        'log_level': 'info',  # 日志级别
        'capture_output': True,  # 捕获应用输出
    }
    
    # 构建命令行参数 - 在Windows环境下使用python -m gunicorn
    cmd = [sys.executable, '-m', 'gunicorn']
    
    for key, value in gunicorn_config.items():
        cmd.extend([f'--{key.replace("_", "-")}', str(value)])
    
    # 指定应用模块
    cmd.append('main:app')
    
    logger.info("🚀 启动生产环境服务器...")
    logger.info(f"服务地址: http://0.0.0.0:8080")
    logger.info(f"工作进程数: {gunicorn_config['workers']}")
    logger.info(f"Worker类型: {gunicorn_config['worker_class']}")
    logger.info(f"命令: {' '.join(cmd)}")
    
    try:
        # 启动Gunicorn服务器
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        logger.info("\n🛑 收到中断信号，正在关闭服务器...")
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ 服务器启动失败: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ 未知错误: {e}")
        sys.exit(1)


def main():
    """
    主函数
    """
    logger.info("=" * 60)
    logger.info("🏭 CEPIEC API 生产环境启动脚本")
    logger.info("=" * 60)
    
    # 设置环境
    setup_environment()
    
    # 检查依赖
    check_dependencies()
    
    # 启动服务器
    start_production_server()


if __name__ == "__main__":
    main()