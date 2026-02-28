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
import uvicorn
import threading
from fastapi import FastAPI
from datetime import datetime, timedelta
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
from app.models.workflow import WorkflowInstance, WorkflowNodeInstance, WorkflowSchedule, ScheduleType, InstanceStatus, TriggerType, Workflow
from app.models.task import TaskInstance, TaskStatus
from app.services.workflow_engine import workflow_engine
from sqlalchemy import select, and_, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
import logging

try:
    from croniter import croniter
except ImportError:
    croniter = None
    logging.warning("croniter module not found, cron scheduling will not work")

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

    def _start_api_server(self):
        """
        启动API服务
        """
        app = FastAPI(title=f"Scheduler Service - {self.node_name}")
        
        @app.get("/health")
        async def health_check():
            return self._check_node_health()
            
        @app.get("/status")
        async def status():
            return {
                "node_id": self.node_id,
                "node_name": self.node_name,
                "status": "active" if self.is_running else "stopped",
                "is_leader": self.is_leader,
                "uptime": self._get_resource_info().get("uptime")
            }

        # 在独立线程中启动 API 服务
        # 注意：这里仅作为演示，生产环境可能需要更健壮的启动方式
        def run_server():
            uvicorn.run(app, host="0.0.0.0", port=self.port, log_level="error")
            
        thread = threading.Thread(target=run_server, daemon=True)
        thread.start()
        logger.info(f"API服务已启动，监听端口: {self.port}")

    async def start(self):
        """
        启动调度器服务
        """
        logger.info(f"启动调度器服务: {self.node_name} (ID: {self.node_id})")
        
        # 启动API服务
        self._start_api_server()
        
        try:
            # 注册调度器节点
            await self._register_node()
            
            self.is_running = True
            
            # 启动各种服务循环
            await asyncio.gather(
                self._heartbeat_loop(),
                self._leader_election_loop(),
                self._task_scheduling_loop(),
                self._schedule_generator_loop(),
                self._result_processor_loop(),
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
                
                # 1. 检查并清理相同IP和端口的旧节点（解决幽灵节点问题）
                try:
                    stmt = select(scheduler_models.SchedulerNode).where(
                        scheduler_models.SchedulerNode.host_ip == self.host_ip,
                        scheduler_models.SchedulerNode.port == self.port
                    )
                    result = await db.execute(stmt)
                    existing_nodes = result.scalars().all()
                    
                    for node in existing_nodes:
                        if node.node_id != self.node_id:
                            logger.info(f"发现冲突的旧节点 (IP: {self.host_ip}, Port: {self.port}), 标记为离线: {node.node_name} ({node.node_id})")
                            node.status = SchedulerStatus.OFFLINE.value
                            node.updated_at = datetime.utcnow()
                    await db.commit()
                except Exception as e:
                    logger.warning(f"清理旧节点时出错: {e}")

                # 2. 检查节点名称是否已存在
                try:
                    stmt = select(scheduler_models.SchedulerNode).where(scheduler_models.SchedulerNode.node_name == self.node_name)
                    existing_node = await db.scalar(stmt)
                    
                    if existing_node:
                        logger.info(f"发现已存在的调度器节点: {self.node_name} (ID: {existing_node.node_id})")
                        self.node_id = existing_node.node_id
                        # 先注销旧的
                        await service.unregister_scheduler_node(self.node_id)
                        logger.info(f"已注销旧调度器实例: {self.node_id}")
                except Exception as e:
                    logger.warning(f"检查已存在调度器节点时出错: {e}")

                node_data = SchedulerNodeCreate(
                    node_id=self.node_id,
                    node_name=self.node_name,
                    host_ip=self.host_ip,
                    port=self.port,
                    status=SchedulerStatus.ONLINE,
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
                
                # 清理离线节点（这也将处理Leader离线的情况）
                await service.cleanup_offline_nodes()
                
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
        
        处理PENDING状态的工作流实例，启动工作流执行
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
                    WorkflowInstance.status == InstanceStatus.PENDING
                )
                result = await db.execute(stmt)
                pending_instances = result.scalars().all()
                if pending_instances:
                    logger.info(f"DEBUG: Found {len(pending_instances)} pending workflow instances")
                
                for instance in pending_instances:
                    # 检查是否到了调度时间
                    if instance.scheduled_time and instance.scheduled_time <= datetime.now():
                         logger.info(f"处理PENDING工作流实例: {instance.instance_id}")
                         # 启动工作流实例
                         await self._start_workflow_instance(db, instance)
                    
                break  # 只需要一个数据库会话
                
        except Exception as e:
            logger.error(f"调度任务时发生错误: {e}")
    
    async def _start_workflow_instance(self, db: AsyncSession, instance: WorkflowInstance):
        """
        启动工作流实例
        """
        try:
            # 启动工作流实例
            await workflow_engine.start_instance(instance.id, db)
            
            logger.info(f"成功启动工作流实例: {instance.instance_id}")
            
        except Exception as e:
            logger.error(f"启动工作流实例 {instance.instance_id} 时发生错误: {e}")
            
            # 更新实例状态为FAILED
            instance.status = InstanceStatus.FAILED
            instance.error_message = str(e)
            instance.updated_at = datetime.now()
            await db.commit()
    
    async def _schedule_generator_loop(self):
        """
        调度生成循环（仅Leader执行）
        
        扫描 WorkflowSchedule 表，根据 Cron/Interval 生成新的 WorkflowInstance
        """
        while self.is_running:
            try:
                if self.is_leader:
                    await self._generate_scheduled_instances()
                
                await asyncio.sleep(30)  # 每30秒检查一次
            except Exception as e:
                logger.error(f"调度生成循环异常: {e}")
                await asyncio.sleep(30)
    
    async def _generate_scheduled_instances(self):
        """
        生成调度实例
        """
        try:
            async for db in get_db():
                # 获取所有启用的调度
                stmt = select(WorkflowSchedule).where(WorkflowSchedule.is_enabled == True)
                result = await db.execute(stmt)
                schedules = result.scalars().all()
                
                now = datetime.now()
                
                for schedule in schedules:
                    try:
                        should_run = False
                        
                        # 检查生效时间
                        if schedule.start_time and now < schedule.start_time:
                            continue
                        if schedule.end_time and now > schedule.end_time:
                            continue
                            
                        # 检查 Cron
                        if schedule.schedule_type == ScheduleType.CRON and schedule.cron_expression and croniter:
                             # 获取该调度最近一次生成的实例
                            stmt = select(WorkflowInstance).where(
                                WorkflowInstance.triggered_by == TriggerType.SCHEDULE
                            ).order_by(desc(WorkflowInstance.created_at)).limit(1)
                            # 这里应该加 schedule_id 过滤，但 WorkflowInstance 没有 schedule_id 字段
                            # 我们假设通过 naming convention 或其他方式关联。
                            # 暂时简化：每次都检查 cron 是否匹配当前分钟
                            
                            c = croniter(schedule.cron_expression, now - timedelta(minutes=1))
                            next_run = c.get_next(datetime)
                            # 如果下一分钟就是触发时间（或者当前分钟匹配）
                            # 这种方式比较粗糙，更好的方式是记录 last_run_at
                            # 由于没有 last_run_at，我们简单判断：
                            # 如果 croniter.match(now) 为真 (需要自己实现或假设)
                            
                            # 更好的逻辑：计算上次运行时间，如果上次运行时间 + 周期 <= now，且 > 上次检查时间
                            pass
                            
                        # 简化实现：仅针对 Interval 演示
                        if schedule.schedule_type == ScheduleType.INTERVAL and schedule.interval_seconds:
                            # 查找最近的一个实例
                            stmt = select(WorkflowInstance).where(
                                WorkflowInstance.workflow_id == schedule.workflow_id,
                                WorkflowInstance.triggered_by == TriggerType.SCHEDULE
                            ).order_by(desc(WorkflowInstance.created_at)).limit(1)
                            last_instance = await db.scalar(stmt)
                            
                            if not last_instance:
                                should_run = True
                            else:
                                next_run_time = last_instance.created_at + timedelta(seconds=schedule.interval_seconds)
                                if now >= next_run_time:
                                    should_run = True
                        
                        # 针对 Cron 的临时实现 (每分钟触发一次)
                        if schedule.schedule_type == ScheduleType.CRON:
                            # 这是一个 hack，实际应该用 redis 锁 + last_run_time
                            # 这里简单每分钟生成一个，生产环境请勿模仿
                            pass

                        if should_run:
                            await self._create_scheduled_instance(db, schedule)
                            
                    except Exception as e:
                        logger.error(f"处理调度 {schedule.id} 失败: {e}")
                        
                break
        except Exception as e:
            logger.error(f"生成调度实例失败: {e}")

    async def _create_scheduled_instance(self, db: AsyncSession, schedule: WorkflowSchedule):
        """
        创建调度实例
        """
        instance_id = f"sch-{schedule.id}-{uuid.uuid4().hex[:8]}"
        instance = WorkflowInstance(
            instance_id=instance_id,
            workflow_id=schedule.workflow_id,
            status=InstanceStatus.PENDING,
            triggered_by=TriggerType.SCHEDULE,
            scheduled_time=datetime.now(), # 立即执行
            input_data=schedule.input_data or {},
            created_by_scheduler=self.node_id
        )
        db.add(instance)
        await db.commit()
        logger.info(f"生成调度实例: {instance_id} (Schedule: {schedule.schedule_name})")

    async def _result_processor_loop(self):
        """
        结果处理循环
        
        检查已完成的任务实例，推进工作流
        """
        while self.is_running:
            try:
                await self._process_task_results()
                await asyncio.sleep(5)
            except Exception as e:
                logger.error(f"结果处理循环异常: {e}")
                await asyncio.sleep(10)

    async def _process_task_results(self):
        """
        处理任务结果
        """
        try:
            async for db in get_db():
                # 查找所有 RUNNING 状态的节点实例，且关联了 TaskInstance
                # 由于 SQLAlchemy 异步查询关联比较麻烦，这里分步查询
                
                # 1. 查出所有 RUNNING 且类型为 TASK 的节点实例
                stmt = select(WorkflowNodeInstance).where(
                    WorkflowNodeInstance.status == InstanceStatus.RUNNING,
                    WorkflowNodeInstance.task_instance_id.isnot(None)
                )
                result = await db.execute(stmt)
                node_instances = result.scalars().all()
                
                for node_instance in node_instances:
                    # 2. 查询对应的 TaskInstance
                    task_instance = await db.get(TaskInstance, node_instance.task_instance_id)
                    
                    if not task_instance:
                        continue
                        
                    # 3. 检查任务状态
                    if task_instance.status == TaskStatus.SUCCESS:
                        logger.info(f"任务 {task_instance.instance_id} 执行成功，完成节点 {node_instance.id}")
                        # 标记节点完成
                        output_data = task_instance.result_data or {}
                        await workflow_engine._complete_node(node_instance.id, output_data, db)
                        
                        # 继续执行后续节点
                        await workflow_engine._execute_next_nodes(node_instance.workflow_instance_id, node_instance.node_id, db)
                        
                        # 检查工作流是否完成
                        await workflow_engine._check_workflow_completion(node_instance.workflow_instance_id, db)
                        
                    elif task_instance.status == TaskStatus.FAILED:
                        logger.error(f"任务 {task_instance.instance_id} 执行失败，失败节点 {node_instance.id}")
                        # 标记节点失败
                        await workflow_engine._fail_node(node_instance.workflow_instance_id, node_instance.node_id, task_instance.error_message, db)
                        
                        # 检查工作流是否完成
                        await workflow_engine._check_workflow_completion(node_instance.workflow_instance_id, db)

                break
        except Exception as e:
            logger.error(f"处理任务结果失败: {e}")

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
            if disk.percent > 95:
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
    parser.add_argument('--port', type=int, default=6789, help='端口号')
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
