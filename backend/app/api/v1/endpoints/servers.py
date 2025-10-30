#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
服务器管理API端点
"""

import asyncio
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.server import Server, GPUResource, ServerMetrics, ServerStatus, ServerType
from app.models.user import User
from app.schemas.server import (
    ServerCreate, ServerUpdate, ServerResponse, ServerListResponse,
    GPUResourceResponse, ServerMetricsResponse, ServerStatusResponse
)
from app.schemas.common import PaginatedResponse, IDResponse
from app.core.exceptions import NotFoundError, ValidationError
from app.api.v1.endpoints.auth import get_current_user
from app.services.server_service import ServerService

router = APIRouter()


@router.get("/", response_model=PaginatedResponse, summary="获取服务器列表")
async def get_servers(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    search: str = Query(None, description="搜索关键词"),
    server_type: Optional[ServerType] = Query(None, description="服务器类型"),
    status: Optional[ServerStatus] = Query(None, description="服务器状态"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取服务器列表"""
    
    # 构建查询
    query = select(Server)
    
    # 搜索条件
    if search:
        query = query.where(
            Server.name.contains(search) |
            Server.ip_address.contains(search) |
            Server.os_info.contains(search)
        )
    
    # 类型筛选
    if server_type:
        query = query.where(Server.server_type == server_type)
    
    # 状态筛选
    if status:
        query = query.where(Server.status == status)
    
    # 获取总数
    count_query = select(func.count(Server.id))
    if search:
        count_query = count_query.where(
            Server.name.contains(search) |
            Server.ip_address.contains(search) |
            Server.os_info.contains(search)
        )
    if server_type:
        count_query = count_query.where(Server.server_type == server_type)
    if status:
        count_query = count_query.where(Server.status == status)
    
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # 分页查询
    offset = (page - 1) * size
    # 使用selectinload预加载gpu_resources关系，避免懒加载导致的greenlet错误
    query = query.options(selectinload(Server.gpu_resources)).offset(offset).limit(size).order_by(Server.created_at.desc())
    
    result = await db.execute(query)
    servers = result.scalars().all()
    
    return PaginatedResponse(
        items=[ServerResponse.from_orm(server) for server in servers],
        total=total,
        page=page,
        size=size,
        pages=(total + size - 1) // size
    )


@router.get("/stats", summary="获取服务器统计数据")
async def get_server_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取服务器统计数据，包括总数、在线数、离线数和GPU总数"""
    try:
        # 获取服务器总数
        total_query = select(func.count(Server.id))
        total_result = await db.execute(total_query)
        total = total_result.scalar() or 0
        
        # 获取各状态服务器数量
        status_query = select(Server.status, func.count(Server.id)).group_by(Server.status)
        status_result = await db.execute(status_query)
        status_counts = dict(status_result.all())
        
        # 获取在线和离线服务器数量
        online = status_counts.get(ServerStatus.online, 0)
        offline = status_counts.get(ServerStatus.offline, 0)
        
        # 获取GPU总数
        gpu_query = select(func.count(GPUResource.id))
        gpu_result = await db.execute(gpu_query)
        total_gpus = gpu_result.scalar() or 0
        
        return {
            "total": total,
            "online": online,
            "offline": offline,
            "total_gpus": total_gpus
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取服务器统计数据失败: {str(e)}"
        )


@router.get("/{server_id}", response_model=ServerResponse, summary="获取服务器详情")
async def get_server(
    server_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取服务器详情"""
    
    # 使用selectinload预加载gpu_resources关系，避免懒加载导致的greenlet错误
    result = await db.execute(select(Server).options(selectinload(Server.gpu_resources)).where(Server.id == server_id))
    server = result.scalar_one_or_none()
    
    if not server:
        raise NotFoundError("服务器不存在")
    
    return ServerResponse.from_orm(server)


@router.post("/", response_model=IDResponse, summary="创建服务器")
async def create_server(
    server_data: ServerCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> IDResponse:
    """创建服务器（仅管理员）"""
    
    # 检查IP地址是否已存在
    existing_server = await db.execute(
        select(Server).where(Server.ip_address == server_data.ip_address)
    )
    if existing_server.scalar_one_or_none():
        raise ValidationError("IP地址已存在")
    
    # 创建服务器
    server = Server(
        name=server_data.name,
        ip_address=server_data.ip_address,
        ssh_port=server_data.ssh_port,
        ssh_username=server_data.ssh_username,
        ssh_key_path=server_data.ssh_key_path,
        ssh_password=server_data.ssh_password,  # 实际应用中需要加密
        server_type=server_data.server_type,
        os_info=server_data.os_info,
        total_memory=server_data.total_memory,
        total_storage=server_data.total_storage,
        total_cpu_cores=server_data.total_cpu_cores,
        status=ServerStatus.offline
    )
    
    db.add(server)
    await db.commit()
    await db.refresh(server)
    
    return IDResponse(id=server.id, message="服务器创建成功")


@router.put("/{server_id}", summary="更新服务器")
async def update_server(
    server_id: int,
    server_data: ServerUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """更新服务器（仅管理员）"""
    
    result = await db.execute(select(Server).where(Server.id == server_id))
    server = result.scalar_one_or_none()
    
    if not server:
        raise NotFoundError("服务器不存在")
    
    # 更新字段
    update_data = server_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(server, field, value)
    
    await db.commit()
    
    return {"message": "服务器更新成功"}


@router.delete("/{server_id}", summary="删除服务器")
async def delete_server(
    server_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """删除服务器（仅管理员）"""
    
    result = await db.execute(select(Server).where(Server.id == server_id))
    server = result.scalar_one_or_none()
    
    if not server:
        raise NotFoundError("服务器不存在")
    
    # 检查是否有正在运行的部署
    from app.models.deployment import Deployment, DeploymentStatus
    deployment_result = await db.execute(
        select(Deployment).where(
            Deployment.server_id == server_id,
            Deployment.status.in_([DeploymentStatus.RUNNING, DeploymentStatus.STARTING])
        )
    )
    if deployment_result.scalar_one_or_none():
        raise ValidationError("服务器上有正在运行的部署，无法删除")
    
    await db.delete(server)
    await db.commit()
    
    return {"message": "服务器删除成功"}


@router.post("/{server_id}/test-connection", summary="测试服务器连接")
async def test_server_connection(
    server_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """测试服务器SSH连接"""
    
    result = await db.execute(select(Server).where(Server.id == server_id))
    server = result.scalar_one_or_none()
    
    if not server:
        raise NotFoundError("服务器不存在")
    
    try:
        # 使用ServerService中的SSH连接测试方法
        service = ServerService(db)
        connection_result = await service.test_ssh_connection(server_id)
        
        if connection_result["success"]:
            # 更新服务器状态
            server.status = ServerStatus.online
            await db.commit()
            return {"status": "success", "message": connection_result["message"]}
        else:
            server.status = ServerStatus.offline
            await db.commit()
            return {"status": "failed", "message": connection_result["message"]}
            
    except Exception as e:
        return {"status": "error", "message": f"测试连接时发生错误: {str(e)}"}


@router.get("/{server_id}/gpus", response_model=List[GPUResourceResponse], summary="获取服务器GPU资源")
async def get_server_gpus(
    server_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取服务器GPU资源列表"""
    
    # 检查服务器是否存在
    server_result = await db.execute(select(Server).where(Server.id == server_id))
    if not server_result.scalar_one_or_none():
        raise NotFoundError("服务器不存在")
    
    # 获取GPU资源
    result = await db.execute(
        select(GPUResource).where(GPUResource.server_id == server_id)
    )
    gpus = result.scalars().all()
    
    return [GPUResourceResponse.from_orm(gpu) for gpu in gpus]


@router.get("/{server_id}/gpu-resources", response_model=List[GPUResourceResponse], summary="获取服务器GPU资源(别名)")
async def get_server_gpu_resources_alias(
    server_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取服务器GPU资源的别名路由，与 /gpus 等效"""
    # 直接复用现有查询逻辑
    result = await db.execute(select(Server).where(Server.id == server_id))
    if not result.scalar_one_or_none():
        raise NotFoundError("服务器不存在")
    gpu_result = await db.execute(select(GPUResource).where(GPUResource.server_id == server_id))
    return [GPUResourceResponse.from_orm(gpu) for gpu in gpu_result.scalars().all()]


@router.post("/{server_id}/scan-gpus", response_model=List[GPUResourceResponse], summary="扫描服务器GPU资源")
async def scan_server_gpus(
    server_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """扫描并更新服务器GPU资源信息，返回最新GPU列表"""
    
    # 校验服务器存在
    server_result = await db.execute(select(Server).where(Server.id == server_id))
    if not server_result.scalar_one_or_none():
        raise NotFoundError("服务器不存在")
    
    # 调用服务进行SSH扫描与持久化
    service = ServerService(db)
    await service.scan_server_gpus(server_id)
    
    # 返回扫描后的最新GPU列表
    gpu_result = await db.execute(select(GPUResource).where(GPUResource.server_id == server_id))
    gpus = gpu_result.scalars().all()
    return [GPUResourceResponse.from_orm(gpu) for gpu in gpus]


@router.get("/{server_id}/status", response_model=ServerStatusResponse, summary="获取服务器实时状态")
async def get_server_status(
    server_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取服务器实时状态信息"""
    
    result = await db.execute(select(Server).where(Server.id == server_id))
    server = result.scalar_one_or_none()
    
    if not server:
        raise NotFoundError("服务器不存在")
    
    # TODO: 实现实际的状态监控逻辑
    # 这里应该通过SSH连接获取实时的CPU、内存、GPU使用情况
    
    return ServerStatusResponse(
        server_id=server_id,
        status=server.status,
        cpu_usage=45.2,
        memory_usage=67.8,
        disk_usage=34.5,
        gpu_usage=[85.3, 92.1],
        uptime="15 days, 3 hours",
        last_updated="2024-01-15T10:30:00Z"
    )