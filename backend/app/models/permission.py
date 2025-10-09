"""
权限模型
定义权限相关的数据结构和关系
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Permission(Base):
    """权限模型"""
    __tablename__ = "acwl_permissions"

    id = Column(Integer, primary_key=True, index=True, comment="权限ID")
    name = Column(String(100), nullable=False, comment="权限名称")
    code = Column(String(100), unique=True, nullable=False, comment="权限代码")
    description = Column(Text, comment="权限描述")
    module = Column(String(50), nullable=False, comment="所属模块")
    resource = Column(String(100), comment="资源标识")
    action = Column(String(50), nullable=False, comment="操作类型")
    is_system = Column(Boolean, default=False, nullable=False, comment="是否为系统权限")
    status = Column(Boolean, default=True, nullable=False, comment="状态：True-启用，False-禁用")
    sort_order = Column(Integer, default=0, comment="排序顺序")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")
    created_by = Column(Integer, ForeignKey("acwl_users.id"), comment="创建者ID")
    updated_by = Column(Integer, ForeignKey("acwl_users.id"), comment="更新者ID")

    # 关系定义
    role_permissions = relationship("RolePermission", back_populates="permission", cascade="all, delete-orphan")
    creator = relationship("User", foreign_keys=[created_by], backref="created_permissions")
    updater = relationship("User", foreign_keys=[updated_by], backref="updated_permissions")

    def __repr__(self):
        return f"<Permission(id={self.id}, name='{self.name}', code='{self.code}')>"

    @property
    def role_count(self):
        """获取拥有此权限的角色数量"""
        return len(self.role_permissions)

    def get_roles(self):
        """获取拥有此权限的所有角色"""
        return [rp.role for rp in self.role_permissions if rp.role.status]

    def get_role_codes(self):
        """获取拥有此权限的所有角色代码"""
        return [rp.role.code for rp in self.role_permissions if rp.role.status]

    @classmethod
    def get_by_module(cls, session, module: str):
        """根据模块获取权限列表"""
        return session.query(cls).filter(cls.module == module, cls.status == True).order_by(cls.sort_order).all()

    @classmethod
    def get_by_resource_action(cls, session, resource: str, action: str):
        """根据资源和操作获取权限"""
        return session.query(cls).filter(
            cls.resource == resource,
            cls.action == action,
            cls.status == True
        ).first()

    @classmethod
    def get_system_permissions(cls, session):
        """获取所有系统权限"""
        return session.query(cls).filter(cls.is_system == True, cls.status == True).order_by(cls.module, cls.sort_order).all()

    @classmethod
    def get_custom_permissions(cls, session):
        """获取所有自定义权限"""
        return session.query(cls).filter(cls.is_system == False, cls.status == True).order_by(cls.module, cls.sort_order).all()

    def to_dict(self):
        """转换为字典格式"""
        return {
            "id": self.id,
            "name": self.name,
            "code": self.code,
            "description": self.description,
            "module": self.module,
            "resource": self.resource,
            "action": self.action,
            "is_system": self.is_system,
            "status": self.status,
            "sort_order": self.sort_order,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "role_count": self.role_count
        }