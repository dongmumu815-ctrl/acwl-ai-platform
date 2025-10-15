#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Windows环境专用启动脚本

使用Waitress作为WSGI服务器启动FastAPI应用
专为Windows环境优化，避免Gunicorn的fcntl依赖问题

Usage:
    python start_windows.py              # 默认8080端口启动
    python start_windows.py --port 9000  # 指定端口启动
    python start_windows.py --threads 8  # 指定线程数

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
        description="CEPIEC API Windows环境启动脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter
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
        "--threads", "-t",
        type=int,
        default=8,
        help="线程数 (默认: 8)"
    )
    
    parser.add_argument(
        "--dev", "-d",
        action="store_true",
        help="开发模式启动 (使用uvicorn)"
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


def check_dependencies(dev_mode=False):
    """
    检查必要的依赖包
    """
    required_packages = {
        'fastapi': 'FastAPI',
        'uvicorn': 'Uvicorn'
    }
    
    if not dev_mode:
        required_packages['waitress'] = 'Waitress'
    
    missing_packages = []
    
    for package, name in required_packages.items():
        try:
            module = __import__(package)
            version = getattr(module, '__version__', '未知版本')
            logger.debug(f"✅ {name} {version} 已安装")
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


def start_production_server(args):
    """
    启动生产环境服务器 (使用Waitress)
    """
    logger.info("🏭 启动生产环境服务器 (Waitress)")
    
    # 使用waitress-serve命令启动
    cmd = [
        sys.executable, "-m", "waitress",
        "--host", args.host,
        "--port", str(args.port),
        "--threads", str(args.threads),
        "--connection-limit", "1000",
        "--cleanup-interval", "30",
        "--channel-timeout", "120",
        "--log-untrusted-proxy-headers",
        "main:app"
    ]
    
    logger.info(f"服务地址: http://{args.host}:{args.port}")
    logger.info(f"API文档: http://{args.host}:{args.port}/docs")
    logger.info(f"线程数: {args.threads}")
    logger.info(f"命令: {' '.join(cmd)}")
    
    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        logger.info("\n🛑 生产服务器已停止")
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ 生产服务器启动失败: {e}")
        sys.exit(1)
    except FileNotFoundError:
        logger.error("❌ 错误: 无法找到waitress模块")
        logger.error("请确保已安装: pip install waitress")
        sys.exit(1)


def main():
    """
    主函数
    """
    # 解析参数
    args = parse_arguments()
    
    # 显示启动信息
    logger.info("=" * 60)
    logger.info("🪟 CEPIEC API Windows环境启动脚本")
    logger.info("=" * 60)
    
    # 设置环境
    backend_dir = setup_environment()
    
    # 检查依赖
    if not check_dependencies(args.dev):
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
        start_production_server(args)


if __name__ == "__main__":
    main()