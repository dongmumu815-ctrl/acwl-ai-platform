#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据资源中心相关模型
"""

from sqlalchemy import Integer, String, Text, Boolean, TIMESTAMP, JSON, Enum, BigInteger, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from typing import List, Optional, TYPE_CHECKING
from enum import Enum as PyEnum
from datetime import datetime

from app.core.database import Base, TimestampMixin, UserMixin

if TYPE_CHECKING:
    from .user import User
    from .datasource import Datasource
    from .sql_query_template import SQLQueryTemplate
    from .resource_package import ResourcePackage


class ResourceType(str, PyEnum):
    """资源类型枚举"""
    DORIS_TABLE = "doris_table"
    ELASTICSEARCH_INDEX = "elasticsearch_index"


class ResourceStatus(str, PyEnum):
    """资源状态枚举"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


class PermissionType(str, PyEnum):
    """权限类型枚举"""
    READ = "read"              # 只读
    WRITE = "write"            # 读写
    ADMIN = "admin"            # 管理员


class AccessType(str, PyEnum):
    """访问类型枚举"""
    VIEW = "view"              # 查看
    QUERY = "query"            # 查询
    DOWNLOAD = "download"      # 下载
    PREVIEW = "preview"        # 预览
    SCHEMA = "schema"          # 查看结构


class TagStatus(str, PyEnum):
    """标签状态枚举"""
    ACTIVE = "active"          # 启用
    DISABLED = "disabled"      # 禁用


class AccessStatus(str, PyEnum):
    """访问状态枚举"""
    SUCCESS = "success"        # 成功
    FAILED = "failed"          # 失败
    TIMEOUT = "timeout"        # 超时
    PERMISSION_DENIED = "permission_denied"  # 权限拒绝


class DataResourceCategory(Base, TimestampMixin):
    """数据资源分类模型"""
    
    __tablename__ = "acwl_data_resource_categories"
    __table_args__ = {"comment": "数据资源分类表"}
    
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="分类ID"
    )
    
    name: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        unique=True,
        comment="分类名称"
    )
    
    display_name: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="显示名称"
    )
    
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="分类描述"
    )
    
    parent_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("acwl_data_resource_categories.id"),
        nullable=True,
        comment="父分类ID"
    )
    
    sort_order: Mapped[int] = mapped_column(
        Integer,
        default=0,
        comment="排序"
    )
    
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        comment="是否启用"
    )
    
    # 关系
    parent: Mapped[Optional["DataResourceCategory"]] = relationship(
        "DataResourceCategory",
        remote_side=[id],
        back_populates="children"
    )
    
    children: Mapped[List["DataResourceCategory"]] = relationship(
        "DataResourceCategory",
        back_populates="parent"
    )
    
    resources: Mapped[List["DataResource"]] = relationship(
        "DataResource",
        back_populates="category"
    )


class DataResource(Base, TimestampMixin, UserMixin):
    """数据资源模型"""
    
    __tablename__ = "acwl_data_resources"
    __table_args__ = {"comment": "数据资源表，存储数据资源的基本信息"}
    
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="资源ID"
    )
    
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="资源名称"
    )
    
    display_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="显示名称"
    )
    
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="资源描述"
    )
    
    resource_type: Mapped[ResourceType] = mapped_column(
        Enum(ResourceType),
        nullable=False,
        comment="资源类型"
    )
    
    datasource_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("acwl_datasources.id"),
        nullable=False,
        comment="数据源ID"
    )
    
    database_name: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="数据库名称(Doris)"
    )
    
    table_name: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="表名称(Doris)"
    )
    
    index_name: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="索引名称(ES)"
    )
    
    schema_info: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="表结构信息"
    )
    
    tags: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="标签信息"
    )
    
    category_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("acwl_data_resource_categories.id"),
        nullable=True,
        comment="分类ID"
    )
    
    is_public: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        comment="是否公开"
    )
    
    status: Mapped[ResourceStatus] = mapped_column(
        Enum(ResourceStatus),
        default=ResourceStatus.ACTIVE,
        comment="状态"
    )
    
    view_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        comment="查看次数"
    )
    
    query_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        comment="查询次数"
    )
    
    last_accessed_at: Mapped[Optional[datetime]] = mapped_column(
        TIMESTAMP,
        nullable=True,
        comment="最后访问时间"
    )
    
    # 关系
    datasource: Mapped["Datasource"] = relationship(
        "Datasource",
        back_populates="data_resources"
    )
    
    category: Mapped[Optional["DataResourceCategory"]] = relationship(
        "DataResourceCategory",
        back_populates="resources"
    )
    
    permissions: Mapped[List["DataResourcePermission"]] = relationship(
        "DataResourcePermission",
        back_populates="resource",
        cascade="all, delete-orphan"
    )
    
    access_logs: Mapped[List["DataResourceAccessLog"]] = relationship(
        "DataResourceAccessLog",
        back_populates="resource"
    )
    
    favorites: Mapped[List["DataResourceFavorite"]] = relationship(
        "DataResourceFavorite",
        back_populates="resource",
        cascade="all, delete-orphan"
    )
    
    query_history: Mapped[List["DataResourceQueryHistory"]] = relationship(
        "DataResourceQueryHistory",
        back_populates="resource"
    )
    
    tag_relations: Mapped[List["DataResourceTagRelation"]] = relationship(
        "DataResourceTagRelation",
        back_populates="resource",
        cascade="all, delete-orphan"
    )
    
    sql_query_templates: Mapped[List["SQLQueryTemplate"]] = relationship(
        "SQLQueryTemplate",
        back_populates="data_resource"
    )
    
    # 资源包关系
    packages: Mapped[List["ResourcePackage"]] = relationship(
        "ResourcePackage",
        back_populates="resource",
        cascade="all, delete-orphan"
    )


class DataResourcePermission(Base, TimestampMixin):
    """数据资源权限模型"""
    
    __tablename__ = "acwl_data_resource_permissions"
    __table_args__ = {"comment": "数据资源权限表"}
    
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="权限ID"
    )
    
    resource_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("acwl_data_resources.id", ondelete="CASCADE"),
        nullable=False,
        comment="资源ID"
    )
    
    user_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("acwl_users.id"),
        nullable=True,
        comment="用户ID"
    )
    
    role_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="角色ID"
    )
    
    permission_type: Mapped[PermissionType] = mapped_column(
        Enum(PermissionType),
        nullable=False,
        comment="权限类型"
    )
    
    granted_by: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("acwl_users.id"),
        nullable=False,
        comment="授权者ID"
    )
    
    granted_at: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        server_default=func.now(),
        comment="授权时间"
    )
    
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        TIMESTAMP,
        nullable=True,
        comment="过期时间"
    )
    
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        comment="是否有效"
    )
    
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="备注"
    )
    
    # 关系
    resource: Mapped["DataResource"] = relationship(
        "DataResource",
        back_populates="permissions"
    )
    
    user: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[user_id]
    )
    
    granter: Mapped["User"] = relationship(
        "User",
        foreign_keys=[granted_by]
    )


class DataResourceAccessLog(Base):
    """数据资源访问日志模型"""
    
    __tablename__ = "acwl_data_resource_access_logs"
    __table_args__ = {"comment": "数据资源访问日志表"}
    
    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        comment="日志ID"
    )
    
    resource_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("acwl_data_resources.id"),
        nullable=False,
        comment="资源ID"
    )
    
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("acwl_users.id"),
        nullable=False,
        comment="用户ID"
    )
    
    access_type: Mapped[AccessType] = mapped_column(
        Enum(AccessType),
        nullable=False,
        comment="访问类型"
    )
    
    query_sql: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="查询SQL"
    )
    
    query_params: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="查询参数"
    )
    
    result_count: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="结果数量"
    )
    
    execution_time: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="执行时间(毫秒)"
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
    
    status: Mapped[AccessStatus] = mapped_column(
        Enum(AccessStatus),
        nullable=False,
        comment="状态"
    )
    
    error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="错误信息"
    )
    
    accessed_at: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        server_default=func.now(),
        comment="访问时间"
    )
    
    # 关系
    resource: Mapped["DataResource"] = relationship(
        "DataResource",
        back_populates="access_logs"
    )
    
    user: Mapped["User"] = relationship("User")


class DataResourceFavorite(Base):
    """数据资源收藏模型"""
    
    __tablename__ = "acwl_data_resource_favorites"
    __table_args__ = {"comment": "数据资源收藏表"}
    
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="收藏ID"
    )
    
    resource_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("acwl_data_resources.id", ondelete="CASCADE"),
        nullable=False,
        comment="资源ID"
    )
    
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("acwl_users.id"),
        nullable=False,
        comment="用户ID"
    )
    
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        server_default=func.now(),
        comment="收藏时间"
    )
    
    # 关系
    resource: Mapped["DataResource"] = relationship(
        "DataResource",
        back_populates="favorites"
    )
    
    user: Mapped["User"] = relationship("User")


class DataResourceQueryHistory(Base):
    """数据资源查询历史模型"""
    
    __tablename__ = "acwl_data_resource_query_history"
    __table_args__ = {"comment": "数据资源查询历史表"}
    
    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        comment="历史ID"
    )
    
    resource_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("acwl_data_resources.id"),
        nullable=False,
        comment="资源ID"
    )
    
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("acwl_users.id"),
        nullable=False,
        comment="用户ID"
    )
    
    query_name: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="查询名称"
    )
    
    query_sql: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="查询SQL"
    )
    
    query_params: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="查询参数"
    )
    
    result_count: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="结果数量"
    )
    
    execution_time: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="执行时间(毫秒)"
    )
    
    is_saved: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        comment="是否保存"
    )
    
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        server_default=func.now(),
        comment="创建时间"
    )
    
    # 关系
    resource: Mapped["DataResource"] = relationship(
        "DataResource",
        back_populates="query_history"
    )
    
    user: Mapped["User"] = relationship("User")


class DataResourceTag(Base, TimestampMixin, UserMixin):
    """数据资源标签模型"""
    
    __tablename__ = "acwl_data_resource_tags"
    __table_args__ = {"comment": "数据资源标签表"}
    
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="标签ID"
    )
    
    name: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        unique=True,
        comment="标签名称"
    )
    
    color: Mapped[str] = mapped_column(
        String(30),
        default="#409EFF",
        comment="标签颜色"
    )
    
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="标签描述"
    )
    
    usage_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        comment="使用次数"
    )
    
    status: Mapped[TagStatus] = mapped_column(
        Enum(TagStatus),
        default=TagStatus.ACTIVE,
        comment="标签状态"
    )
    
    # 关系
    tag_relations: Mapped[List["DataResourceTagRelation"]] = relationship(
        "DataResourceTagRelation",
        back_populates="tag",
        cascade="all, delete-orphan"
    )


class DataResourceTagRelation(Base):
    """数据资源标签关联模型"""
    
    __tablename__ = "acwl_data_resource_tag_relations"
    __table_args__ = {"comment": "数据资源标签关联表"}
    
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="关联ID"
    )
    
    resource_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("acwl_data_resources.id", ondelete="CASCADE"),
        nullable=False,
        comment="资源ID"
    )
    
    tag_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("acwl_data_resource_tags.id", ondelete="CASCADE"),
        nullable=False,
        comment="标签ID"
    )
    
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        server_default=func.now(),
        comment="创建时间"
    )
    
    # 关系
    resource: Mapped["DataResource"] = relationship(
        "DataResource",
        back_populates="tag_relations"
    )
    
    tag: Mapped["DataResourceTag"] = relationship(
        "DataResourceTag",
        back_populates="tag_relations"
    )