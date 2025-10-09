"""
权限相关的Pydantic schemas
用于API接口的数据验证和序列化
"""
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class PermissionBase(BaseModel):
    """权限基础模型"""
    name: str = Field(..., description="权限名称", max_length=100)
    code: str = Field(..., description="权限代码", max_length=100)
    description: Optional[str] = Field(None, description="权限描述")
    module: str = Field(..., description="所属模块", max_length=50)
    resource: Optional[str] = Field(None, description="资源标识", max_length=100)
    action: str = Field(..., description="操作类型", max_length=50)
    status: bool = Field(True, description="状态：True-启用，False-禁用")
    sort_order: int = Field(0, description="排序顺序")


class PermissionCreate(PermissionBase):
    """创建权限的请求模型"""
    pass


class PermissionUpdate(BaseModel):
    """更新权限的请求模型"""
    name: Optional[str] = Field(None, description="权限名称", max_length=100)
    description: Optional[str] = Field(None, description="权限描述")
    module: Optional[str] = Field(None, description="所属模块", max_length=50)
    resource: Optional[str] = Field(None, description="资源标识", max_length=100)
    action: Optional[str] = Field(None, description="操作类型", max_length=50)
    status: Optional[bool] = Field(None, description="状态：True-启用，False-禁用")
    sort_order: Optional[int] = Field(None, description="排序顺序")


class PermissionResponse(PermissionBase):
    """权限响应模型"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int = Field(..., description="权限ID")
    is_system: bool = Field(..., description="是否为系统权限")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    created_by: Optional[int] = Field(None, description="创建者ID")
    updated_by: Optional[int] = Field(None, description="更新者ID")
    role_count: int = Field(0, description="拥有此权限的角色数量")


class PermissionListResponse(BaseModel):
    """权限列表响应模型"""
    total: int = Field(..., description="总数量")
    items: List[PermissionResponse] = Field(..., description="权限列表")


class PermissionTreeNode(BaseModel):
    """权限树节点模型"""
    id: int = Field(..., description="权限ID")
    name: str = Field(..., description="权限名称")
    code: str = Field(..., description="权限代码")
    module: str = Field(..., description="所属模块")
    resource: Optional[str] = Field(None, description="资源标识")
    action: str = Field(..., description="操作类型")
    is_system: bool = Field(..., description="是否为系统权限")
    status: bool = Field(..., description="状态")
    sort_order: int = Field(..., description="排序顺序")
    role_count: int = Field(0, description="拥有此权限的角色数量")


class PermissionTreeResponse(BaseModel):
    """权限树响应模型"""
    module: str = Field(..., description="模块名称")
    permissions: List[PermissionTreeNode] = Field(..., description="模块下的权限列表")


class PermissionTreeListResponse(BaseModel):
    """权限树列表响应模型"""
    modules: List[PermissionTreeResponse] = Field(..., description="所有模块的权限树")


class PermissionModuleResponse(BaseModel):
    """权限模块响应模型"""
    modules: List[str] = Field(..., description="所有模块列表")


class PermissionWithRoles(PermissionResponse):
    """包含角色信息的权限响应模型"""
    roles: List["RoleResponse"] = Field([], description="拥有此权限的角色列表")


class UserPermissionResponse(BaseModel):
    """用户权限响应模型"""
    user_id: int = Field(..., description="用户ID")
    username: str = Field(..., description="用户名")
    permissions: List[PermissionResponse] = Field([], description="用户拥有的权限列表")
    permission_codes: List[str] = Field([], description="用户拥有的权限代码列表")


# 为了避免循环导入，在文件末尾导入Role相关的schema
from .role import RoleResponse
PermissionWithRoles.model_rebuild()