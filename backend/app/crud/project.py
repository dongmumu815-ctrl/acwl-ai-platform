#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
项目管理CRUD操作
"""

from sqlalchemy.orm import Session, joinedload
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, or_, func, desc, asc
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, date

from app.models.project import (
    Project, ProjectMember, ProjectDatasource, ProjectQuota,
    ProjectActivity, ProjectTemplate, ProjectStatus, ProjectType,
    ProjectPriority, ProjectMemberRole, ProjectDatasourceAccessType,
    ProjectResourceType, ProjectActivityType, ProjectActivityTargetType
)
from app.models.user import User
from app.models.datasource import Datasource
from app.schemas.project import (
    ProjectCreate, ProjectUpdate, ProjectMemberCreate, ProjectMemberUpdate,
    ProjectDatasourceCreate, ProjectDatasourceUpdate, ProjectQuotaCreate,
    ProjectQuotaUpdate, ProjectActivityCreate, ProjectTemplateCreate,
    ProjectTemplateUpdate, ProjectQueryParams, ProjectMemberQueryParams,
    ProjectDatasourceQueryParams, ProjectActivityQueryParams,
    ProjectStats, ProjectDashboard
)


# ============ 项目管理 ============

def create_project(db: Session, project_in: ProjectCreate, creator_id: int) -> Project:
    """
    创建新项目
    """
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
        created_by=creator_id
    )
    
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    
    # 自动添加创建者为项目管理员
    add_project_member(
        db,
        project_id=db_project.id,
        member_in=ProjectMemberCreate(
            user_id=creator_id,
            role=ProjectMemberRole.ADMIN,
            notes="项目创建者"
        ),
        invited_by=creator_id
    )
    
    # 如果使用了模板，应用模板配置
    if project_in.template_id:
        apply_project_template(db, db_project.id, project_in.template_id)
    
    return db_project


def get_project(db: Session, project_id: int) -> Optional[Project]:
    """
    根据ID获取项目
    """
    return db.query(Project).options(
        joinedload(Project.creator),
        joinedload(Project.members).joinedload(ProjectMember.user),
        joinedload(Project.datasource_associations).joinedload(ProjectDatasource.datasource)
    ).filter(
        Project.id == project_id,
        Project.is_active.is_(True)
    ).first()


def get_project_by_name(db: Session, name: str) -> Optional[Project]:
    """
    根据名称获取项目
    """
    return db.query(Project).filter(
        Project.name == name,
        Project.is_active.is_(True)
    ).first()


def get_projects(db: Session, params: ProjectQueryParams) -> Tuple[List[Project], int]:
    """
    获取项目列表
    """
    query = db.query(Project).options(
        joinedload(Project.creator)
    ).filter(Project.is_active.is_(True))
    
    # 应用过滤条件
    if params.search:
        search_term = f"%{params.search}%"
        query = query.filter(
            or_(
                Project.name.ilike(search_term),
                Project.description.ilike(search_term)
            )
        )
    
    if params.project_type:
        query = query.filter(Project.project_type == params.project_type)
    
    if params.status:
        query = query.filter(Project.status == params.status)
    
    if params.priority:
        query = query.filter(Project.priority == params.priority)
    
    if params.created_by:
        query = query.filter(Project.created_by == params.created_by)
    
    if params.start_date_from:
        query = query.filter(Project.start_date >= params.start_date_from)
    
    if params.start_date_to:
        query = query.filter(Project.start_date <= params.start_date_to)
    
    # 获取总数
    total = query.count()
    
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
    projects = query.offset(offset).limit(params.size).all()
    
    # 添加统计信息
    for project in projects:
        project.member_count = len(project.members)
        project.datasource_count = len(project.datasource_associations)
        project.creator_name = project.creator.username if project.creator else None
    
    return projects, total


def get_user_projects(db: Session, user_id: int, params: ProjectQueryParams) -> Tuple[List[Project], int]:
    """
    获取用户参与的项目列表
    """
    query = db.query(Project).join(
        ProjectMember, Project.id == ProjectMember.project_id
    ).options(
        joinedload(Project.creator)
    ).filter(
        ProjectMember.user_id == user_id,
        ProjectMember.is_active.is_(True),
        Project.is_active.is_(True)
    )
    
    # 应用过滤条件（与get_projects相同的逻辑）
    if params.search:
        search_term = f"%{params.search}%"
        query = query.filter(
            or_(
                Project.name.ilike(search_term),
                Project.description.ilike(search_term)
            )
        )
    
    if params.project_type:
        query = query.filter(Project.project_type == params.project_type)
    
    if params.status:
        query = query.filter(Project.status == params.status)
    
    if params.priority:
        query = query.filter(Project.priority == params.priority)
    
    if params.start_date_from:
        query = query.filter(Project.start_date >= params.start_date_from)
    
    if params.start_date_to:
        query = query.filter(Project.start_date <= params.start_date_to)
    
    # 获取总数
    total = query.count()
    
    # 应用排序和分页
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
    
    offset = (params.page - 1) * params.size
    projects = query.offset(offset).limit(params.size).all()
    
    # 添加统计信息
    for project in projects:
        project.member_count = len(project.members)
        project.datasource_count = len(project.datasource_associations)
        project.creator_name = project.creator.username if project.creator else None
    
    return projects, total


def update_project(db: Session, project_id: int, project_in: ProjectUpdate) -> Optional[Project]:
    """
    更新项目信息
    """
    db_project = db.query(Project).filter(Project.id == project_id).first()
    if not db_project:
        return None
    
    update_data = project_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_project, field, value)
    
    db_project.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_project)
    
    return db_project


def delete_project(db: Session, project_id: int) -> bool:
    """
    删除项目（软删除）
    """
    db_project = db.query(Project).filter(Project.id == project_id).first()
    if not db_project:
        return False
    
    db_project.is_active = False
    db_project.status = ProjectStatus.ARCHIVED
    db_project.updated_at = datetime.utcnow()
    
    # 同时停用所有项目成员
    db.query(ProjectMember).filter(
        ProjectMember.project_id == project_id
    ).update({"is_active": False})
    
    # 同时停用所有项目数据源关联
    db.query(ProjectDatasource).filter(
        ProjectDatasource.project_id == project_id
    ).update({"is_active": False})
    
    db.commit()
    return True


# ============ 项目成员管理 ============

def add_project_member(
    db: Session, 
    project_id: int, 
    member_in: ProjectMemberCreate, 
    invited_by: int
) -> ProjectMember:
    """
    添加项目成员
    """
    db_member = ProjectMember(
        project_id=project_id,
        user_id=member_in.user_id,
        role=member_in.role,
        permissions=member_in.permissions,
        notes=member_in.notes,
        invited_by=invited_by
    )
    
    db.add(db_member)
    db.commit()
    db.refresh(db_member)
    
    return db_member


def get_project_member(db: Session, project_id: int, user_id: int) -> Optional[ProjectMember]:
    """
    获取项目成员
    """
    return db.query(ProjectMember).filter(
        ProjectMember.project_id == project_id,
        ProjectMember.user_id == user_id,
        ProjectMember.is_active.is_(True)
    ).first()


def get_project_member_by_id(db: Session, member_id: int) -> Optional[ProjectMember]:
    """
    根据ID获取项目成员
    """
    return db.query(ProjectMember).options(
        joinedload(ProjectMember.user)
    ).filter(
        ProjectMember.id == member_id,
        ProjectMember.is_active.is_(True)
    ).first()


def get_project_members(
    db: Session, 
    project_id: int, 
    params: ProjectMemberQueryParams
) -> Tuple[List[ProjectMember], int]:
    """
    获取项目成员列表
    """
    query = db.query(ProjectMember).options(
        joinedload(ProjectMember.user),
        joinedload(ProjectMember.inviter)
    ).filter(
        ProjectMember.project_id == project_id,
        ProjectMember.is_active.is_(True)
    )
    
    # 应用过滤条件
    if params.role:
        query = query.filter(ProjectMember.role == params.role)
    
    if params.is_active is not None:
        query = query.filter(ProjectMember.is_active == params.is_active)
    
    if params.search:
        search_term = f"%{params.search}%"
        query = query.join(User, ProjectMember.user_id == User.id).filter(
            or_(
                User.username.ilike(search_term),
                User.email.ilike(search_term)
            )
        )
    
    # 获取总数
    total = query.count()
    
    # 应用分页
    offset = (params.page - 1) * params.size
    members = query.order_by(desc(ProjectMember.joined_at)).offset(offset).limit(params.size).all()
    
    # 添加用户信息
    for member in members:
        member.username = member.user.username if member.user else None
        member.email = member.user.email if member.user else None
        member.inviter_name = member.inviter.username if member.inviter else None
    
    return members, total


def update_project_member(
    db: Session, 
    member_id: int, 
    member_in: ProjectMemberUpdate
) -> Optional[ProjectMember]:
    """
    更新项目成员信息
    """
    db_member = db.query(ProjectMember).filter(ProjectMember.id == member_id).first()
    if not db_member:
        return None
    
    update_data = member_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_member, field, value)
    
    db.commit()
    db.refresh(db_member)
    
    return db_member


def remove_project_member(db: Session, member_id: int) -> bool:
    """
    移除项目成员
    """
    db_member = db.query(ProjectMember).filter(ProjectMember.id == member_id).first()
    if not db_member:
        return False
    
    db_member.is_active = False
    db.commit()
    
    return True


# ============ 项目数据源管理 ============

async def assign_project_datasource(
    db: AsyncSession,
    project_id: int,
    datasource_in: ProjectDatasourceCreate,
    assigned_by: int
) -> ProjectDatasource:
    """
    为项目分配数据源
    """
    db_assignment = ProjectDatasource(
        project_id=project_id,
        datasource_id=datasource_in.datasource_id,
        access_type=datasource_in.access_type,
        is_primary=datasource_in.is_primary,
        config=datasource_in.config,
        expires_at=datasource_in.expires_at,
        notes=datasource_in.notes,
        assigned_by=assigned_by
    )
    
    db.add(db_assignment)
    await db.commit()
    await db.refresh(db_assignment)
    
    return db_assignment


async def get_project_datasource(
    db: AsyncSession, 
    project_id: int, 
    datasource_id: int
) -> Optional[ProjectDatasource]:
    """
    获取项目数据源关联
    """
    from sqlalchemy import select
    result = await db.execute(
        select(ProjectDatasource).filter(
            ProjectDatasource.project_id == project_id,
            ProjectDatasource.datasource_id == datasource_id,
            ProjectDatasource.is_active.is_(True)
        )
    )
    return result.scalar_one_or_none()


def get_project_datasources(
    db: Session,
    project_id: int,
    params: ProjectDatasourceQueryParams
) -> Tuple[List[ProjectDatasource], int]:
    """
    获取项目数据源列表
    """
    query = db.query(ProjectDatasource).options(
        joinedload(ProjectDatasource.datasource),
        joinedload(ProjectDatasource.assigner)
    ).filter(
        ProjectDatasource.project_id == project_id,
        ProjectDatasource.is_active.is_(True)
    )
    
    # 应用过滤条件
    if params.access_type:
        query = query.filter(ProjectDatasource.access_type == params.access_type)
    
    if params.is_primary is not None:
        query = query.filter(ProjectDatasource.is_primary == params.is_primary)
    
    if params.is_active is not None:
        query = query.filter(ProjectDatasource.is_active == params.is_active)
    
    if params.datasource_type:
        query = query.join(Datasource, ProjectDatasource.datasource_id == Datasource.id).filter(
            Datasource.datasource_type == params.datasource_type
        )
    
    if params.search:
        search_term = f"%{params.search}%"
        query = query.join(Datasource, ProjectDatasource.datasource_id == Datasource.id).filter(
            Datasource.name.ilike(search_term)
        )
    
    # 获取总数
    total = query.count()
    
    # 应用分页
    offset = (params.page - 1) * params.size
    datasources = query.order_by(desc(ProjectDatasource.assigned_at)).offset(offset).limit(params.size).all()
    
    # 添加数据源信息
    for ds in datasources:
        ds.datasource_name = ds.datasource.name if ds.datasource else None
        ds.datasource_type = ds.datasource.datasource_type if ds.datasource else None
        ds.datasource_status = ds.datasource.status if ds.datasource else None
        ds.assigner_name = ds.assigner.username if ds.assigner else None
    
    return datasources, total


# ============ 项目活动日志 ============

def create_activity(
    db: Session,
    project_id: int,
    user_id: Optional[int],
    activity_type: str,
    target_type: str,
    target_id: Optional[int],
    description: str,
    details: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
) -> ProjectActivity:
    """
    创建项目活动日志
    """
    db_activity = ProjectActivity(
        project_id=project_id,
        user_id=user_id,
        activity_type=ProjectActivityType(activity_type),
        target_type=ProjectActivityTargetType(target_type),
        target_id=target_id,
        description=description,
        details=details,
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    db.add(db_activity)
    db.commit()
    db.refresh(db_activity)
    
    return db_activity


def get_project_activities(
    db: Session,
    project_id: int,
    params: ProjectActivityQueryParams
) -> Tuple[List[ProjectActivity], int]:
    """
    获取项目活动日志列表
    """
    query = db.query(ProjectActivity).options(
        joinedload(ProjectActivity.user)
    ).filter(
        ProjectActivity.project_id == project_id
    )
    
    # 应用过滤条件
    if params.activity_type:
        query = query.filter(ProjectActivity.activity_type == params.activity_type)
    
    if params.target_type:
        query = query.filter(ProjectActivity.target_type == params.target_type)
    
    if params.user_id:
        query = query.filter(ProjectActivity.user_id == params.user_id)
    
    if params.date_from:
        query = query.filter(ProjectActivity.created_at >= params.date_from)
    
    if params.date_to:
        query = query.filter(ProjectActivity.created_at <= params.date_to)
    
    # 获取总数
    total = query.count()
    
    # 应用分页
    offset = (params.page - 1) * params.size
    activities = query.order_by(desc(ProjectActivity.created_at)).offset(offset).limit(params.size).all()
    
    # 添加用户信息
    for activity in activities:
        activity.username = activity.user.username if activity.user else None
    
    return activities, total


# ============ 项目统计 ============

def get_project_stats(db: Session) -> ProjectStats:
    """
    获取项目统计信息
    """
    # 项目总数统计
    total_projects = db.query(Project).filter(Project.is_active.is_(True)).count()
    active_projects = db.query(Project).filter(
        Project.is_active.is_(True),
        Project.status == ProjectStatus.ACTIVE
    ).count()
    inactive_projects = db.query(Project).filter(
        Project.is_active.is_(True),
        Project.status == ProjectStatus.INACTIVE
    ).count()
    archived_projects = db.query(Project).filter(
        Project.status == ProjectStatus.ARCHIVED
    ).count()
    
    # 按类型分组统计
    projects_by_type = {}
    type_stats = db.query(
        Project.project_type,
        func.count(Project.id)
    ).filter(
        Project.is_active.is_(True)
    ).group_by(Project.project_type).all()
    
    for project_type, count in type_stats:
        projects_by_type[project_type.value] = count
    
    # 按优先级分组统计
    projects_by_priority = {}
    priority_stats = db.query(
        Project.priority,
        func.count(Project.id)
    ).filter(
        Project.is_active.is_(True)
    ).group_by(Project.priority).all()
    
    for priority, count in priority_stats:
        projects_by_priority[priority.value] = count
    
    # 成员和数据源统计
    total_members = db.query(ProjectMember).filter(
        ProjectMember.is_active.is_(True)
    ).count()

    total_datasources = db.query(ProjectDatasource).filter(
        ProjectDatasource.is_active.is_(True)
    ).count()
    
    return ProjectStats(
        total_projects=total_projects,
        active_projects=active_projects,
        inactive_projects=inactive_projects,
        archived_projects=archived_projects,
        projects_by_type=projects_by_type,
        projects_by_priority=projects_by_priority,
        total_members=total_members,
        total_datasources=total_datasources
    )


def get_user_project_stats(db: Session, user_id: int) -> ProjectStats:
    """
    获取用户项目统计信息
    """
    # 用户参与的项目统计
    user_projects_query = db.query(Project).join(
        ProjectMember, Project.id == ProjectMember.project_id
    ).filter(
        ProjectMember.user_id == user_id,
        ProjectMember.is_active.is_(True)
    )
    
    total_projects = user_projects_query.filter(Project.is_active.is_(True)).count()
    active_projects = user_projects_query.filter(
        Project.is_active.is_(True),
        Project.status == ProjectStatus.ACTIVE
    ).count()
    inactive_projects = user_projects_query.filter(
        Project.is_active.is_(True),
        Project.status == ProjectStatus.INACTIVE
    ).count()
    archived_projects = user_projects_query.filter(
        Project.status == ProjectStatus.ARCHIVED
    ).count()
    
    # 其他统计信息类似，但限制在用户参与的项目范围内
    projects_by_type = {}
    projects_by_priority = {}
    
    return ProjectStats(
        total_projects=total_projects,
        active_projects=active_projects,
        inactive_projects=inactive_projects,
        archived_projects=archived_projects,
        projects_by_type=projects_by_type,
        projects_by_priority=projects_by_priority,
        total_members=0,  # 可以进一步实现
        total_datasources=0  # 可以进一步实现
    )


def get_project_dashboard(db: Session, user_id: Optional[int] = None) -> ProjectDashboard:
    """
    获取项目仪表板数据
    """
    # 获取统计信息
    if user_id:
        stats = get_user_project_stats(db, user_id)
    else:
        stats = get_project_stats(db)
    
    # 获取最近活动（最近10条）
    activities_query = db.query(ProjectActivity).options(
        joinedload(ProjectActivity.user)
    )
    
    if user_id:
        # 限制在用户参与的项目
        activities_query = activities_query.join(
            ProjectMember, ProjectActivity.project_id == ProjectMember.project_id
        ).filter(
            ProjectMember.user_id == user_id,
            ProjectMember.is_active.is_(True)
        )
    
    recent_activities = activities_query.order_by(
        desc(ProjectActivity.created_at)
    ).limit(10).all()
    
    # 添加用户名信息
    for activity in recent_activities:
        activity.username = activity.user.username if activity.user else None
    
    # 获取配额使用情况（暂时返回空列表，可以进一步实现）
    quota_usage = []
    
    # 获取即将过期的数据源
    expiring_datasources = db.query(ProjectDatasource).options(
        joinedload(ProjectDatasource.datasource)
    ).filter(
        ProjectDatasource.is_active.is_(True),
        ProjectDatasource.expires_at.isnot(None),
        ProjectDatasource.expires_at <= datetime.utcnow().replace(hour=23, minute=59, second=59)
    ).limit(10).all()
    
    # 添加数据源信息
    for ds in expiring_datasources:
        ds.datasource_name = ds.datasource.name if ds.datasource else None
        ds.datasource_type = ds.datasource.datasource_type if ds.datasource else None
    
    return ProjectDashboard(
        project_stats=stats,
        recent_activities=recent_activities,
        quota_usage=quota_usage,
        expiring_datasources=expiring_datasources
    )


# ============ 项目模板管理 ============

def apply_project_template(db: Session, project_id: int, template_id: int) -> bool:
    """
    应用项目模板
    """
    template = db.query(ProjectTemplate).filter(
        ProjectTemplate.id == template_id,
        ProjectTemplate.is_active.is_(True)
    ).first()
    
    if not template:
        return False
    
    # 应用模板配置到项目
    # 这里可以根据template.template_config来配置项目的各种设置
    # 例如默认角色、默认配额等
    
    return True