#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
部署相关数据库模型
"""

from sqlalchemy import Integer, String, Text, Boolean, TIMESTAMP, JSON, ForeignKey, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, Dict, Any, List, TYPE_CHECKING
import enum

from app.core.database import Base, TimestampMixin, UserMixin

if TYPE_CHECKING:
    from .model import Model
    from .server import Server, GPUResource


class DeploymentType(str, enum.Enum):
    """部署类型枚举"""
    VLLM = "vLLM"
    OLLAMA = "Ollama"
    HUGGINGFACE = "HuggingFace"
    OTHER = "Other"


class DeploymentStatus(str, enum.Enum):
    """部署状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    STOPPED = "stopped"
    FAILED = "failed"


class Deployment(Base, TimestampMixin, UserMixin):
    """模型部署实例表"""
    
    __tablename__ = "acwl_deployments"
    __table_args__ = {"comment": "模型部署实例表，记录模型的部署信息和运行状态"}
    
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="部署ID，自增主键"
    )
    
    model_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("acwl_models.id"),
        nullable=False,
        comment="关联的模型ID"
    )
    
    deployment_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="部署名称"
    )
    
    deployment_type: Mapped[DeploymentType] = mapped_column(
        Enum(DeploymentType),
        nullable=False,
        comment="部署类型：vLLM、Ollama、HuggingFace或其他"
    )
    
    server_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("acwl_servers.id"),
        nullable=True,
        comment="部署服务器ID"
    )
    
    status: Mapped[DeploymentStatus] = mapped_column(
        Enum(DeploymentStatus),
        nullable=False,
        comment="部署状态：待处理、运行中、已停止、失败"
    )
    
    endpoint_url: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="端点URL"
    )
    
    deploy_path: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="部署路径"
    )
    
    config: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        comment="部署配置，如资源分配等"
    )
    
    gpu_config: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        comment="GPU配置，如设备ID列表、显存限制等"
    )
    
    runtime_env: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        comment="运行环境配置，如CUDA版本、Python环境等"
    )
    
    restart_policy: Mapped[str] = mapped_column(
        String(50),
        default="no",
        comment="重启策略：no, always, on-failure等"
    )
    
    max_concurrent_requests: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="最大并发请求数"
    )
    
    deployment_logs: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="部署日志路径"
    )
    
    # 关联关系
    model: Mapped["Model"] = relationship(
        "Model",
        back_populates="deployments"
    )
    
    server: Mapped[Optional["Server"]] = relationship(
        "Server",
        back_populates="deployments"
    )
    
    deployment_gpus: Mapped[List["DeploymentGPU"]] = relationship(
        "DeploymentGPU",
        back_populates="deployment",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<Deployment(id={self.id}, name='{self.deployment_name}', status='{self.status}')>"
    
    @property
    def is_running(self) -> bool:
        """是否正在运行"""
        return self.status == DeploymentStatus.RUNNING
    
    @property
    def is_healthy(self) -> bool:
        """是否健康"""
        return self.status == DeploymentStatus.RUNNING and self.endpoint_url is not None


class DeploymentGPU(Base):
    """部署GPU关联表"""
    
    __tablename__ = "acwl_deployment_gpus"
    __table_args__ = {"comment": "部署GPU关联表，记录部署使用的GPU资源"}
    
    deployment_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("acwl_deployments.id"),
        primary_key=True,
        comment="部署ID"
    )
    
    gpu_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("acwl_gpu_resources.id"),
        primary_key=True,
        comment="GPU ID"
    )
    
    memory_limit: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="显存限制"
    )
    
    created_at: Mapped[TIMESTAMP] = mapped_column(
        TIMESTAMP,
        server_default="CURRENT_TIMESTAMP",
        comment="创建时间"
    )
    
    # 关联关系
    deployment: Mapped["Deployment"] = relationship(
        "Deployment",
        back_populates="deployment_gpus"
    )
    
    gpu: Mapped["GPUResource"] = relationship(
        "GPUResource",
        back_populates="deployment_gpus"
    )
    
    def __repr__(self) -> str:
        return f"<DeploymentGPU(deployment_id={self.deployment_id}, gpu_id={self.gpu_id})>"


class DeploymentTemplate(Base, TimestampMixin, UserMixin):
    """部署模板表"""
    
    __tablename__ = "acwl_deployment_templates"
    __table_args__ = {"comment": "部署模板表，存储预定义的部署配置模板"}
    
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="模板ID，自增主键"
    )
    
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="模板名称"
    )
    
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="模板描述"
    )
    
    deployment_type: Mapped[DeploymentType] = mapped_column(
        Enum(DeploymentType),
        nullable=False,
        comment="部署类型"
    )
    
    template_config: Mapped[Dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        comment="模板配置"
    )
    
    def __repr__(self) -> str:
        return f"<DeploymentTemplate(id={self.id}, name='{self.name}', type='{self.deployment_type}')>"