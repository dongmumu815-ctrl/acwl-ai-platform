#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API v1 主路由
"""

from fastapi import APIRouter

from .endpoints import auth, users, models, deployments, health, servers, datasets, datasources, projects, workflows, tasks, executors, schedulers, unified_nodes

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