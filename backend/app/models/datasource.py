#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据源相关模型
"""

from sqlalchemy import Integer, String, Text, Boolean, TIMESTAMP, JSON, Enum, Date, BigInteger, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from typing import List, Optional, TYPE_CHECKING
from enum import Enum as PyEnum
from datetime import datetime, date

from app.core.database import Base, TimestampMixin, UserMixin

if TYPE_CHECKING:
    from .user import User


class DatasourceType(str, PyEnum):
    """数据源类型枚举"""
    MYSQL = "mysql"
    DORIS = "doris"
    ORACLE = "oracle"
    POSTGRESQL = "postgresql"
    SQLSERVER = "sqlserver"
    CLICKHOUSE = "clickhouse"
    MONGODB = "mongodb"
    REDIS = "redis"
    ELASTICSEARCH = "elasticsearch"
    MINIO = "minio"


class DatasourceStatus(str, PyEnum):
    """数据源状态枚举"""
    ACTIVE = "active"          # 激活
    INACTIVE = "inactive"      # 未激活
    TESTING = "testing"        # 测试中
    ERROR = "error"            # 错误


class TestResult(str, PyEnum):
    """测试结果枚举"""
    SUCCESS = "success"        # 成功
    FAILED = "failed"          # 失败


class PermissionType(str, PyEnum):
    """权限类型枚举"""
    READ = "read"              # 只读
    WRITE = "write"            # 读写
    ADMIN = "admin"            # 管理员


class Datasource(Base, TimestampMixin, UserMixin):
    """数据源模型"""
    
    __tablename__ = "acwl_datasources"
    __table_args__ = {"comment": "数据源表，存储各种类型数据库的连接配置信息"}
    
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="数据源ID，自增主键"
    )
    
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="数据源名称"
    )
    
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="数据源描述"
    )
    
    datasource_type: Mapped[DatasourceType] = mapped_column(
        Enum(DatasourceType),
        nullable=False,
        comment="数据源类型"
    )
    
    host: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="主机地址"
    )
    
    port: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="端口号"
    )
    
    database_name: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="数据库名称"
    )
    
    username: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="用户名"
    )
    
    password: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="密码（加密存储）"
    )
    
    connection_params: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="连接参数，如SSL配置、超时设置等"
    )
    
    pool_config: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="连接池配置"
    )
    
    status: Mapped[DatasourceStatus] = mapped_column(
        Enum(DatasourceStatus),
        nullable=False,
        default=DatasourceStatus.INACTIVE,
        comment="数据源状态：激活、未激活、测试中、错误"
    )
    
    last_test_time: Mapped[Optional[datetime]] = mapped_column(
        TIMESTAMP,
        nullable=True,
        comment="最后测试时间"
    )
    
    last_test_result: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="最后测试结果"
    )
    
    is_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        comment="是否启用"
    )
    
    # 关系
    test_logs: Mapped[List["DatasourceTestLog"]] = relationship(
        "DatasourceTestLog",
        back_populates="datasource",
        cascade="all, delete-orphan"
    )
    
    usage_stats: Mapped[List["DatasourceUsageStats"]] = relationship(
        "DatasourceUsageStats",
        back_populates="datasource",
        cascade="all, delete-orphan"
    )
    
    permissions: Mapped[List["DatasourcePermission"]] = relationship(
        "DatasourcePermission",
        back_populates="datasource",
        cascade="all, delete-orphan"
    )
    
    creator: Mapped["User"] = relationship(
        "User",
        foreign_keys="[Datasource.created_by]",
        back_populates="datasources"
    )
    
    project_associations: Mapped[List["ProjectDatasource"]] = relationship(
        "ProjectDatasource",
        back_populates="datasource",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<Datasource(id={self.id}, name='{self.name}', type='{self.datasource_type}', status='{self.status}')>"
    
    @property
    def connection_url(self) -> str:
        """生成连接URL"""
        # 根据数据源类型生成相应的连接URL
        if self.datasource_type == DatasourceType.MYSQL:
            return f"mysql+pymysql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database_name}"
        elif self.datasource_type == DatasourceType.POSTGRESQL:
            return f"postgresql+psycopg2://{self.username}:{self.password}@{self.host}:{self.port}/{self.database_name}"
        elif self.datasource_type == DatasourceType.ORACLE:
            return f"oracle+cx_oracle://{self.username}:{self.password}@{self.host}:{self.port}/{self.database_name}"
        elif self.datasource_type == DatasourceType.SQLSERVER:
            return f"mssql+pyodbc://{self.username}:{self.password}@{self.host}:{self.port}/{self.database_name}"
        elif self.datasource_type == DatasourceType.CLICKHOUSE:
            return f"clickhouse+native://{self.username}:{self.password}@{self.host}:{self.port}/{self.database_name}"
        elif self.datasource_type == DatasourceType.MONGODB:
            return f"mongodb://{self.username}:{self.password}@{self.host}:{self.port}/{self.database_name}"
        elif self.datasource_type == DatasourceType.REDIS:
            return f"redis://{self.username}:{self.password}@{self.host}:{self.port}/{self.database_name or '0'}"
        elif self.datasource_type == DatasourceType.ELASTICSEARCH:
            return f"http://{self.host}:{self.port}"
        else:
            return f"{self.datasource_type}://{self.username}:{self.password}@{self.host}:{self.port}/{self.database_name}"


class DatasourceTestLog(Base, TimestampMixin):
    """数据源连接测试日志模型"""
    
    __tablename__ = "acwl_datasource_test_logs"
    __table_args__ = {"comment": "数据源连接测试日志表，记录数据源连接测试的历史记录"}
    
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="测试日志ID，自增主键"
    )
    
    datasource_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("acwl_datasources.id", ondelete="CASCADE"),
        nullable=False,
        comment="数据源ID"
    )
    
    test_time: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        server_default=func.current_timestamp(),
        comment="测试时间"
    )
    
    test_result: Mapped[TestResult] = mapped_column(
        Enum(TestResult),
        nullable=False,
        comment="测试结果：成功、失败"
    )
    
    response_time: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="响应时间（毫秒）"
    )
    
    error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="错误信息"
    )
    
    test_details: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="测试详情"
    )
    
    tested_by: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="测试者ID"
    )
    
    # 关系
    datasource: Mapped["Datasource"] = relationship(
        "Datasource",
        back_populates="test_logs"
    )
    
    def __repr__(self) -> str:
        return f"<DatasourceTestLog(id={self.id}, datasource_id={self.datasource_id}, result='{self.test_result}')>"


class DatasourceUsageStats(Base, TimestampMixin):
    """数据源使用统计模型"""
    
    __tablename__ = "acwl_datasource_usage_stats"
    __table_args__ = {"comment": "数据源使用统计表，记录数据源的使用情况和性能指标"}
    
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="统计ID，自增主键"
    )
    
    datasource_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("acwl_datasources.id", ondelete="CASCADE"),
        nullable=False,
        comment="数据源ID"
    )
    
    date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment="统计日期"
    )
    
    connection_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        comment="连接次数"
    )
    
    query_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        comment="查询次数"
    )
    
    total_response_time: Mapped[int] = mapped_column(
        BigInteger,
        default=0,
        comment="总响应时间（毫秒）"
    )
    
    error_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        comment="错误次数"
    )
    
    # 关系
    datasource: Mapped["Datasource"] = relationship(
        "Datasource",
        back_populates="usage_stats"
    )
    
    def __repr__(self) -> str:
        return f"<DatasourceUsageStats(id={self.id}, datasource_id={self.datasource_id}, date={self.date})>"
    
    @property
    def average_response_time(self) -> float:
        """平均响应时间"""
        if self.query_count > 0:
            return self.total_response_time / self.query_count
        return 0.0


class DatasourcePermission(Base):
    """数据源权限模型"""
    
    __tablename__ = "acwl_datasource_permissions"
    __table_args__ = {"comment": "数据源权限表，管理用户对数据源的访问权限"}
    
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="权限ID，自增主键"
    )
    
    datasource_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("acwl_datasources.id", ondelete="CASCADE"),
        nullable=False,
        comment="数据源ID"
    )
    
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("acwl_users.id", ondelete="CASCADE"),
        nullable=False,
        comment="用户ID"
    )
    
    permission_type: Mapped[PermissionType] = mapped_column(
        Enum(PermissionType),
        nullable=False,
        comment="权限类型：只读、读写、管理员"
    )
    
    granted_by: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="授权者ID"
    )
    
    granted_at: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        server_default=func.current_timestamp(),
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
        comment="是否激活"
    )
    
    # 关系
    datasource: Mapped["Datasource"] = relationship(
        "Datasource",
        back_populates="permissions"
    )
    
    user: Mapped["User"] = relationship(
        "User",
        foreign_keys=[user_id],
        back_populates="datasource_permissions"
    )
    
    def __repr__(self) -> str:
        return f"<DatasourcePermission(id={self.id}, datasource_id={self.datasource_id}, user_id={self.user_id}, permission='{self.permission_type}')>"
    
    @property
    def is_expired(self) -> bool:
        """是否已过期"""
        if self.expires_at is None:
            return False
        return datetime.now() > self.expires_at


class DatasourceTemplate(Base, TimestampMixin, UserMixin):
    """数据源配置模板模型"""
    
    __tablename__ = "acwl_datasource_templates"
    __table_args__ = {"comment": "数据源配置模板表，存储不同数据库类型的默认配置模板"}
    
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
    
    datasource_type: Mapped[DatasourceType] = mapped_column(
        Enum(DatasourceType),
        nullable=False,
        comment="数据源类型"
    )
    
    default_port: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="默认端口"
    )
    
    default_params: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="默认连接参数"
    )
    
    connection_url_template: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="连接URL模板"
    )
    
    driver_class: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
        comment="驱动类名"
    )
    
    validation_query: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
        comment="验证查询语句"
    )
    
    is_system: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        comment="是否系统模板"
    )
    
    def __repr__(self) -> str:
        return f"<DatasourceTemplate(id={self.id}, name='{self.name}', type='{self.datasource_type}')>"