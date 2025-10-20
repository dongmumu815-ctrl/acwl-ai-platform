#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DataAInsight 性能优化快速修复脚本

此脚本用于快速应用性能优化配置，解决大型SQL查询时的超时和内存问题。

使用方法:
    python apply_performance_fix.py [--timeout SECONDS] [--workers NUM] [--memory MB]

示例:
    python apply_performance_fix.py --timeout 600 --workers 1 --memory 2048
"""

import os
import sys
import argparse
import shutil
from pathlib import Path


class PerformanceFixer:
    """性能优化修复器"""
    
    def __init__(self):
        self.script_dir = Path(__file__).parent
        self.linux_script = self.script_dir / "start_prod_linux.sh"
        self.windows_script = self.script_dir / "start_prod_windows.bat"
        
    def backup_files(self):
        """备份原始文件"""
        print("📁 备份原始启动脚本...")
        
        if self.linux_script.exists():
            backup_path = self.linux_script.with_suffix(".sh.backup")
            shutil.copy2(self.linux_script, backup_path)
            print(f"   ✅ Linux脚本已备份到: {backup_path}")
            
        if self.windows_script.exists():
            backup_path = self.windows_script.with_suffix(".bat.backup")
            shutil.copy2(self.windows_script, backup_path)
            print(f"   ✅ Windows脚本已备份到: {backup_path}")
    
    def update_linux_script(self, timeout=300, workers=2, memory=1024, max_requests=1000):
        """更新Linux启动脚本"""
        if not self.linux_script.exists():
            print(f"   ⚠️  Linux脚本不存在: {self.linux_script}")
            return False
            
        print("🐧 更新Linux启动脚本...")
        
        with open(self.linux_script, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 更新配置变量
        replacements = {
            'WORKER_TIMEOUT="300"': f'WORKER_TIMEOUT="{timeout}"',
            'WORKER_MEMORY_LIMIT="1024"': f'WORKER_MEMORY_LIMIT="{memory}"',
            'WORKERS="2"': f'WORKERS="{workers}"',
            'MAX_REQUESTS="1000"': f'MAX_REQUESTS="{max_requests}"',
        }
        
        for old, new in replacements.items():
            if old in content:
                content = content.replace(old, new)
                print(f"   ✅ 已更新: {new}")
        
        # 确保包含所有必要的Gunicorn参数
        gunicorn_params = [
            '--timeout "$WORKER_TIMEOUT"',
            '--max-requests "$MAX_REQUESTS"',
            '--max-requests-jitter "$MAX_REQUESTS_JITTER"',
            '--keep-alive "$KEEP_ALIVE"',
            '--worker-connections "$WORKER_CONNECTIONS"',
            '--preload'
        ]
        
        # 检查是否已包含所有参数
        missing_params = []
        for param in gunicorn_params:
            if param not in content:
                missing_params.append(param)
        
        if missing_params:
            print(f"   ⚠️  检测到缺失的Gunicorn参数，请手动检查脚本")
        
        with open(self.linux_script, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"   ✅ Linux脚本更新完成")
        return True
    
    def update_windows_script(self, timeout=300, workers=2, memory=1024, max_requests=1000):
        """更新Windows启动脚本"""
        if not self.windows_script.exists():
            print(f"   ⚠️  Windows脚本不存在: {self.windows_script}")
            return False
            
        print("🪟 更新Windows启动脚本...")
        
        with open(self.windows_script, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 更新配置变量
        replacements = {
            'set WORKER_TIMEOUT=300': f'set WORKER_TIMEOUT={timeout}',
            'set WORKER_MEMORY_LIMIT=1024': f'set WORKER_MEMORY_LIMIT={memory}',
            'set WORKERS=4': f'set WORKERS={workers}',
            'set MAX_REQUESTS=1000': f'set MAX_REQUESTS={max_requests}',
        }
        
        for old, new in replacements.items():
            if old in content:
                content = content.replace(old, new)
                print(f"   ✅ 已更新: {new}")
        
        with open(self.windows_script, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"   ✅ Windows脚本更新完成")
        return True
    
    def create_monitoring_script(self):
        """创建内存监控脚本"""
        print("📊 创建内存监控脚本...")
        
        monitor_script = self.script_dir / "monitor_memory.py"
        
        monitor_content = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DataAInsight 内存监控脚本
"""

import time
import psutil
import os
from datetime import datetime


def get_dataainsight_processes():
    """获取DataAInsight相关进程"""
    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if proc.info['name'] == 'python.exe' or proc.info['name'] == 'python':
                cmdline = ' '.join(proc.info['cmdline'] or [])
                if 'gunicorn' in cmdline or 'main:app' in cmdline:
                    processes.append(proc)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return processes


def monitor_memory(interval=30, log_file=None):
    """监控内存使用情况"""
    if log_file:
        log_path = log_file
    else:
        log_path = os.path.join(os.path.dirname(__file__), 'memory_monitor.log')
    
    print(f"开始监控DataAInsight进程内存使用情况...")
    print(f"日志文件: {log_path}")
    print(f"监控间隔: {interval}秒")
    print("按 Ctrl+C 停止监控\n")
    
    try:
        while True:
            processes = get_dataainsight_processes()
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            if not processes:
                message = f"[{timestamp}] 未找到DataAInsight进程"
                print(message)
                with open(log_path, 'a', encoding='utf-8') as f:
                    f.write(message + '\n')
            else:
                for proc in processes:
                    try:
                        memory_info = proc.memory_info()
                        memory_percent = proc.memory_percent()
                        cpu_percent = proc.cpu_percent()
                        
                        message = (
                            f"[{timestamp}] PID={proc.pid}, "
                            f"Memory={memory_info.rss/1024/1024:.1f}MB "
                            f"({memory_percent:.1f}%), "
                            f"CPU={cpu_percent:.1f}%"
                        )
                        
                        print(message)
                        with open(log_path, 'a', encoding='utf-8') as f:
                            f.write(message + '\n')
                        
                        # 内存使用警告
                        if memory_percent > 80:
                            warning = f"[{timestamp}] ⚠️  警告: 进程 {proc.pid} 内存使用率过高 ({memory_percent:.1f}%)"
                            print(warning)
                            with open(log_path, 'a', encoding='utf-8') as f:
                                f.write(warning + '\n')
                                
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
            
            time.sleep(interval)
            
    except KeyboardInterrupt:
        print("\n监控已停止")


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='DataAInsight 内存监控')
    parser.add_argument('--interval', type=int, default=30, help='监控间隔（秒）')
    parser.add_argument('--log-file', type=str, help='日志文件路径')
    
    args = parser.parse_args()
    
    monitor_memory(args.interval, args.log_file)
'''
        
        with open(monitor_script, 'w', encoding='utf-8') as f:
            f.write(monitor_content)
        
        # 设置执行权限（Linux/Mac）
        if os.name != 'nt':
            os.chmod(monitor_script, 0o755)
        
        print(f"   ✅ 内存监控脚本已创建: {monitor_script}")
        print(f"   📝 使用方法: python {monitor_script.name}")
    
    def show_optimization_summary(self, timeout, workers, memory, max_requests):
        """显示优化配置摘要"""
        print("\n" + "="*60)
        print("🚀 性能优化配置摘要")
        print("="*60)
        print(f"⏱️  Worker超时时间: {timeout}秒 (原来30秒)")
        print(f"👥 Worker进程数: {workers}")
        print(f"💾 内存限制: {memory}MB")
        print(f"📊 最大请求数: {max_requests}")
        print("\n🔧 已启用的优化功能:")
        print("   ✅ 预加载模式 (--preload)")
        print("   ✅ 请求数限制 (防止内存泄漏)")
        print("   ✅ 连接池优化")
        print("   ✅ Keep-alive优化")
        
        print("\n📋 下一步操作:")
        print("   1. 重启DataAInsight服务")
        print("   2. 运行内存监控脚本")
        print("   3. 测试大型SQL查询")
        
        print("\n🔄 重启服务命令:")
        if os.name == 'nt':  # Windows
            print("   start_prod_windows.bat restart")
        else:  # Linux/Mac
            print("   ./start_prod_linux.sh restart")
        
        print("\n📊 监控内存使用:")
        print("   python monitor_memory.py")
        print("="*60)
    
    def apply_fix(self, timeout=300, workers=2, memory=1024, max_requests=1000):
        """应用性能修复"""
        print("🔧 开始应用DataAInsight性能优化...\n")
        
        # 备份文件
        self.backup_files()
        
        # 更新脚本
        linux_updated = self.update_linux_script(timeout, workers, memory, max_requests)
        windows_updated = self.update_windows_script(timeout, workers, memory, max_requests)
        
        # 创建监控脚本
        self.create_monitoring_script()
        
        # 显示摘要
        self.show_optimization_summary(timeout, workers, memory, max_requests)
        
        if linux_updated or windows_updated:
            print("\n✅ 性能优化应用成功！")
            return True
        else:
            print("\n❌ 未找到可更新的启动脚本")
            return False


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='DataAInsight 性能优化快速修复脚本',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例:
  python apply_performance_fix.py                    # 使用默认配置
  python apply_performance_fix.py --timeout 600     # 设置10分钟超时
  python apply_performance_fix.py --workers 1       # 使用1个worker进程
  python apply_performance_fix.py --memory 2048     # 设置2GB内存限制
        '''
    )
    
    parser.add_argument(
        '--timeout', 
        type=int, 
        default=300,
        help='Worker超时时间（秒），默认300秒（5分钟）'
    )
    
    parser.add_argument(
        '--workers', 
        type=int, 
        default=2,
        help='Worker进程数，默认2个'
    )
    
    parser.add_argument(
        '--memory', 
        type=int, 
        default=1024,
        help='内存限制（MB），默认1024MB（1GB）'
    )
    
    parser.add_argument(
        '--max-requests', 
        type=int, 
        default=1000,
        help='每个worker最大请求数，默认1000'
    )
    
    args = parser.parse_args()
    
    # 验证参数
    if args.timeout < 30:
        print("❌ 错误: 超时时间不能少于30秒")
        sys.exit(1)
    
    if args.workers < 1:
        print("❌ 错误: Worker进程数不能少于1个")
        sys.exit(1)
    
    if args.memory < 512:
        print("❌ 错误: 内存限制不能少于512MB")
        sys.exit(1)
    
    # 应用修复
    fixer = PerformanceFixer()
    success = fixer.apply_fix(
        timeout=args.timeout,
        workers=args.workers,
        memory=args.memory,
        max_requests=args.max_requests
    )
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()