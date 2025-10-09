"""
角色相关的Pydantic schemas
用于API接口的数据验证和序列化
"""
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class RoleBase(BaseModel):
    """角色基础模型"""
    name: str = Field(..., description="角色名称", max_length=50)
    code: str = Field(..., description="角色代码", max_length=50)
    description: Optional[str] = Field(None, description="角色描述")
    status: bool = Field(True, description="状态：True-启用，False-禁用")


class RoleCreate(RoleBase):
    """创建角色的请求模型"""
    pass


class RoleUpdate(BaseModel):
    """更新角色的请求模型"""
    name: Optional[str] = Field(None, description="角色名称", max_length=50)
    description: Optional[str] = Field(None, description="角色描述")
    status: Optional[bool] = Field(None, description="状态：True-启用，False-禁用")


class RoleResponse(RoleBase):
    """角色响应模型"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int = Field(..., description="角色ID")
    is_system: bool = Field(..., description="是否为系统角色")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    created_by: Optional[int] = Field(None, description="创建者ID")
    updated_by: Optional[int] = Field(None, description="更新者ID")
    user_count: int = Field(0, description="拥有此角色的用户数量")
    permission_count: int = Field(0, description="此角色拥有的权限数量")


class RoleListResponse(BaseModel):
    """角色列表响应模型"""
    total: int = Field(..., description="总数量")
    items: List[RoleResponse] = Field(..., description="角色列表")


class UserRoleBase(BaseModel):
    """用户角色关联基础模型"""
    user_id: int = Field(..., description="用户ID")
    role_id: int = Field(..., description="角色ID")


class UserRoleCreate(UserRoleBase):
    """创建用户角色关联的请求模型"""
    pass


class UserRoleResponse(UserRoleBase):
    """用户角色关联响应模型"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int = Field(..., description="关联ID")
    created_at: datetime = Field(..., description="创建时间")
    created_by: Optional[int] = Field(None, description="创建者ID")


class RolePermissionBase(BaseModel):
    """角色权限关联基础模型"""
    role_id: int = Field(..., description="角色ID")
    permission_id: int = Field(..., description="权限ID")


class RolePermissionCreate(RolePermissionBase):
    """创建角色权限关联的请求模型"""
    pass


class RolePermissionBatchCreate(BaseModel):
    """批量创建角色权限关联的请求模型"""
    role_id: int = Field(..., description="角色ID")
    permission_ids: List[int] = Field(..., description="权限ID列表")


class RolePermissionResponse(RolePermissionBase):
    """角色权限关联响应模型"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int = Field(..., description="关联ID")
    created_at: datetime = Field(..., description="创建时间")
    created_by: Optional[int] = Field(None, description="创建者ID")


class RoleWithPermissions(RoleResponse):
    """包含权限信息的角色响应模型"""
    permissions: List["PermissionResponse"] = Field([], description="角色拥有的权限列表")


class UserWithRoles(BaseModel):
    """包含角色信息的用户响应模型"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int = Field(..., description="用户ID")
    username: str = Field(..., description="用户名")
    email: str = Field(..., description="邮箱")
    roles: List[RoleResponse] = Field([], description="用户拥有的角色列表")


# 为了避免循环导入，在文件末尾导入Permission相关的schema
from .permission import PermissionResponse
RoleWithPermissions.model_rebuild()