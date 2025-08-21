#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
项目管理相关的Pydantic Schema
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from decimal import Decimal
from enum import Enum

from app.models.project import (
    ProjectStatus, ProjectType, ProjectPriority, ProjectMemberRole,
    ProjectDatasourceAccessType, ProjectResourceType, ProjectQuotaResetPeriod,
    ProjectActivityType, ProjectActivityTargetType
)


# ============ 基础Schema ============

class ProjectBase(BaseModel):
    """项目基础Schema"""
    name: str = Field(..., min_length=1, max_length=100, description="项目名称")
    description: Optional[str] = Field(None, description="项目描述")
    project_type: ProjectType = Field(ProjectType.GENERAL, description="项目类型")
    status: ProjectStatus = Field(ProjectStatus.ACTIVE, description="项目状态")
    priority: ProjectPriority = Field(ProjectPriority.MEDIUM, description="项目优先级")
    start_date: Optional[date] = Field(None, description="项目开始日期")
    end_date: Optional[date] = Field(None, description="项目结束日期")
    members_count: Optional[int] = Field(1, ge=1, description="团队成员数量")
    tags: Optional[Dict[str, Any]] = Field(None, description="项目标签")
    project_metadata: Optional[Dict[str, Any]] = Field(None, description="项目元数据")


class ProjectCreate(ProjectBase):
    """创建项目Schema"""
    template_id: Optional[int] = Field(None, description="项目模板ID")
    initial_members: Optional[List[Dict[str, Any]]] = Field(None, description="初始成员列表")
    initial_datasources: Optional[List[Dict[str, Any]]] = Field(None, description="初始数据源列表")


class ProjectUpdate(BaseModel):
    """更新项目Schema"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="项目名称")
    description: Optional[str] = Field(None, description="项目描述")
    status: Optional[ProjectStatus] = Field(None, description="项目状态")
    priority: Optional[ProjectPriority] = Field(None, description="项目优先级")
    start_date: Optional[date] = Field(None, description="项目开始日期")
    end_date: Optional[date] = Field(None, description="项目结束日期")
    members_count: Optional[int] = Field(None, ge=1, description="团队成员数量")
    tags: Optional[Dict[str, Any]] = Field(None, description="项目标签")
    project_metadata: Optional[Dict[str, Any]] = Field(None, description="项目元数据")


class ProjectInDB(ProjectBase):
    """数据库中的项目Schema"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    created_by: int
    created_at: datetime
    updated_at: datetime
    is_active: bool
    is_expired: bool


class Project(ProjectInDB):
    """项目响应Schema"""
    member_count: Optional[int] = Field(None, description="成员数量")
    datasource_count: Optional[int] = Field(None, description="数据源数量")
    creator_name: Optional[str] = Field(None, description="创建者姓名")


# ============ 项目成员Schema ============

class ProjectMemberBase(BaseModel):
    """项目成员基础Schema"""
    role: ProjectMemberRole = Field(..., description="项目角色")
    permissions: Optional[Dict[str, Any]] = Field(None, description="具体权限配置")
    notes: Optional[str] = Field(None, description="备注信息")


class ProjectMemberCreate(ProjectMemberBase):
    """创建项目成员Schema"""
    user_id: int = Field(..., description="用户ID")


class ProjectMemberUpdate(BaseModel):
    """更新项目成员Schema"""
    role: Optional[ProjectMemberRole] = Field(None, description="项目角色")
    permissions: Optional[Dict[str, Any]] = Field(None, description="具体权限配置")
    is_active: Optional[bool] = Field(None, description="是否激活")
    notes: Optional[str] = Field(None, description="备注信息")


class ProjectMemberInDB(ProjectMemberBase):
    """数据库中的项目成员Schema"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    project_id: int
    user_id: int
    joined_at: datetime
    invited_by: Optional[int]
    is_active: bool
    is_admin: bool
    can_manage_members: bool
    can_write: bool


class ProjectMember(ProjectMemberInDB):
    """项目成员响应Schema"""
    username: Optional[str] = Field(None, description="用户名")
    email: Optional[str] = Field(None, description="用户邮箱")
    inviter_name: Optional[str] = Field(None, description="邀请者姓名")


# ============ 项目数据源Schema ============

class ProjectDatasourceBase(BaseModel):
    """项目数据源基础Schema"""
    access_type: ProjectDatasourceAccessType = Field(ProjectDatasourceAccessType.READ, description="访问类型")
    is_primary: bool = Field(False, description="是否为主数据源")
    config: Optional[Dict[str, Any]] = Field(None, description="数据源在项目中的配置")
    expires_at: Optional[datetime] = Field(None, description="过期时间")
    notes: Optional[str] = Field(None, description="备注信息")


class ProjectDatasourceCreate(ProjectDatasourceBase):
    """创建项目数据源Schema"""
    datasource_id: int = Field(..., description="数据源ID")


class ProjectDatasourceUpdate(BaseModel):
    """更新项目数据源Schema"""
    access_type: Optional[ProjectDatasourceAccessType] = Field(None, description="访问类型")
    is_primary: Optional[bool] = Field(None, description="是否为主数据源")
    config: Optional[Dict[str, Any]] = Field(None, description="数据源在项目中的配置")
    expires_at: Optional[datetime] = Field(None, description="过期时间")
    is_active: Optional[bool] = Field(None, description="是否激活")
    notes: Optional[str] = Field(None, description="备注信息")


class ProjectDatasourceInDB(ProjectDatasourceBase):
    """数据库中的项目数据源Schema"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    project_id: int
    datasource_id: int
    assigned_by: Optional[int]
    assigned_at: datetime
    is_active: bool
    is_expired: bool
    can_write: bool
    can_admin: bool


class ProjectDatasource(ProjectDatasourceInDB):
    """项目数据源响应Schema"""
    datasource_name: Optional[str] = Field(None, description="数据源名称")
    datasource_type: Optional[str] = Field(None, description="数据源类型")
    datasource_status: Optional[str] = Field(None, description="数据源状态")
    assigner_name: Optional[str] = Field(None, description="分配者姓名")


# ============ 项目配额Schema ============

class ProjectQuotaBase(BaseModel):
    """项目配额基础Schema"""
    resource_type: ProjectResourceType = Field(..., description="资源类型")
    quota_limit: int = Field(..., ge=0, description="配额限制")
    unit: str = Field(..., min_length=1, max_length=20, description="单位")
    reset_period: ProjectQuotaResetPeriod = Field(ProjectQuotaResetPeriod.MONTHLY, description="重置周期")


class ProjectQuotaCreate(ProjectQuotaBase):
    """创建项目配额Schema"""
    pass


class ProjectQuotaUpdate(BaseModel):
    """更新项目配额Schema"""
    quota_limit: Optional[int] = Field(None, ge=0, description="配额限制")
    quota_used: Optional[int] = Field(None, ge=0, description="已使用配额")
    unit: Optional[str] = Field(None, min_length=1, max_length=20, description="单位")
    reset_period: Optional[ProjectQuotaResetPeriod] = Field(None, description="重置周期")
    is_active: Optional[bool] = Field(None, description="是否激活")


class ProjectQuotaInDB(ProjectQuotaBase):
    """数据库中的项目配额Schema"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    project_id: int
    quota_used: int
    last_reset_at: Optional[datetime]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    usage_percentage: float
    is_exceeded: bool
    remaining_quota: int


class ProjectQuota(ProjectQuotaInDB):
    """项目配额响应Schema"""
    pass


# ============ 项目活动Schema ============

class ProjectActivityBase(BaseModel):
    """项目活动基础Schema"""
    activity_type: ProjectActivityType = Field(..., description="活动类型")
    target_type: ProjectActivityTargetType = Field(..., description="目标类型")
    target_id: Optional[int] = Field(None, description="目标ID")
    description: str = Field(..., min_length=1, description="活动描述")
    details: Optional[Dict[str, Any]] = Field(None, description="活动详情")


class ProjectActivityCreate(ProjectActivityBase):
    """创建项目活动Schema"""
    ip_address: Optional[str] = Field(None, description="IP地址")
    user_agent: Optional[str] = Field(None, description="用户代理")


class ProjectActivityInDB(ProjectActivityBase):
    """数据库中的项目活动Schema"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    project_id: int
    user_id: Optional[int]
    ip_address: Optional[str]
    user_agent: Optional[str]
    created_at: datetime


class ProjectActivity(ProjectActivityInDB):
    """项目活动响应Schema"""
    username: Optional[str] = Field(None, description="操作用户名")


# ============ 项目模板Schema ============

class ProjectTemplateBase(BaseModel):
    """项目模板基础Schema"""
    name: str = Field(..., min_length=1, max_length=100, description="模板名称")
    description: Optional[str] = Field(None, description="模板描述")
    project_type: ProjectType = Field(..., description="项目类型")
    template_config: Dict[str, Any] = Field(..., description="模板配置")
    default_roles: Optional[Dict[str, Any]] = Field(None, description="默认角色配置")
    default_quotas: Optional[Dict[str, Any]] = Field(None, description="默认配额配置")


class ProjectTemplateCreate(ProjectTemplateBase):
    """创建项目模板Schema"""
    pass


class ProjectTemplateUpdate(BaseModel):
    """更新项目模板Schema"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="模板名称")
    description: Optional[str] = Field(None, description="模板描述")
    template_config: Optional[Dict[str, Any]] = Field(None, description="模板配置")
    default_roles: Optional[Dict[str, Any]] = Field(None, description="默认角色配置")
    default_quotas: Optional[Dict[str, Any]] = Field(None, description="默认配额配置")
    is_active: Optional[bool] = Field(None, description="是否激活")


class ProjectTemplateInDB(ProjectTemplateBase):
    """数据库中的项目模板Schema"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    is_system: bool
    is_active: bool
    created_by: Optional[int]
    created_at: datetime
    updated_at: datetime


class ProjectTemplate(ProjectTemplateInDB):
    """项目模板响应Schema"""
    creator_name: Optional[str] = Field(None, description="创建者姓名")


# ============ 查询参数Schema ============

class ProjectQueryParams(BaseModel):
    """项目查询参数Schema"""
    page: int = Field(1, ge=1, description="页码")
    size: int = Field(20, ge=1, le=100, description="每页数量")
    search: Optional[str] = Field(None, description="搜索关键词")
    project_type: Optional[ProjectType] = Field(None, description="项目类型")
    status: Optional[ProjectStatus] = Field(None, description="项目状态")
    priority: Optional[ProjectPriority] = Field(None, description="项目优先级")
    created_by: Optional[int] = Field(None, description="创建者ID")
    start_date_from: Optional[date] = Field(None, description="开始日期范围-起始")
    start_date_to: Optional[date] = Field(None, description="开始日期范围-结束")
    sort_by: Optional[str] = Field("created_at", description="排序字段")
    sort_order: Optional[str] = Field("desc", pattern="^(asc|desc)$", description="排序方向")


class ProjectMemberQueryParams(BaseModel):
    """项目成员查询参数Schema"""
    page: int = Field(1, ge=1, description="页码")
    size: int = Field(20, ge=1, le=100, description="每页数量")
    role: Optional[ProjectMemberRole] = Field(None, description="项目角色")
    is_active: Optional[bool] = Field(None, description="是否激活")
    search: Optional[str] = Field(None, description="搜索关键词（用户名或邮箱）")


class ProjectDatasourceQueryParams(BaseModel):
    """项目数据源查询参数Schema"""
    page: int = Field(1, ge=1, description="页码")
    size: int = Field(20, ge=1, le=100, description="每页数量")
    access_type: Optional[ProjectDatasourceAccessType] = Field(None, description="访问类型")
    is_primary: Optional[bool] = Field(None, description="是否为主数据源")
    is_active: Optional[bool] = Field(None, description="是否激活")
    datasource_type: Optional[str] = Field(None, description="数据源类型")
    search: Optional[str] = Field(None, description="搜索关键词（数据源名称）")


class ProjectActivityQueryParams(BaseModel):
    """项目活动查询参数Schema"""
    page: int = Field(1, ge=1, description="页码")
    size: int = Field(20, ge=1, le=100, description="每页数量")
    activity_type: Optional[ProjectActivityType] = Field(None, description="活动类型")
    target_type: Optional[ProjectActivityTargetType] = Field(None, description="目标类型")
    user_id: Optional[int] = Field(None, description="操作用户ID")
    date_from: Optional[datetime] = Field(None, description="日期范围-起始")
    date_to: Optional[datetime] = Field(None, description="日期范围-结束")


# ============ 统计Schema ============

class ProjectStats(BaseModel):
    """项目统计Schema"""
    total_projects: int = Field(..., description="项目总数")
    active_projects: int = Field(..., description="活跃项目数")
    inactive_projects: int = Field(..., description="非活跃项目数")
    archived_projects: int = Field(..., description="已归档项目数")
    projects_by_type: Dict[str, int] = Field(..., description="按类型分组的项目数")
    projects_by_priority: Dict[str, int] = Field(..., description="按优先级分组的项目数")
    total_members: int = Field(..., description="成员总数")
    total_datasources: int = Field(..., description="数据源总数")


class ProjectDashboard(BaseModel):
    """项目仪表板Schema"""
    project_stats: ProjectStats = Field(..., description="项目统计")
    recent_activities: List[ProjectActivity] = Field(..., description="最近活动")
    quota_usage: List[ProjectQuota] = Field(..., description="配额使用情况")
    expiring_datasources: List[ProjectDatasource] = Field(..., description="即将过期的数据源")


# ============ 响应Schema ============

class ProjectListResponse(BaseModel):
    """项目列表响应Schema"""
    items: List[Project] = Field(..., description="项目列表")
    total: int = Field(..., description="总数")
    page: int = Field(..., description="当前页码")
    size: int = Field(..., description="每页数量")
    pages: int = Field(..., description="总页数")


class ProjectMemberListResponse(BaseModel):
    """项目成员列表响应Schema"""
    items: List[ProjectMember] = Field(..., description="成员列表")
    total: int = Field(..., description="总数")
    page: int = Field(..., description="当前页码")
    size: int = Field(..., description="每页数量")
    pages: int = Field(..., description="总页数")


class ProjectDatasourceListResponse(BaseModel):
    """项目数据源列表响应Schema"""
    items: List[ProjectDatasource] = Field(..., description="数据源列表")
    total: int = Field(..., description="总数")
    page: int = Field(..., description="当前页码")
    size: int = Field(..., description="每页数量")
    pages: int = Field(..., description="总页数")


class ProjectActivityListResponse(BaseModel):
    """项目活动列表响应Schema"""
    items: List[ProjectActivity] = Field(..., description="活动列表")
    total: int = Field(..., description="总数")
    page: int = Field(..., description="当前页码")
    size: int = Field(..., description="每页数量")
    pages: int = Field(..., description="总页数")