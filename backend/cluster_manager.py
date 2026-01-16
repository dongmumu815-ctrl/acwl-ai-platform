#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
集群管理器

用于批量启动和管理多个执行器和调度器实例
"""

import argparse
import json
import os
import subprocess
import sys
import time
from typing import Dict, List, Any


class ClusterManager:
    """
    集群管理器类
    
    负责启动、停止和管理多个执行器和调度器实例
    """
    
    def __init__(self, config_file: str = None):
        self.config_file = config_file or 'cluster_config.json'
        self.processes = {}  # 存储进程信息
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """
        加载集群配置
        """
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            # 返回默认配置
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """
        获取默认配置
        """
        return {
            "schedulers": [
                {
                    "node_id": "scheduler-001",
                    "node_name": "主调度器-1",
                    "host_ip": "127.0.0.1",
                    "port": 8002,
                    "log_level": "INFO"
                },
                {
                    "node_id": "scheduler-002",
                    "node_name": "主调度器-2",
                    "host_ip": "127.0.0.1",
                    "port": 8003,
                    "log_level": "INFO"
                },
                {
                    "node_id": "scheduler-003",
                    "node_name": "主调度器-3",
                    "host_ip": "127.0.0.1",
                    "port": 8004,
                    "log_level": "INFO"
                }
            ],
            "executors": [
                {
                    "node_id": "executor-001",
                    "node_name": "执行器-1",
                    "group_id": "default",
                    "host_ip": "127.0.0.1",
                    "port": 8011,
                    "max_concurrent_tasks": 5,
                    "log_level": "INFO"
                },
                {
                    "node_id": "executor-002",
                    "node_name": "执行器-2",
                    "group_id": "default",
                    "host_ip": "127.0.0.1",
                    "port": 8012,
                    "max_concurrent_tasks": 5,
                    "log_level": "INFO"
                },
                {
                    "node_id": "executor-003",
                    "node_name": "执行器-3",
                    "group_id": "high-performance",
                    "host_ip": "127.0.0.1",
                    "port": 8013,
                    "max_concurrent_tasks": 10,
                    "log_level": "INFO"
                }
            ],
            "monitor": {
                "enabled": True,
                "heartbeat_timeout": 300,
                "cleanup_interval": 600,
                "offline_retention": 3600,
                "log_level": "INFO"
            }
        }
    
    def save_config(self):
        """
        保存配置到文件
        """
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)
        print(f"配置已保存到: {self.config_file}")
    
    def start_schedulers(self, count: int = None):
        """
        启动调度器实例
        """
        schedulers = self.config.get('schedulers', [])
        if count:
            schedulers = schedulers[:count]
        
        print(f"启动 {len(schedulers)} 个调度器实例...")
        
        for scheduler in schedulers:
            self._start_scheduler(scheduler)
            time.sleep(2)  # 间隔2秒启动下一个
    
    def start_executors(self, count: int = None, group: str = None):
        """
        启动执行器实例
        """
        executors = self.config.get('executors', [])
        
        if group:
            executors = [e for e in executors if e.get('group_id') == group]
        
        if count:
            executors = executors[:count]
        
        print(f"启动 {len(executors)} 个执行器实例...")
        
        for executor in executors:
            self._start_executor(executor)
            time.sleep(1)  # 间隔1秒启动下一个
    
    def start_monitor(self):
        """
        启动监控服务
        """
        config = self.config.get('monitor', {})
        if not config.get('enabled', True):
            print("监控服务未启用")
            return
            
        print("启动执行器监控服务...")
        
        cmd = [
            sys.executable,
            'executor_monitor.py',
            '--heartbeat-timeout', str(config.get('heartbeat_timeout', 300)),
            '--cleanup-interval', str(config.get('cleanup_interval', 600)),
            '--offline-retention', str(config.get('offline_retention', 3600)),
            '--log-level', config.get('log_level', 'INFO')
        ]
        
        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            self.processes['executor-monitor'] = {
                'process': process,
                'type': 'monitor',
                'config': config,
                'start_time': time.time()
            }
            
            print(f"✓ 监控服务启动成功 (PID: {process.pid})")
            
        except Exception as e:
            print(f"✗ 监控服务启动失败: {e}")

    def _start_scheduler(self, config: Dict[str, Any]):
        """
        启动单个调度器实例
        """
        cmd = [
            sys.executable,
            'scheduler_service.py',
            '--node-id', config['node_id'],
            '--node-name', config['node_name'],
            '--host-ip', config['host_ip'],
            '--port', str(config['port']),
            '--log-level', config.get('log_level', 'INFO')
        ]
        
        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            self.processes[f"scheduler-{config['node_id']}"] = {
                'process': process,
                'type': 'scheduler',
                'config': config,
                'start_time': time.time()
            }
            
            print(f"✓ 调度器启动成功: {config['node_name']} (PID: {process.pid})")
            
        except Exception as e:
            print(f"✗ 调度器启动失败: {config['node_name']} - {e}")
    
    def _start_executor(self, config: Dict[str, Any]):
        """
        启动单个执行器实例
        """
        cmd = [
            sys.executable,
            'executor_service.py',
            '--node-id', config['node_id'],
            '--node-name', config['node_name'],
            '--group-id', config['group_id'],
            '--host-ip', config['host_ip'],
            '--port', str(config['port']),
            '--max-concurrent-tasks', str(config.get('max_concurrent_tasks', 5)),
            '--log-level', config.get('log_level', 'INFO')
        ]
        
        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            self.processes[f"executor-{config['node_id']}"] = {
                'process': process,
                'type': 'executor',
                'config': config,
                'start_time': time.time()
            }
            
            print(f"✓ 执行器启动成功: {config['node_name']} (PID: {process.pid})")
            
        except Exception as e:
            print(f"✗ 执行器启动失败: {config['node_name']} - {e}")
    
    def stop_all(self):
        """
        停止所有实例
        """
        print("停止所有实例...")
        
        for name, info in self.processes.items():
            try:
                process = info['process']
                if process.poll() is None:  # 进程还在运行
                    process.terminate()
                    print(f"✓ 已停止: {name} (PID: {process.pid})")
                else:
                    print(f"- 已停止: {name} (进程已结束)")
            except Exception as e:
                print(f"✗ 停止失败: {name} - {e}")
        
        self.processes.clear()
    
    def stop_schedulers(self):
        """
        停止所有调度器
        """
        print("停止所有调度器...")
        
        to_remove = []
        for name, info in self.processes.items():
            if info['type'] == 'scheduler':
                try:
                    process = info['process']
                    if process.poll() is None:
                        process.terminate()
                        print(f"✓ 已停止调度器: {name} (PID: {process.pid})")
                    to_remove.append(name)
                except Exception as e:
                    print(f"✗ 停止调度器失败: {name} - {e}")
        
        for name in to_remove:
            del self.processes[name]
    
    def stop_executors(self, group: str = None):
        """
        停止执行器
        """
        print(f"停止执行器{f' (分组: {group})' if group else ''}...")
        
        to_remove = []
        for name, info in self.processes.items():
            if info['type'] == 'executor':
                if group and info['config'].get('group_id') != group:
                    continue
                
                try:
                    process = info['process']
                    if process.poll() is None:
                        process.terminate()
                        print(f"✓ 已停止执行器: {name} (PID: {process.pid})")
                    to_remove.append(name)
                except Exception as e:
                    print(f"✗ 停止执行器失败: {name} - {e}")
        
        for name in to_remove:
            del self.processes[name]

    def stop_monitor(self):
        """
        停止监控服务
        """
        print("停止监控服务...")
        
        if 'executor-monitor' in self.processes:
            try:
                info = self.processes['executor-monitor']
                process = info['process']
                if process.poll() is None:
                    process.terminate()
                    print(f"✓ 已停止监控服务 (PID: {process.pid})")
                del self.processes['executor-monitor']
            except Exception as e:
                print(f"✗ 停止监控服务失败: {e}")
    
    def status(self):
        """
        显示集群状态
        """
        print("\n=== 集群状态 ===")
        
        if not self.processes:
            print("没有运行的实例")
            return
        
        schedulers = []
        executors = []
        monitor = None
        
        for name, info in self.processes.items():
            process = info['process']
            status = "运行中" if process.poll() is None else "已停止"
            uptime = int(time.time() - info['start_time'])
            
            item = {
                'name': name,
                'pid': process.pid,
                'status': status,
                'uptime': f"{uptime}秒",
                'config': info['config']
            }
            
            if info['type'] == 'scheduler':
                schedulers.append(item)
            elif info['type'] == 'executor':
                executors.append(item)
            elif info['type'] == 'monitor':
                monitor = item
        
        if monitor:
            print(f"\n监控服务:")
            print(f"  - {monitor['name']}: {monitor['status']} (PID: {monitor['pid']}, 运行时间: {monitor['uptime']})")

        if schedulers:
            print(f"\n调度器 ({len(schedulers)} 个):")
            for s in schedulers:
                print(f"  - {s['name']}: {s['status']} (PID: {s['pid']}, 运行时间: {s['uptime']})")
        
        if executors:
            print(f"\n执行器 ({len(executors)} 个):")
            for e in executors:
                group = e['config'].get('group_id', 'default')
                print(f"  - {e['name']}: {e['status']} (PID: {e['pid']}, 分组: {group}, 运行时间: {e['uptime']})")
    
    def restart_all(self):
        """
        重启所有实例
        """
        print("重启所有实例...")
        self.stop_all()
        time.sleep(3)
        self.start_schedulers()
        time.sleep(5)
        self.start_executors()


def parse_args():
    """
    解析命令行参数
    """
    parser = argparse.ArgumentParser(description='集群管理器')
    parser.add_argument('--config', default='cluster_config.json', help='配置文件路径')
    
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # 启动命令
    start_parser = subparsers.add_parser('start', help='启动服务')
    start_parser.add_argument('--schedulers', type=int, help='启动调度器数量')
    start_parser.add_argument('--executors', type=int, help='启动执行器数量')
    start_parser.add_argument('--group', help='执行器分组')
    
    # 停止命令
    stop_parser = subparsers.add_parser('stop', help='停止服务')
    stop_parser.add_argument('--type', choices=['all', 'schedulers', 'executors', 'monitor'], default='all', help='停止类型')
    stop_parser.add_argument('--group', help='执行器分组')
    
    # 状态命令
    subparsers.add_parser('status', help='查看状态')
    
    # 重启命令
    subparsers.add_parser('restart', help='重启所有服务')
    
    # 配置命令
    subparsers.add_parser('init-config', help='初始化配置文件')
    
    return parser.parse_args()


def main():
    """
    主函数
    """
    args = parse_args()
    
    manager = ClusterManager(args.config)
    
    try:
        if args.command == 'start':
            if args.schedulers:
                manager.start_schedulers(args.schedulers)
            if args.executors:
                manager.start_executors(args.executors, args.group)
            if not args.schedulers and not args.executors:
                manager.start_schedulers()
                time.sleep(5)
                manager.start_executors()
        
        elif args.command == 'stop':
            if args.type == 'schedulers':
                manager.stop_schedulers()
            elif args.type == 'executors':
                manager.stop_executors(args.group)
            else:
                manager.stop_all()
        
        elif args.command == 'status':
            manager.status()
        
        elif args.command == 'restart':
            manager.restart_all()
        
        elif args.command == 'init-config':
            manager.save_config()
        
        else:
            print("请指定命令。使用 --help 查看帮助。")
    
    except KeyboardInterrupt:
        print("\n操作被用户中断")
        manager.stop_all()
    except Exception as e:
        print(f"操作失败: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()