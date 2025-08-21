#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工作流执行引擎

负责工作流实例的执行、节点调度、状态管理等核心功能
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload

from app.models.workflow import (
    Workflow, WorkflowConnection, WorkflowInstance, 
    WorkflowNodeInstance, InstanceStatus, NodeType, ConnectionType
)
from app.models.unified_node import UnifiedNode, UnifiedNodeType
from app.models.task import TaskDefinition
from app.core.database import get_db

logger = logging.getLogger(__name__)


class WorkflowEngine:
    """
    工作流执行引擎
    
    负责工作流实例的执行调度和状态管理
    """
    
    def __init__(self):
        self.running_instances = {}  # 正在运行的实例
        self.is_running = False
    
    async def start_instance(self, instance_id: int, db: AsyncSession) -> bool:
        """
        启动工作流实例执行
        
        Args:
            instance_id: 工作流实例ID
            db: 数据库会话
            
        Returns:
            bool: 启动是否成功
        """
        try:
            # 获取工作流实例
            result = await db.execute(
                select(WorkflowInstance)
                .options(selectinload(WorkflowInstance.workflow))
                .filter(WorkflowInstance.id == instance_id)
            )
            instance = result.scalar_one_or_none()
            
            if not instance:
                logger.error(f"工作流实例 {instance_id} 不存在")
                return False
            
            if instance.status != InstanceStatus.PENDING:
                logger.warning(f"工作流实例 {instance_id} 状态不是 PENDING，当前状态: {instance.status}")
                return False
            
            # 更新实例状态为运行中
            await db.execute(
                update(WorkflowInstance)
                .where(WorkflowInstance.id == instance_id)
                .values(
                    status=InstanceStatus.RUNNING,
                    started_at=datetime.now(),
                    updated_at=datetime.now()
                )
            )
            await db.commit()
            
            # 创建工作流节点实例
            await self._create_node_instances(instance, db)
            
            # 启动执行
            await self._execute_workflow(instance, db)
            
            logger.info(f"工作流实例 {instance_id} 启动成功")
            return True
            
        except Exception as e:
            logger.error(f"启动工作流实例 {instance_id} 失败: {e}")
            # 更新实例状态为失败
            try:
                await db.execute(
                    update(WorkflowInstance)
                    .where(WorkflowInstance.id == instance_id)
                    .values(
                        status=InstanceStatus.FAILED,
                        error_message=str(e),
                        finished_at=datetime.now(),
                        updated_at=datetime.now()
                    )
                )
                await db.commit()
            except Exception as commit_error:
                logger.error(f"更新实例状态失败: {commit_error}")
            return False
    
    async def _create_node_instances(self, workflow_instance: WorkflowInstance, db: AsyncSession):
        """
        为工作流实例创建节点实例
        
        Args:
            workflow_instance: 工作流实例
            db: 数据库会话
        """
        # 获取工作流的所有节点（从统一节点表）
        from app.models.unified_node import UnifiedNode
        
        result = await db.execute(
            select(UnifiedNode)
            .filter(UnifiedNode.workflow_id == workflow_instance.workflow_id)
            .order_by(UnifiedNode.id)
        )
        nodes = result.scalars().all()
        
        # 为每个节点创建实例
        for node in nodes:
            node_instance = WorkflowNodeInstance(
                workflow_instance_id=workflow_instance.id,
                node_id=node.id,
                node_name=node.name,
                node_type=node.node_type.value,  # 从枚举值获取字符串
                status=InstanceStatus.PENDING,
                input_data=node.config or {},
                scheduled_time=datetime.now(),
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            db.add(node_instance)
        
        await db.commit()
        logger.info(f"为工作流实例 {workflow_instance.id} 创建了 {len(nodes)} 个节点实例")
    
    async def _execute_workflow(self, workflow_instance: WorkflowInstance, db: AsyncSession):
        """
        执行工作流
        
        Args:
            workflow_instance: 工作流实例
            db: 数据库会话
        """
        try:
            # 找到开始节点
            start_nodes = await self._find_start_nodes(workflow_instance.workflow_id, db)
            
            if not start_nodes:
                raise Exception("未找到开始节点")
            
            # 执行开始节点
            for start_node in start_nodes:
                await self._execute_node(workflow_instance.id, start_node.id, db)
            
            # 检查工作流是否完成
            await self._check_workflow_completion(workflow_instance.id, db)
            
        except Exception as e:
            logger.error(f"执行工作流实例 {workflow_instance.id} 失败: {e}")
            # 更新实例状态为失败
            await db.execute(
                update(WorkflowInstance)
                .where(WorkflowInstance.id == workflow_instance.id)
                .values(
                    status=InstanceStatus.FAILED,
                    error_message=str(e),
                    finished_at=datetime.now(),
                    updated_at=datetime.now()
                )
            )
            await db.commit()
    
    async def _find_start_nodes(self, workflow_id: int, db: AsyncSession) -> List[UnifiedNode]:
        """
        查找工作流的开始节点
        
        Args:
            workflow_id: 工作流ID
            db: 数据库会话
            
        Returns:
            List[UnifiedNode]: 开始节点列表
        """
        result = await db.execute(
            select(UnifiedNode)
            .filter(
                UnifiedNode.workflow_id == workflow_id,
                UnifiedNode.node_type == UnifiedNodeType.START
            )
        )
        return result.scalars().all()
    
    async def _execute_node(self, workflow_instance_id: int, node_id: int, db: AsyncSession):
        """
        执行工作流节点
        
        Args:
            workflow_instance_id: 工作流实例ID
            node_id: 节点ID
            db: 数据库会话
        """
        try:
            # 获取节点实例
            result = await db.execute(
                select(WorkflowNodeInstance)
                .filter(
                    WorkflowNodeInstance.workflow_instance_id == workflow_instance_id,
                    WorkflowNodeInstance.node_id == node_id
                )
            )
            node_instance = result.scalar_one_or_none()
            
            if not node_instance:
                logger.error(f"节点实例不存在: workflow_instance_id={workflow_instance_id}, node_id={node_id}")
                return
            
            # 更新节点状态为运行中
            await db.execute(
                update(WorkflowNodeInstance)
                .where(WorkflowNodeInstance.id == node_instance.id)
                .values(
                    status=InstanceStatus.RUNNING,
                    started_at=datetime.now(),
                    updated_at=datetime.now()
                )
            )
            await db.commit()
            
            # 根据节点类型执行不同的逻辑
            if node_instance.node_type == NodeType.START:
                # 开始节点直接标记为完成
                await self._complete_node(node_instance.id, {"message": "工作流开始"}, db)
            elif node_instance.node_type == NodeType.END:
                # 结束节点直接标记为完成
                await self._complete_node(node_instance.id, {"message": "工作流结束"}, db)
            elif node_instance.node_type == NodeType.TASK:
                # 任务节点需要实际执行
                await self._execute_task_node(node_instance, db)
            else:
                # 其他类型节点暂时标记为完成
                await self._complete_node(node_instance.id, {"message": f"节点类型 {node_instance.node_type} 执行完成"}, db)
            
            # 执行后续节点
            await self._execute_next_nodes(workflow_instance_id, node_id, db)
            
        except Exception as e:
            logger.error(f"执行节点失败: workflow_instance_id={workflow_instance_id}, node_id={node_id}, error={e}")
            # 标记节点为失败
            await self._fail_node(workflow_instance_id, node_id, str(e), db)
    
    async def _execute_task_node(self, node_instance: WorkflowNodeInstance, db: AsyncSession):
        """
        执行任务节点
        
        Args:
            node_instance: 节点实例
            db: 数据库会话
        """
        # 这里应该根据任务类型执行具体的任务
        # 目前简化处理，直接标记为完成
        output_data = {
            "message": f"任务节点 {node_instance.node_name} 执行完成",
            "execution_time": datetime.now().isoformat(),
            "node_type": node_instance.node_type.value if node_instance.node_type else "unknown"
        }
        
        await self._complete_node(node_instance.id, output_data, db)
    
    async def _complete_node(self, node_instance_id: int, output_data: Dict[str, Any], db: AsyncSession):
        """
        标记节点为完成
        
        Args:
            node_instance_id: 节点实例ID
            output_data: 输出数据
            db: 数据库会话
        """
        await db.execute(
            update(WorkflowNodeInstance)
            .where(WorkflowNodeInstance.id == node_instance_id)
            .values(
                status=InstanceStatus.COMPLETED,
                output_data=output_data,
                finished_at=datetime.now(),
                updated_at=datetime.now()
            )
        )
        await db.commit()
        logger.info(f"节点实例 {node_instance_id} 执行完成")
    
    async def _fail_node(self, workflow_instance_id: int, node_id: int, error_message: str, db: AsyncSession):
        """
        标记节点为失败
        
        Args:
            workflow_instance_id: 工作流实例ID
            node_id: 节点ID
            error_message: 错误信息
            db: 数据库会话
        """
        result = await db.execute(
            select(WorkflowNodeInstance)
            .filter(
                WorkflowNodeInstance.workflow_instance_id == workflow_instance_id,
                WorkflowNodeInstance.node_id == node_id
            )
        )
        node_instance = result.scalar_one_or_none()
        
        if node_instance:
            await db.execute(
                update(WorkflowNodeInstance)
                .where(WorkflowNodeInstance.id == node_instance.id)
                .values(
                    status=InstanceStatus.FAILED,
                    error_message=error_message,
                    finished_at=datetime.now(),
                    updated_at=datetime.now()
                )
            )
            await db.commit()
            logger.error(f"节点实例 {node_instance.id} 执行失败: {error_message}")
    
    async def _execute_next_nodes(self, workflow_instance_id: int, current_node_id: int, db: AsyncSession):
        """
        执行当前节点的后续节点
        
        Args:
            workflow_instance_id: 工作流实例ID
            current_node_id: 当前节点ID
            db: 数据库会话
        """
        # 获取当前节点的所有输出连接
        result = await db.execute(
            select(WorkflowConnection)
            .filter(WorkflowConnection.source_node_id == current_node_id)
        )
        connections = result.scalars().all()
        
        # 执行所有后续节点
        for connection in connections:
            await self._execute_node(workflow_instance_id, connection.target_node_id, db)
    
    async def _check_workflow_completion(self, workflow_instance_id: int, db: AsyncSession):
        """
        检查工作流是否完成
        
        Args:
            workflow_instance_id: 工作流实例ID
            db: 数据库会话
        """
        # 获取所有节点实例的状态
        result = await db.execute(
            select(WorkflowNodeInstance)
            .filter(WorkflowNodeInstance.workflow_instance_id == workflow_instance_id)
        )
        node_instances = result.scalars().all()
        
        if not node_instances:
            return
        
        # 检查是否所有节点都已完成或失败
        completed_count = 0
        failed_count = 0
        
        for node_instance in node_instances:
            if node_instance.status == InstanceStatus.COMPLETED:
                completed_count += 1
            elif node_instance.status == InstanceStatus.FAILED:
                failed_count += 1
        
        total_count = len(node_instances)
        
        # 判断工作流最终状态
        if failed_count > 0:
            # 有节点失败，工作流失败
            final_status = InstanceStatus.FAILED
            error_message = f"工作流执行失败，{failed_count} 个节点失败"
        elif completed_count == total_count:
            # 所有节点完成，工作流成功
            final_status = InstanceStatus.COMPLETED
            error_message = None
        else:
            # 还有节点在执行中，不更新状态
            return
        
        # 更新工作流实例状态
        await db.execute(
            update(WorkflowInstance)
            .where(WorkflowInstance.id == workflow_instance_id)
            .values(
                status=final_status,
                error_message=error_message,
                finished_at=datetime.now(),
                updated_at=datetime.now()
            )
        )
        await db.commit()
        
        logger.info(f"工作流实例 {workflow_instance_id} 执行完成，最终状态: {final_status}")


# 全局工作流引擎实例
workflow_engine = WorkflowEngine()