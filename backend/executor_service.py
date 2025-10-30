#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
执行器独立服务启动脚本

用于启动独立的执行器节点，支持多实例部署
"""

import asyncio
import argparse
import logging
import os
import signal
import sys
import uuid
from datetime import datetime
from typing import Dict, Any, Optional

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import get_db
from app.services.executor_cluster import ExecutorClusterService
from app.schemas.executor import ExecutorNodeCreate, ExecutorNodeHeartbeat, ExecutorGroupCreate, ExecutorStatus
from app.core.logger import logger


class ExecutorService:
    """
    执行器服务类
    
    负责执行器节点的注册、心跳维护、任务执行等功能
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.node_id = config.get('node_id') or str(uuid.uuid4())
        self.node_name = config.get('node_name') or f'executor-{self.node_id[:8]}'
        self.group_id = config.get('group_id', 'default')
        self.host_ip = config.get('host_ip', '10.20.1.200')
        self.port = config.get('port', 8001)
        self.max_concurrent_tasks = config.get('max_concurrent_tasks', 5)
        
        self.is_running = False
        self.heartbeat_interval = 30  # 心跳间隔（秒）
        self.running_tasks = {}  # 正在运行的任务
        
        # 设置日志
        self._setup_logging()
        
        # 注册信号处理
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _setup_logging(self):
        """
        设置日志配置
        """
        log_level = self.config.get('log_level', 'INFO')
        log_file = self.config.get('log_file', f'logs/executor_{self.node_id[:8]}.log')
        
        # 创建日志目录
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        
        logging.basicConfig(
            level=getattr(logging, log_level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
    
    def _signal_handler(self, signum, frame):
        """
        信号处理器
        """
        logger.info(f"接收到信号 {signum}，准备关闭执行器服务...")
        self.is_running = False
    
    async def start(self):
        """
        启动执行器服务
        """
        logger.info(f"启动执行器服务: {self.node_name} (ID: {self.node_id})")
        
        try:
            # 注册执行器节点
            await self._register_node()
            
            self.is_running = True
            
            # 启动各种服务循环
            await asyncio.gather(
                self._heartbeat_loop(),
                self._task_execution_loop(),
                self._health_check_loop()
            )
            
        except Exception as e:
            logger.error(f"执行器服务启动失败: {e}")
            raise
        finally:
            await self._cleanup()
    
    async def _register_node(self):
        """
        注册执行器节点到集群
        """
        try:
            async for db in get_db():
                service = ExecutorClusterService(db)
                
                # 获取或创建默认执行器分组
                group_id = await self._get_or_create_default_group(service)
                
                node_data = ExecutorNodeCreate(
                    node_id=self.node_id,
                    node_name=self.node_name,
                    group_id=group_id,
                    host_ip=self.host_ip,
                    port=self.port,
                    status=ExecutorStatus.ONLINE,
                    max_concurrent_tasks=self.max_concurrent_tasks,
                    current_load=0,
                    capabilities=self._get_node_capabilities(),
                    resource_info=self._get_resource_info(),
                    tags=[],
                    node_metadata={}
                )
                
                node = await service.register_executor_node(node_data)
                logger.info(f"执行器节点注册成功: {node.node_name}")
                break
                
        except Exception as e:
            logger.error(f"执行器节点注册失败: {e}")
            raise
    
    async def _get_or_create_default_group(self, service: ExecutorClusterService) -> int:
        """
        获取或创建默认执行器分组
        
        Args:
            service: 执行器集群服务
            
        Returns:
            分组ID
        """
        try:
            # 尝试获取默认分组
            from app.schemas.executor import ExecutorGroupQueryParams
            params = ExecutorGroupQueryParams(group_name="default")
            groups, total = await service.get_executor_groups(params)
            
            if groups:
                return groups[0].id
            
            # 如果不存在，创建默认分组
            group_data = ExecutorGroupCreate(
                group_name="default",
                display_name="默认执行器分组",
                description="系统默认的执行器分组",
                group_type="DEFAULT",
                max_concurrent_tasks=50,
                tags=[],
                group_metadata={}
            )
            
            group = await service.create_executor_group(group_data)
            logger.info(f"创建默认执行器分组: {group.group_name}")
            return group.id
            
        except Exception as e:
             logger.error(f"获取或创建默认分组失败: {e}")
             # 返回一个默认值，假设ID为1的分组存在
             return 1
    
    async def _heartbeat_loop(self):
        """
        心跳循环
        """
        while self.is_running:
            try:
                await self._send_heartbeat()
                await asyncio.sleep(self.heartbeat_interval)
            except Exception as e:
                logger.error(f"心跳发送失败: {e}")
                await asyncio.sleep(5)
    
    async def _send_heartbeat(self):
        """
        发送心跳
        """
        try:
            async for db in get_db():
                service = ExecutorClusterService(db)
                
                heartbeat_data = ExecutorNodeHeartbeat(
                    current_load=len(self.running_tasks),
                    resource_usage=self._get_resource_info()
                )
                
                await service.update_heartbeat(self.node_id, heartbeat_data)
                break
                
        except Exception as e:
            logger.error(f"心跳更新失败: {e}")
    
    async def _task_execution_loop(self):
        """
        任务执行循环
        """
        while self.is_running:
            try:
                # 检查是否有新任务需要执行
                await self._check_and_execute_tasks()
                await asyncio.sleep(5)
            except Exception as e:
                logger.error(f"任务执行循环异常: {e}")
                await asyncio.sleep(10)
    
    async def _check_and_execute_tasks(self):
        """
        检查并执行任务
        
        这里应该从任务队列中获取任务并执行
        目前只是一个占位实现
        """
        # TODO: 实现任务队列获取和执行逻辑
        pass
    
    async def _health_check_loop(self):
        """
        健康检查循环
        """
        while self.is_running:
            try:
                # 检查节点健康状态
                health_status = self._check_node_health()
                if not health_status['healthy']:
                    logger.warning(f"节点健康检查失败: {health_status['reason']}")
                
                await asyncio.sleep(60)  # 每分钟检查一次
            except Exception as e:
                logger.error(f"健康检查异常: {e}")
                await asyncio.sleep(30)
    
    def _check_node_health(self) -> Dict[str, Any]:
        """
        检查节点健康状态
        """
        try:
            import psutil
            
            # 检查CPU使用率
            cpu_percent = psutil.cpu_percent(interval=1)
            if cpu_percent > 90:
                return {'healthy': False, 'reason': f'CPU使用率过高: {cpu_percent}%'}
            
            # 检查内存使用率
            memory = psutil.virtual_memory()
            if memory.percent > 90:
                return {'healthy': False, 'reason': f'内存使用率过高: {memory.percent}%'}
            
            # 检查磁盘使用率
            disk = psutil.disk_usage('/')
            if disk.percent > 90:
                return {'healthy': False, 'reason': f'磁盘使用率过高: {disk.percent}%'}
            
            return {'healthy': True, 'reason': 'OK'}
            
        except Exception as e:
            return {'healthy': False, 'reason': f'健康检查异常: {e}'}
    
    def _get_node_capabilities(self) -> Dict[str, Any]:
        """
        获取节点能力信息
        """
        return {
            'supported_task_types': ['python', 'shell', 'sql'],
            'max_memory_mb': 4096,
            'max_cpu_cores': 4,
            'gpu_available': False
        }
    
    def _get_resource_info(self) -> Dict[str, Any]:
        """
        获取资源信息
        """
        try:
            import psutil
            
            return {
                'cpu_percent': psutil.cpu_percent(interval=1),
                'memory_percent': psutil.virtual_memory().percent,
                'disk_percent': psutil.disk_usage('/').percent,
                'running_tasks': len(self.running_tasks),
                'max_concurrent_tasks': self.max_concurrent_tasks
            }
        except Exception:
            return {
                'cpu_percent': 0,
                'memory_percent': 0,
                'disk_percent': 0,
                'running_tasks': len(self.running_tasks),
                'max_concurrent_tasks': self.max_concurrent_tasks
            }
    
    async def _cleanup(self):
        """
        清理资源
        """
        logger.info("开始清理执行器资源...")
        
        try:
            # 注销执行器节点
            async for db in get_db():
                service = ExecutorClusterService(db)
                await service.unregister_executor_node(self.node_id)
                logger.info(f"执行器节点注销成功: {self.node_id}")
                break
                
        except Exception as e:
            logger.error(f"执行器节点注销失败: {e}")
        
        logger.info("执行器服务已停止")


def parse_args():
    """
    解析命令行参数
    """
    parser = argparse.ArgumentParser(description='执行器独立服务')
    parser.add_argument('--node-id', help='节点ID')
    parser.add_argument('--node-name', help='节点名称')
    parser.add_argument('--group-id', default='default', help='执行器分组ID')
    parser.add_argument('--host-ip', default='10.20.1.200', help='主机IP地址')
    parser.add_argument('--port', type=int, default=8001, help='端口号')
    parser.add_argument('--max-concurrent-tasks', type=int, default=5, help='最大并发任务数')
    parser.add_argument('--log-level', default='INFO', help='日志级别')
    parser.add_argument('--log-file', help='日志文件路径')
    
    return parser.parse_args()


def main():
    """
    主函数
    """
    args = parse_args()
    
    # 构建配置
    config = {
        'node_id': args.node_id,
        'node_name': args.node_name,
        'group_id': args.group_id,
        'host_ip': args.host_ip,
        'port': args.port,
        'max_concurrent_tasks': args.max_concurrent_tasks,
        'log_level': args.log_level,
        'log_file': args.log_file or f'logs/executor_{args.node_id[:8] if args.node_id else "default"}.log'
    }
    
    # 创建并启动执行器服务
    executor_service = ExecutorService(config)
    
    try:
        asyncio.run(executor_service.start())
    except KeyboardInterrupt:
        print("\n执行器服务被用户中断")
    except Exception as e:
        print(f"执行器服务异常退出: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()