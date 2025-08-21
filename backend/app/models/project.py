#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
项目管理相关数据模型
"""

from sqlalchemy import Integer, String, Text, Boolean, TIMESTAMP, JSON, Enum, Date, DECIMAL, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from typing import List, Optional, TYPE_CHECKING
from enum import Enum as PyEnum
from datetime import datetime, date
from decimal import Decimal

from app.core.database import Base, TimestampMixin, UserMixin

if TYPE_CHECKING:
    from .user import User
    from .datasource import Datasource
    from .dataset import Dataset
    from .model import Model
    from .task import TaskDefinition
    from .workflow import Workflow
    from .unified_node import UnifiedNode


class ProjectStatus(str, PyEnum):
    """项目状态枚举"""
    ACTIVE = "ACTIVE"          # 激活
    INACTIVE = "INACTIVE"      # 未激活
    ARCHIVED = "ARCHIVED"      # 已归档


class ProjectType(str, PyEnum):
    """项目类型枚举"""
    DATA_ANALYSIS = "DATA_ANALYSIS"    # 数据分析
    MODEL_TRAINING = "MODEL_TRAINING"  # 模型训练
    ETL_PIPELINE = "ETL_PIPELINE"      # ETL管道
    GENERAL = "GENERAL"                # 通用


class ProjectPriority(str, PyEnum):
    """项目优先级枚举"""
    LOW = "LOW"                # 低
    MEDIUM = "MEDIUM"          # 中
    HIGH = "HIGH"              # 高
    CRITICAL = "CRITICAL"      # 紧急


class ProjectMemberRole(str, PyEnum):
    """项目成员角色枚举"""
    ADMIN = "ADMIN"            # 管理员
    DEVELOPER = "DEVELOPER"    # 开发者
    VIEWER = "VIEWER"          # 访客


class ProjectDatasourceAccessType(str, PyEnum):
    """项目数据源访问类型枚举"""
    READ = "read"              # 只读
    WRITE = "write"            # 读写
    ADMIN = "admin"            # 管理


class ProjectResourceType(str, PyEnum):
    """项目资源类型枚举"""
    STORAGE = "storage"        # 存储
    COMPUTE = "compute"        # 计算
    MEMORY = "memory"          # 内存
    GPU = "gpu"                # GPU
    API_CALLS = "api_calls"    # API调用


class ProjectQuotaResetPeriod(str, PyEnum):
    """项目配额重置周期枚举"""
    DAILY = "daily"            # 每日
    WEEKLY = "weekly"          # 每周
    MONTHLY = "monthly"        # 每月
    YEARLY = "yearly"          # 每年
    NEVER = "never"            # 永不


class ProjectActivityType(str, PyEnum):
    """项目活动类型枚举"""
    CREATE = "create"                      # 创建
    UPDATE = "update"                      # 更新
    DELETE = "delete"                      # 删除
    MEMBER_ADD = "member_add"              # 添加成员
    MEMBER_REMOVE = "member_remove"        # 移除成员
    DATASOURCE_ADD = "datasource_add"      # 添加数据源
    DATASOURCE_REMOVE = "datasource_remove"# 移除数据源
    PERMISSION_CHANGE = "permission_change"# 权限变更


class ProjectActivityTargetType(str, PyEnum):
    """项目活动目标类型枚举"""
    PROJECT = "project"        # 项目
    MEMBER = "member"          # 成员
    DATASOURCE = "datasource"  # 数据源
    QUOTA = "quota"            # 配额
    OTHER = "other"            # 其他


class Project(Base, TimestampMixin, UserMixin):
    """项目模型"""
    
    __tablename__ = "acwl_projects"
    __table_args__ = {"comment": "项目表，管理数据中台的各个项目"}
    
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="项目ID，自增主键"
    )
    
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="项目名称"
    )
    
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="项目描述"
    )
    
    status: Mapped[ProjectStatus] = mapped_column(
        Enum(ProjectStatus),
        nullable=False,
        default=ProjectStatus.ACTIVE,
        comment="项目状态：激活、未激活、已归档"
    )
    
    project_type: Mapped[ProjectType] = mapped_column(
        Enum(ProjectType),
        nullable=False,
        default=ProjectType.GENERAL,
        comment="项目类型：数据分析、模型训练、ETL管道、通用"
    )
    
    start_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="项目开始日期"
    )
    
    end_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="项目结束日期"
    )
    
    members_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        comment="团队成员数量"
    )
    
    priority: Mapped[ProjectPriority] = mapped_column(
        Enum(ProjectPriority),
        nullable=False,
        default=ProjectPriority.MEDIUM,
        comment="项目优先级"
    )
    
    tags: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="项目标签"
    )
    
    project_metadata: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="项目元数据"
    )
    
    # 关联关系
    members: Mapped[List["ProjectMember"]] = relationship(
        "ProjectMember",
        back_populates="project",
        cascade="all, delete-orphan"
    )
    
    datasources: Mapped[List["ProjectDatasource"]] = relationship(
        "ProjectDatasource",
        back_populates="project",
        cascade="all, delete-orphan"
    )
    
    quotas: Mapped[List["ProjectQuota"]] = relationship(
        "ProjectQuota",
        back_populates="project",
        cascade="all, delete-orphan"
    )
    
    activities: Mapped[List["ProjectActivity"]] = relationship(
        "ProjectActivity",
        back_populates="project",
        cascade="all, delete-orphan"
    )
    
    creator: Mapped["User"] = relationship(
        "User",
        foreign_keys="[Project.created_by]",
        back_populates="created_projects"
    )
    
    # 任务定义关系
    task_definitions: Mapped[List["TaskDefinition"]] = relationship(
        "TaskDefinition",
        back_populates="project",
        cascade="all, delete-orphan"
    )
    
    # 工作流关系
    workflows: Mapped[List["Workflow"]] = relationship(
        "Workflow",
        back_populates="project",
        cascade="all, delete-orphan"
    )
    
    # 关联的统一节点
    unified_nodes: Mapped[List["UnifiedNode"]] = relationship(
        "UnifiedNode",
        back_populates="project",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<Project(id={self.id}, name='{self.name}', type='{self.project_type}')>"
    
    @property
    def is_active(self) -> bool:
        """项目是否激活"""
        return self.status == ProjectStatus.ACTIVE
    
    @property
    def is_expired(self) -> bool:
        """项目是否过期"""
        if self.end_date:
            from datetime import date
            return date.today() > self.end_date
        return False


class ProjectMember(Base):
    """项目成员模型"""
    
    __tablename__ = "acwl_project_members"
    __table_args__ = {"comment": "项目成员表，管理项目的成员和角色权限"}
    
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="成员ID，自增主键"
    )
    
    project_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("acwl_projects.id", ondelete="CASCADE"),
        nullable=False,
        comment="项目ID"
    )
    
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("acwl_users.id", ondelete="CASCADE"),
        nullable=False,
        comment="用户ID"
    )
    
    role: Mapped[ProjectMemberRole] = mapped_column(
        Enum(ProjectMemberRole),
        nullable=False,
        comment="项目角色：管理员、开发者、访客"
    )
    
    permissions: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="具体权限配置"
    )
    
    joined_at: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        server_default=func.current_timestamp(),
        comment="加入时间"
    )
    
    invited_by: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("acwl_users.id", ondelete="SET NULL"),
        nullable=True,
        comment="邀请者ID"
    )
    
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        comment="是否激活"
    )
    
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="备注信息"
    )
    
    # 关联关系
    project: Mapped["Project"] = relationship(
        "Project",
        back_populates="members"
    )
    
    user: Mapped["User"] = relationship(
        "User",
        foreign_keys=[user_id],
        back_populates="project_memberships"
    )
    
    inviter: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[invited_by]
    )
    
    def __repr__(self) -> str:
        return f"<ProjectMember(id={self.id}, project_id={self.project_id}, user_id={self.user_id}, role='{self.role}')>"
    
    @property
    def is_admin(self) -> bool:
        """是否为项目管理员"""
        return self.role == ProjectMemberRole.ADMIN
    
    @property
    def can_manage_members(self) -> bool:
        """是否可以管理成员"""
        return self.role == ProjectMemberRole.ADMIN
    
    @property
    def can_write(self) -> bool:
        """是否有写权限"""
        return self.role in [ProjectMemberRole.ADMIN, ProjectMemberRole.DEVELOPER]


class ProjectDatasource(Base):
    """项目数据源关联模型"""
    
    __tablename__ = "acwl_project_datasources"
    __table_args__ = {"comment": "项目数据源关联表，管理项目可访问的数据源及权限"}
    
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="关联ID，自增主键"
    )
    
    project_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("acwl_projects.id", ondelete="CASCADE"),
        nullable=False,
        comment="项目ID"
    )
    
    datasource_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("acwl_datasources.id", ondelete="CASCADE"),
        nullable=False,
        comment="数据源ID"
    )
    
    access_type: Mapped[ProjectDatasourceAccessType] = mapped_column(
        Enum(ProjectDatasourceAccessType),
        nullable=False,
        default=ProjectDatasourceAccessType.READ,
        comment="访问类型：只读、读写、管理"
    )
    
    is_primary: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        comment="是否为主数据源"
    )
    
    config: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="数据源在项目中的配置"
    )
    
    assigned_by: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("acwl_users.id", ondelete="SET NULL"),
        nullable=True,
        comment="分配者ID"
    )
    
    assigned_at: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        server_default=func.current_timestamp(),
        comment="分配时间"
    )
    
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        TIMESTAMP,
        nullable=True,
        comment="过期时间"
    )
    
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        comment="是否激活"
    )
    
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="备注信息"
    )
    
    # 关联关系
    project: Mapped["Project"] = relationship(
        "Project",
        back_populates="datasources"
    )
    
    datasource: Mapped["Datasource"] = relationship(
        "Datasource",
        back_populates="project_associations"
    )
    
    assigner: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[assigned_by]
    )
    
    def __repr__(self) -> str:
        return f"<ProjectDatasource(id={self.id}, project_id={self.project_id}, datasource_id={self.datasource_id}, access='{self.access_type}')>"
    
    @property
    def is_expired(self) -> bool:
        """是否过期"""
        if self.expires_at:
            from datetime import datetime
            return datetime.now() > self.expires_at
        return False
    
    @property
    def can_write(self) -> bool:
        """是否有写权限"""
        return self.access_type in [ProjectDatasourceAccessType.WRITE, ProjectDatasourceAccessType.ADMIN]
    
    @property
    def can_admin(self) -> bool:
        """是否有管理权限"""
        return self.access_type == ProjectDatasourceAccessType.ADMIN


class ProjectQuota(Base, TimestampMixin):
    """项目资源配额模型"""
    
    __tablename__ = "acwl_project_quotas"
    __table_args__ = {"comment": "项目资源配额表，管理项目的资源使用限制"}
    
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="配额ID，自增主键"
    )
    
    project_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("acwl_projects.id", ondelete="CASCADE"),
        nullable=False,
        comment="项目ID"
    )
    
    resource_type: Mapped[ProjectResourceType] = mapped_column(
        Enum(ProjectResourceType),
        nullable=False,
        comment="资源类型"
    )
    
    quota_limit: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="配额限制"
    )
    
    quota_used: Mapped[int] = mapped_column(
        Integer,
        default=0,
        comment="已使用配额"
    )
    
    unit: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="单位，如GB、hours、calls等"
    )
    
    reset_period: Mapped[ProjectQuotaResetPeriod] = mapped_column(
        Enum(ProjectQuotaResetPeriod),
        default=ProjectQuotaResetPeriod.MONTHLY,
        comment="重置周期"
    )
    
    last_reset_at: Mapped[Optional[datetime]] = mapped_column(
        TIMESTAMP,
        nullable=True,
        comment="最后重置时间"
    )
    
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        comment="是否激活"
    )
    
    # 关联关系
    project: Mapped["Project"] = relationship(
        "Project",
        back_populates="quotas"
    )
    
    def __repr__(self) -> str:
        return f"<ProjectQuota(id={self.id}, project_id={self.project_id}, type='{self.resource_type}', limit={self.quota_limit})>"
    
    @property
    def usage_percentage(self) -> float:
        """使用率百分比"""
        if self.quota_limit == 0:
            return 0.0
        return (self.quota_used / self.quota_limit) * 100
    
    @property
    def is_exceeded(self) -> bool:
        """是否超出配额"""
        return self.quota_used > self.quota_limit
    
    @property
    def remaining_quota(self) -> int:
        """剩余配额"""
        return max(0, self.quota_limit - self.quota_used)


class ProjectActivity(Base):
    """项目活动日志模型"""
    
    __tablename__ = "acwl_project_activities"
    __table_args__ = {"comment": "项目活动日志表，记录项目相关的所有操作活动"}
    
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="活动ID，自增主键"
    )
    
    project_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("acwl_projects.id", ondelete="CASCADE"),
        nullable=False,
        comment="项目ID"
    )
    
    user_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("acwl_users.id", ondelete="SET NULL"),
        nullable=True,
        comment="操作用户ID"
    )
    
    activity_type: Mapped[ProjectActivityType] = mapped_column(
        Enum(ProjectActivityType),
        nullable=False,
        comment="活动类型"
    )
    
    target_type: Mapped[ProjectActivityTargetType] = mapped_column(
        Enum(ProjectActivityTargetType),
        nullable=False,
        comment="目标类型"
    )
    
    target_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="目标ID"
    )
    
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="活动描述"
    )
    
    details: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="活动详情"
    )
    
    ip_address: Mapped[Optional[str]] = mapped_column(
        String(45),
        nullable=True,
        comment="IP地址"
    )
    
    user_agent: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="用户代理"
    )
    
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        server_default=func.current_timestamp(),
        comment="创建时间"
    )
    
    # 关联关系
    project: Mapped["Project"] = relationship(
        "Project",
        back_populates="activities"
    )
    
    user: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[user_id]
    )
    
    def __repr__(self) -> str:
        return f"<ProjectActivity(id={self.id}, project_id={self.project_id}, type='{self.activity_type}')>"


class ProjectTemplate(Base, TimestampMixin, UserMixin):
    """项目模板模型"""
    
    __tablename__ = "acwl_project_templates"
    __table_args__ = {"comment": "项目模板表，存储项目创建的预定义模板"}
    
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
    
    project_type: Mapped[ProjectType] = mapped_column(
        Enum(ProjectType),
        nullable=False,
        comment="项目类型"
    )
    
    template_config: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        comment="模板配置"
    )
    
    default_roles: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="默认角色配置"
    )
    
    default_quotas: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="默认配额配置"
    )
    
    is_system: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        comment="是否系统模板"
    )
    
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        comment="是否激活"
    )
    
    def __repr__(self) -> str:
        return f"<ProjectTemplate(id={self.id}, name='{self.name}', type='{self.project_type}')>"