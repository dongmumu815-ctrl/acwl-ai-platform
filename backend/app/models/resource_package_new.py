"""资源包数据模型 - 重构版本"""

from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from sqlalchemy import Column, Integer, String, Text, Enum, Boolean, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship, validates
from sqlalchemy.sql import func

from app.core.database import Base


class ResourcePackage(Base):
    """资源包模型 - 重构版本
    
    通过关联查询模板来避免数据冗余，提高数据一致性
    """
    __tablename__ = "resource_packages"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, comment="资源包名称")
    description = Column(Text, comment="资源包描述")
    type = Column(Enum('sql', 'elasticsearch', name='package_type'), nullable=False, comment="资源包类型")
    
    # 关联查询模板
    template_id = Column(Integer, nullable=True, comment="关联的查询模板ID")
    template_type = Column(Enum('sql', 'elasticsearch', name='template_type'), nullable=False, comment="模板类型")
    
    # 动态参数配置，用于覆盖模板中的默认参数
    dynamic_params = Column(JSON, comment="动态参数配置，用于覆盖模板中的参数")
    
    # 保留的原有字段
    datasource_id = Column(Integer, ForeignKey("acwl_datasources.id", ondelete="CASCADE"), nullable=False, comment="数据源ID")
    resource_id = Column(Integer, ForeignKey("acwl_data_resources.id", ondelete="SET NULL"), comment="数据资源ID")
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

    @validates('template_type', 'type')
    def validate_template_type(self, key, value):
        """验证模板类型与资源包类型一致"""
        if key == 'template_type' and hasattr(self, 'type') and self.type:
            if value != self.type:
                raise ValueError(f"模板类型 {value} 与资源包类型 {self.type} 不匹配")
        elif key == 'type' and hasattr(self, 'template_type') and self.template_type:
            if value != self.template_type:
                raise ValueError(f"资源包类型 {value} 与模板类型 {self.template_type} 不匹配")
        return value

    @property
    def template(self) -> Union["SQLQueryTemplate", "ESQueryTemplate", None]:
        """获取关联的查询模板"""
        if self.template_type == 'sql':
            from app.models.sql_query_template import SQLQueryTemplate
            from app.core.database import SessionLocal
            
            with SessionLocal() as db:
                return db.query(SQLQueryTemplate).filter(SQLQueryTemplate.id == self.template_id).first()
        elif self.template_type == 'elasticsearch':
            from app.models.es_query_template import ESQueryTemplate
            from app.core.database import SessionLocal
            
            with SessionLocal() as db:
                return db.query(ESQueryTemplate).filter(ESQueryTemplate.id == self.template_id).first()
        return None

    def get_effective_config(self) -> Dict[str, Any]:
        """获取有效的配置信息
        
        合并模板配置和动态参数配置
        
        Returns:
            Dict[str, Any]: 合并后的配置信息
        """
        template = self.template
        if not template:
            return self.dynamic_params or {}
        
        # 获取模板的配置
        template_config = getattr(template, 'config', {}) or {}
        
        # 合并动态参数
        effective_config = template_config.copy()
        if self.dynamic_params:
            effective_config.update(self.dynamic_params)
        
        return effective_config

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

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        template = self.template
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "type": self.type,
            "templateId": self.template_id,
            "templateType": self.template_type,
            "templateName": template.name if template else None,
            "dynamicParams": self.dynamic_params or {},
            "datasourceId": self.datasource_id,
            "resourceId": self.resource_id,
            "isActive": self.is_active,
            "createdBy": self.created_by,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
            "updatedAt": self.updated_at.isoformat() if self.updated_at else None,
            "effectiveConfig": self.get_effective_config(),
            "queryContent": self.get_query_content()
        }

    def __repr__(self):
        return f"<ResourcePackage(id={self.id}, name='{self.name}', type='{self.type}', template_id={self.template_id})>"


# 其他关联模型保持不变
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