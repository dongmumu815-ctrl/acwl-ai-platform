#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调度器节点模型
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, Enum, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.core.database import Base


class SchedulerRole(enum.Enum):
    """调度器角色枚举"""
    LEADER = "leader"
    FOLLOWER = "follower"
    CANDIDATE = "candidate"


class SchedulerStatus(enum.Enum):
    """调度器状态枚举"""
    ACTIVE = "active"
    STANDBY = "standby"
    OFFLINE = "offline"
    ERROR = "error"
    MAINTENANCE = "maintenance"
    STARTING = "starting"


class SchedulerNode(Base):
    """调度器节点模型"""
    __tablename__ = "acwl_scheduler_nodes"

    id = Column(Integer, primary_key=True, index=True, comment="调度器ID，自增主键")
    node_id = Column(String(100), unique=True, nullable=False, index=True, comment="调度器节点唯一标识")
    node_name = Column(String(100), nullable=False, comment="节点名称")
    host_ip = Column(String(45), nullable=False, comment="主机IP地址")
    port = Column(Integer, nullable=False, comment="服务端口")
    status = Column(String(20), default="standby", nullable=False, comment="节点状态")
    role = Column(String(20), default="follower", nullable=False, comment="集群角色")
    version = Column(String(50), comment="调度器版本")
    election_priority = Column(Integer, default=100, comment="选举优先级")
    last_heartbeat = Column(DateTime, comment="最后心跳时间")
    leader_lease_expires = Column(DateTime, comment="Leader租约过期时间")
    registration_time = Column(DateTime, default=datetime.utcnow, comment="注册时间")
    node_metadata = Column('metadata', JSON, comment="节点元数据")
    capabilities = Column(JSON, comment="节点能力列表")
    metrics = Column(JSON, comment="性能指标")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")

    def __repr__(self):
        return f"<SchedulerNode(node_id='{self.node_id}', role='{self.role}', status='{self.status}')>"


class SchedulerLock(Base):
    """调度器锁模型（用于分布式锁和Leader选举）"""
    __tablename__ = "acwl_scheduler_locks"

    id = Column(Integer, primary_key=True, index=True, comment="锁ID，自增主键")
    lock_name = Column(String(100), unique=True, nullable=False, comment="锁名称")
    lock_owner = Column(String(100), nullable=False, comment="锁持有者（调度器节点ID）")
    lock_value = Column(String(255), comment="锁值")
    acquired_at = Column(DateTime, default=datetime.utcnow, comment="获取时间")
    expires_at = Column(DateTime, nullable=False, comment="过期时间")
    lock_metadata = Column(JSON, comment="锁元数据")

    def __repr__(self):
        return f"<SchedulerLock(lock_name='{self.lock_name}', owner='{self.lock_owner}')>"