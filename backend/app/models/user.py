#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用户相关模型
"""

from sqlalchemy import Integer, String, Boolean, TIMESTAMP, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from typing import List, TYPE_CHECKING

from app.core.database import Base, TimestampMixin

if TYPE_CHECKING:
    from .dataset import Dataset
    from .datasource import Datasource, DatasourcePermission
    from .project import Project, ProjectMember
    from .task import TaskDefinition, TaskTemplate, TaskSchedule, ExecutorGroup
    from .workflow import Workflow, WorkflowInstance, WorkflowSchedule
    from .unified_node import UnifiedNode


class User(Base, TimestampMixin):
    """用户模型"""
    
    __tablename__ = "acwl_users"
    __table_args__ = {"comment": "系统用户信息表，存储用户账号和权限信息"}
    
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="用户ID，自增主键"
    )
    
    username: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        comment="用户名，唯一"
    )
    
    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="密码哈希值"
    )
    
    email: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        comment="电子邮箱，唯一"
    )
    
    role: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="user",
        comment="用户角色，如admin、user等"
    )
    
    # 关联关系
    datasets: Mapped[List["Dataset"]] = relationship(
        "Dataset",
        back_populates="creator",
        cascade="all, delete-orphan"
    )
    
    # 数据源相关关系
    datasources: Mapped[List["Datasource"]] = relationship(
        "Datasource",
        back_populates="creator",
        cascade="all, delete-orphan"
    )
    
    datasource_permissions: Mapped[List["DatasourcePermission"]] = relationship(
        "DatasourcePermission",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    
    # 项目相关关系
    created_projects: Mapped[List["Project"]] = relationship(
        "Project",
        back_populates="creator",
        cascade="all, delete-orphan"
    )
    
    project_memberships: Mapped[List["ProjectMember"]] = relationship(
        "ProjectMember",
        foreign_keys="[ProjectMember.user_id]",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    
    # 任务相关关系
    created_task_definitions: Mapped[List["TaskDefinition"]] = relationship(
        "TaskDefinition",
        foreign_keys="[TaskDefinition.created_by]",
        back_populates="creator",
        cascade="all, delete-orphan"
    )
    
    created_task_templates: Mapped[List["TaskTemplate"]] = relationship(
        "TaskTemplate",
        foreign_keys="[TaskTemplate.created_by]",
        back_populates="creator",
        cascade="all, delete-orphan"
    )
    
    # 工作流相关关系
    created_workflows: Mapped[List["Workflow"]] = relationship(
        "Workflow",
        foreign_keys="[Workflow.created_by]",
        back_populates="creator",
        cascade="all, delete-orphan"
    )
    
    triggered_workflow_instances: Mapped[List["WorkflowInstance"]] = relationship(
        "WorkflowInstance",
        foreign_keys="[WorkflowInstance.triggered_by_user]",
        back_populates="triggered_user",
        cascade="all, delete-orphan"
    )
    
    created_workflow_schedules: Mapped[List["WorkflowSchedule"]] = relationship(
        "WorkflowSchedule",
        foreign_keys="[WorkflowSchedule.created_by]",
        back_populates="creator",
        cascade="all, delete-orphan"
    )
    
    # 执行器相关关系
    created_executor_groups: Mapped[List["ExecutorGroup"]] = relationship(
        "ExecutorGroup",
        foreign_keys="[ExecutorGroup.created_by]",
        back_populates="creator",
        cascade="all, delete-orphan"
    )
    
    # 任务调度相关关系
    created_task_schedules: Mapped[List["TaskSchedule"]] = relationship(
        "TaskSchedule",
        foreign_keys="[TaskSchedule.created_by]",
        back_populates="creator",
        cascade="all, delete-orphan"
    )
    
    # 统一节点相关关系
    created_unified_nodes: Mapped[List["UnifiedNode"]] = relationship(
        "UnifiedNode",
        foreign_keys="[UnifiedNode.created_by]",
        back_populates="creator",
        cascade="all, delete-orphan"
    )
    
    # 暂时注释掉不存在的模型关系
    # api_keys: Mapped[List["APIKey"]] = relationship(
    #     "APIKey",
    #     back_populates="user",
    #     cascade="all, delete-orphan"
    # )
    # 
    # usage_logs: Mapped[List["UsageLog"]] = relationship(
    #     "UsageLog",
    #     back_populates="user"
    # )
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, username='{self.username}', role='{self.role}')>"
    
    @property
    def is_admin(self) -> bool:
        """是否为管理员"""
        return self.role == "admin"
    
    @property
    def is_active(self) -> bool:
        """用户是否激活（可扩展）"""
        return True