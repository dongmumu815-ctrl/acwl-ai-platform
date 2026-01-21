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
import socket
import uuid
import uvicorn
import threading
from fastapi import FastAPI
from datetime import datetime
from typing import Dict, Any, Optional

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import get_db
from app.services.executor_cluster import ExecutorClusterService
from app.services.task_executor import TaskExecutionExecutor
from app.core.logger import logger
from app.models.executor import ExecutorStatus
from app.schemas.executor import ExecutorNodeCreate, ExecutorNodeHeartbeat, ExecutorGroupCreate


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
        self.host_ip = config.get('host_ip') or self._get_local_ip()
        self.port = config.get('port', 8001)
        self.max_concurrent_tasks = config.get('max_concurrent_tasks', 5)
        
        self.is_running = False
        self.heartbeat_interval = 30  # 心跳间隔（秒）
        self.running_tasks = {}  # 正在运行的任务
        
        # 初始化任务执行器
        self.task_executor = TaskExecutionExecutor()
        
        # 设置日志
        self._setup_logging()
        
        # 注册信号处理
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _get_local_ip(self) -> str:
        """
        获取本机IP地址
        """
        try:
            # 创建一个UDP socket连接到外网地址（不会实际发送数据）
            # 这里使用Google DNS作为目标，仅为了选择正确的网络接口
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(('8.8.8.8', 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return '127.0.0.1'
    
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

    def _start_api_server(self):
        """
        启动API服务
        """
        app = FastAPI(title=f"Executor Service - {self.node_name}")
        
        @app.get("/health")
        async def health_check():
            return self._check_node_health()
            
        @app.get("/status")
        async def status():
            return {
                "node_id": self.node_id,
                "node_name": self.node_name,
                "status": "online" if self.is_running else "offline",
                "running_tasks": len(self.running_tasks),
                "max_concurrent_tasks": self.max_concurrent_tasks,
                "resource_usage": self._get_resource_info()
            }

        def run_server():
            uvicorn.run(app, host="0.0.0.0", port=self.port, log_level="error")
            
        thread = threading.Thread(target=run_server, daemon=True)
        thread.start()
        logger.info(f"API服务已启动，监听端口: {self.port}")

    async def start(self):
        """
        启动执行器服务
        """
        logger.info(f"启动执行器服务: {self.node_name} (ID: {self.node_id})")
        
        # 启动API服务
        self._start_api_server()
        
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
                
                # 1. 检查并清理相同IP和端口的旧节点（解决幽灵节点问题）
                try:
                    from app.models.executor import ExecutorNode, ExecutorStatus
                    from sqlalchemy import select
                    
                    stmt = select(ExecutorNode).where(
                        ExecutorNode.host_ip == self.host_ip,
                        ExecutorNode.port == self.port
                    )
                    result = await db.execute(stmt)
                    existing_nodes = result.scalars().all()
                    
                    for node in existing_nodes:
                        if node.node_id != self.node_id:
                            logger.info(f"发现冲突的旧执行器节点 (IP: {self.host_ip}, Port: {self.port}), 标记为离线: {node.node_name} ({node.node_id})")
                            node.status = ExecutorStatus.OFFLINE.value
                            node.updated_at = datetime.utcnow()
                    await db.commit()
                except Exception as e:
                    logger.warning(f"清理旧执行器节点时出错: {e}")

                # 2. 检查节点是否已存在
                try:
                    from sqlalchemy import select
                    from app.models.executor import ExecutorNode, ExecutorStatus
                    from app.schemas.executor import ExecutorNodeCreate
                    
                    stmt = select(ExecutorNode).where(ExecutorNode.node_name == self.node_name)
                    existing_node = await db.scalar(stmt)
                    
                    if existing_node:
                        logger.info(f"发现已存在的执行器节点: {self.node_name} (ID: {existing_node.node_id})")
                        self.node_id = existing_node.node_id
                        # 尝试注销旧节点
                        try:
                            await service.unregister_executor_node(self.node_id)
                            logger.info(f"已注销旧节点实例: {self.node_id}")
                        except Exception as e:
                            logger.warning(f"注销旧节点失败 (可能不存在): {e}")
                            
                except Exception as e:
                    logger.warning(f"检查已存在节点时出错: {e}")

                try:
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
                    
        except Exception as e:
            logger.error(f"注册节点过程中发生未捕获异常: {e}")
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
        """
        # 检查当前并发数是否已满
        if len(self.running_tasks) >= self.max_concurrent_tasks:
            return

        try:
            async for db in get_db():
                service = ExecutorClusterService(db)
                
                # 获取可执行的任务数量
                slots_available = self.max_concurrent_tasks - len(self.running_tasks)
                
                # 从服务获取待执行任务
                tasks = await service.fetch_pending_tasks(self.node_id, limit=slots_available)
                
                for task in tasks:
                    # 启动任务执行协程
                    task_id = str(task.id)
                    self.running_tasks[task_id] = asyncio.create_task(
                        self._execute_single_task(service, task)
                    )
                    
                break
                
        except Exception as e:
            logger.error(f"获取任务失败: {e}")

    async def _execute_single_task(self, service: ExecutorClusterService, task: Any):
        """
        执行单个任务
        """
        task_id = str(task.id)
        logger.info(f"开始处理任务: {task_id}")
        
        try:
            # 1. 更新任务状态为运行中
            await service.update_task_status(task.id, 'running')
            
            # 2. 准备任务信息
            # 优先从 runtime_config 获取配置，如果没有则从 task_definition 获取
            runtime_config = getattr(task, 'runtime_config', {}) or {}
            task_def = getattr(task, 'task_definition', None)
            
            # 获取任务类型
            original_type = 'unknown'
            if runtime_config and runtime_config.get('task_type'):
                original_type = runtime_config.get('task_type')
            elif task_def:
                # 处理 Enum 类型
                original_type = task_def.task_type.value if hasattr(task_def.task_type, 'value') else str(task_def.task_type)
            
            logger.info(f"DEBUG: 任务 {task_id} 原始类型: {original_type}")
            logger.info(f"DEBUG: runtime_config keys: {list(runtime_config.keys()) if runtime_config else 'None'}")
            if runtime_config and 'config' in runtime_config:
                logger.info(f"DEBUG: runtime_config['config']: {runtime_config['config']}")
            
            # 类型映射：前端类型 -> 执行器类型
            type_mapping = {
                'python': 'python_code',
                'shell': 'shell_script',
                'sql-execute': 'sql_query',
                'database-query': 'sql_query',
                'data_sync': 'data_sync',
                'model_train': 'model_train',
                'PYTHON_CODE': 'python_code', # 支持大写枚举值
                'SHELL_SCRIPT': 'shell_script',
                'SQL_QUERY': 'sql_query',
                # 'custom': 'python_code'  # 移除 custom 映射
            }
            task_type = type_mapping.get(original_type, original_type)
            # 如果映射后仍然是大写（例如 original_type 是 PYTHON_CODE 但不在 mapping 中），尝试转小写
            if task_type.upper() == task_type:
                 task_type = task_type.lower()
            
            # 获取任务名称
            task_name = f'task-{task_id}'
            if task_def and task_def.name:
                task_name = task_def.name
            
            # 获取任务内容和配置
            task_content = {}
            task_config = {}
            env_vars = {}
            
            if runtime_config:
                task_content = runtime_config.get('task_content', {})
                # 兼容旧格式或不同字段名
                if not task_content and 'code' in runtime_config:
                    task_content = {'code': runtime_config['code']}
                
                # 如果从标准字段没找到，尝试从 config 结构中查找 (针对 WorkflowEngine 传来的数据结构)
                if not task_content and 'config' in runtime_config:
                    node_cfg = runtime_config['config']
                    if isinstance(node_cfg, dict):
                        # 尝试直接从 config 对象获取 (情况1: config = {"code": "..."})
                        if 'code' in node_cfg:
                            task_content['code'] = node_cfg['code']
                        if 'script' in node_cfg:
                            task_content['script_content'] = node_cfg['script']
                        if 'sql' in node_cfg:
                            task_content['sql'] = node_cfg['sql']
                            
                        # 如果没有找到，尝试获取内部的 config 对象 (情况2: config = {"config": {"code": "..."}})
                        if not task_content:
                            inner_cfg = node_cfg.get('config')
                            if isinstance(inner_cfg, dict):
                                # Python 任务
                                if 'code' in inner_cfg:
                                    task_content['code'] = inner_cfg['code']
                                # Shell 任务
                                if 'script' in inner_cfg:
                                    task_content['script_content'] = inner_cfg['script']
                                # SQL 任务
                                if 'sql' in inner_cfg:
                                    task_content['sql'] = inner_cfg['sql']

                task_config = runtime_config.get('task_config', {})
                # 如果 runtime_config 本身包含配置项，也合并进去
                for k, v in runtime_config.items():
                    if k not in ['task_type', 'task_content', 'task_config', 'code', 'environment_variables']:
                        task_config[k] = v
                
                # 获取环境变量
                env_vars = runtime_config.get('environment_variables', {})
            
            # 如果 runtime_config 中没有内容，尝试从 task_definition 获取
            if not task_content and task_def:
                if task_def.script_content:
                    task_content = {'code': task_def.script_content}
                elif task_def.command_template:
                    task_content = {'command': task_def.command_template}
                elif task_def.task_config:
                    # 某些任务类型可能将内容放在 task_config 中
                    pass
            
            # 如果 runtime_config 中没有配置，尝试从 task_definition 获取合并
            if task_def and task_def.task_config:
                # runtime_config 优先级更高，所以只补充缺失的
                def_config = task_def.task_config or {}
                for k, v in def_config.items():
                    if k not in task_config:
                        task_config[k] = v
            
            # 合并环境变量
            if task_def and task_def.environment_variables:
                for k, v in task_def.environment_variables.items():
                    if k not in env_vars:
                        env_vars[k] = v

            # 将环境变量放入 task_config，以便传递给 TaskExecutor
            if env_vars:
                task_config['environment_variables'] = env_vars

            task_info = {
                'task_name': task_name,
                'task_type': task_type,
                'task_content': task_content,
                'task_config': task_config,
                'instance_id': task.instance_id
            }
            
            # 3. 执行任务
            result = await self.task_executor.execute_task(task_info)
            
            # 4. 更新任务状态为完成或失败
            status = 'success' if result['success'] else 'failed'
            await service.update_task_status(task.id, status, result)
            
            logger.info(f"任务 {task_id} 执行完成: {status}")
            
        except Exception as e:
            logger.error(f"任务 {task_id} 执行异常: {e}")
            try:
                await service.update_task_status(task.id, 'failed', {'error': str(e)})
            except:
                pass
        finally:
            # 从运行列表中移除
            if task_id in self.running_tasks:
                del self.running_tasks[task_id]

    
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
            disk = psutil.disk_usage('c:\\') if os.name == 'nt' else psutil.disk_usage('/')
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
    parser.add_argument('--port', type=int, default=9876, help='端口号')
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