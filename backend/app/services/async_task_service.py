#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
异步任务服务
用于处理长时间运行的任务，如内容审读等
"""

import asyncio
import uuid
from typing import Dict, Any, Optional, Callable
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass
from sqlalchemy.orm import Session
from app.core.logger import logger


class TaskStatus(str, Enum):
    """任务状态枚举"""
    PENDING = "pending"      # 等待执行
    RUNNING = "running"      # 正在执行
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"        # 执行失败
    CANCELLED = "cancelled"  # 已取消


@dataclass
class TaskResult:
    """任务结果数据类"""
    task_id: str
    status: TaskStatus
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    progress: float = 0.0
    created_at: datetime = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


class AsyncTaskService:
    """异步任务服务类"""
    
    def __init__(self):
        self._tasks: Dict[str, TaskResult] = {}
        self._running_tasks: Dict[str, asyncio.Task] = {}
        self._cleanup_interval = 3600  # 1小时清理一次过期任务
        self._task_ttl = 86400  # 任务结果保留24小时
        self._cleanup_task = None
        
    async def start(self):
        """启动异步任务服务"""
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._cleanup_expired_tasks())
            logger.info("异步任务服务已启动")
    
    async def stop(self):
        """停止异步任务服务"""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None
        
        # 取消所有运行中的任务
        for task_id, task in self._running_tasks.items():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                self._tasks[task_id].status = TaskStatus.CANCELLED
        
        self._running_tasks.clear()
        logger.info("异步任务服务已停止")
    
    def create_task(
        self,
        task_func: Callable,
        task_args: tuple = (),
        task_kwargs: dict = None,
        task_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        创建异步任务
        
        Args:
            task_func: 任务函数
            task_args: 任务参数
            task_kwargs: 任务关键字参数
            task_id: 任务ID（可选，不提供则自动生成）
            metadata: 任务元数据
            
        Returns:
            任务ID
        """
        if task_kwargs is None:
            task_kwargs = {}
        
        if task_id is None:
            task_id = str(uuid.uuid4())
        
        # 创建任务结果对象
        task_result = TaskResult(
            task_id=task_id,
            status=TaskStatus.PENDING,
            metadata=metadata or {}
        )
        
        self._tasks[task_id] = task_result
        
        # 创建并启动异步任务
        async_task = asyncio.create_task(
            self._execute_task(task_id, task_func, task_args, task_kwargs)
        )
        self._running_tasks[task_id] = async_task
        
        logger.info(f"创建异步任务: {task_id}")
        return task_id
    
    async def _execute_task(
        self,
        task_id: str,
        task_func: Callable,
        task_args: tuple,
        task_kwargs: dict
    ):
        """
        执行异步任务
        
        Args:
            task_id: 任务ID
            task_func: 任务函数
            task_args: 任务参数
            task_kwargs: 任务关键字参数
        """
        task_result = self._tasks[task_id]
        
        try:
            # 更新任务状态为运行中
            task_result.status = TaskStatus.RUNNING
            task_result.started_at = datetime.now()
            
            logger.info(f"开始执行任务: {task_id}")
            
            # 执行任务函数
            if asyncio.iscoroutinefunction(task_func):
                result = await task_func(*task_args, **task_kwargs)
            else:
                result = task_func(*task_args, **task_kwargs)
            
            # 更新任务状态为已完成
            task_result.status = TaskStatus.COMPLETED
            task_result.result = result
            task_result.progress = 1.0
            task_result.completed_at = datetime.now()
            
            logger.info(f"任务执行完成: {task_id}")
            
        except asyncio.CancelledError:
            task_result.status = TaskStatus.CANCELLED
            task_result.completed_at = datetime.now()
            logger.info(f"任务被取消: {task_id}")
            raise
            
        except Exception as e:
            task_result.status = TaskStatus.FAILED
            task_result.error = str(e)
            task_result.completed_at = datetime.now()
            logger.error(f"任务执行失败: {task_id}, 错误: {str(e)}")
            
        finally:
            # 从运行中任务列表移除
            if task_id in self._running_tasks:
                del self._running_tasks[task_id]
    
    def get_task_status(self, task_id: str) -> Optional[TaskResult]:
        """
        获取任务状态
        
        Args:
            task_id: 任务ID
            
        Returns:
            任务结果对象，如果任务不存在则返回None
        """
        return self._tasks.get(task_id)
    
    def cancel_task(self, task_id: str) -> bool:
        """
        取消任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            是否成功取消任务
        """
        if task_id in self._running_tasks:
            self._running_tasks[task_id].cancel()
            return True
        return False
    
    def get_all_tasks(self) -> Dict[str, TaskResult]:
        """
        获取所有任务状态
        
        Returns:
            所有任务的状态字典
        """
        return self._tasks.copy()
    
    async def _cleanup_expired_tasks(self):
        """
        清理过期任务
        """
        while True:
            try:
                await asyncio.sleep(self._cleanup_interval)
                
                current_time = datetime.now()
                expired_task_ids = []
                
                for task_id, task_result in self._tasks.items():
                    # 检查任务是否过期
                    if (task_result.completed_at and 
                        current_time - task_result.completed_at > timedelta(seconds=self._task_ttl)):
                        expired_task_ids.append(task_id)
                
                # 删除过期任务
                for task_id in expired_task_ids:
                    del self._tasks[task_id]
                    logger.info(f"清理过期任务: {task_id}")
                
                if expired_task_ids:
                    logger.info(f"清理了 {len(expired_task_ids)} 个过期任务")
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"清理过期任务时发生错误: {str(e)}")


# 全局异步任务服务实例
async_task_service = AsyncTaskService()


async def create_review_task(
    db: Session,
    content: str,
    instruction_set_id: int,
    model_config_id: int,
    user_id: int
) -> str:
    """
    创建内容审读任务
    
    Args:
        db: 数据库会话
        content: 待审读内容
        instruction_set_id: 指令集ID
        model_config_id: 模型配置ID
        user_id: 用户ID
        
    Returns:
        任务ID
    """
    from app.services.content_review_service import ContentReviewService
    
    async def review_task():
        """审读任务函数"""
        review_service = ContentReviewService(db)
        return await review_service.review_content(
            content=content,
            instruction_set_id=instruction_set_id,
            model_config_id=model_config_id
        )
    
    task_id = async_task_service.create_task(
        task_func=review_task,
        metadata={
            "task_type": "content_review",
            "user_id": user_id,
            "instruction_set_id": instruction_set_id,
            "model_config_id": model_config_id,
            "content_length": len(content)
        }
    )
    
    return task_id