#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调度器独立服务启动脚本

用于启动独立的调度器节点，支持多实例部署和Leader选举
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
from app.services.scheduler_cluster import SchedulerClusterService
from app.schemas.scheduler import (
    SchedulerNodeCreate,
    SchedulerNodeHeartbeat,
    SchedulerNodeStatusUpdate,
    SchedulerStatus,
    SchedulerRole
)
from app.models import scheduler as scheduler_models
from app.models.workflow import WorkflowInstance, WorkflowNodeInstance
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import logging

logger = logging.getLogger(__name__)


class SchedulerService:
    """
    调度器服务类
    
    负责调度器节点的注册、心跳维护、Leader选举、任务调度等功能
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.node_id = config.get('node_id') or str(uuid.uuid4())
        # 确保node_name有默认值
        self.node_name = config.get('node_name') or f'scheduler-{self.node_id[:8]}'
        self.host_ip = config.get('host_ip', '127.0.0.1')
        self.port = config.get('port', 8002)
        
        self.is_running = False
        self.is_leader = False
        self.heartbeat_interval = 30  # 心跳间隔（秒）
        self.leader_check_interval = 60  # Leader检查间隔（秒）
        
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
        log_file = self.config.get('log_file', f'logs/scheduler_{self.node_id[:8]}.log')
        
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
        logger.info(f"接收到信号 {signum}，准备关闭调度器服务...")
        self.is_running = False
    
    async def start(self):
        """
        启动调度器服务
        """
        logger.info(f"启动调度器服务: {self.node_name} (ID: {self.node_id})")
        
        try:
            # 注册调度器节点
            await self._register_node()
            
            self.is_running = True
            
            # 启动各种服务循环
            await asyncio.gather(
                self._heartbeat_loop(),
                self._leader_election_loop(),
                self._task_scheduling_loop(),
                self._health_check_loop()
            )
            
        except Exception as e:
            logger.error(f"调度器服务启动失败: {e}")
            raise
        finally:
            await self._cleanup()
    
    async def _register_node(self):
        """
        注册调度器节点到集群
        """
        try:
            async for db in get_db():
                service = SchedulerClusterService(db)
                
                node_data = SchedulerNodeCreate(
                    node_id=self.node_id,
                    node_name=self.node_name,
                    host_ip=self.host_ip,
                    port=self.port,
                    capabilities=self._get_node_capabilities(),
                    resource_info=self._get_resource_info()
                )
                
                node = await service.register_scheduler_node(node_data)
                logger.info(f"调度器节点注册成功: {node.node_name}")
                break
                
        except Exception as e:
            logger.error(f"调度器节点注册失败: {e}")
            raise
    
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
                service = SchedulerClusterService(db)
                
                heartbeat_data = SchedulerNodeHeartbeat(
                    resource_usage=self._get_resource_info()
                )
                
                await service.update_heartbeat(self.node_id, heartbeat_data)
                break
                
        except Exception as e:
            logger.error(f"心跳更新失败: {e}")
    
    async def _leader_election_loop(self):
        """
        Leader选举循环
        """
        while self.is_running:
            try:
                await self._check_leader_status()
                await asyncio.sleep(self.leader_check_interval)
            except Exception as e:
                logger.error(f"Leader选举检查异常: {e}")
                await asyncio.sleep(30)
    
    async def _check_leader_status(self):
        """
        检查Leader状态
        """
        try:
            async for db in get_db():
                service = SchedulerClusterService(db)
                
                # 获取集群状态
                cluster_status = await service.get_cluster_status()
                
                if not cluster_status.leader_node_id:
                    # 没有Leader，尝试选举
                    logger.info("集群中没有Leader，尝试选举...")
                    election_result = await service.trigger_leader_election()
                    
                    if election_result.get('new_leader_id') == self.node_id:
                        self.is_leader = True
                        logger.info(f"成为新的Leader: {self.node_id}")
                    else:
                        self.is_leader = False
                        logger.info(f"选举结果，Leader是: {election_result.get('new_leader_id')}")
                
                elif cluster_status.leader_node_id == self.node_id:
                    # 当前节点是Leader
                    if not self.is_leader:
                        self.is_leader = True
                        logger.info(f"确认为Leader: {self.node_id}")
                
                else:
                    # 其他节点是Leader
                    if self.is_leader:
                        self.is_leader = False
                        logger.info(f"不再是Leader，当前Leader: {cluster_status.leader_node_id}")
                
                break
                
        except Exception as e:
            logger.error(f"Leader状态检查失败: {e}")
    
    async def _task_scheduling_loop(self):
        """
        任务调度循环（仅Leader执行）
        """
        while self.is_running:
            try:
                if self.is_leader:
                    await self._schedule_tasks()
                
                await asyncio.sleep(10)  # 每10秒检查一次
            except Exception as e:
                logger.error(f"任务调度循环异常: {e}")
                await asyncio.sleep(30)
    
    async def _schedule_tasks(self):
        """
        调度任务（仅Leader执行）
        
        处理PENDING状态的工作流实例，启动工作流执行
        """
        try:
            async for db in get_db():
                # 查找所有PENDING状态的工作流实例
                stmt = select(WorkflowInstance).where(
                    WorkflowInstance.status == 'PENDING'
                )
                result = await db.execute(stmt)
                pending_instances = result.scalars().all()
                
                for instance in pending_instances:
                    logger.info(f"处理PENDING工作流实例: {instance.instance_id}")
                    
                    # 检查是否到了调度时间
                    if instance.scheduled_time and instance.scheduled_time <= datetime.now():
                        # 启动工作流实例
                        await self._start_workflow_instance(db, instance)
                    
                break  # 只需要一个数据库会话
                
        except Exception as e:
            logger.error(f"调度任务时发生错误: {e}")
    
    async def _start_workflow_instance(self, db: AsyncSession, instance: WorkflowInstance):
        """
        启动工作流实例
        
        Args:
            db: 数据库会话
            instance: 工作流实例
        """
        try:
            # 导入工作流引擎
            from workflow_engine import workflow_engine
            
            # 启动工作流实例
            await workflow_engine.start_instance(instance.instance_id)
            
            logger.info(f"成功启动工作流实例: {instance.instance_id}")
            
        except Exception as e:
            logger.error(f"启动工作流实例 {instance.instance_id} 时发生错误: {e}")
            
            # 更新实例状态为FAILED
            instance.status = 'FAILED'
            instance.error_message = str(e)
            instance.updated_at = datetime.now()
            await db.commit()
    
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
            'max_scheduled_tasks': 1000,
            'supported_schedule_types': ['cron', 'interval', 'once'],
            'load_balancing': True,
            'fault_tolerance': True
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
                'is_leader': self.is_leader,
                'uptime': datetime.utcnow().isoformat()
            }
        except Exception:
            return {
                'cpu_percent': 0,
                'memory_percent': 0,
                'disk_percent': 0,
                'is_leader': self.is_leader,
                'uptime': datetime.utcnow().isoformat()
            }
    
    async def _cleanup(self):
        """
        清理资源
        """
        logger.info("开始清理调度器资源...")
        
        try:
            # 注销调度器节点
            async for db in get_db():
                service = SchedulerClusterService(db)
                await service.unregister_scheduler_node(self.node_id)
                logger.info(f"调度器节点注销成功: {self.node_id}")
                break
                
        except Exception as e:
            logger.error(f"调度器节点注销失败: {e}")
        
        logger.info("调度器服务已停止")


def parse_args():
    """
    解析命令行参数
    """
    parser = argparse.ArgumentParser(description='调度器独立服务')
    parser.add_argument('--node-id', dest='node_id', help='节点ID')
    parser.add_argument('--node-name', dest='node_name', help='节点名称')
    parser.add_argument('--host-ip', dest='host_ip', default='127.0.0.1', help='主机IP地址')
    parser.add_argument('--port', type=int, default=8002, help='端口号')
    parser.add_argument('--log-level', dest='log_level', default='INFO', help='日志级别')
    parser.add_argument('--log-file', dest='log_file', help='日志文件路径')
    
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
        'host_ip': args.host_ip,
        'port': args.port,
        'log_level': args.log_level,
        'log_file': args.log_file or f'logs/scheduler_{args.node_id[:8] if args.node_id else "default"}.log'
    }
    
    # 创建并启动调度器服务
    scheduler_service = SchedulerService(config)
    
    try:
        asyncio.run(scheduler_service.start())
    except KeyboardInterrupt:
        print("\n调度器服务被用户中断")
    except Exception as e:
        print(f"调度器服务异常退出: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()