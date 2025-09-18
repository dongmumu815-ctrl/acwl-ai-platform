"""资源包数据模型"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import Column, Integer, String, Text, Enum, Boolean, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class ResourcePackage(Base):
    """资源包模型"""
    __tablename__ = "resource_packages"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, comment="资源包名称")
    description = Column(Text, comment="资源包描述")
    type = Column(Enum('sql', 'elasticsearch', name='package_type'), nullable=False, comment="资源包类型")
    datasource_id = Column(Integer, ForeignKey("acwl_datasources.id", ondelete="CASCADE"), nullable=False, comment="数据源ID")
    resource_id = Column(Integer, ForeignKey("acwl_data_resources.id", ondelete="SET NULL"), comment="数据资源ID")
    base_config = Column(JSON, comment="基础配置(schema, table, fields等)")
    locked_conditions = Column(JSON, comment="锁定条件配置")
    dynamic_conditions = Column(JSON, comment="动态条件配置")
    order_config = Column(JSON, comment="排序配置")
    limit_config = Column(Integer, default=1000, comment="默认限制条数")
    is_active = Column(Boolean, default=True, comment="是否启用")
    created_by = Column(Integer, ForeignKey("acwl_users.id", ondelete="CASCADE"), nullable=False, comment="创建者ID")
    created_at = Column(DateTime, default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), comment="更新时间")

    # 关联关系
    datasource = relationship("Datasource", back_populates="resource_packages")
    resource = relationship("DataResource", back_populates="packages")
    creator = relationship("User", foreign_keys=[created_by], back_populates="created_resource_packages")
    permissions = relationship("ResourcePackagePermission", back_populates="package", cascade="all, delete-orphan")
    query_histories = relationship("ResourcePackageQueryHistory", back_populates="package", cascade="all, delete-orphan")
    tags = relationship("ResourcePackageTag", back_populates="package", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<ResourcePackage(id={self.id}, name='{self.name}', type='{self.type}')>"


class ResourcePackagePermission(Base):
    """资源包权限模型"""
    __tablename__ = "resource_package_permissions"

    id = Column(Integer, primary_key=True, index=True)
    package_id = Column(Integer, ForeignKey("resource_packages.id", ondelete="CASCADE"), nullable=False, comment="资源包ID")
    user_id = Column(Integer, ForeignKey("acwl_users.id", ondelete="CASCADE"), nullable=False, comment="用户ID")
    permission_type = Column(Enum('read', 'write', 'admin', name='permission_type'), nullable=False, comment="权限类型")
    granted_by = Column(Integer, ForeignKey("acwl_users.id", ondelete="CASCADE"), nullable=False, comment="授权者ID")
    granted_at = Column(DateTime, default=func.now(), comment="授权时间")
    expires_at = Column(DateTime, comment="过期时间")
    is_active = Column(Boolean, default=True, comment="是否有效")

    # 关联关系
    package = relationship("ResourcePackage", back_populates="permissions")
    user = relationship("User", foreign_keys=[user_id], back_populates="resource_package_permissions")
    granter = relationship("User", foreign_keys=[granted_by], back_populates="granted_resource_package_permissions")

    def __repr__(self):
        return f"<ResourcePackagePermission(package_id={self.package_id}, user_id={self.user_id}, type='{self.permission_type}')>"


class ResourcePackageQueryHistory(Base):
    """资源包查询历史模型"""
    __tablename__ = "resource_package_query_history"

    id = Column(Integer, primary_key=True, index=True)
    package_id = Column(Integer, ForeignKey("resource_packages.id", ondelete="CASCADE"), nullable=False, comment="资源包ID")
    user_id = Column(Integer, ForeignKey("acwl_users.id", ondelete="CASCADE"), nullable=False, comment="查询用户ID")
    dynamic_params = Column(JSON, comment="动态参数值")
    generated_query = Column(Text, comment="生成的查询语句")
    result_count = Column(Integer, default=0, comment="结果行数")
    execution_time = Column(Integer, default=0, comment="执行时间(毫秒)")
    status = Column(Enum('success', 'error', 'timeout', name='query_status'), default='success', comment="执行状态")
    error_message = Column(Text, comment="错误信息")
    created_at = Column(DateTime, default=func.now(), comment="创建时间")

    # 关联关系
    package = relationship("ResourcePackage", back_populates="query_histories")
    user = relationship("User", back_populates="resource_package_query_histories")

    def __repr__(self):
        return f"<ResourcePackageQueryHistory(id={self.id}, package_id={self.package_id}, status='{self.status}')>"


class ResourcePackageTag(Base):
    """资源包标签模型"""
    __tablename__ = "resource_package_tags"

    id = Column(Integer, primary_key=True, index=True)
    package_id = Column(Integer, ForeignKey("resource_packages.id", ondelete="CASCADE"), nullable=False, comment="资源包ID")
    tag_name = Column(String(100), nullable=False, comment="标签名称")
    tag_color = Column(String(20), default="#409EFF", comment="标签颜色")
    created_at = Column(DateTime, default=func.now(), comment="创建时间")

    # 关联关系
    package = relationship("ResourcePackage", back_populates="tags")

    def __repr__(self):
        return f"<ResourcePackageTag(package_id={self.package_id}, tag_name='{self.tag_name}')>"