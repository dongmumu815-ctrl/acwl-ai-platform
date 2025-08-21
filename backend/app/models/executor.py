#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
执行器节点模型
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, Enum, Boolean, Float, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.core.database import Base


class ExecutorStatus(enum.Enum):
    """执行器状态枚举"""
    ONLINE = "online"
    OFFLINE = "offline"
    BUSY = "busy"
    MAINTENANCE = "maintenance"
    ERROR = "error"


class GroupType(enum.Enum):
    """执行器分组类型枚举"""
    DEFAULT = "DEFAULT"
    COMPUTE = "COMPUTE"
    GPU = "GPU"
    MEMORY_INTENSIVE = "MEMORY_INTENSIVE"
    CPU_INTENSIVE = "CPU_INTENSIVE"
    IO_INTENSIVE = "IO_INTENSIVE"
    CUSTOM = "custom"


class LoadBalanceStrategy(enum.Enum):
    """负载均衡策略枚举"""
    ROUND_ROBIN = "ROUND_ROBIN"
    LEAST_CONNECTIONS = "LEAST_CONNECTIONS"
    RESOURCE_BASED = "RESOURCE_BASED"
    RANDOM = "RANDOM"


class ExecutorGroup(Base):
    """执行器分组模型"""
    __tablename__ = "acwl_executor_groups"

    id = Column(Integer, primary_key=True, index=True, comment="分组ID，自增主键")
    group_name = Column(String(50), unique=True, nullable=False, comment="分组名称")
    display_name = Column(String(100), comment="分组显示名称")
    description = Column(Text, comment="分组描述")
    group_type = Column(Enum(GroupType), default=GroupType.DEFAULT, nullable=False, comment="分组类型")
    resource_profile = Column(JSON, comment="资源配置文件")
    max_concurrent_tasks = Column(Integer, default=10, comment="最大并发任务数")
    task_types = Column(JSON, comment="支持的任务类型列表")
    load_balance_strategy = Column(Enum(LoadBalanceStrategy), default=LoadBalanceStrategy.ROUND_ROBIN, comment="负载均衡策略")
    is_active = Column(Boolean, default=True, comment="是否激活")
    created_by = Column(Integer, ForeignKey("acwl_users.id"), comment="创建者ID")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")

    # 关系
    executors = relationship("ExecutorNode", back_populates="group")
    creator = relationship("User", back_populates="created_executor_groups")

    def __repr__(self):
        return f"<ExecutorGroup(group_name='{self.group_name}', type='{self.group_type}')>"


class ExecutorNode(Base):
    """执行器节点模型"""
    __tablename__ = "acwl_executor_nodes"

    id = Column(Integer, primary_key=True, index=True, comment="执行器ID，自增主键")
    node_id = Column(String(100), unique=True, nullable=False, index=True, comment="执行器节点唯一标识")
    node_name = Column(String(100), nullable=False, comment="节点名称")
    group_id = Column(Integer, ForeignKey("acwl_executor_groups.id"), nullable=False, comment="所属分组ID")
    host_ip = Column(String(45), nullable=False, comment="主机IP地址")
    port = Column(Integer, nullable=False, comment="服务端口")
    status = Column(Enum(ExecutorStatus), default=ExecutorStatus.OFFLINE, nullable=False, comment="节点状态")
    version = Column(String(50), comment="执行器版本")
    supported_task_types = Column(JSON, comment="支持的任务类型")
    resource_capacity = Column(JSON, comment="资源容量")
    resource_usage = Column(JSON, comment="当前资源使用情况")
    max_concurrent_tasks = Column(Integer, default=5, comment="最大并发任务数")
    current_load = Column(Integer, default=0, comment="当前负载（正在执行的任务数）")
    total_tasks_executed = Column(Integer, default=0, comment="总执行任务数")
    last_heartbeat = Column(DateTime, comment="最后心跳时间")
    registration_time = Column(DateTime, default=datetime.utcnow, comment="注册时间")
    tags = Column(JSON, comment="标签")
    node_metadata = Column(JSON, comment="元数据")
    capabilities = Column(JSON, comment="节点能力配置")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")

    # 关系
    group = relationship("ExecutorGroup", back_populates="executors")
    task_instances = relationship(
        "TaskInstance",
        foreign_keys="[TaskInstance.assigned_executor_node]",
        primaryjoin="ExecutorNode.node_id == foreign(TaskInstance.assigned_executor_node)",
        back_populates="assigned_executor"
    )

    def __repr__(self):
        return f"<ExecutorNode(node_id='{self.node_id}', status='{self.status}', load={self.current_load})>"

    @property
    def utilization_rate(self) -> float:
        """计算利用率"""
        if self.max_concurrent_tasks == 0:
            return 0.0
        return (self.current_load / self.max_concurrent_tasks) * 100

    @property
    def is_available(self) -> bool:
        """检查节点是否可用"""
        return (
            self.status == ExecutorStatus.ONLINE and
            self.current_load < self.max_concurrent_tasks
        )