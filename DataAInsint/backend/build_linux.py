#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Linux打包脚本
使用PyInstaller将DataAInsight后端打包成Linux可执行文件
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def check_pyinstaller():
    """检查PyInstaller是否已安装"""
    try:
        import PyInstaller
        print(f"PyInstaller版本: {PyInstaller.__version__}")
        return True
    except ImportError:
        print("PyInstaller未安装，正在安装...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        return True

def create_spec_file():
    """创建PyInstaller spec文件"""
    spec_content = '''
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('app', 'app'),
        ('dist', 'dist'),
        ('.env.example', '.'),
    ],
    hiddenimports=[
        'uvicorn.lifespan.on',
        'uvicorn.lifespan.off',
        'uvicorn.protocols.websockets.auto',
        'uvicorn.protocols.http.auto',
        'uvicorn.protocols.websockets.websockets_impl',
        'uvicorn.protocols.http.httptools_impl',
        'uvicorn.protocols.http.h11_impl',
        'uvicorn.logging',
        'sqlalchemy.dialects.mysql',
        'sqlalchemy.dialects.postgresql',
        'sqlalchemy.dialects.oracle',
        'sqlalchemy.dialects.mssql',
        'sqlalchemy.dialects.sqlite',
        'pymysql',
        'psycopg2',
        'cx_Oracle',
        'pyodbc',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='datainsight-backend',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
'''
    
    with open('datainsight.spec', 'w', encoding='utf-8') as f:
        f.write(spec_content)
    print("已创建 datainsight.spec 文件")

def create_startup_script():
    """创建启动脚本"""
    startup_script = '''#!/bin/bash
# DataAInsight Backend 启动脚本

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# 切换到应用目录
cd "$SCRIPT_DIR"

# 检查.env文件是否存在
if [ ! -f ".env" ]; then
    echo "警告: .env文件不存在，正在复制.env.example为.env"
    cp .env.example .env
    echo "请编辑.env文件设置正确的配置参数"
fi

# 设置默认端口
PORT=${PORT:-8000}
HOST=${HOST:-0.0.0.0}

echo "启动DataAInsight后端服务..."
echo "访问地址: http://$HOST:$PORT"
echo "按 Ctrl+C 停止服务"

# 启动应用
./datainsight-backend --host $HOST --port $PORT
'''
    
    with open('start.sh', 'w', encoding='utf-8') as f:
        f.write(startup_script)
    
    # 设置执行权限
    os.chmod('start.sh', 0o755)
    print("已创建启动脚本 start.sh")

def create_systemd_service():
    """创建systemd服务文件"""
    service_content = '''[Unit]
Description=DataAInsight Backend Service
After=network.target

[Service]
Type=simple
User=datainsight
WorkingDirectory=/opt/datainsight
ExecStart=/opt/datainsight/datainsight-backend --host 0.0.0.0 --port 8000
Restart=always
RestartSec=3
Environment=PATH=/opt/datainsight

[Install]
WantedBy=multi-user.target
'''
    
    with open('datainsight.service', 'w', encoding='utf-8') as f:
        f.write(service_content)
    print("已创建systemd服务文件 datainsight.service")

def create_install_script():
    """创建安装脚本"""
    install_script = '''#!/bin/bash
# DataAInsight 安装脚本

set -e

echo "开始安装DataAInsight..."

# 检查是否为root用户
if [ "$EUID" -ne 0 ]; then
    echo "请使用root权限运行此脚本"
    exit 1
fi

# 创建用户和目录
echo "创建datainsight用户和目录..."
useradd -r -s /bin/false datainsight || true
mkdir -p /opt/datainsight
cp -r * /opt/datainsight/
chown -R datainsight:datainsight /opt/datainsight
chmod +x /opt/datainsight/datainsight-backend
chmod +x /opt/datainsight/start.sh

# 安装systemd服务
echo "安装systemd服务..."
cp datainsight.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable datainsight

echo "安装完成！"
echo "使用以下命令管理服务:"
echo "  启动服务: systemctl start datainsight"
echo "  停止服务: systemctl stop datainsight"
echo "  查看状态: systemctl status datainsight"
echo "  查看日志: journalctl -u datainsight -f"
echo ""
echo "配置文件位置: /opt/datainsight/.env"
echo "请编辑配置文件后启动服务"
'''
    
    with open('install.sh', 'w', encoding='utf-8') as f:
        f.write(install_script)
    
    os.chmod('install.sh', 0o755)
    print("已创建安装脚本 install.sh")

def modify_main_for_packaging():
    """修改main.py以支持命令行参数"""
    main_content = '''from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.config import load_env_file  # 加载环境变量配置
from app.api import datasource, explorer, auth
from app.database.sqlite_db import init_db
from app.middleware.auth_middleware import AuthMiddleware
import os
import sys
import argparse
import uvicorn

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时初始化数据库
    init_db()
    yield
    # 关闭时的清理工作（如果需要）

app = FastAPI(
    title="DataAInsight API",
    description="数据探查工具后端API",
    version="1.0.0",
    lifespan=lifespan
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 添加认证中间件
app.add_middleware(AuthMiddleware)

# 包含路由
app.include_router(auth.router, prefix="/api/auth", tags=["认证"])
app.include_router(datasource.router, prefix="/api/datasource", tags=["数据源管理"])
app.include_router(explorer.router, prefix="/api/explorer", tags=["数据探查"])

# 静态文件服务
static_dir = os.path.join(os.path.dirname(__file__), "dist")
if os.path.exists(static_dir):
    app.mount("/assets", StaticFiles(directory=os.path.join(static_dir, "assets")), name="assets")
    
    @app.get("/")
    async def serve_frontend():
        return FileResponse(os.path.join(static_dir, "index.html"))

def main():
    parser = argparse.ArgumentParser(description="DataAInsight Backend Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    parser.add_argument("--workers", type=int, default=1, help="Number of worker processes")
    
    args = parser.parse_args()
    
    print(f"启动DataAInsight后端服务...")
    print(f"访问地址: http://{args.host}:{args.port}")
    
    uvicorn.run(
        "main:app",
        host=args.host,
        port=args.port,
        workers=args.workers,
        access_log=True
    )

if __name__ == "__main__":
    main()
'''
    
    # 备份原文件
    shutil.copy('main.py', 'main.py.backup')
    
    with open('main.py', 'w', encoding='utf-8') as f:
        f.write(main_content)
    
    print("已修改main.py以支持命令行参数")

def build_executable():
    """构建可执行文件"""
    print("开始构建Linux可执行文件...")
    
    # 清理之前的构建
    if os.path.exists('build'):
        shutil.rmtree('build')
    if os.path.exists('dist'):
        # 保留前端dist目录，删除PyInstaller的dist
        for item in os.listdir('dist'):
            if item != 'assets' and item != 'index.html':
                item_path = os.path.join('dist', item)
                if os.path.isdir(item_path):
                    shutil.rmtree(item_path)
                else:
                    os.remove(item_path)
    
    # 运行PyInstaller
    cmd = [sys.executable, "-m", "PyInstaller", "datainsight.spec", "--clean"]
    subprocess.check_call(cmd)
    
    print("构建完成！")

def create_package():
    """创建发布包"""
    package_dir = "datainsight-linux-package"
    
    if os.path.exists(package_dir):
        shutil.rmtree(package_dir)
    
    os.makedirs(package_dir)
    
    # 复制可执行文件
    shutil.copy('dist/datainsight-backend', package_dir)
    
    # 复制配置文件
    shutil.copy('.env.example', package_dir)
    
    # 复制前端文件
    if os.path.exists('dist'):
        frontend_dist = os.path.join(package_dir, 'dist')
        shutil.copytree('dist', frontend_dist, ignore=shutil.ignore_patterns('datainsight-backend'))
    
    # 复制脚本文件
    for script in ['start.sh', 'install.sh', 'datainsight.service']:
        if os.path.exists(script):
            shutil.copy(script, package_dir)
    
    # 创建README
    readme_content = '''# DataAInsight Linux 部署包

## 系统要求
- CentOS 7.8 或更高版本
- 至少 512MB 内存
- 至少 100MB 磁盘空间

## 快速安装

1. 解压部署包到目标目录
2. 以root权限运行安装脚本：
   ```bash
   sudo ./install.sh
   ```

3. 编辑配置文件：
   ```bash
   sudo nano /opt/datainsight/.env
   ```

4. 启动服务：
   ```bash
   sudo systemctl start datainsight
   ```

## 手动运行

如果不想安装为系统服务，可以手动运行：

1. 复制.env.example为.env并编辑配置
2. 运行启动脚本：
   ```bash
   ./start.sh
   ```

## 配置说明

编辑.env文件设置以下参数：
- DATAINSIGHT_SECRET_KEY: 用户访问密钥
- DATAINSIGHT_JWT_SECRET: JWT签名密钥
- DATAINSIGHT_TOKEN_EXPIRE_HOURS: Token过期时间

## 访问应用

默认访问地址：http://服务器IP:8000

## 服务管理

- 启动服务：`systemctl start datainsight`
- 停止服务：`systemctl stop datainsight`
- 重启服务：`systemctl restart datainsight`
- 查看状态：`systemctl status datainsight`
- 查看日志：`journalctl -u datainsight -f`
'''
    
    with open(os.path.join(package_dir, 'README.md'), 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    print(f"发布包已创建: {package_dir}")
    print(f"可以将整个 {package_dir} 目录打包传输到Linux服务器")

def main():
    """主函数"""
    print("DataAInsight Linux打包工具")
    print("=" * 50)
    
    try:
        # 检查PyInstaller
        check_pyinstaller()
        
        # 创建配置文件
        create_spec_file()
        create_startup_script()
        create_systemd_service()
        create_install_script()
        
        # 修改main.py
        modify_main_for_packaging()
        
        # 构建可执行文件
        build_executable()
        
        # 创建发布包
        create_package()
        
        print("\n" + "=" * 50)
        print("打包完成！")
        print("发布包位置: datainsight-linux-package/")
        print("\n部署步骤:")
        print("1. 将datainsight-linux-package目录复制到Linux服务器")
        print("2. 在服务器上运行: sudo ./install.sh")
        print("3. 编辑配置: sudo nano /opt/datainsight/.env")
        print("4. 启动服务: sudo systemctl start datainsight")
        
    except Exception as e:
        print(f"打包失败: {e}")
        sys.exit(1)
    finally:
        # 恢复原始main.py
        if os.path.exists('main.py.backup'):
            shutil.move('main.py.backup', 'main.py')
            print("已恢复原始main.py文件")

if __name__ == "__main__":
    main()