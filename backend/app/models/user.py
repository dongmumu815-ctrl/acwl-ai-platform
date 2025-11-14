#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用户相关模型
"""

from sqlalchemy import Integer, String, Boolean, TIMESTAMP, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from typing import List, TYPE_CHECKING, Optional

from app.core.database import Base, TimestampMixin

if TYPE_CHECKING:
    from .dataset import Dataset
    from .datasource import Datasource, DatasourcePermission
    from .project import Project, ProjectMember
    from .task import TaskDefinition, TaskTemplate, TaskSchedule, ExecutorGroup
    from .workflow import Workflow, WorkflowInstance, WorkflowSchedule
    from .unified_node import UnifiedNode
    from .es_query_template import ESQueryTemplate
    from .sql_query_template import SQLQueryTemplate
    from .resource_package import ResourcePackage, ResourcePackagePermission, ResourcePackageQueryHistory
    from .role import Role, UserRole, RolePermission
    from .permission import Permission


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

    department: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="部门"
    )

    phone: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        comment="手机号"
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="active",
        comment="用户状态：active/disabled/pending"
    )

    remark: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="备注"
    )
    
    # 关联关系
    datasets: Mapped[List["Dataset"]] = relationship(
        "Dataset",
        foreign_keys="[Dataset.created_by]",
        back_populates="creator",
        cascade="all, delete-orphan"
    )
    
    # 数据源相关关系
    datasources: Mapped[List["Datasource"]] = relationship(
        "Datasource",
        foreign_keys="[Datasource.created_by]",
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
        foreign_keys="[Project.created_by]",
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
    
    # ES查询模板关系
    es_query_templates: Mapped[List["ESQueryTemplate"]] = relationship(
        "ESQueryTemplate",
        foreign_keys="[ESQueryTemplate.created_by]",
        back_populates="creator",
        cascade="all, delete-orphan"
    )
    
    # SQL查询模板关系
    sql_query_templates: Mapped[List["SQLQueryTemplate"]] = relationship(
        "SQLQueryTemplate",
        foreign_keys="[SQLQueryTemplate.created_by]",
        back_populates="creator",
        cascade="all, delete-orphan"
    )
    
    # 资源包相关关系
    created_resource_packages: Mapped[List["ResourcePackage"]] = relationship(
        "ResourcePackage",
        foreign_keys="[ResourcePackage.created_by]",
        back_populates="creator",
        cascade="all, delete-orphan"
    )
    
    resource_package_permissions: Mapped[List["ResourcePackagePermission"]] = relationship(
        "ResourcePackagePermission",
        foreign_keys="[ResourcePackagePermission.user_id]",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    
    granted_resource_package_permissions: Mapped[List["ResourcePackagePermission"]] = relationship(
        "ResourcePackagePermission",
        foreign_keys="[ResourcePackagePermission.granted_by]",
        back_populates="granter",
        cascade="all, delete-orphan"
    )
    
    resource_package_query_histories: Mapped[List["ResourcePackageQueryHistory"]] = relationship(
        "ResourcePackageQueryHistory",
        foreign_keys="[ResourcePackageQueryHistory.user_id]",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    
    # 角色权限系统关系
    user_roles: Mapped[List["UserRole"]] = relationship(
        "UserRole",
        foreign_keys="[UserRole.user_id]",
        back_populates="user",
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
        """用户是否激活（根据状态字段）"""
        try:
            return (self.status or "active") == "active"
        except Exception:
            return True
    
    # 新的角色权限系统方法
    def get_roles(self):
        """获取用户的所有角色"""
        return [ur.role for ur in self.user_roles if ur.role.status]
    
    def get_role_codes(self):
        """获取用户的所有角色代码"""
        return [ur.role.code for ur in self.user_roles if ur.role.status]
    
    def has_role(self, role_code: str) -> bool:
        """检查用户是否拥有指定角色"""
        return role_code in self.get_role_codes()
    
    def has_permission(self, permission_code: str) -> bool:
        """检查用户是否拥有指定权限"""
        for user_role in self.user_roles:
            if user_role.role.status and user_role.role.has_permission(permission_code):
                return True
        return False
    
    def get_permissions(self):
        """获取用户的所有权限"""
        permissions = []
        for user_role in self.user_roles:
            if user_role.role.status:
                permissions.extend(user_role.role.get_permissions())
        # 去重
        unique_permissions = {}
        for perm in permissions:
            unique_permissions[perm.code] = perm
        return list(unique_permissions.values())
    
    def get_permission_codes(self):
        """获取用户的所有权限代码"""
        permission_codes = set()
        for user_role in self.user_roles:
            if user_role.role.status:
                permission_codes.update(user_role.role.get_permission_codes())
        return list(permission_codes)
    
    @property
    def is_super_admin(self) -> bool:
        """是否为超级管理员（基于新角色系统）"""
        return self.has_role('super_admin')
    
    @property
    def is_admin_new(self) -> bool:
        """是否为管理员（基于新角色系统）"""
        return self.has_role('admin') or self.has_role('super_admin')