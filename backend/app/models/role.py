"""
角色模型
定义角色相关的数据结构和关系
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Role(Base):
    """角色模型"""
    __tablename__ = "acwl_roles"

    id = Column(Integer, primary_key=True, index=True, comment="角色ID")
    name = Column(String(50), unique=True, nullable=False, comment="角色名称")
    code = Column(String(50), unique=True, nullable=False, comment="角色代码")
    description = Column(Text, comment="角色描述")
    is_system = Column(Boolean, default=False, nullable=False, comment="是否为系统角色")
    status = Column(Boolean, default=True, nullable=False, comment="状态：True-启用，False-禁用")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")
    created_by = Column(Integer, ForeignKey("acwl_users.id"), comment="创建者ID")
    updated_by = Column(Integer, ForeignKey("acwl_users.id"), comment="更新者ID")

    # 关系定义
    user_roles = relationship("UserRole", back_populates="role", cascade="all, delete-orphan")
    role_permissions = relationship("RolePermission", back_populates="role", cascade="all, delete-orphan")
    creator = relationship("User", foreign_keys=[created_by], backref="created_roles")
    updater = relationship("User", foreign_keys=[updated_by], backref="updated_roles")

    def __repr__(self):
        return f"<Role(id={self.id}, name='{self.name}', code='{self.code}')>"

    @property
    def user_count(self):
        """获取拥有此角色的用户数量"""
        return len(self.user_roles)

    @property
    def permission_count(self):
        """获取此角色拥有的权限数量"""
        return len(self.role_permissions)

    def has_permission(self, permission_code: str) -> bool:
        """检查角色是否拥有指定权限"""
        for role_permission in self.role_permissions:
            if role_permission.permission.code == permission_code:
                return True
        return False

    def get_permissions(self):
        """获取角色的所有权限"""
        return [rp.permission for rp in self.role_permissions if rp.permission.status]

    def get_permission_codes(self):
        """获取角色的所有权限代码"""
        return [rp.permission.code for rp in self.role_permissions if rp.permission.status]

    @property
    def permissions(self):
        """角色权限列表属性
        说明：为Pydantic模型（如RoleWithPermissions）提供可序列化的`permissions`字段，
        以便通过`from_attributes=True`正确映射到权限响应模型。
        返回值：启用状态的`Permission`对象列表。
        """
        return self.get_permissions()


class UserRole(Base):
    """用户角色关联模型"""
    __tablename__ = "acwl_user_roles"

    id = Column(Integer, primary_key=True, index=True, comment="关联ID")
    user_id = Column(Integer, ForeignKey("acwl_users.id"), nullable=False, comment="用户ID")
    role_id = Column(Integer, ForeignKey("acwl_roles.id"), nullable=False, comment="角色ID")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    created_by = Column(Integer, ForeignKey("acwl_users.id"), comment="创建者ID")

    # 关系定义
    user = relationship("User", foreign_keys=[user_id], back_populates="user_roles")
    role = relationship("Role", back_populates="user_roles")
    creator = relationship("User", foreign_keys=[created_by], backref="created_user_roles")

    def __repr__(self):
        return f"<UserRole(id={self.id}, user_id={self.user_id}, role_id={self.role_id})>"


class RolePermission(Base):
    """角色权限关联模型"""
    __tablename__ = "acwl_role_permissions"

    id = Column(Integer, primary_key=True, index=True, comment="关联ID")
    role_id = Column(Integer, ForeignKey("acwl_roles.id"), nullable=False, comment="角色ID")
    permission_id = Column(Integer, ForeignKey("acwl_permissions.id"), nullable=False, comment="权限ID")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    created_by = Column(Integer, ForeignKey("acwl_users.id"), comment="创建者ID")

    # 关系定义
    role = relationship("Role", back_populates="role_permissions")
    permission = relationship("Permission", back_populates="role_permissions")
    creator = relationship("User", foreign_keys=[created_by], backref="created_role_permissions")

    def __repr__(self):
        return f"<RolePermission(id={self.id}, role_id={self.role_id}, permission_id={self.permission_id})>"