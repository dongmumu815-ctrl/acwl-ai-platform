#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
应用管理相关数据模型
"""

from sqlalchemy import Integer, String, Boolean, Text, Enum as SQLEnum, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from enum import Enum
from typing import List, Optional, Dict, Any, TYPE_CHECKING

from app.core.database import Base, TimestampMixin, UserMixin

if TYPE_CHECKING:
    from app.models.server import Server

class AppType(str, Enum):
    """应用类型枚举"""
    docker_compose = "docker_compose"
    docker_image = "docker_image"
    shell_script = "shell_script"
    helm_chart = "helm_chart"  # 保留扩展

class AppStatus(str, Enum):
    """应用状态枚举"""
    installing = "installing"
    running = "running"
    stopped = "stopped"
    error = "error"
    upgrading = "upgrading"
    uninstalling = "uninstalling"
    uninstalled = "uninstalled"

class HarborConfig(Base, TimestampMixin, UserMixin):
    """Harbor镜像仓库配置表"""
    
    __tablename__ = "acwl_harbor_configs"
    __table_args__ = {"comment": "Harbor镜像仓库配置"}
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="ID")
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, comment="配置名称")
    url: Mapped[str] = mapped_column(String(255), nullable=False, comment="Harbor地址")
    username: Mapped[Optional[str]] = mapped_column(String(100), comment="用户名")
    password: Mapped[Optional[str]] = mapped_column(String(255), comment="密码")
    project: Mapped[Optional[str]] = mapped_column(String(100), comment="默认项目")
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否默认仓库")
    insecure_registry: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否跳过HTTPS验证(Insecure Registry)")
    
    description: Mapped[Optional[str]] = mapped_column(Text, comment="描述")

class AppTemplate(Base, TimestampMixin, UserMixin):
    """应用模板表"""
    
    __tablename__ = "acwl_app_templates"
    __table_args__ = {"comment": "应用模板表"}
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="ID")
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, comment="应用名称")
    display_name: Mapped[Optional[str]] = mapped_column(String(100), comment="显示名称")
    version: Mapped[str] = mapped_column(String(50), nullable=False, default="latest", comment="版本")
    description: Mapped[Optional[str]] = mapped_column(Text, comment="应用描述")
    icon: Mapped[Optional[str]] = mapped_column(Text, comment="应用图标(Base64或URL)")
    
    app_type: Mapped[AppType] = mapped_column(SQLEnum(AppType), nullable=False, comment="应用类型")
    
    # 配置模板，定义可配置的参数，Schema格式
    config_schema: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, comment="配置参数Schema(JSON)")
    
    # 默认配置值
    default_config: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, comment="默认配置值(JSON)")
    
    # 部署脚本或Compose文件模板
    deploy_template: Mapped[Optional[str]] = mapped_column(Text, comment="部署模板(Compose/Script)")
    
    is_system: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否系统内置")
    
    instances: Mapped[List["AppInstance"]] = relationship("AppInstance", back_populates="template")

class AppInstance(Base, TimestampMixin, UserMixin):
    """应用实例表"""
    
    __tablename__ = "acwl_app_instances"
    __table_args__ = {"comment": "应用实例表"}
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="ID")
    name: Mapped[str] = mapped_column(String(100), nullable=False, comment="实例名称")
    
    template_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("acwl_app_templates.id", ondelete="SET NULL"), comment="关联模板ID")
    template: Mapped[Optional["AppTemplate"]] = relationship("AppTemplate", back_populates="instances")
    
    status: Mapped[AppStatus] = mapped_column(SQLEnum(AppStatus), default=AppStatus.installing, comment="当前状态")
    
    # 实际使用的配置
    config: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, comment="实例配置(JSON)")
    
    description: Mapped[Optional[str]] = mapped_column(Text, comment="实例描述")
    
    deployments: Mapped[List["AppDeployment"]] = relationship("AppDeployment", back_populates="instance", cascade="all, delete-orphan")

class AppDeployment(Base, TimestampMixin):
    """应用部署详情表(多机部署)"""
    
    __tablename__ = "acwl_app_deployments"
    __table_args__ = {"comment": "应用部署详情表"}
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="ID")
    
    instance_id: Mapped[int] = mapped_column(Integer, ForeignKey("acwl_app_instances.id", ondelete="CASCADE"), nullable=False, comment="应用实例ID")
    instance: Mapped["AppInstance"] = relationship("AppInstance", back_populates="deployments")
    
    server_id: Mapped[int] = mapped_column(Integer, ForeignKey("acwl_servers.id", ondelete="CASCADE"), nullable=False, comment="服务器ID")
    server: Mapped["Server"] = relationship("Server")
    
    role: Mapped[Optional[str]] = mapped_column(String(50), default="default", comment="节点角色(master/worker/fe/be)")
    
    container_id: Mapped[Optional[str]] = mapped_column(String(100), comment="容器ID或服务标识")
    
    status: Mapped[str] = mapped_column(String(50), default="unknown", comment="节点状态")
    
    # 资源分配
    cpu_limit: Mapped[Optional[str]] = mapped_column(String(20), comment="CPU限制")
    mem_limit: Mapped[Optional[str]] = mapped_column(String(20), comment="内存限制")
    
    # 端口映射记录
    ports: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, comment="端口映射记录")
