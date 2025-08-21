#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
服务器相关数据模型
"""

from sqlalchemy import Integer, String, Boolean, Text, Enum as SQLEnum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from enum import Enum
from typing import List, Optional

from app.core.database import Base, TimestampMixin


class ServerType(str, Enum):
    """服务器类型枚举"""
    physical = "physical"  # 物理机
    virtual = "virtual"    # 虚拟机
    cloud = "cloud"        # 云服务器


class ServerStatus(str, Enum):
    """服务器状态枚举"""
    online = "online"          # 在线
    offline = "offline"        # 离线
    maintenance = "maintenance" # 维护中


class Server(Base, TimestampMixin):
    """服务器表"""
    
    __tablename__ = "acwl_servers"
    __table_args__ = {"comment": "服务器表，存储部署大模型服务的物理或虚拟服务器信息"}
    
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="服务器ID，自增主键"
    )
    
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="服务器名称"
    )
    
    ip_address: Mapped[str] = mapped_column(
        String(45),
        nullable=False,
        unique=True,
        comment="服务器IP地址"
    )
    
    ssh_port: Mapped[int] = mapped_column(
        Integer,
        default=22,
        comment="SSH端口"
    )
    
    ssh_username: Mapped[Optional[str]] = mapped_column(
        String(50),
        comment="SSH用户名"
    )
    
    ssh_key_path: Mapped[Optional[str]] = mapped_column(
        Text,
        comment="SSH密钥路径"
    )
    
    ssh_password: Mapped[Optional[str]] = mapped_column(
        String(255),
        comment="SSH密码（加密存储）"
    )
    
    server_type: Mapped[ServerType] = mapped_column(
        SQLEnum(ServerType),
        nullable=False,
        comment="服务器类型：物理机、虚拟机、云服务器"
    )
    
    os_info: Mapped[Optional[str]] = mapped_column(
        String(100),
        comment="操作系统信息"
    )
    
    status: Mapped[ServerStatus] = mapped_column(
        SQLEnum(ServerStatus),
        nullable=False,
        default=ServerStatus.offline,
        comment="服务器状态"
    )
    
    total_memory: Mapped[Optional[str]] = mapped_column(
        String(50),
        comment="总内存"
    )
    
    total_storage: Mapped[Optional[str]] = mapped_column(
        String(50),
        comment="总存储空间"
    )
    
    total_cpu_cores: Mapped[Optional[int]] = mapped_column(
        Integer,
        comment="总CPU核心数"
    )
    
    # 关系
    gpu_resources: Mapped[List["GPUResource"]] = relationship(
        "GPUResource",
        back_populates="server",
        cascade="all, delete-orphan"
    )
    
    deployments: Mapped[List["Deployment"]] = relationship(
        "Deployment",
        back_populates="server"
    )
    
    def __repr__(self) -> str:
        return f"<Server(id={self.id}, name='{self.name}', ip='{self.ip_address}', status='{self.status}')>"


class GPUResource(Base, TimestampMixin):
    """GPU资源表"""
    
    __tablename__ = "acwl_gpu_resources"
    __table_args__ = {"comment": "GPU资源表，记录服务器上的GPU资源信息"}
    
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="GPU资源ID，自增主键"
    )
    
    server_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("acwl_servers.id"),
        nullable=False,
        comment="所属服务器ID"
    )
    
    gpu_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="GPU名称"
    )
    
    gpu_type: Mapped[Optional[str]] = mapped_column(
        String(50),
        comment="GPU类型，如NVIDIA A100, V100等"
    )
    
    memory_size: Mapped[Optional[str]] = mapped_column(
        String(50),
        comment="GPU内存大小"
    )
    
    cuda_version: Mapped[Optional[str]] = mapped_column(
        String(20),
        comment="CUDA版本"
    )
    
    device_id: Mapped[Optional[str]] = mapped_column(
        String(20),
        comment="设备ID"
    )
    
    is_available: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        comment="是否可用"
    )
    
    # 关系
    server: Mapped["Server"] = relationship(
        "Server",
        back_populates="gpu_resources"
    )
    
    deployment_gpus: Mapped[List["DeploymentGPU"]] = relationship(
        "DeploymentGPU",
        back_populates="gpu"
    )
    
    def __repr__(self) -> str:
        return f"<GPUResource(id={self.id}, name='{self.gpu_name}', server_id={self.server_id}, available={self.is_available})>"


class ServerMetrics(Base, TimestampMixin):
    """服务器监控指标表"""
    
    __tablename__ = "acwl_server_metrics"
    __table_args__ = {"comment": "服务器监控指标表，记录服务器的实时监控数据"}
    
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="指标ID，自增主键"
    )
    
    server_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("acwl_servers.id"),
        nullable=False,
        comment="服务器ID"
    )
    
    cpu_usage: Mapped[Optional[float]] = mapped_column(
        comment="CPU使用率（百分比）"
    )
    
    memory_usage: Mapped[Optional[float]] = mapped_column(
        comment="内存使用率（百分比）"
    )
    
    disk_usage: Mapped[Optional[float]] = mapped_column(
        comment="磁盘使用率（百分比）"
    )
    
    network_in: Mapped[Optional[float]] = mapped_column(
        comment="网络入流量（MB/s）"
    )
    
    network_out: Mapped[Optional[float]] = mapped_column(
        comment="网络出流量（MB/s）"
    )
    
    gpu_metrics: Mapped[Optional[str]] = mapped_column(
        Text,
        comment="GPU监控数据（JSON格式）"
    )
    
    # 关系
    server: Mapped["Server"] = relationship("Server")
    
    def __repr__(self) -> str:
        return f"<ServerMetrics(id={self.id}, server_id={self.server_id}, cpu={self.cpu_usage}%)>"