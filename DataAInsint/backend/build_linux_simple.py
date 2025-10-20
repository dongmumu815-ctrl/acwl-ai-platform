#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化的Linux打包脚本
在Windows环境下为CentOS 7.8构建Linux可执行文件
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def install_requirements():
    """安装打包所需的依赖"""
    print("安装打包依赖...")
    requirements = [
        "pyinstaller>=5.0",
        "staticx",  # 用于创建静态链接的可执行文件
    ]
    
    for req in requirements:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", req])
        except subprocess.CalledProcessError:
            print(f"警告: 无法安装 {req}，继续执行...")

def create_simple_spec():
    """创建简化的spec文件"""
    spec_content = '''# -*- mode: python ; coding: utf-8 -*-

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
        'jwt',
        'passlib',
        'bcrypt',
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
    
    with open('datainsight-linux.spec', 'w', encoding='utf-8') as f:
        f.write(spec_content)
    print("已创建 datainsight-linux.spec 文件")

def modify_main_py():
    """修改main.py添加命令行支持"""
    # 备份原文件
    if os.path.exists('main.py'):
        shutil.copy('main.py', 'main.py.backup')
    
    # 读取原文件内容
    with open('main.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 添加命令行参数支持
    if 'import argparse' not in content:
        # 在导入部分添加必要的导入
        imports_to_add = [
            'import argparse',
            'import uvicorn'
        ]
        
        lines = content.split('\n')
        import_end = 0
        for i, line in enumerate(lines):
            if line.strip().startswith('import ') or line.strip().startswith('from '):
                import_end = i
        
        # 在导入结束后添加新的导入
        for imp in imports_to_add:
            if imp not in content:
                lines.insert(import_end + 1, imp)
                import_end += 1
        
        # 添加main函数
        main_function = '''
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
        
        # 如果没有main函数，添加它
        if 'def main():' not in content:
            lines.append('')
            lines.extend(main_function.split('\n'))
        
        content = '\n'.join(lines)
        
        with open('main.py', 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("已修改main.py添加命令行支持")

def build_linux_executable():
    """构建Linux可执行文件"""
    print("开始构建Linux可执行文件...")
    
    # 清理之前的构建
    build_dirs = ['build', 'dist/datainsight-backend']
    for build_dir in build_dirs:
        if os.path.exists(build_dir):
            if os.path.isfile(build_dir):
                os.remove(build_dir)
            else:
                shutil.rmtree(build_dir)
    
    try:
        # 使用PyInstaller构建
        cmd = [
            sys.executable, "-m", "PyInstaller", 
            "datainsight-linux.spec", 
            "--clean",
            "--noconfirm"
        ]
        
        print(f"执行命令: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"构建失败: {result.stderr}")
            return False
        
        print("PyInstaller构建完成")
        return True
        
    except Exception as e:
        print(f"构建过程中出现错误: {e}")
        return False

def create_deployment_package():
    """创建部署包"""
    package_name = "datainsight-centos7-package"
    
    if os.path.exists(package_name):
        shutil.rmtree(package_name)
    
    os.makedirs(package_name)
    
    # 复制可执行文件
    exe_path = 'dist/datainsight-backend'
    if os.path.exists(exe_path):
        shutil.copy(exe_path, package_name)
        print(f"已复制可执行文件到 {package_name}")
    else:
        print("警告: 可执行文件不存在")
        return False
    
    # 复制配置文件
    if os.path.exists('.env.example'):
        shutil.copy('.env.example', package_name)
    
    # 复制前端文件（如果存在）
    frontend_dist = 'dist'
    if os.path.exists(frontend_dist) and os.path.isdir(frontend_dist):
        target_dist = os.path.join(package_name, 'dist')
        shutil.copytree(frontend_dist, target_dist, 
                       ignore=shutil.ignore_patterns('datainsight-backend'))
        print("已复制前端文件")
    
    # 创建启动脚本
    start_script = '''#!/bin/bash
# DataAInsight 启动脚本

# 获取脚本目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

# 检查.env文件
if [ ! -f ".env" ]; then
    echo "复制配置文件模板..."
    cp .env.example .env
    echo "请编辑 .env 文件设置正确的配置"
fi

# 设置默认参数
HOST=${HOST:-"0.0.0.0"}
PORT=${PORT:-8000}

echo "启动DataAInsight后端服务..."
echo "访问地址: http://$HOST:$PORT"
echo "按 Ctrl+C 停止服务"
echo ""

# 启动应用
./datainsight-backend --host $HOST --port $PORT
'''
    
    start_script_path = os.path.join(package_name, 'start.sh')
    with open(start_script_path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(start_script)
    
    # 创建安装说明
    readme = '''# DataAInsight CentOS 7.8 部署包

## 系统要求
- CentOS 7.8 或更高版本
- 至少 512MB 内存
- 至少 100MB 磁盘空间

## 部署步骤

1. 将此目录上传到CentOS服务器

2. 设置执行权限：
   ```bash
   chmod +x datainsight-backend
   chmod +x start.sh
   ```

3. 复制并编辑配置文件：
   ```bash
   cp .env.example .env
   nano .env
   ```

4. 启动服务：
   ```bash
   ./start.sh
   ```

## 配置说明

编辑 .env 文件中的以下参数：

- `DATAINSIGHT_SECRET_KEY`: 用户登录密钥
- `DATAINSIGHT_JWT_SECRET`: JWT签名密钥  
- `DATAINSIGHT_TOKEN_EXPIRE_HOURS`: Token过期时间（小时）

## 访问应用

默认访问地址：http://服务器IP:8000

## 自定义端口

```bash
# 指定端口启动
PORT=9000 ./start.sh

# 或直接使用可执行文件
./datainsight-backend --host 0.0.0.0 --port 9000
```

## 后台运行

```bash
# 使用nohup后台运行
nohup ./start.sh > datainsight.log 2>&1 &

# 查看日志
tail -f datainsight.log

# 停止服务
pkill -f datainsight-backend
```

## 故障排除

1. 如果提示权限不足，检查文件执行权限
2. 如果端口被占用，修改PORT环境变量
3. 如果数据库连接失败，检查.env配置
4. 查看详细日志排查问题
'''
    
    readme_path = os.path.join(package_name, 'README.md')
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(readme)
    
    print(f"\n部署包已创建: {package_name}/")
    print("包含以下文件:")
    for item in os.listdir(package_name):
        print(f"  - {item}")
    
    return True

def restore_main_py():
    """恢复原始main.py文件"""
    if os.path.exists('main.py.backup'):
        shutil.move('main.py.backup', 'main.py')
        print("已恢复原始main.py文件")

def main():
    """主函数"""
    print("DataAInsight Linux打包工具 (CentOS 7.8)")
    print("=" * 50)
    
    try:
        # 安装依赖
        install_requirements()
        
        # 创建spec文件
        create_simple_spec()
        
        # 修改main.py
        modify_main_py()
        
        # 构建可执行文件
        if build_linux_executable():
            # 创建部署包
            if create_deployment_package():
                print("\n" + "=" * 50)
                print("✅ 打包成功！")
                print("\n📦 部署包: datainsight-centos7-package/")
                print("\n🚀 部署步骤:")
                print("1. 上传整个目录到CentOS服务器")
                print("2. chmod +x datainsight-backend start.sh")
                print("3. 编辑 .env 配置文件")
                print("4. 运行 ./start.sh 启动服务")
            else:
                print("❌ 创建部署包失败")
        else:
            print("❌ 构建可执行文件失败")
            
    except KeyboardInterrupt:
        print("\n用户中断操作")
    except Exception as e:
        print(f"❌ 打包失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # 恢复原始文件
        restore_main_py()

if __name__ == "__main__":
    main()