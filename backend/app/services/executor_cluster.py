#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
执行器集群管理服务
"""

import asyncio
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from uuid import uuid4

from sqlalchemy import select, update, delete, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..core.database import get_db
from ..models.executor import ExecutorGroup, ExecutorNode, ExecutorStatus, GroupType, LoadBalanceStrategy
from ..models.task import TaskInstance, TaskStatus
from ..schemas.executor import (
    ExecutorGroupCreate,
    ExecutorGroupUpdate,
    ExecutorGroupQueryParams,
    ExecutorNodeCreate,
    ExecutorNodeUpdate,
    ExecutorNodeHeartbeat,
    ExecutorNodeStatusUpdate,
    ExecutorNodeQueryParams,
    ExecutorNodeStatus
)
from ..core.exceptions import (
    NotFoundError,
    ConflictError,
    ValidationError
)
from ..core.logger import logger


class ExecutorClusterService:
    """
    执行器集群管理服务
    
    提供执行器分组和节点的管理功能
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.heartbeat_timeout = 30  # 心跳超时时间（秒）
    
    # ==================== 执行器分组管理 ====================
    
    async def get_executor_groups(
        self,
        params: ExecutorGroupQueryParams
    ) -> tuple[List[ExecutorGroup], int]:
        """
        获取执行器分组列表
        
        Args:
            params: 查询参数
            
        Returns:
            执行器分组列表和总数
        """
        query = select(ExecutorGroup)
        
        # 应用过滤条件
        if params.group_name:
            query = query.where(ExecutorGroup.group_name.ilike(f"%{params.group_name}%"))
        if params.group_type:
            query = query.where(ExecutorGroup.group_type == params.group_type)
        if params.is_active is not None:
            query = query.where(ExecutorGroup.is_active == params.is_active)
        
        # 获取总数
        count_query = select(func.count()).select_from(query.subquery())
        total = await self.db.scalar(count_query)
        
        # 应用排序
        if params.sort_by:
            if hasattr(ExecutorGroup, params.sort_by):
                order_column = getattr(ExecutorGroup, params.sort_by)
                if params.sort_order == "desc":
                    query = query.order_by(order_column.desc())
                else:
                    query = query.order_by(order_column.asc())
        else:
            query = query.order_by(ExecutorGroup.created_at.desc())
        
        # 应用分页
        if params.page and params.size:
            offset = (params.page - 1) * params.size
            query = query.offset(offset).limit(params.size)
        
        # 加载关联的节点信息
        query = query.options(selectinload(ExecutorGroup.executors))
        
        result = await self.db.execute(query)
        groups = result.scalars().all()
        
        return list(groups), total or 0
    
    async def create_executor_group(
        self,
        group_data: ExecutorGroupCreate
    ) -> ExecutorGroup:
        """
        创建执行器分组
        
        Args:
            group_data: 分组创建数据
            
        Returns:
            创建的执行器分组
            
        Raises:
            ConflictException: 分组已存在
        """
        # 检查分组名称是否已存在
        existing_group = await self.db.scalar(
            select(ExecutorGroup).where(ExecutorGroup.group_name == group_data.group_name)
        )
        
        if existing_group:
            raise ConflictException(f"执行器分组已存在: {group_data.group_name}")
        
        # 创建新分组
        group = ExecutorGroup(
            group_name=group_data.group_name,
            display_name=group_data.group_display_name,
            description=group_data.group_description,
            group_type=group_data.group_type,
            load_balance_strategy=group_data.load_balance_strategy,
            max_concurrent_tasks=group_data.max_concurrent_tasks,
            is_active=group_data.is_active,
            resource_profile=group_data.config or {},
            task_types=group_data.tags or [],
            created_by=1  # 临时设置为1，实际应该从认证上下文获取
        )
        
        self.db.add(group)
        await self.db.commit()
        await self.db.refresh(group)
        
        logger.info(f"执行器分组已创建: {group.group_name} ({group.id})")
        
        return group
    
    async def get_executor_group(self, group_id: str) -> ExecutorGroup:
        """
        获取执行器分组详情
        
        Args:
            group_id: 分组ID
            
        Returns:
            执行器分组
            
        Raises:
            NotFoundException: 分组不存在
        """
        group = await self.db.scalar(
            select(ExecutorGroup)
            .where(ExecutorGroup.group_id == group_id)
            .options(selectinload(ExecutorGroup.executors))
        )
        
        if not group:
            raise NotFoundError(f"执行器分组不存在: {group_id}")
        
        return group
    
    async def update_executor_group(
        self,
        group_id: str,
        group_data: ExecutorGroupUpdate
    ) -> ExecutorGroup:
        """
        更新执行器分组
        
        Args:
            group_id: 分组ID
            group_data: 更新数据
            
        Returns:
            更新后的执行器分组
            
        Raises:
            NotFoundException: 分组不存在
        """
        group = await self.get_executor_group(group_id)
        
        # 更新字段
        update_data = group_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(group, field):
                setattr(group, field, value)
        
        group.updated_at = datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(group)
        
        logger.info(f"执行器分组已更新: {group.group_name} ({group.group_id})")
        
        return group
    
    async def delete_executor_group(self, group_id: str) -> bool:
        """
        删除执行器分组
        
        Args:
            group_id: 分组ID
            
        Returns:
            是否成功删除
            
        Raises:
            NotFoundException: 分组不存在
            ConflictException: 分组下还有节点
        """
        group = await self.get_executor_group(group_id)
        
        # 检查是否还有节点
        if group.executors:
            raise ConflictException(f"无法删除分组，还有 {len(group.executors)} 个节点")
        
        # 删除分组
        await self.db.delete(group)
        await self.db.commit()
        
        logger.info(f"执行器分组已删除: {group.group_name} ({group.group_id})")
        
        return True
    
    # ==================== 执行器节点管理 ====================
    
    async def get_executor_nodes(
        self,
        params: ExecutorNodeQueryParams
    ) -> tuple[List[ExecutorNode], int]:
        """
        获取执行器节点列表
        
        Args:
            params: 查询参数
            
        Returns:
            执行器节点列表和总数
        """
        query = select(ExecutorNode)
        
        # 应用过滤条件
        if params.group_id:
            query = query.where(ExecutorNode.group_id == params.group_id)
        if params.node_name:
            query = query.where(ExecutorNode.node_name.ilike(f"%{params.node_name}%"))
        # 注意：ExecutorNodeQueryParams 没有 host 属性，这里注释掉
        # if params.host:
        #     query = query.where(ExecutorNode.host_ip.ilike(f"%{params.host}%"))
        if params.status:
            query = query.where(ExecutorNode.status == params.status)
        
        # 获取总数
        count_query = select(func.count()).select_from(query.subquery())
        total = await self.db.scalar(count_query)
        
        # 应用排序
        if params.sort_by:
            if hasattr(ExecutorNode, params.sort_by):
                order_column = getattr(ExecutorNode, params.sort_by)
                if params.sort_order == "desc":
                    query = query.order_by(order_column.desc())
                else:
                    query = query.order_by(order_column.asc())
        else:
            query = query.order_by(ExecutorNode.created_at.desc())
        
        # 应用分页
        if params.page and params.size:
            offset = (params.page - 1) * params.size
            query = query.offset(offset).limit(params.size)
        
        # 加载关联的分组信息
        query = query.options(selectinload(ExecutorNode.group))
        
        result = await self.db.execute(query)
        nodes = result.scalars().all()
        
        return list(nodes), total or 0
    
    async def register_executor_node(
        self,
        node_data: ExecutorNodeCreate
    ) -> ExecutorNode:
        """
        注册执行器节点
        
        Args:
            node_data: 节点注册数据
            
        Returns:
            注册的执行器节点
            
        Raises:
            ConflictException: 节点已存在
            NotFoundException: 分组不存在
        """
        # 检查分组是否存在
        if node_data.group_id:
            group = await self.db.scalar(
                select(ExecutorGroup).where(ExecutorGroup.id == node_data.group_id)
            )
            if not group:
                raise NotFoundError(f"执行器分组不存在: {node_data.group_id}")
        
        # 检查节点是否已存在
        existing_node = await self.db.scalar(
            select(ExecutorNode).where(
                and_(
                    ExecutorNode.node_name == node_data.node_name,
                    ExecutorNode.host_ip == node_data.host_ip,
                    ExecutorNode.port == node_data.port
                )
            )
        )
        
        if existing_node:
            raise ConflictError(f"执行器节点已存在: {node_data.node_name}")
        
        # 创建新节点
        node = ExecutorNode(
            node_id=node_data.node_id or str(uuid4()),
            group_id=node_data.group_id,
            node_name=node_data.node_name,
            host_ip=node_data.host_ip,
            port=node_data.port,
            status=node_data.status,
            version=node_data.version,
            capabilities=node_data.capabilities or {},
            resource_capacity=node_data.resource_info or {},
            max_concurrent_tasks=node_data.max_concurrent_tasks,
            current_load=node_data.current_load,
            tags=node_data.tags or [],
            node_metadata=node_data.node_metadata or {},
            last_heartbeat=datetime.utcnow()
        )
        
        self.db.add(node)
        await self.db.commit()
        await self.db.refresh(node)
        
        logger.info(f"执行器节点已注册: {node.node_name} ({node.node_id})")
        
        return node
    
    async def get_executor_node(self, node_id: str) -> ExecutorNode:
        """
        获取执行器节点详情
        
        Args:
            node_id: 节点ID
            
        Returns:
            执行器节点
            
        Raises:
            NotFoundException: 节点不存在
        """
        node = await self.db.scalar(
            select(ExecutorNode)
            .where(ExecutorNode.node_id == node_id)
            .options(selectinload(ExecutorNode.group))
        )
        
        if not node:
            raise NotFoundError(f"执行器节点不存在: {node_id}")
        
        return node
    
    async def update_executor_node(
        self,
        node_id: str,
        node_data: ExecutorNodeUpdate
    ) -> ExecutorNode:
        """
        更新执行器节点
        
        Args:
            node_id: 节点ID
            node_data: 更新数据
            
        Returns:
            更新后的执行器节点
            
        Raises:
            NotFoundException: 节点不存在
        """
        node = await self.get_executor_node(node_id)
        
        # 更新字段
        update_data = node_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(node, field):
                setattr(node, field, value)
        
        node.updated_at = datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(node)
        
        logger.info(f"执行器节点已更新: {node.node_name} ({node.node_id})")
        
        return node
    
    async def unregister_executor_node(self, node_id: str) -> bool:
        """
        注销执行器节点
        
        Args:
            node_id: 节点ID
            
        Returns:
            是否成功注销
            
        Raises:
            NotFoundException: 节点不存在
        """
        node = await self.get_executor_node(node_id)
        
        # 删除节点
        await self.db.delete(node)
        await self.db.commit()
        
        logger.info(f"执行器节点已注销: {node.node_name} ({node.node_id})")
        
        return True
    
    async def update_heartbeat(
        self,
        node_id: str,
        heartbeat_data: ExecutorNodeHeartbeat
    ) -> ExecutorNode:
        """
        更新执行器节点心跳
        
        Args:
            node_id: 节点ID
            heartbeat_data: 心跳数据
            
        Returns:
            更新后的执行器节点
            
        Raises:
            NotFoundException: 节点不存在
        """
        node = await self.get_executor_node(node_id)
        
        # 更新心跳信息
        node.last_heartbeat = datetime.utcnow()
        
        # 更新资源使用情况
        if heartbeat_data.resource_usage:
            node.resource_usage = heartbeat_data.resource_usage
        
        # 更新当前负载
        if heartbeat_data.current_load is not None:
            node.current_load = heartbeat_data.current_load
        
        # 更新版本信息
        if heartbeat_data.version:
            node.version = heartbeat_data.version
        
        # 更新能力配置
        if heartbeat_data.capabilities:
            node.capabilities = heartbeat_data.capabilities
        
        # 更新元数据
        if heartbeat_data.node_metadata:
            node.node_metadata = heartbeat_data.node_metadata
        
        # 如果节点状态不是ONLINE，更新为ONLINE
        if node.status != ExecutorStatus.ONLINE:
            node.status = ExecutorStatus.ONLINE
        
        await self.db.commit()
        await self.db.refresh(node)
        
        return node
    
    async def update_node_status(
        self,
        node_id: str,
        status_data: ExecutorNodeStatusUpdate
    ) -> ExecutorNode:
        """
        更新执行器节点状态
        
        Args:
            node_id: 节点ID
            status_data: 状态更新数据
            
        Returns:
            更新后的执行器节点
            
        Raises:
            NotFoundException: 节点不存在
        """
        node = await self.get_executor_node(node_id)
        
        old_status = node.status
        node.status = status_data.status
        
        if status_data.error_message:
            node.error_message = status_data.error_message
        
        node.updated_at = datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(node)
        
        logger.info(
            f"执行器节点状态已更新: {node.node_name} ({node.node_id}) "
            f"{old_status} -> {node.status}"
        )
        
        return node
    
    async def get_node_status(self, node_id: str) -> ExecutorNodeStatus:
        """
        获取执行器节点状态
        
        Args:
            node_id: 节点ID
            
        Returns:
            执行器节点状态
            
        Raises:
            NotFoundException: 节点不存在
        """
        node = await self.get_executor_node(node_id)
        
        return ExecutorNodeStatus(
            node_id=node.node_id,
            node_name=node.node_name,
            status=node.status,
            cpu_usage=node.cpu_usage,
            memory_usage=node.memory_usage,
            disk_usage=node.disk_usage,
            active_tasks=node.active_tasks,
            pending_tasks=node.pending_tasks,
            last_heartbeat=node.last_heartbeat,
            error_message=node.error_message
        )
    
    async def cleanup_offline_nodes(self) -> int:
        """
        清理离线节点
        
        Returns:
            清理的节点数量
        """
        # 查找超时的节点
        timeout_threshold = datetime.utcnow() - timedelta(seconds=self.heartbeat_timeout * 3)
        
        result = await self.db.execute(
            select(ExecutorNode).where(
                and_(
                    ExecutorNode.last_heartbeat < timeout_threshold,
                    ExecutorNode.status != ExecutorStatus.OFFLINE
                )
            )
        )
        timeout_nodes = result.scalars().all()
        
        cleaned_count = 0
        
        for node in timeout_nodes:
            node.status = ExecutorStatus.OFFLINE
            node.updated_at = datetime.utcnow()
            cleaned_count += 1
            
            logger.warning(f"执行器节点已离线: {node.node_name} ({node.node_id})")
        
        await self.db.commit()
        
        return cleaned_count
    
    async def get_group_nodes(self, group_id: str) -> List[ExecutorNode]:
        """
        获取分组下的所有执行器节点
        
        Args:
            group_id: 分组ID
            
        Returns:
            执行器节点列表
            
        Raises:
            NotFoundException: 分组不存在
        """
        # 检查分组是否存在
        group = await self.db.scalar(
            select(ExecutorGroup).where(ExecutorGroup.group_id == group_id)
        )
        
        if not group:
            raise NotFoundError(f"执行器分组不存在: {group_id}")
        
        # 获取分组下的所有节点
        result = await self.db.execute(
            select(ExecutorNode)
            .where(ExecutorNode.group_id == group_id)
            .order_by(ExecutorNode.created_at.desc())
        )
        nodes = result.scalars().all()
        
        return list(nodes)

    async def fetch_pending_tasks(self, node_id: str, limit: int = 1) -> List[TaskInstance]:
        """
        获取分配给指定执行器节点的待执行任务
        
        Args:
            node_id: 执行器节点ID
            limit: 获取数量
            
        Returns:
            任务列表 (TaskInstance)
        """
        # 1. 获取节点信息，包括其所属的分组名称
        node = await self.get_executor_node(node_id)
        if not node or not node.group:
            logger.warning(f"节点 {node_id} 不存在或未分配分组")
            return []
            
        group_name = node.group.group_name
        
        # 2. 查找待执行的任务
        # 条件：
        # - 状态为 PENDING
        # - 执行器分组匹配 (executor_group == group_name)
        # - 未被分配给其他节点 (assigned_executor_node 为空 或 等于当前节点ID)
        
        stmt = select(TaskInstance).options(
            selectinload(TaskInstance.task_definition)
        ).where(
            and_(
                TaskInstance.status == TaskStatus.PENDING,
                TaskInstance.executor_group == group_name,
                or_(
                    TaskInstance.assigned_executor_node.is_(None),
                    TaskInstance.assigned_executor_node == node_id
                )
            )
        ).order_by(
            TaskInstance.priority.desc(),
            TaskInstance.scheduled_time.asc()
        ).limit(limit)
        
        result = await self.db.execute(stmt)
        tasks = result.scalars().all()
        
        # 3. 锁定这些任务（简单乐观锁：更新 assigned_executor_node）
        # 注意：这里可能存在并发竞争，更严谨的做法是使用 SELECT ... FOR UPDATE 或 atomic update
        # 但考虑到 SQLAlchemy Async 的限制和简单性，我们这里直接返回，
        # 在 execute_single_task 中会将状态改为 RUNNING，那时会再次确认
        
        return list(tasks)

    async def update_task_status(self, task_instance_id: int, status: str, result: Dict[str, Any] = None):
        """
        更新任务状态
        """
        stmt = select(TaskInstance).where(TaskInstance.id == task_instance_id)
        task = await self.db.scalar(stmt)
        
        if not task:
            logger.warning(f"任务实例 {task_instance_id} 不存在")
            return
            
        # 更新状态
        old_status = task.status
        # 将字符串状态转换为枚举
        try:
            new_status = TaskStatus(status)
        except ValueError:
            logger.warning(f"无效的任务状态: {status}")
            return

        task.status = new_status
        
        now = datetime.utcnow()
        
        # 根据状态更新时间字段
        if new_status == TaskStatus.RUNNING:
            if not task.actual_start_time:
                task.actual_start_time = now
        elif new_status in [TaskStatus.SUCCESS, TaskStatus.FAILED, TaskStatus.CANCELLED, TaskStatus.TIMEOUT]:
            task.actual_end_time = now
            if task.actual_start_time:
                task.duration_seconds = int((now - task.actual_start_time).total_seconds())
        
        # 更新结果数据
        if result:
            # 序列化 datetime 对象
            serialized_result = {}
            for k, v in result.items():
                if isinstance(v, datetime):
                    serialized_result[k] = v.isoformat()
                else:
                    serialized_result[k] = v
            result = serialized_result

            if task.result_data:
                # 合并结果而不是覆盖，如果有必要
                # 这里简单起见直接更新/覆盖
                current_result = dict(task.result_data)
                current_result.update(result)
                task.result_data = current_result
            else:
                task.result_data = result
                
            # 如果有错误信息
            if 'error' in result:
                task.error_message = str(result['error'])
        
        await self.db.commit()
        await self.db.refresh(task)
        
        logger.info(f"任务 {task_instance_id} 状态更新: {old_status} -> {new_status}")


async def get_executor_cluster_service(db: AsyncSession = None) -> ExecutorClusterService:
    """
    获取执行器集群管理服务实例
    
    Args:
        db: 数据库会话
        
    Returns:
        执行器集群管理服务实例
    """
    if db is None:
        async for session in get_db():
            db = session
            break
    
    return ExecutorClusterService(db)