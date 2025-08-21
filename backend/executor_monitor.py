#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
执行器节点监控程序

定期清理过期的执行器节点数据，防止数据库中积累无效节点
"""

import asyncio
import argparse
import logging
import sys
import os
from datetime import datetime, timedelta
from typing import List

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import get_db
from app.services.executor_cluster import ExecutorClusterService
from app.models.executor import ExecutorNode, ExecutorStatus
from app.core.logger import logger
from sqlalchemy import select, and_, func


class ExecutorMonitor:
    """
    执行器节点监控器
    
    负责监控和清理过期的执行器节点
    """
    
    def __init__(self, config: dict):
        """
        初始化监控器
        
        Args:
            config: 配置参数
        """
        self.config = config
        self.heartbeat_timeout = config.get('heartbeat_timeout', 300)  # 5分钟心跳超时
        self.cleanup_interval = config.get('cleanup_interval', 600)   # 10分钟清理间隔
        self.offline_retention = config.get('offline_retention', 3600)  # 1小时离线保留时间
        self.is_running = False
        
        # 设置日志
        self._setup_logging()
    
    def _setup_logging(self):
        """
        设置日志配置
        """
        log_level = self.config.get('log_level', 'INFO')
        log_file = self.config.get('log_file', 'logs/executor_monitor.log')
        
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
    
    async def start(self):
        """
        启动监控程序
        """
        logger.info("启动执行器节点监控程序")
        
        self.is_running = True
        
        try:
            while self.is_running:
                await self._monitor_cycle()
                await asyncio.sleep(self.cleanup_interval)
                
        except Exception as e:
            logger.error(f"监控程序异常: {e}")
            raise
        finally:
            logger.info("执行器节点监控程序已停止")
    
    async def _monitor_cycle(self):
        """
        执行一次监控周期
        """
        try:
            async for db in get_db():
                service = ExecutorClusterService(db)
                
                # 1. 标记超时节点为离线
                offline_count = await self._mark_timeout_nodes_offline(service)
                if offline_count > 0:
                    logger.info(f"标记 {offline_count} 个超时节点为离线状态")
                
                # 2. 清理长期离线的节点
                cleaned_count = await self._cleanup_expired_nodes(service)
                if cleaned_count > 0:
                    logger.info(f"清理了 {cleaned_count} 个过期节点")
                
                # 3. 统计当前节点状态
                await self._log_node_statistics(service)
                
                break
                
        except Exception as e:
            logger.error(f"监控周期执行失败: {e}")
    
    async def _mark_timeout_nodes_offline(self, service: ExecutorClusterService) -> int:
        """
        标记超时节点为离线状态
        
        Args:
            service: 执行器集群服务
            
        Returns:
            标记为离线的节点数量
        """
        timeout_threshold = datetime.utcnow() - timedelta(seconds=self.heartbeat_timeout)
        
        result = await service.db.execute(
            select(ExecutorNode).where(
                and_(
                    ExecutorNode.last_heartbeat < timeout_threshold,
                    ExecutorNode.status.in_([ExecutorStatus.ONLINE, ExecutorStatus.BUSY])
                )
            )
        )
        timeout_nodes = result.scalars().all()
        
        offline_count = 0
        for node in timeout_nodes:
            node.status = ExecutorStatus.OFFLINE
            node.updated_at = datetime.utcnow()
            offline_count += 1
            
            logger.warning(
                f"节点心跳超时，标记为离线: {node.node_name} ({node.node_id}) "
                f"最后心跳: {node.last_heartbeat}"
            )
        
        if offline_count > 0:
            await service.db.commit()
        
        return offline_count
    
    async def _cleanup_expired_nodes(self, service: ExecutorClusterService) -> int:
        """
        清理长期离线的过期节点
        
        Args:
            service: 执行器集群服务
            
        Returns:
            清理的节点数量
        """
        # 计算过期时间阈值
        expiry_threshold = datetime.utcnow() - timedelta(seconds=self.offline_retention)
        
        result = await service.db.execute(
            select(ExecutorNode).where(
                and_(
                    ExecutorNode.status == ExecutorStatus.OFFLINE,
                    ExecutorNode.updated_at < expiry_threshold
                )
            )
        )
        expired_nodes = result.scalars().all()
        
        cleaned_count = 0
        for node in expired_nodes:
            logger.info(
                f"清理过期节点: {node.node_name} ({node.node_id}) "
                f"离线时间: {node.updated_at}"
            )
            
            await service.db.delete(node)
            cleaned_count += 1
        
        if cleaned_count > 0:
            await service.db.commit()
        
        return cleaned_count
    
    async def _log_node_statistics(self, service: ExecutorClusterService):
        """
        记录节点统计信息
        
        Args:
            service: 执行器集群服务
        """
        result = await service.db.execute(
            select(ExecutorNode.status, func.count(ExecutorNode.id))
            .group_by(ExecutorNode.status)
        )
        
        stats = dict(result.fetchall())
        
        if stats:
            stats_str = ", ".join([f"{status.value}: {count}" for status, count in stats.items()])
            logger.info(f"当前节点状态统计: {stats_str}")
    
    def stop(self):
        """
        停止监控程序
        """
        logger.info("正在停止执行器节点监控程序...")
        self.is_running = False


def parse_args():
    """
    解析命令行参数
    """
    parser = argparse.ArgumentParser(description='执行器节点监控程序')
    parser.add_argument('--heartbeat-timeout', type=int, default=300, 
                       help='心跳超时时间（秒），默认300秒')
    parser.add_argument('--cleanup-interval', type=int, default=600, 
                       help='清理检查间隔（秒），默认600秒')
    parser.add_argument('--offline-retention', type=int, default=3600, 
                       help='离线节点保留时间（秒），默认3600秒')
    parser.add_argument('--log-level', default='INFO', 
                       help='日志级别，默认INFO')
    parser.add_argument('--log-file', 
                       help='日志文件路径，默认logs/executor_monitor.log')
    
    return parser.parse_args()


def main():
    """
    主函数
    """
    args = parse_args()
    
    # 构建配置
    config = {
        'heartbeat_timeout': args.heartbeat_timeout,
        'cleanup_interval': args.cleanup_interval,
        'offline_retention': args.offline_retention,
        'log_level': args.log_level,
        'log_file': args.log_file or 'logs/executor_monitor.log'
    }
    
    # 创建并启动监控程序
    monitor = ExecutorMonitor(config)
    
    try:
        asyncio.run(monitor.start())
    except KeyboardInterrupt:
        print("\n监控程序被用户中断")
        monitor.stop()
    except Exception as e:
        print(f"监控程序异常退出: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()