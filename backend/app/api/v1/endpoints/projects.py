#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
项目管理API端点
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict, Any
from datetime import datetime, date

from app.core.database import get_db
from app.api.v1.endpoints.auth import get_current_active_user as get_current_user
from app.models.user import User
from app.models.datasource import Datasource
from app.models.project import (
    Project, ProjectMember, ProjectDatasource, ProjectQuota, 
    ProjectActivity, ProjectTemplate, ProjectStatus, ProjectType,
    ProjectPriority, ProjectMemberRole, ProjectDatasourceAccessType
)
from app.schemas.project import (
    ProjectCreate, ProjectUpdate, Project as ProjectSchema,
    ProjectMemberCreate, ProjectMemberUpdate, ProjectMember as ProjectMemberSchema,
    ProjectDatasourceCreate, ProjectDatasourceUpdate, ProjectDatasource as ProjectDatasourceSchema,
    ProjectQuotaCreate, ProjectQuotaUpdate, ProjectQuota as ProjectQuotaSchema,
    ProjectActivityCreate, ProjectActivity as ProjectActivitySchema,
    ProjectTemplateCreate, ProjectTemplateUpdate, ProjectTemplate as ProjectTemplateSchema,
    ProjectQueryParams, ProjectMemberQueryParams, ProjectDatasourceQueryParams,
    ProjectActivityQueryParams, ProjectListResponse, ProjectMemberListResponse,
    ProjectDatasourceListResponse, ProjectActivityListResponse,
    ProjectStats, ProjectDashboard
)
from app.crud import project as crud_project
from app.core.security import check_project_permission
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


# ============ 项目管理 ============

@router.post("/", response_model=ProjectSchema, status_code=status.HTTP_201_CREATED)
async def create_project(
    project_in: ProjectCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    创建新项目
    """
    try:
        # 检查项目名称是否已存在
        from sqlalchemy import select
        result = await db.execute(
            select(Project).where(
                Project.name == project_in.name,
                Project.status == ProjectStatus.ACTIVE
            )
        )
        existing_project = result.scalar_one_or_none()
        if existing_project:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="项目名称已存在"
            )
        
        # 创建项目
        db_project = Project(
            name=project_in.name,
            description=project_in.description,
            project_type=project_in.project_type,
            status=project_in.status,
            priority=project_in.priority,
            start_date=project_in.start_date,
            end_date=project_in.end_date,
            members_count=project_in.members_count,
            tags=project_in.tags,
            project_metadata=project_in.project_metadata,
            created_by=current_user.id
        )
        
        db.add(db_project)
        await db.commit()
        await db.refresh(db_project)
        
        # 自动添加创建者为项目管理员
        member = ProjectMember(
            project_id=db_project.id,
            user_id=current_user.id,
            role=ProjectMemberRole.ADMIN,
            notes="项目创建者",
            invited_by=current_user.id
        )
        db.add(member)
        await db.commit()
        
        logger.info(f"用户 {current_user.username} 创建了项目 {db_project.name}")
        return db_project
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        logger.error(f"创建项目失败: {str(e)}")
        logger.error(f"错误详情: {traceback.format_exc()}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建项目失败: {str(e)}"
        )


@router.get("/", response_model=ProjectListResponse)
async def get_projects(
    params: ProjectQueryParams = Depends(),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取项目列表
    """
    try:
        from sqlalchemy import select, func, or_, desc, asc
        from sqlalchemy.orm import selectinload
        
        # 构建基础查询
        query = select(Project).options(
            selectinload(Project.creator),
            selectinload(Project.members),
            selectinload(Project.datasources)
        ).where(Project.status == ProjectStatus.ACTIVE)
        
        # 非管理员用户只能查看自己参与的项目
        if not current_user.is_admin:
            from app.models.project import ProjectMember
            query = query.join(
                ProjectMember, Project.id == ProjectMember.project_id
            ).where(
                ProjectMember.user_id == current_user.id,
                ProjectMember.is_active.is_(True)
            )
        
        # 应用过滤条件
        if params.search:
            search_term = f"%{params.search}%"
            query = query.where(
                or_(
                    Project.name.ilike(search_term),
                    Project.description.ilike(search_term)
                )
            )
        
        if params.project_type:
            query = query.where(Project.project_type == params.project_type)
        
        if params.status:
            query = query.where(Project.status == params.status)
        
        if params.priority:
            query = query.where(Project.priority == params.priority)
        
        if params.created_by:
            query = query.where(Project.created_by == params.created_by)
        
        if params.start_date_from:
            query = query.where(Project.start_date >= params.start_date_from)
        
        if params.start_date_to:
            query = query.where(Project.start_date <= params.start_date_to)
        
        # 获取总数
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar()
        
        # 应用排序
        if params.sort_by == "name":
            order_column = Project.name
        elif params.sort_by == "status":
            order_column = Project.status
        elif params.sort_by == "priority":
            order_column = Project.priority
        elif params.sort_by == "start_date":
            order_column = Project.start_date
        else:
            order_column = Project.created_at
        
        if params.sort_order == "asc":
            query = query.order_by(asc(order_column))
        else:
            query = query.order_by(desc(order_column))
        
        # 应用分页
        offset = (params.page - 1) * params.size
        query = query.offset(offset).limit(params.size)
        
        # 执行查询
        result = await db.execute(query)
        projects = result.scalars().all()
        
        # 添加统计信息
        for project in projects:
            project.member_count = len(project.members)
            project.datasource_count = len(project.datasources)
            project.creator_name = project.creator.username if project.creator else None
        
        pages = (total + params.size - 1) // params.size
        
        return ProjectListResponse(
            items=projects,
            total=total,
            page=params.page,
            size=params.size,
            pages=pages
        )
        
    except Exception as e:
        logger.error(f"获取项目列表失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取项目列表失败"
        )


@router.get("/{project_id}", response_model=ProjectSchema)
async def get_project(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取项目详情
    """
    try:
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload
        
        # 查询项目
        query = select(Project).options(
            selectinload(Project.creator),
            selectinload(Project.members),
            selectinload(Project.datasources)
        ).where(
            Project.id == project_id,
            Project.status == ProjectStatus.ACTIVE
        )
        
        result = await db.execute(query)
        project = result.scalar_one_or_none()
        
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="项目不存在"
            )
        
        # 检查权限 - 暂时简化权限检查
        if not current_user.is_admin:
            # 检查用户是否是项目创建者或成员
            is_creator = project.created_by == current_user.id
            is_member = any(member.user_id == current_user.id and member.is_active for member in project.members)
            
            if not (is_creator or is_member):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="无权限访问此项目"
                )
        
        # 添加统计信息
        project.member_count = len([m for m in project.members if m.is_active])
        project.datasource_count = len([d for d in project.datasources if d.is_active])
        project.creator_name = project.creator.username if project.creator else None
        
        return project
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取项目详情失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取项目详情失败"
        )


@router.put("/{project_id}", response_model=ProjectSchema)
async def update_project(
    project_id: int,
    project_in: ProjectUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    更新项目信息
    """
    try:
        project = crud_project.get_project(db, project_id=project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="项目不存在"
            )
        
        # 检查权限
        if not check_project_permission(db, current_user, project_id, "admin"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权限修改此项目"
            )
        
        # 检查项目名称是否已存在（如果要修改名称）
        if project_in.name and project_in.name != project.name:
            existing_project = crud_project.get_project_by_name(db, name=project_in.name)
            if existing_project:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="项目名称已存在"
                )
        
        # 更新项目
        updated_project = crud_project.update_project(db, project_id=project_id, project_in=project_in)
        
        # 记录活动日志
        crud_project.create_activity(
            db,
            project_id=project_id,
            user_id=current_user.id,
            activity_type="UPDATE",
            target_type="PROJECT",
            target_id=project_id,
            description=f"更新项目信息: {project.name}"
        )
        
        logger.info(f"用户 {current_user.username} 更新了项目 {project.name}")
        return updated_project
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新项目失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新项目失败"
        )


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    删除项目（软删除）
    """
    try:
        project = crud_project.get_project(db, project_id=project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="项目不存在"
            )
        
        # 检查权限（只有项目创建者或管理员可以删除）
        if not (current_user.is_admin or project.created_by == current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权限删除此项目"
            )
        
        # 软删除项目
        crud_project.delete_project(db, project_id=project_id)
        
        # 记录活动日志
        crud_project.create_activity(
            db,
            project_id=project_id,
            user_id=current_user.id,
            activity_type="DELETE",
            target_type="PROJECT",
            target_id=project_id,
            description=f"删除项目: {project.name}"
        )
        
        logger.info(f"用户 {current_user.username} 删除了项目 {project.name}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除项目失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="删除项目失败"
        )


# ============ 项目成员管理 ============

@router.post("/{project_id}/members", response_model=ProjectMemberSchema, status_code=status.HTTP_201_CREATED)
async def add_project_member(
    project_id: int,
    member_in: ProjectMemberCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    添加项目成员
    """
    try:
        # 检查项目是否存在
        project = crud_project.get_project(db, project_id=project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="项目不存在"
            )
        
        # 检查权限
        if not check_project_permission(db, current_user, project_id, "manage_members"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权限管理项目成员"
            )
        
        # 检查用户是否已是项目成员
        existing_member = crud_project.get_project_member(db, project_id=project_id, user_id=member_in.user_id)
        if existing_member:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户已是项目成员"
            )
        
        # 添加成员
        member = crud_project.add_project_member(
            db, project_id=project_id, member_in=member_in, invited_by=current_user.id
        )
        
        # 记录活动日志
        crud_project.create_activity(
            db,
            project_id=project_id,
            user_id=current_user.id,
            activity_type="ADD",
            target_type="MEMBER",
            target_id=member.user_id,
            description=f"添加项目成员: {member.username}"
        )
        
        logger.info(f"用户 {current_user.username} 向项目 {project.name} 添加了成员 {member.username}")
        return member
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"添加项目成员失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="添加项目成员失败"
        )


@router.get("/{project_id}/members", response_model=ProjectMemberListResponse)
async def get_project_members(
    project_id: int,
    params: ProjectMemberQueryParams = Depends(),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取项目成员列表
    """
    try:
        from sqlalchemy import select, func, or_
        from sqlalchemy.orm import selectinload
        from app.models.project import ProjectMember
        
        # 简化权限检查 - 检查项目是否存在且用户有权限
        project_query = select(Project).where(
            Project.id == project_id,
            Project.status == ProjectStatus.ACTIVE
        )
        project_result = await db.execute(project_query)
        project = project_result.scalar_one_or_none()
        
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="项目不存在"
            )
        
        # 检查权限
        if not current_user.is_admin:
            # 检查用户是否是项目创建者或成员
            member_check_query = select(ProjectMember).where(
                ProjectMember.project_id == project_id,
                ProjectMember.user_id == current_user.id,
                ProjectMember.is_active.is_(True)
            )
            member_check_result = await db.execute(member_check_query)
            is_member = member_check_result.scalar_one_or_none() is not None
            is_creator = project.created_by == current_user.id
            
            if not (is_creator or is_member):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="无权限访问此项目"
                )
        
        # 构建成员查询
        query = select(ProjectMember).options(
            selectinload(ProjectMember.user)
        ).where(
            ProjectMember.project_id == project_id,
            ProjectMember.is_active.is_(True)
        )
        
        # 应用搜索过滤
        if params.search:
            search_term = f"%{params.search}%"
            query = query.join(ProjectMember.user).where(
                or_(
                    User.username.ilike(search_term),
                    User.email.ilike(search_term)
                )
            )
        
        # 应用角色过滤
        if params.role:
            query = query.where(ProjectMember.role == params.role)
        
        # 获取总数
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar()
        
        # 应用分页
        offset = (params.page - 1) * params.size
        query = query.offset(offset).limit(params.size)
        
        # 执行查询
        result = await db.execute(query)
        members = result.scalars().all()
        
        # 手动设置用户信息字段
        member_list = []
        for member in members:
            member_dict = {
                "id": member.id,
                "project_id": member.project_id,
                "user_id": member.user_id,
                "role": member.role,
                "permissions": member.permissions,
                "joined_at": member.joined_at,
                "invited_by": member.invited_by,
                "is_active": member.is_active,
                "notes": member.notes,
                "is_admin": member.is_admin,
                "can_manage_members": member.can_manage_members,
                "can_write": member.can_write,
                "username": member.user.username if member.user else None,
                "email": member.user.email if member.user else None,
                "inviter_name": member.inviter.username if member.inviter else None
            }
            member_list.append(member_dict)
        
        pages = (total + params.size - 1) // params.size
        
        return ProjectMemberListResponse(
            items=member_list,
            total=total,
            page=params.page,
            size=params.size,
            pages=pages
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取项目成员列表失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取项目成员列表失败"
        )


@router.put("/{project_id}/members/{member_id}", response_model=ProjectMemberSchema)
async def update_project_member(
    project_id: int,
    member_id: int,
    member_in: ProjectMemberUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    更新项目成员信息
    """
    try:
        # 检查权限
        if not check_project_permission(db, current_user, project_id, "manage_members"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权限管理项目成员"
            )
        
        # 更新成员
        member = crud_project.update_project_member(db, member_id=member_id, member_in=member_in)
        if not member:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="项目成员不存在"
            )
        
        # 记录活动日志
        crud_project.create_activity(
            db,
            project_id=project_id,
            user_id=current_user.id,
            activity_type="UPDATE",
            target_type="MEMBER",
            target_id=member.user_id,
            description=f"更新项目成员信息: {member.username}"
        )
        
        logger.info(f"用户 {current_user.username} 更新了项目成员 {member.username} 的信息")
        return member
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新项目成员失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新项目成员失败"
        )


@router.delete("/{project_id}/members/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_project_member(
    project_id: int,
    member_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    移除项目成员
    """
    try:
        # 检查权限
        if not check_project_permission(db, current_user, project_id, "manage_members"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权限管理项目成员"
            )
        
        # 获取成员信息
        member = crud_project.get_project_member_by_id(db, member_id=member_id)
        if not member:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="项目成员不存在"
            )
        
        # 移除成员
        crud_project.remove_project_member(db, member_id=member_id)
        
        # 记录活动日志
        crud_project.create_activity(
            db,
            project_id=project_id,
            user_id=current_user.id,
            activity_type="REMOVE",
            target_type="MEMBER",
            target_id=member.user_id,
            description=f"移除项目成员: {member.username}"
        )
        
        logger.info(f"用户 {current_user.username} 移除了项目成员 {member.username}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"移除项目成员失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="移除项目成员失败"
        )


# ============ 项目数据源管理 ============

@router.post("/{project_id}/datasources", response_model=ProjectDatasourceSchema, status_code=status.HTTP_201_CREATED)
async def assign_project_datasource(
    project_id: int,
    datasource_in: ProjectDatasourceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    为项目分配数据源
    """
    try:
        # 简化权限检查 - 检查项目是否存在且用户有权限
        from sqlalchemy import select
        project_query = select(Project).where(
            Project.id == project_id,
            Project.status == ProjectStatus.ACTIVE
        )
        project_result = await db.execute(project_query)
        project = project_result.scalar_one_or_none()
        
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="项目不存在"
            )
        
        # 简化权限检查 - 只检查是否是项目创建者或管理员
        if not current_user.is_admin and project.created_by != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权限管理项目数据源"
            )
        
        # 检查数据源是否已分配给项目
        existing_assignment = await crud_project.get_project_datasource(
            db, project_id=project_id, datasource_id=datasource_in.datasource_id
        )
        if existing_assignment:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="数据源已分配给此项目"
            )
        
        # 分配数据源
        assignment = await crud_project.assign_project_datasource(
            db, project_id=project_id, datasource_in=datasource_in, assigned_by=current_user.id
        )
        
        logger.info(f"用户 {current_user.username} 为项目 {project_id} 分配了数据源 {datasource_in.datasource_id}")
        return assignment
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"分配项目数据源失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="分配项目数据源失败"
        )


@router.get("/{project_id}/datasources", response_model=ProjectDatasourceListResponse)
async def get_project_datasources(
    project_id: int,
    params: ProjectDatasourceQueryParams = Depends(),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取项目数据源列表
    """
    try:
        from sqlalchemy import select, func, or_
        from sqlalchemy.orm import selectinload
        from app.models.project import ProjectMember, ProjectDatasource
        
        # 简化权限检查 - 检查项目是否存在且用户有权限
        project_query = select(Project).where(
            Project.id == project_id,
            Project.status == ProjectStatus.ACTIVE
        )
        project_result = await db.execute(project_query)
        project = project_result.scalar_one_or_none()
        
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="项目不存在"
            )
        
        # 检查权限
        if not current_user.is_admin:
            # 检查用户是否是项目创建者或成员
            member_check_query = select(ProjectMember).where(
                ProjectMember.project_id == project_id,
                ProjectMember.user_id == current_user.id,
                ProjectMember.is_active.is_(True)
            )
            member_check_result = await db.execute(member_check_query)
            is_member = member_check_result.scalar_one_or_none() is not None
            is_creator = project.created_by == current_user.id
            
            if not (is_creator or is_member):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="无权限访问此项目"
                )
        
        # 构建数据源查询
        query = select(ProjectDatasource).options(
            selectinload(ProjectDatasource.datasource),
            selectinload(ProjectDatasource.assigner)
        ).where(
            ProjectDatasource.project_id == project_id,
            ProjectDatasource.is_active.is_(True)
        )
        
        # 应用搜索过滤
        if params.search:
            search_term = f"%{params.search}%"
            query = query.join(ProjectDatasource.datasource).where(
                or_(
                    Datasource.name.ilike(search_term),
                    Datasource.description.ilike(search_term)
                )
            )
        
        # 应用访问类型过滤
        if params.access_type:
            query = query.where(ProjectDatasource.access_type == params.access_type)
        
        # 获取总数
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar()
        
        # 应用分页
        offset = (params.page - 1) * params.size
        query = query.offset(offset).limit(params.size)
        
        # 执行查询
        result = await db.execute(query)
        datasources = result.scalars().all()
        
        # 添加数据源信息到响应对象
        for ds in datasources:
            ds.datasource_name = ds.datasource.name if ds.datasource else None
            ds.datasource_type = ds.datasource.datasource_type if ds.datasource else None
            ds.datasource_status = ds.datasource.status if ds.datasource else None
            # 设置分配者名称，如果没有分配者则显示"系统"
            if ds.assigner and hasattr(ds.assigner, 'username'):
                ds.assigner_name = ds.assigner.username
            elif ds.assigned_by:
                # 如果有assigned_by但assigner关系没有加载，尝试手动查询
                from sqlalchemy import select
                user_query = select(User).where(User.id == ds.assigned_by)
                user_result = await db.execute(user_query)
                user = user_result.scalar_one_or_none()
                ds.assigner_name = user.username if user else "未知用户"
            else:
                ds.assigner_name = "系统"
        
        pages = (total + params.size - 1) // params.size
        
        return ProjectDatasourceListResponse(
            items=datasources,
            total=total,
            page=params.page,
            size=params.size,
            pages=pages
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取项目数据源列表失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取项目数据源列表失败"
        )


# ============ 项目活动日志 ============

@router.get("/{project_id}/activities", response_model=ProjectActivityListResponse)
async def get_project_activities(
    project_id: int,
    params: ProjectActivityQueryParams = Depends(),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取项目活动日志
    """
    try:
        from sqlalchemy import select, func, desc
        from sqlalchemy.orm import selectinload
        from app.models.project import ProjectMember, ProjectActivity
        
        # 简化权限检查 - 检查项目是否存在且用户有权限
        project_query = select(Project).where(
            Project.id == project_id,
            Project.status == ProjectStatus.ACTIVE
        )
        project_result = await db.execute(project_query)
        project = project_result.scalar_one_or_none()
        
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="项目不存在"
            )
        
        # 检查权限
        if not current_user.is_admin:
            # 检查用户是否是项目创建者或成员
            member_check_query = select(ProjectMember).where(
                ProjectMember.project_id == project_id,
                ProjectMember.user_id == current_user.id,
                ProjectMember.is_active.is_(True)
            )
            member_check_result = await db.execute(member_check_query)
            is_member = member_check_result.scalar_one_or_none() is not None
            is_creator = project.created_by == current_user.id
            
            if not (is_creator or is_member):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="无权限访问此项目"
                )
        
        # 构建活动查询
        query = select(ProjectActivity).options(
            selectinload(ProjectActivity.user)
        ).where(
            ProjectActivity.project_id == project_id
        )
        
        # 应用活动类型过滤
        if params.activity_type:
            query = query.where(ProjectActivity.activity_type == params.activity_type)
        
        # 应用目标类型过滤
        if params.target_type:
            query = query.where(ProjectActivity.target_type == params.target_type)
        
        # 应用用户过滤
        if params.user_id:
            query = query.where(ProjectActivity.user_id == params.user_id)
        
        # 应用时间范围过滤
        if params.start_date:
            query = query.where(ProjectActivity.created_at >= params.start_date)
        
        if params.end_date:
            query = query.where(ProjectActivity.created_at <= params.end_date)
        
        # 获取总数
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar()
        
        # 按时间倒序排列
        query = query.order_by(desc(ProjectActivity.created_at))
        
        # 应用分页
        offset = (params.page - 1) * params.size
        query = query.offset(offset).limit(params.size)
        
        # 执行查询
        result = await db.execute(query)
        activities = result.scalars().all()
        
        pages = (total + params.size - 1) // params.size
        
        return ProjectActivityListResponse(
            items=activities,
            total=total,
            page=params.page,
            size=params.size,
            pages=pages
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取项目活动日志失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取项目活动日志失败"
        )


# ============ 项目统计 ============

@router.get("/stats/overview", response_model=ProjectStats)
async def get_project_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取项目统计信息
    """
    try:
        # 非管理员用户只能查看自己参与的项目统计
        if not current_user.is_admin:
            stats = crud_project.get_user_project_stats(db, user_id=current_user.id)
        else:
            stats = crud_project.get_project_stats(db)
        
        return stats
        
    except Exception as e:
        logger.error(f"获取项目统计失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取项目统计失败"
        )


@router.get("/dashboard", response_model=ProjectDashboard)
async def get_project_dashboard(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取项目仪表板数据
    """
    try:
        dashboard = crud_project.get_project_dashboard(db, user_id=current_user.id if not current_user.is_admin else None)
        return dashboard
        
    except Exception as e:
        logger.error(f"获取项目仪表板失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取项目仪表板失败"
        )