"""资源包数据模型"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import Column, Integer, String, Text, Enum, Boolean, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class ResourcePackage(Base):
    """资源包模型（优化版）"""
    __tablename__ = "resource_packages"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, comment="资源包名称")
    description = Column(Text, comment="资源包描述")
    type = Column(Enum('sql', 'elasticsearch', name='package_type'), nullable=False, comment="资源包类型")
    
    # 核心关联字段
    template_id = Column(Integer, nullable=True, comment="关联的查询模板ID")
    template_type = Column(Enum('sql', 'elasticsearch', name='template_type'), nullable=False, comment="模板类型")
    dynamic_params = Column(JSON, comment="动态参数配置，用于覆盖模板中的参数")
    
    # 保留的业务字段（用于快速筛选和权限控制）
    datasource_id = Column(Integer, ForeignKey("acwl_datasources.id", ondelete="CASCADE"), nullable=False, comment="数据源ID（冗余字段，用于快速筛选）")
    resource_id = Column(Integer, ForeignKey("acwl_data_resources.id", ondelete="SET NULL"), comment="数据资源ID（业务关联）")
    
    # 系统字段
    is_active = Column(Boolean, default=True, comment="是否启用")
    is_lock = Column(String(1), default="0", comment="是否锁定（禁止删除）0-否，1-是")
    created_by = Column(Integer, ForeignKey("acwl_users.id", ondelete="CASCADE"), nullable=False, comment="创建者ID")
    created_at = Column(DateTime, default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), comment="更新时间")
    
    # 下载/生成相关字段
    download_time = Column(DateTime, nullable=True, comment="最后下载时间")
    download_url = Column(String(500), nullable=True, comment="MinIO对象路径（minio://host/bucket/object）")
    excel_time = Column(DateTime, nullable=True, comment="最后Excel生成时间")

    # 关联关系
    datasource = relationship("Datasource", back_populates="resource_packages")
    resource = relationship("DataResource", back_populates="packages")
    creator = relationship("User", foreign_keys=[created_by], back_populates="created_resource_packages")
    permissions = relationship("ResourcePackagePermission", back_populates="package", cascade="all, delete-orphan")
    query_histories = relationship("ResourcePackageQueryHistory", back_populates="package", cascade="all, delete-orphan")
    tags = relationship("ResourcePackageTag", back_populates="package", cascade="all, delete-orphan")
    files = relationship("ResourcePackageFile", back_populates="package", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<ResourcePackage(id={self.id}, name='{self.name}', type='{self.type}', template_id={self.template_id})>"

    @property
    def template(self):
        """获取关联的查询模板"""
        from app.core.database import SessionLocal
        
        if self.template_type == 'sql':
            from app.models.sql_query_template import SQLQueryTemplate
            with SessionLocal() as db:
                return db.query(SQLQueryTemplate).filter(SQLQueryTemplate.id == self.template_id).first()
        elif self.template_type == 'elasticsearch':
            from app.models.es_query_template import ESQueryTemplate
            with SessionLocal() as db:
                return db.query(ESQueryTemplate).filter(ESQueryTemplate.id == self.template_id).first()
        return None

    def get_query_content(self) -> Optional[str]:
        """获取查询内容"""
        template = self.template
        if not template:
            return None
        
        if self.template_type == 'sql':
            return getattr(template, 'query', None)
        elif self.template_type == 'elasticsearch':
            return getattr(template, 'query', None)
        
        return None

    def get_effective_params(self, request_params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """获取有效的动态参数
        
        Args:
            request_params: 请求中的参数
            
        Returns:
            Dict[str, Any]: 合并后的有效参数
        """
        effective_params = {}
        
        # 首先使用资源包的动态参数
        if self.dynamic_params:
            effective_params.update(self.dynamic_params)
        
        # 然后使用请求中的参数覆盖
        if request_params:
            effective_params.update(request_params)
        
        return effective_params


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


class ResourcePackageFile(Base):
    """资源包Excel文件历史模型"""
    __tablename__ = "resource_package_files"

    id = Column(Integer, primary_key=True, index=True)
    package_id = Column(Integer, ForeignKey("resource_packages.id", ondelete="CASCADE"), nullable=False, comment="资源包ID")
    filename = Column(String(255), nullable=False, comment="文件名")
    object_path = Column(String(500), nullable=False, comment="MinIO对象路径")
    generated_at = Column(DateTime, default=func.now(), comment="生成时间")

    # 关联关系
    package = relationship("ResourcePackage", back_populates="files")

    def __repr__(self):
        return f"<ResourcePackageFile(id={self.id}, package_id={self.package_id}, filename='{self.filename}')>"