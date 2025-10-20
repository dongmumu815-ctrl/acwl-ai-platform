#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API v1 主路由
"""

from fastapi import APIRouter

from .endpoints import auth, users, models, model_service_configs, deployments, health, servers, datasets, datasources, projects, workflows, tasks, executors, schedulers, unified_nodes, agents, es_query, sql_query, resource_package_secure, roles, permissions, api_management
from . import instruction_sets, data_resource, resource_package, resource_type

# 创建API路由器
api_router = APIRouter()

# 注册各个模块的路由
api_router.include_router(
    health.router,
    prefix="/health",
    tags=["健康检查"]
)

api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["认证"]
)

api_router.include_router(
    users.router,
    prefix="/users",
    tags=["用户管理"]
)

api_router.include_router(
    models.router,
    prefix="/models",
    tags=["模型管理"]
)

api_router.include_router(
    model_service_configs.router,
    prefix="/model-service-configs",
    tags=["模型服务配置"]
)

api_router.include_router(
    deployments.router,
    prefix="/deployments",
    tags=["部署管理"]
)

api_router.include_router(
    servers.router,
    prefix="/servers",
    tags=["服务器管理"]
)

api_router.include_router(
    datasets.router,
    prefix="/datasets",
    tags=["数据集管理"]
)

api_router.include_router(
    datasources.router,
    prefix="/datasources",
    tags=["数据源管理"]
)

api_router.include_router(
    projects.router,
    prefix="/projects",
    tags=["项目管理"]
)

api_router.include_router(
    workflows.router,
    prefix="/workflows",
    tags=["工作流管理"]
)

api_router.include_router(
    tasks.router,
    prefix="/tasks",
    tags=["任务管理"]
)

api_router.include_router(
    executors.router,
    prefix="/executors",
    tags=["执行器管理"]
)

api_router.include_router(
    schedulers.router,
    prefix="/schedulers",
    tags=["调度器管理"]
)

api_router.include_router(
    unified_nodes.router,
    prefix="/unified-nodes",
    tags=["统一节点管理"]
)

api_router.include_router(
    agents.router,
    prefix="/agents",
    tags=["智能体管理"]
)

api_router.include_router(
    instruction_sets.router,
    prefix="/instruction-sets",
    tags=["指令集管理"]
)

api_router.include_router(
    data_resource.router,
    tags=["数据资源中心"]
)

api_router.include_router(
    resource_type.router,
    tags=["资源类型管理"]
)

api_router.include_router(
    es_query.router,
    prefix="/es",
    tags=["Elasticsearch查询"]
)

api_router.include_router(
    sql_query.router,
    prefix="/sql",
    tags=["SQL查询模板"]
)

api_router.include_router(
    resource_package.router,
    prefix="/resource-packages",
    tags=["资源包管理"]
)

api_router.include_router(
    resource_package_secure.router,
    prefix="/resource-packages",
    tags=["安全资源包查询"]
)

api_router.include_router(
    roles.router,
    prefix="/roles",
    tags=["角色管理"]
)

api_router.include_router(
    permissions.router,
    prefix="/permissions",
    tags=["权限管理"]
)

api_router.include_router(
    api_management.router,
    prefix="",
    tags=["API管理"]
)