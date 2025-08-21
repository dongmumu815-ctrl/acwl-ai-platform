#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调度器集群管理服务
"""

import asyncio
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from uuid import uuid4

from sqlalchemy import select, update, delete, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..core.database import get_db
from ..models.scheduler import SchedulerNode, SchedulerLock, SchedulerRole, SchedulerStatus
from ..schemas.scheduler import (
    SchedulerNodeCreate,
    SchedulerNodeUpdate,
    SchedulerNodeHeartbeat,
    SchedulerNodeStatusUpdate,
    SchedulerClusterStatus,
    SchedulerNodeQueryParams
)
from ..core.exceptions import (
    NotFoundError,
    ConflictError,
    ValidationError
)
import logging

logger = logging.getLogger(__name__)


class SchedulerClusterService:
    """
    调度器集群管理服务
    
    提供调度器节点的注册、心跳、状态管理、Leader选举等功能
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.heartbeat_timeout = 30  # 心跳超时时间（秒）
        self.leader_election_timeout = 60  # Leader选举超时时间（秒）
    
    async def get_scheduler_nodes(
        self,
        params: SchedulerNodeQueryParams
    ) -> tuple[List[SchedulerNode], int]:
        """
        获取调度器节点列表
        
        Args:
            params: 查询参数
            
        Returns:
            调度器节点列表和总数
        """
        query = select(SchedulerNode)
        
        # 应用过滤条件
        if params.status:
            query = query.where(SchedulerNode.status == params.status)
        if params.role:
            query = query.where(SchedulerNode.role == params.role)
        if params.node_name:
            query = query.where(SchedulerNode.node_name.ilike(f"%{params.node_name}%"))
        # 注意：SchedulerNodeQueryParams 没有 host 属性，这里注释掉
        # if params.host:
        #     query = query.where(SchedulerNode.host_ip.ilike(f"%{params.host}%"))
        
        # 获取总数
        count_query = select(func.count()).select_from(query.subquery())
        total = await self.db.scalar(count_query)
        
        # 应用排序
        if params.sort_by:
            if hasattr(SchedulerNode, params.sort_by):
                order_column = getattr(SchedulerNode, params.sort_by)
                if params.sort_order == "desc":
                    query = query.order_by(order_column.desc())
                else:
                    query = query.order_by(order_column.asc())
        else:
            query = query.order_by(SchedulerNode.created_at.desc())
        
        # 应用分页
        if params.page and params.size:
            offset = (params.page - 1) * params.size
            query = query.offset(offset).limit(params.size)
        
        result = await self.db.execute(query)
        nodes = result.scalars().all()
        
        return list(nodes), total or 0
    
    async def register_scheduler_node(
        self,
        node_data: SchedulerNodeCreate
    ) -> SchedulerNode:
        """
        注册调度器节点
        
        Args:
            node_data: 节点创建数据
            
        Returns:
            创建的调度器节点
            
        Raises:
            ConflictException: 节点已存在
        """
        # 检查节点是否已存在
        existing_node = await self.db.scalar(
            select(SchedulerNode).where(
                and_(
                    SchedulerNode.node_name == node_data.node_name,
                    SchedulerNode.host_ip == node_data.host_ip,
                    SchedulerNode.port == node_data.port
                )
            )
        )
        
        if existing_node:
            raise ConflictError(f"调度器节点已存在: {node_data.node_name}")
        
        # 创建新节点
        node = SchedulerNode(
            node_id=node_data.node_id,
            node_name=node_data.node_name,
            host_ip=node_data.host_ip,
            port=node_data.port,
            status="standby",
            role="follower",
            version=node_data.version,
            capabilities=node_data.capabilities or {},
            node_metadata=node_data.node_metadata or {},
            last_heartbeat=datetime.utcnow()
        )
        
        self.db.add(node)
        await self.db.commit()
        await self.db.refresh(node)
        
        logger.info(f"调度器节点已注册: {node.node_name} ({node.node_id})")
        
        # 如果是第一个节点，自动成为Leader
        await self._check_and_elect_leader()
        
        return node
    
    async def get_scheduler_node(self, node_id: str) -> SchedulerNode:
        """
        获取调度器节点详情
        
        Args:
            node_id: 节点ID
            
        Returns:
            调度器节点
            
        Raises:
            NotFoundException: 节点不存在
        """
        node = await self.db.scalar(
            select(SchedulerNode).where(SchedulerNode.node_id == node_id)
        )
        
        if not node:
            raise NotFoundError(f"调度器节点不存在: {node_id}")
        
        return node
    
    async def update_scheduler_node(
        self,
        node_id: str,
        node_data: SchedulerNodeUpdate
    ) -> SchedulerNode:
        """
        更新调度器节点信息
        
        Args:
            node_id: 节点ID
            node_data: 更新数据
            
        Returns:
            更新后的调度器节点
            
        Raises:
            NotFoundException: 节点不存在
        """
        node = await self.get_scheduler_node(node_id)
        
        # 更新字段
        update_data = node_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(node, field):
                setattr(node, field, value)
        
        node.updated_at = datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(node)
        
        logger.info(f"调度器节点已更新: {node.node_name} ({node.node_id})")
        
        return node
    
    async def unregister_scheduler_node(self, node_id: str) -> bool:
        """
        注销调度器节点
        
        Args:
            node_id: 节点ID
            
        Returns:
            是否成功注销
            
        Raises:
            NotFoundException: 节点不存在
        """
        node = await self.get_scheduler_node(node_id)
        
        # 如果是Leader节点，需要触发重新选举
        if node.role == "leader":
            await self._trigger_leader_election()
        
        # 删除节点
        await self.db.delete(node)
        await self.db.commit()
        
        logger.info(f"调度器节点已注销: {node.node_name} ({node.node_id})")
        
        return True
    
    async def update_heartbeat(
        self,
        node_id: str,
        heartbeat_data: SchedulerNodeHeartbeat
    ) -> SchedulerNode:
        """
        更新调度器节点心跳
        
        Args:
            node_id: 节点ID
            heartbeat_data: 心跳数据
            
        Returns:
            更新后的调度器节点
            
        Raises:
            NotFoundException: 节点不存在
        """
        node = await self.get_scheduler_node(node_id)
        
        # 更新心跳信息
        node.last_heartbeat = datetime.utcnow()
        
        # 更新资源使用情况（如果提供）
        if heartbeat_data.resource_usage:
            # 这里可以根据需要更新节点的资源信息
            # 暂时将资源信息存储在node_metadata中
            if not hasattr(node, 'node_metadata') or node.node_metadata is None:
                node.node_metadata = {}
            node.node_metadata.update(heartbeat_data.resource_usage)
        
        # 如果节点状态不是ACTIVE，更新为ACTIVE
        if node.status != "active":
            node.status = "active"
        
        await self.db.commit()
        await self.db.refresh(node)
        
        return node
    
    async def update_node_status(
        self,
        node_id: str,
        status_data: SchedulerNodeStatusUpdate
    ) -> SchedulerNode:
        """
        更新调度器节点状态
        
        Args:
            node_id: 节点ID
            status_data: 状态更新数据
            
        Returns:
            更新后的调度器节点
            
        Raises:
            NotFoundException: 节点不存在
        """
        node = await self.get_scheduler_node(node_id)
        
        old_status = node.status
        node.status = status_data.status
        
        if status_data.error_message:
            node.error_message = status_data.error_message
        
        node.updated_at = datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(node)
        
        logger.info(
            f"调度器节点状态已更新: {node.node_name} ({node.node_id}) "
            f"{old_status} -> {node.status}"
        )
        
        # 如果节点状态变为OFFLINE，可能需要重新选举Leader
        if node.status == "offline" and node.role == "leader":
            await self._trigger_leader_election()
        
        return node
    
    async def get_cluster_status(self) -> SchedulerClusterStatus:
        """
        获取调度器集群状态
        
        Returns:
            集群状态信息
        """
        # 获取所有节点
        result = await self.db.execute(select(SchedulerNode))
        nodes = result.scalars().all()
        
        # 统计各状态节点数量
        total_nodes = len(nodes)
        running_nodes = sum(1 for node in nodes if node.status == "running")
        offline_nodes = sum(1 for node in nodes if node.status == "offline")
        error_nodes = sum(1 for node in nodes if node.status == "error")
        
        # 查找Leader节点
        leader_node = next((node for node in nodes if node.role == "leader"), None)
        
        # 计算集群健康度
        health_score = (running_nodes / total_nodes * 100) if total_nodes > 0 else 0
        
        return SchedulerClusterStatus(
            total_nodes=total_nodes,
            online_nodes=running_nodes,
            leader_node_id=leader_node.node_id if leader_node else None,
            leader_node_name=leader_node.node_name if leader_node else None,
            leader_election_time=leader_node.updated_at if leader_node else None,
            cluster_health="healthy" if health_score > 80 else "degraded" if health_score > 50 else "critical",
            nodes=list(nodes)
        )
    
    async def trigger_leader_election(self) -> Dict[str, Any]:
        """
        触发Leader选举
        
        Returns:
            选举结果
        """
        return await self._trigger_leader_election()
    
    async def cleanup_offline_nodes(self) -> int:
        """
        清理离线节点
        
        Returns:
            清理的节点数量
        """
        # 查找超时的节点
        timeout_threshold = datetime.utcnow() - timedelta(seconds=self.heartbeat_timeout * 3)
        
        result = await self.db.execute(
            select(SchedulerNode).where(
                and_(
                    SchedulerNode.last_heartbeat < timeout_threshold,
                    SchedulerNode.status != "offline"
                )
            )
        )
        timeout_nodes = result.scalars().all()
        
        cleaned_count = 0
        leader_offline = False
        
        for node in timeout_nodes:
            if node.role == "leader":
                leader_offline = True
            
            node.status = "offline"
            node.updated_at = datetime.utcnow()
            cleaned_count += 1
            
            logger.warning(f"调度器节点已离线: {node.node_name} ({node.node_id})")
        
        await self.db.commit()
        
        # 如果Leader离线，触发重新选举
        if leader_offline:
            await self._trigger_leader_election()
        
        return cleaned_count
    
    async def _check_and_elect_leader(self) -> Optional[SchedulerNode]:
        """
        检查并选举Leader
        
        Returns:
            当前Leader节点
        """
        # 查找当前Leader
        current_leader = await self.db.scalar(
            select(SchedulerNode).where(
                and_(
                    SchedulerNode.role == "leader",
                    SchedulerNode.status == "running"
                )
            )
        )
        
        if current_leader:
            return current_leader
        
        # 没有Leader，进行选举
        return await self._elect_new_leader()
    
    async def _trigger_leader_election(self) -> Dict[str, Any]:
        """
        触发Leader选举
        
        Returns:
            选举结果
        """
        # 将当前Leader设为Follower
        await self.db.execute(
            update(SchedulerNode)
            .where(SchedulerNode.role == "leader")
            .values(role="follower", updated_at=datetime.utcnow())
        )
        
        # 选举新Leader
        new_leader = await self._elect_new_leader()
        
        await self.db.commit()
        
        if new_leader:
            logger.info(f"新Leader已选举: {new_leader.node_name} ({new_leader.node_id})")
            return {
                "success": True,
                "new_leader_id": new_leader.node_id,
                "new_leader_name": new_leader.node_name,
                "election_time": datetime.utcnow().isoformat()
            }
        else:
            logger.warning("Leader选举失败: 没有可用的候选节点")
            return {
                "success": False,
                "message": "没有可用的候选节点",
                "election_time": datetime.utcnow().isoformat()
            }
    
    async def _elect_new_leader(self) -> Optional[SchedulerNode]:
        """
        选举新Leader
        
        Returns:
            新选举的Leader节点
        """
        # 查找所有可用的节点（运行中或待机），按注册时间排序（最早注册的优先）
        result = await self.db.execute(
            select(SchedulerNode)
            .where(
                and_(
                    SchedulerNode.status.in_(["running", "standby"]),
                    SchedulerNode.role == "follower"
                )
            )
            .order_by(SchedulerNode.created_at.asc())
        )
        candidates = result.scalars().all()
        
        if not candidates:
            return None
        
        # 选择第一个候选节点作为Leader
        new_leader = candidates[0]
        new_leader.role = "leader"
        new_leader.updated_at = datetime.utcnow()
        
        return new_leader


async def get_scheduler_cluster_service(db: AsyncSession = None) -> SchedulerClusterService:
    """
    获取调度器集群管理服务实例
    
    Args:
        db: 数据库会话
        
    Returns:
        调度器集群管理服务实例
    """
    if db is None:
        async for session in get_db():
            db = session
            break
    
    return SchedulerClusterService(db)