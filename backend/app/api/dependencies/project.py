#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
项目管理相关依赖
"""

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional

from app.core.database import get_db
from app.models.user import User
from app.models.project import Project, ProjectMember, ProjectMemberRole
from app.core.security import PermissionType, check_project_permission
from app.api.v1.endpoints.auth import get_current_active_user


async def get_project_by_id(
    project_id: int,
    db: AsyncSession = Depends(get_db)
) -> Project:
    """
    根据ID获取项目
    """
    result = await db.execute(
        select(Project).where(
            Project.id == project_id,
            Project.is_deleted.is_(False)
        )
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="项目不存在"
        )
    return project


async def check_project_access(
    project_id: int,
    permission: PermissionType,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Project:
    """
    检查用户对项目的访问权限
    """
    # 获取项目
    project = await get_project_by_id(project_id, db)
    
    # 检查权限
    has_permission = await check_project_permission(
        db, current_user.id, project_id, permission
    )
    
    if not has_permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="没有足够的权限访问此项目"
        )
    
    return project


async def check_project_read_access(
    project_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Project:
    """
    检查项目读取权限
    """
    return await check_project_access(project_id, PermissionType.READ, current_user, db)


async def check_project_write_access(
    project_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Project:
    """
    检查项目写入权限
    """
    return await check_project_access(project_id, PermissionType.WRITE, current_user, db)


async def check_project_manage_access(
    project_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Project:
    """
    检查项目管理权限
    """
    return await check_project_access(project_id, PermissionType.MANAGE, current_user, db)


async def check_project_member_manage_access(
    project_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Project:
    """
    检查项目成员管理权限
    """
    return await check_project_access(project_id, PermissionType.MANAGE_MEMBERS, current_user, db)


async def check_project_datasource_manage_access(
    project_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Project:
    """
    检查项目数据源管理权限
    """
    return await check_project_access(project_id, PermissionType.MANAGE_DATASOURCES, current_user, db)


async def get_user_project_role(
    project_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Optional[ProjectMemberRole]:
    """
    获取用户在项目中的角色
    """
    # 管理员拥有所有权限
    if current_user.is_admin:
        return ProjectMemberRole.ADMIN
    
    # 查询用户在项目中的角色
    result = await db.execute(
        select(ProjectMember.role).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == current_user.id,
            ProjectMember.is_active == True
        )
    )
    role = result.scalar_one_or_none()
    return role