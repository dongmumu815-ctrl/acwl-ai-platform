#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
部署管理API端点
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional

from app.core.database import get_db
from app.core.exceptions import NotFoundError, ValidationError
from app.models.user import User
from app.models.deployment import Deployment, DeploymentStatus, DeploymentType, DeploymentGPU
from app.models.server import Server, GPUResource
from app.schemas.common import PaginatedResponse, IDResponse
from app.schemas.deployment import DeploymentCreate, DeploymentUpdate, DeploymentResponse, DeploymentListResponse
from app.api.v1.endpoints.auth import get_current_active_user, get_current_admin_user

router = APIRouter()


@router.get("/", summary="获取部署列表", response_model=DeploymentListResponse)
async def get_deployments(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    search: str = Query(None, description="搜索关键词"),
    deployment_type: Optional[DeploymentType] = Query(None, description="部署类型"),
    status: Optional[DeploymentStatus] = Query(None, description="部署状态"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取部署列表"""
    
    # 构建查询
    query = select(Deployment)
    
    # 搜索条件
    if search:
        query = query.where(
            Deployment.deployment_name.contains(search)
        )
    
    # 类型筛选
    if deployment_type:
        query = query.where(Deployment.deployment_type == deployment_type)
    
    # 状态筛选
    if status:
        query = query.where(Deployment.status == status)
    
    # 获取总数
    count_query = select(func.count(Deployment.id))
    if search:
        count_query = count_query.where(
            Deployment.deployment_name.contains(search)
        )
    if deployment_type:
        count_query = count_query.where(Deployment.deployment_type == deployment_type)
    if status:
        count_query = count_query.where(Deployment.status == status)
    
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # 分页查询
    offset = (page - 1) * size
    query = query.offset(offset).limit(size).order_by(Deployment.created_at.desc())
    
    result = await db.execute(query)
    deployments = result.scalars().all()
    
    return DeploymentListResponse(
        items=deployments,
        total=total,
        page=page,
        size=size,
        pages=(total + size - 1) // size
    )


@router.get("/{deployment_id}", summary="获取部署详情", response_model=DeploymentResponse)
async def get_deployment(
    deployment_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取部署详情"""
    
    result = await db.execute(select(Deployment).where(Deployment.id == deployment_id))
    deployment = result.scalar_one_or_none()
    
    if not deployment:
        raise NotFoundError("部署不存在")
    
    return deployment


@router.post("/", summary="创建部署", response_model=IDResponse)
async def create_deployment(
    deployment_data: DeploymentCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> IDResponse:
    """创建部署"""
    # 1. 验证模型存在
    from app.models.model import Model
    model_result = await db.execute(select(Model).where(Model.id == deployment_data.model_id))
    model = model_result.scalar_one_or_none()
    if not model:
        raise NotFoundError("模型不存在")
    
    # 2. 验证服务器资源和GPU可用性
    if deployment_data.server_id:
        server_result = await db.execute(select(Server).where(Server.id == deployment_data.server_id))
        server = server_result.scalar_one_or_none()
        if not server:
            raise NotFoundError("服务器不存在")
    
    # 创建部署记录
    new_deployment = Deployment(
        model_id=deployment_data.model_id,
        deployment_name=deployment_data.deployment_name,
        deployment_type=deployment_data.deployment_type,
        server_id=deployment_data.server_id,
        status=DeploymentStatus.PENDING,
        config=deployment_data.config,
        gpu_config=deployment_data.gpu_config,
        runtime_env=deployment_data.runtime_env,
        restart_policy=deployment_data.restart_policy,
        max_concurrent_requests=deployment_data.max_concurrent_requests,
        created_by=current_user.id,
        updated_by=current_user.id
    )
    
    db.add(new_deployment)
    await db.flush()
    
    # 3. 创建GPU关联
    if deployment_data.gpu_ids:
        for gpu_id in deployment_data.gpu_ids:
            # 验证GPU存在
            gpu_result = await db.execute(select(GPUResource).where(GPUResource.id == gpu_id))
            gpu = gpu_result.scalar_one_or_none()
            if not gpu:
                raise NotFoundError(f"GPU ID {gpu_id} 不存在")
            
            # 创建关联
            gpu_association = DeploymentGPU(
                deployment_id=new_deployment.id,
                gpu_id=gpu_id,
                memory_limit=deployment_data.gpu_config.get("memory_limit") if deployment_data.gpu_config else None
            )
            db.add(gpu_association)
    
    await db.commit()
    
    # 4. 启动部署任务 (异步任务，这里只是示例)
    # TODO: 实现异步部署任务
    
    return IDResponse(id=new_deployment.id, message="部署创建成功")


@router.put("/{deployment_id}", summary="更新部署")
async def update_deployment(
    deployment_id: int,
    deployment_data: DeploymentUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """更新部署"""
    # 查询部署是否存在
    result = await db.execute(select(Deployment).where(Deployment.id == deployment_id))
    deployment = result.scalar_one_or_none()
    
    if not deployment:
        raise NotFoundError("部署不存在")
    
    # 更新部署信息
    update_data = deployment_data.dict(exclude_unset=True)
    
    if update_data:
        # 添加更新者信息
        update_data["updated_by"] = current_user.id
        
        for key, value in update_data.items():
            setattr(deployment, key, value)
        
        await db.commit()
    
    return {"message": "部署更新成功"}


@router.post("/{deployment_id}/start", summary="启动部署")
async def start_deployment(
    deployment_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """启动部署"""
    
    result = await db.execute(select(Deployment).where(Deployment.id == deployment_id))
    deployment = result.scalar_one_or_none()
    
    if not deployment:
        raise NotFoundError("部署不存在")
    
    # TODO: 实现部署启动逻辑
    deployment.status = DeploymentStatus.RUNNING
    await db.commit()
    
    return {"message": "部署启动成功"}


@router.post("/{deployment_id}/stop", summary="停止部署")
async def stop_deployment(
    deployment_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """停止部署"""
    
    result = await db.execute(select(Deployment).where(Deployment.id == deployment_id))
    deployment = result.scalar_one_or_none()
    
    if not deployment:
        raise NotFoundError("部署不存在")
    
    # TODO: 实现部署停止逻辑
    deployment.status = DeploymentStatus.STOPPED
    await db.commit()
    
    return {"message": "部署停止成功"}


@router.post("/{deployment_id}/restart", summary="重启部署")
async def restart_deployment(
    deployment_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """重启部署"""
    
    result = await db.execute(select(Deployment).where(Deployment.id == deployment_id))
    deployment = result.scalar_one_or_none()
    
    if not deployment:
        raise NotFoundError("部署不存在")
    
    # TODO: 实现部署重启逻辑
    deployment.status = DeploymentStatus.RESTARTING
    await db.commit()
    
    return {"message": "部署重启中"}


@router.delete("/{deployment_id}", summary="删除部署")
async def delete_deployment(
    deployment_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """删除部署（仅管理员）"""
    
    result = await db.execute(select(Deployment).where(Deployment.id == deployment_id))
    deployment = result.scalar_one_or_none()
    
    if not deployment:
        raise NotFoundError("部署不存在")
    
    await db.delete(deployment)
    await db.commit()
    
    return {"message": "部署删除成功"}


@router.get("/available-servers", summary="获取可用服务器")
async def get_available_servers(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取可用的部署服务器列表"""
    # TODO: 实现获取可用服务器逻辑
    # 返回在线状态的服务器及其GPU资源信息
    return {
        "servers": [
            {
                "id": 1,
                "name": "GPU-Server-01",
                "ip_address": "10.20.1.201",
                "status": "online",
                "total_cpu_cores": 32,
                "total_memory": "128GB",
                "gpu_count": 2,
                "available_gpu_count": 1,
                "cpu_usage": 45,
                "memory_usage": 62
            },
            {
                "id": 2,
                "name": "GPU-Server-02",
                "ip_address": "10.20.1.202",
                "status": "online",
                "total_cpu_cores": 64,
                "total_memory": "256GB",
                "gpu_count": 4,
                "available_gpu_count": 3,
                "cpu_usage": 30,
                "memory_usage": 45
            }
        ]
    }


@router.get("/server-gpus/{server_id}", summary="获取服务器GPU资源")
async def get_server_gpus(
    server_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取指定服务器的GPU资源"""
    # TODO: 实现获取服务器GPU资源逻辑
    # 根据server_id返回对应的GPU资源列表
    gpu_data = {
        1: [
            {
                "id": 1,
                "gpu_name": "NVIDIA A100",
                "gpu_type": "A100",
                "memory_size": "80GB",
                "cuda_version": "12.1",
                "device_id": "0",
                "is_available": True
            },
            {
                "id": 2,
                "gpu_name": "NVIDIA A100",
                "gpu_type": "A100",
                "memory_size": "80GB",
                "cuda_version": "12.1",
                "device_id": "1",
                "is_available": False
            }
        ],
        2: [
            {
                "id": 3,
                "gpu_name": "NVIDIA A100",
                "gpu_type": "A100",
                "memory_size": "80GB",
                "cuda_version": "12.1",
                "device_id": "0",
                "is_available": True
            },
            {
                "id": 4,
                "gpu_name": "NVIDIA A100",
                "gpu_type": "A100",
                "memory_size": "80GB",
                "cuda_version": "12.1",
                "device_id": "1",
                "is_available": True
            },
            {
                "id": 5,
                "gpu_name": "NVIDIA RTX 4090",
                "gpu_type": "RTX 4090",
                "memory_size": "24GB",
                "cuda_version": "12.1",
                "device_id": "2",
                "is_available": True
            },
            {
                "id": 6,
                "gpu_name": "NVIDIA RTX 4090",
                "gpu_type": "RTX 4090",
                "memory_size": "24GB",
                "cuda_version": "12.1",
                "device_id": "3",
                "is_available": False
            }
        ]
    }
    
    return {"gpus": gpu_data.get(server_id, [])}


@router.get("/{deployment_id}/logs", summary="获取部署日志")
async def get_deployment_logs(
    deployment_id: int,
    lines: int = Query(100, ge=1, le=1000, description="日志行数"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取部署日志"""
    
    result = await db.execute(select(Deployment).where(Deployment.id == deployment_id))
    deployment = result.scalar_one_or_none()
    
    if not deployment:
        raise NotFoundError("部署不存在")
    
    # TODO: 实现日志获取逻辑
    return {
        "logs": [],
        "total_lines": 0,
        "deployment_id": deployment_id
    }