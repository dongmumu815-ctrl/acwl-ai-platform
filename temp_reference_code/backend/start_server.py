#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化的服务器启动脚本

使用Gunicorn配置文件启动生产环境服务器

Usage:
    python start_server.py              # 使用默认配置启动
    python start_server.py --dev        # 开发模式启动
    python start_server.py --config custom.conf.py  # 使用自定义配置

Author: System
Date: 2024
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path
from loguru import logger


def parse_arguments():
    """
    解析命令行参数
    """
    parser = argparse.ArgumentParser(
        description="CEPIEC API服务器启动脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "--config", "-c",
        default="gunicorn.conf.py",
        help="Gunicorn配置文件路径 (默认: gunicorn.conf.py)"
    )
    
    parser.add_argument(
        "--dev", "-d",
        action="store_true",
        help="开发模式启动 (使用uvicorn)"
    )
    
    parser.add_argument(
        "--port", "-p",
        type=int,
        default=8080,
        help="服务端口 (默认: 8080)"
    )
    
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="绑定主机 (默认: 0.0.0.0)"
    )
    
    parser.add_argument(
        "--workers", "-w",
        type=int,
        help="工作进程数 (仅生产模式)"
    )
    
    parser.add_argument(
        "--reload", "-r",
        action="store_true",
        help="启用自动重载 (仅开发模式)"
    )
    
    return parser.parse_args()


def setup_environment():
    """
    设置运行环境
    """
    # 确保在backend目录下运行
    backend_dir = Path(__file__).parent.absolute()
    os.chdir(backend_dir)
    
    # 添加当前目录到Python路径
    if str(backend_dir) not in sys.path:
        sys.path.insert(0, str(backend_dir))
    
    logger.info(f"工作目录: {backend_dir}")
    return backend_dir


def check_dependencies():
    """
    检查必要的依赖包
    """
    required_packages = {
        'fastapi': 'FastAPI',
        'uvicorn': 'Uvicorn',
        'gunicorn': 'Gunicorn'
    }
    
    missing_packages = []
    
    for package, name in required_packages.items():
        try:
            __import__(package)
            logger.debug(f"✅ {name} 已安装")
        except ImportError:
            missing_packages.append(package)
            logger.error(f"❌ {name} 未安装")
    
    if missing_packages:
        logger.error("缺少必要依赖包，请运行: pip install -r requirements.txt")
        return False
    
    return True


def start_development_server(args):
    """
    启动开发环境服务器 (使用Uvicorn)
    """
    logger.info("🔧 启动开发环境服务器 (Uvicorn)")
    
    # 在Windows环境下使用python -m uvicorn
    cmd = [
        sys.executable, "-m", "uvicorn",
        "main:app",
        "--host", args.host,
        "--port", str(args.port),
        "--log-level", "debug"
    ]
    
    if args.reload:
        cmd.append("--reload")
        cmd.extend(["--reload-exclude", "test_*.py"])
        cmd.extend(["--reload-exclude", "*_test.py"])
    
    logger.info(f"服务地址: http://{args.host}:{args.port}")
    logger.info(f"API文档: http://{args.host}:{args.port}/docs")
    logger.info(f"命令: {' '.join(cmd)}")
    
    try:
        # 在Windows下使用creationflags确保Ctrl+C可以正确传递
        if sys.platform == 'win32':
            process = subprocess.Popen(
                cmd,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
            )
            try:
                process.wait()
            except KeyboardInterrupt:
                logger.info("\n🛑 接收到Ctrl+C，正在停止开发服务器...")
                # 向进程发送Ctrl+Break信号 (Windows特有)
                import signal
                process.send_signal(signal.CTRL_BREAK_EVENT)
                process.terminate()
                process.wait(timeout=5)
                logger.info("🛑 开发服务器已停止")
        else:
            # 非Windows平台使用标准方式
            subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        logger.info("\n🛑 开发服务器已停止")
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ 开发服务器启动失败: {e}")
        sys.exit(1)
    except FileNotFoundError:
        logger.error("❌ 错误: 无法找到uvicorn模块")
        logger.error("请确保已安装: pip install uvicorn")
        sys.exit(1)


def start_production_server(args, backend_dir):
    """
    启动生产环境服务器 (使用Gunicorn)
    """
    logger.info("🏭 启动生产环境服务器 (Gunicorn)")
    
    config_file = backend_dir / args.config
    if not config_file.exists():
        logger.error(f"❌ 配置文件不存在: {config_file}")
        sys.exit(1)
    
    # 在Windows环境下使用python -m gunicorn来避免路径问题
    cmd = [
        sys.executable, "-m", "gunicorn",
        "--config", str(config_file),
        "main:app"
    ]
    
    # 覆盖配置文件中的设置
    if args.host != "0.0.0.0" or args.port != 8080:
        cmd.extend(["--bind", f"{args.host}:{args.port}"])
    
    if args.workers:
        cmd.extend(["--workers", str(args.workers)])
    
    logger.info(f"配置文件: {config_file}")
    logger.info(f"服务地址: http://{args.host}:{args.port}")
    logger.info(f"API文档: http://{args.host}:{args.port}/docs")
    logger.info(f"命令: {' '.join(cmd)}")
    
    try:
        # 在Windows下使用creationflags确保Ctrl+C可以正确传递
        if sys.platform == 'win32':
            import signal
            process = subprocess.Popen(
                cmd,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
            )
            try:
                process.wait()
            except KeyboardInterrupt:
                logger.info("\n🛑 接收到Ctrl+C，正在停止生产服务器...")
                # 向进程发送Ctrl+Break信号 (Windows特有)
                process.send_signal(signal.CTRL_BREAK_EVENT)
                process.terminate()
                process.wait(timeout=5)
                logger.info("🛑 生产服务器已停止")
        else:
            # 非Windows平台使用标准方式
            subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        logger.info("\n🛑 生产服务器已停止")
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ 生产服务器启动失败: {e}")
        sys.exit(1)
    except FileNotFoundError:
        logger.error("❌ 错误: 无法找到gunicorn模块")
        logger.error("请确保已安装: pip install gunicorn")
        sys.exit(1)


def setup_signal_handlers():
    """
    设置信号处理器，特别是针对Windows平台
    """
    import signal
    
    # Windows平台特殊处理
    if sys.platform == 'win32':
        # 在Windows下，需要特殊处理Ctrl+C信号
        def handle_ctrl_c(sig, frame):
            logger.info("\n🛑 接收到Ctrl+C信号，正在停止服务器...")
            # 不调用sys.exit()，让程序自然结束
            # 这样可以确保子进程也被正确终止
            return True
        
        # 注册SIGINT信号处理器
        signal.signal(signal.SIGINT, handle_ctrl_c)
        logger.debug("已设置Windows平台的Ctrl+C信号处理器")


def main():
    """
    主函数
    """
    # 解析参数
    args = parse_arguments()
    
    # 显示启动信息
    logger.info("=" * 60)
    logger.info("🚀 CEPIEC API 服务器启动脚本")
    logger.info("=" * 60)
    
    # 设置环境
    backend_dir = setup_environment()
    
    # 设置信号处理器
    setup_signal_handlers()
    
    # 检查依赖
    if not check_dependencies():
        sys.exit(1)
    
    # 检查配置文件
    env_file = backend_dir / '.env'
    if not env_file.exists():
        logger.warning("⚠️  未找到.env配置文件")
        if (backend_dir / '.env.example').exists():
            logger.info("💡 建议复制.env.example为.env并配置相应参数")
    
    # 根据模式启动服务器
    if args.dev:
        start_development_server(args)
    else:
        start_production_server(args, backend_dir)


if __name__ == "__main__":
    main()