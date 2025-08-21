#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
安全相关工具函数
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from cryptography.fernet import Fernet
import base64
import hashlib

from .config import settings

# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """获取密码哈希值"""
    return pwd_context.hash(password)


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """创建访问令牌"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    
    return encoded_jwt


def decode_access_token(token: str) -> Dict[str, Any]:
    """解码访问令牌"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        raise ValueError("无效的令牌")


def create_refresh_token(data: Dict[str, Any]) -> str:
    """创建刷新令牌"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def verify_refresh_token(token: str) -> Dict[str, Any]:
    """验证刷新令牌"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if payload.get("type") != "refresh":
            raise ValueError("无效的刷新令牌")
        return payload
    except JWTError:
        raise ValueError("无效的刷新令牌")


def generate_api_key() -> str:
    """生成API密钥"""
    import secrets
    import string
    
    # 生成32位随机字符串
    alphabet = string.ascii_letters + string.digits
    api_key = ''.join(secrets.choice(alphabet) for _ in range(32))
    
    return f"acwl_{api_key}"


def hash_api_key(api_key: str) -> str:
    """哈希API密钥"""
    return get_password_hash(api_key)


def verify_api_key(plain_api_key: str, hashed_api_key: str) -> bool:
    """验证API密钥"""
    return verify_password(plain_api_key, hashed_api_key)


def _get_encryption_key() -> bytes:
    """获取加密密钥"""
    # 使用配置中的密钥生成固定的加密密钥
    key_material = settings.SECRET_KEY.encode('utf-8')
    # 使用SHA256生成32字节的密钥
    key = hashlib.sha256(key_material).digest()
    # 转换为Fernet需要的base64编码格式
    return base64.urlsafe_b64encode(key)


def encrypt_datasource_password(password: str) -> str:
    """加密数据源密码"""
    if not password:
        return password
    
    key = _get_encryption_key()
    fernet = Fernet(key)
    encrypted_password = fernet.encrypt(password.encode('utf-8'))
    return base64.urlsafe_b64encode(encrypted_password).decode('utf-8')


def decrypt_datasource_password(encrypted_password: str) -> str:
    """解密数据源密码"""
    if not encrypted_password:
        return encrypted_password
    
    try:
        key = _get_encryption_key()
        fernet = Fernet(key)
        encrypted_data = base64.urlsafe_b64decode(encrypted_password.encode('utf-8'))
        decrypted_password = fernet.decrypt(encrypted_data)
        return decrypted_password.decode('utf-8')
    except Exception:
        # 如果解密失败，可能是明文密码，直接返回
        return encrypted_password


# ============ 项目权限检查 ============

from sqlalchemy.orm import Session
from typing import List
from enum import Enum


class PermissionType(str, Enum):
    """权限类型枚举"""
    READ = "read"  # 读取权限
    WRITE = "write"  # 写入权限
    ADMIN = "admin"  # 管理权限
    MANAGE_MEMBERS = "manage_members"  # 管理成员权限
    MANAGE_DATASOURCES = "manage_datasources"  # 管理数据源权限


def check_project_permission(
    db: Session, 
    user, 
    project_id: int, 
    permission: str
) -> bool:
    """
    检查用户是否有项目的特定权限
    
    Args:
        db: 数据库会话
        user: 用户对象
        project_id: 项目ID
        permission: 权限类型
    
    Returns:
        bool: 是否有权限
    """
    # 系统管理员拥有所有权限
    if user.is_admin:
        return True
    
    # 获取项目信息
    from app.models.project import Project, ProjectMember, ProjectMemberRole
    
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.is_active.is_(True)
    ).first()
    
    if not project:
        return False
    
    # 项目创建者拥有所有权限
    if project.created_by == user.id:
        return True
    
    # 获取用户在项目中的成员信息
    member = db.query(ProjectMember).filter(
        ProjectMember.project_id == project_id,
        ProjectMember.user_id == user.id,
        ProjectMember.is_active.is_(True)
    ).first()
    
    if not member:
        return False
    
    # 根据权限类型和用户角色检查权限
    return _check_role_permission(member.role, permission, member)


def _check_role_permission(
    role, 
    permission: str, 
    member
) -> bool:
    """
    根据角色检查权限
    
    Args:
        role: 项目角色
        permission: 权限类型
        member: 项目成员对象
    
    Returns:
        bool: 是否有权限
    """
    from app.models.project import ProjectMemberRole
    
    # 项目管理员拥有所有权限
    if role == ProjectMemberRole.ADMIN:
        return True
    
    # 根据具体权限类型检查
    if permission == PermissionType.READ:
        # 所有角色都有读取权限
        return True
    
    elif permission == PermissionType.WRITE:
        # 开发者和管理员有写入权限
        return role in [ProjectMemberRole.ADMIN, ProjectMemberRole.DEVELOPER] or member.can_write
    
    elif permission == PermissionType.ADMIN:
        # 只有管理员有管理权限
        return role == ProjectMemberRole.ADMIN or member.is_admin
    
    elif permission == PermissionType.MANAGE_MEMBERS:
        # 管理员和有管理成员权限的用户
        return role == ProjectMemberRole.ADMIN or member.can_manage_members
    
    elif permission == PermissionType.MANAGE_DATASOURCES:
        # 管理员有管理数据源权限
        return role == ProjectMemberRole.ADMIN
    
    # 默认无权限
    return False


def get_user_project_permissions(
    db: Session, 
    user, 
    project_id: int
) -> List[str]:
    """
    获取用户在项目中的所有权限
    
    Args:
        db: 数据库会话
        user: 用户对象
        project_id: 项目ID
    
    Returns:
        List[str]: 权限列表
    """
    permissions = []
    
    # 检查各种权限
    for perm in PermissionType:
        if check_project_permission(db, user, project_id, perm.value):
            permissions.append(perm.value)
    
    return permissions


def check_datasource_permission(
    db: Session, 
    user, 
    datasource_id: int, 
    permission: str
) -> bool:
    """
    检查用户是否有数据源的特定权限
    
    Args:
        db: 数据库会话
        user: 用户对象
        datasource_id: 数据源ID
        permission: 权限类型
    
    Returns:
        bool: 是否有权限
    """
    # 系统管理员拥有所有权限
    if user.is_admin:
        return True
    
    # 检查数据源的直接权限（通过acwl_datasource_permissions表）
    from app.models.datasource import DatasourcePermission, PermissionType as DsPermissionType
    
    ds_permission = db.query(DatasourcePermission).filter(
        DatasourcePermission.datasource_id == datasource_id,
        DatasourcePermission.user_id == user.id
    ).first()
    
    if ds_permission:
        if permission == "read":
            return ds_permission.permission_type in [
                DsPermissionType.READ_ONLY, 
                DsPermissionType.READ_WRITE, 
                DsPermissionType.ADMIN
            ]
        elif permission == "write":
            return ds_permission.permission_type in [
                DsPermissionType.READ_WRITE, 
                DsPermissionType.ADMIN
            ]
        elif permission == "admin":
            return ds_permission.permission_type == DsPermissionType.ADMIN
    
    # 检查通过项目获得的数据源权限
    from app.models.project import ProjectDatasource, ProjectDatasourceAccessType, ProjectMember
    
    project_datasources = db.query(ProjectDatasource).join(
        ProjectMember, ProjectDatasource.project_id == ProjectMember.project_id
    ).filter(
        ProjectDatasource.datasource_id == datasource_id,
        ProjectDatasource.is_active == True,
        ProjectMember.user_id == user.id,
        ProjectMember.is_active == True
    ).all()
    
    for pd in project_datasources:
        # 检查项目中的数据源访问权限
        if permission == "read":
            return True  # 项目成员都有读取权限
        elif permission == "write":
            return pd.access_type in [
                ProjectDatasourceAccessType.READ_WRITE,
                ProjectDatasourceAccessType.ADMIN
            ] or pd.can_write
        elif permission == "admin":
            return pd.access_type == ProjectDatasourceAccessType.ADMIN or pd.can_admin
    
    return False


def get_accessible_projects(db: Session, user) -> List[int]:
    """
    获取用户可访问的项目ID列表
    
    Args:
        db: 数据库会话
        user: 用户对象
    
    Returns:
        List[int]: 项目ID列表
    """
    from app.models.project import Project, ProjectMember
    
    # 系统管理员可以访问所有项目
    if user.is_admin:
        projects = db.query(Project.id).filter(Project.is_active.is_(True)).all()
        return [p.id for p in projects]
    
    # 获取用户创建的项目
    created_projects = db.query(Project.id).filter(
        Project.created_by == user.id,
        Project.is_active.is_(True)
    ).all()
    
    # 获取用户参与的项目
    member_projects = db.query(ProjectMember.project_id).filter(
        ProjectMember.user_id == user.id,
        ProjectMember.is_active.is_(True)
    ).all()
    
    # 合并并去重
    project_ids = set()
    project_ids.update([p.id for p in created_projects])
    project_ids.update([p.project_id for p in member_projects])
    
    return list(project_ids)