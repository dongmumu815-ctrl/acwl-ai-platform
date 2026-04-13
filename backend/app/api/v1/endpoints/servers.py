#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
服务器管理API端点
"""

import asyncio
import logging
from enum import Enum
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, or_
from sqlalchemy.orm import selectinload

from app.core.database import get_db, get_db_context
from app.models.server import Server, GPUResource, ServerMetrics, ServerStatus, ServerType
from app.models.server_group import ServerGroup
from app.models.user import User
from app.schemas.server import (
    ServerCreate, ServerUpdate, ServerResponse, ServerListResponse,
    GPUResourceResponse, ServerMetricsResponse, ServerStatusResponse,
    BatchTestConnectionRequest, BatchUpdatePasswordRequest,
    BatchRestartRequest, BatchDeleteRequest, BatchExecuteScriptRequest
)
from app.schemas.common import PaginatedResponse, IDResponse
from app.core.exceptions import NotFoundError, ValidationError
from app.api.v1.endpoints.auth import get_current_user
from app.services.server_service import ServerService

router = APIRouter()


@router.get("/", response_model=PaginatedResponse, summary="获取服务器列表")
async def get_servers(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=1000, description="每页数量"),
    sort_by: str = Query("sort_order", description="排序字段: created_at, name, status, cpu, sort_order"),
    sort_order: str = Query("asc", description="排序顺序: asc, desc"),
    search: str = Query(None, description="搜索关键词"),
    server_type: Optional[ServerType] = Query(None, description="服务器类型"),
    status: Optional[ServerStatus] = Query(None, description="服务器状态"),
    group_id: Optional[int] = Query(None, description="服务器分组ID"),
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
        
    # 分组筛选
    if group_id:
        query = query.where(Server.group_id == group_id)
    
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
    if group_id:
        count_query = count_query.where(Server.group_id == group_id)
    
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # 分页查询
    offset = (page - 1) * size
    
    # 排序处理
    # 始终将 sort_order 作为第一排序键（实现置顶功能）
    # 除非用户明确要求按 sort_order 排序（此时由下方逻辑处理）
    if sort_by != "sort_order":
        query = query.order_by(Server.sort_order.asc())

    order_column = None
    if sort_by == "created_at":
        order_column = Server.created_at.asc() if sort_order == "asc" else Server.created_at.desc()
    elif sort_by == "name":
        order_column = Server.name.asc() if sort_order == "asc" else Server.name.desc()
    elif sort_by == "status":
        order_column = Server.status.asc() if sort_order == "asc" else Server.status.desc()
    elif sort_by == "cpu":
        order_column = Server.total_cpu_cores.asc() if sort_order == "asc" else Server.total_cpu_cores.desc()
    elif sort_by == "sort_order":
        order_column = Server.sort_order.asc() if sort_order == "asc" else Server.sort_order.desc()
    
    # 应用用户选择的排序
    if order_column is not None:
        query = query.order_by(order_column)
        
    # 辅助排序：当主要排序字段相同时，使用 created_at 降序作为第二排序键
    query = query.options(selectinload(Server.group)).offset(offset).limit(size).order_by(Server.created_at.desc())
    
    result = await db.execute(query)
    servers = result.scalars().all()
    
    # 手动加载 GPU 资源，避免 selectinload 在复杂查询下的潜在问题
    server_ids = [s.id for s in servers]
    gpu_map = {}
    if server_ids:
        gpu_query = select(GPUResource).where(GPUResource.server_id.in_(server_ids))
        gpu_result = await db.execute(gpu_query)
        all_gpus = gpu_result.scalars().all()
        
        from collections import defaultdict
        gpu_map = defaultdict(list)
        for gpu in all_gpus:
            gpu_map[gpu.server_id].append(gpu)
    
    # 构建响应
    items = []
    for server in servers:
        # 转换为 Pydantic 模型
        server_dto = ServerResponse.from_orm(server)
        # 手动填充 GPU 资源
        if server.id in gpu_map:
            server_dto.gpu_resources = [GPUResourceResponse.from_orm(g) for g in gpu_map[server.id]]
        else:
            server_dto.gpu_resources = []
        items.append(server_dto)
    
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        size=size,
        pages=(total + size - 1) // size
    )


@router.get("/stats", summary="获取服务器统计数据")
async def get_server_stats(
    group_id: Optional[int] = Query(None, description="服务器分组ID"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    server_type: Optional[ServerType] = Query(None, description="服务器类型"),
    status: Optional[ServerStatus] = Query(None, description="服务器状态"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取服务器统计数据，包括总数、在线数、离线数和GPU总数"""
    logger = logging.getLogger(__name__)
    
    try:
        # 获取各状态服务器数量
        status_query = select(Server.status, func.count(Server.id)).group_by(Server.status)
        if group_id is not None:
            status_query = status_query.where(Server.group_id == group_id)
        if search:
            status_query = status_query.where(
                or_(
                    Server.name.ilike(f"%{search}%"),
                    Server.ip_address.ilike(f"%{search}%")
                )
            )
        if server_type:
            status_query = status_query.where(Server.server_type == server_type)
        if status:
            status_query = status_query.where(Server.status == status)
        
        status_result = await db.execute(status_query)
        status_counts = dict(status_result.all())
        
        # 统一将 key 转换为字符串，确保枚举匹配正确
        counts_by_str = {}
        for k, v in status_counts.items():
            if isinstance(k, Enum):
                counts_by_str[k.value] = v
            else:
                counts_by_str[str(k)] = v
        
        # 获取GPU总数
        gpu_query = select(func.count(GPUResource.id)).join(Server, GPUResource.server_id == Server.id)
        if group_id is not None:
            gpu_query = gpu_query.where(Server.group_id == group_id)
        if search:
            gpu_query = gpu_query.where(
                or_(
                    Server.name.ilike(f"%{search}%"),
                    Server.ip_address.ilike(f"%{search}%")
                )
            )
        if server_type:
            gpu_query = gpu_query.where(Server.server_type == server_type)
        if status:
            gpu_query = gpu_query.where(Server.status == status)
            
        gpu_result = await db.execute(gpu_query)
        
        # 获取在线和离线服务器数量
        online = counts_by_str.get(ServerStatus.online.value, 0)
        offline = counts_by_str.get(ServerStatus.offline.value, 0)
        
        # 计算总数 (直接累加各状态数量)
        total = sum(status_counts.values())
        
        # 处理GPU统计结果
        total_gpus = gpu_result.scalar() or 0
        
        result = {
            "total": total,
            "online": online,
            "offline": offline,
            "total_gpus": total_gpus
        }
        return result
        
    except Exception as e:
        import traceback
        logger.error(f"获取服务器统计数据失败: {str(e)}")
        logger.error(f"堆栈信息: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取服务器统计数据失败: {str(e)}"
        )


@router.post("/batch/test-connection", summary="批量测试服务器连接")
async def batch_test_server_connection(
    request: BatchTestConnectionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """批量测试服务器SSH连接"""
    try:
        service = ServerService(db)
        results = await service.batch_test_ssh_connection(request.ids)
        return {"results": results}
    except Exception as e:
        return {"status": "error", "message": f"批量测试连接时发生错误: {str(e)}"}


@router.post("/batch/update-password", summary="批量更新服务器密码")
async def batch_update_server_password(
    request: BatchUpdatePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """批量更新服务器SSH密码"""
    try:
        service = ServerService(db)
        results = await service.batch_update_password(request.ids, request.password)
        return {"results": results}
    except Exception as e:
        return {"status": "error", "message": f"批量更新密码时发生错误: {str(e)}"}


@router.post("/batch/restart", summary="批量重启服务器")
async def batch_restart_server(
    request: BatchRestartRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """批量重启服务器"""
    try:
        service = ServerService(db)
        results = await service.batch_restart_servers(request.ids)
        return {"results": results}
    except Exception as e:
        return {"status": "error", "message": f"批量重启时发生错误: {str(e)}"}


@router.post("/batch/delete", summary="批量删除服务器")
async def batch_delete_server(
    request: BatchDeleteRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """批量删除服务器"""
    try:
        service = ServerService(db)
        results = await service.batch_delete_servers(request.ids)
        return {"results": results}
    except Exception as e:
        return {"status": "error", "message": f"批量删除时发生错误: {str(e)}"}


@router.post("/batch/execute-script", summary="批量执行脚本")
async def batch_execute_script(
    request: BatchExecuteScriptRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    批量执行脚本（异步）
    
    1. 创建执行记录和详情
    2. 启动后台任务执行脚本
    3. 立即返回任务ID
    """
    try:
        service = ServerService(db)
        # 创建任务记录
        title = request.script.split('\n')[0][:50] if request.script else "未命名脚本"
        task_id = await service.create_script_execution_task(
            server_ids=request.ids,
            script=request.script,
            title=title,
            user_id=current_user.id
        )
        
        # 启动后台任务
        # 注意：这里我们传递一个特殊的包装函数，它会自己获取新的 DB session
        background_tasks.add_task(run_script_task, task_id)
        
        return {"task_id": task_id, "message": "脚本执行任务已提交"}
    except Exception as e:
        return {"status": "error", "message": f"批量执行脚本提交失败: {str(e)}"}

async def run_script_task(task_id: int):
    """后台任务包装函数"""
    async with get_db_context() as db:
        service = ServerService(db)
        await service.execute_script_background(task_id)

@router.get("/batch/execute-script/{task_id}", summary="获取脚本执行任务详情")
async def get_script_execution_status(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取脚本执行任务详情（用于轮询进度）"""
    try:
        service = ServerService(db)
        return await service.get_execution_record(task_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取任务详情失败: {str(e)}")


@router.post("/{server_id}/restart", summary="重启服务器")
async def restart_server(
    server_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """重启服务器"""
    try:
        service = ServerService(db)
        result = await service.restart_server(server_id)
        return result
    except Exception as e:
        return {"status": "error", "message": f"重启服务器时发生错误: {str(e)}"}


@router.get("/{server_id}", response_model=ServerResponse, summary="获取服务器详情")
async def get_server(
    server_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取服务器详情"""
    # 使用selectinload预加载gpu_resources和group关系
    query = select(Server).options(selectinload(Server.gpu_resources), selectinload(Server.group)).where(Server.id == server_id)
    result = await db.execute(query)
    server = result.scalar_one_or_none()
    
    if not server:
        raise NotFoundError("服务器不存在")
        
    # 手动填充 group_name
    server_dict = server.__dict__.copy()
    if server.group:
        server_dict['group_name'] = server.group.name
        
    return server_dict


@router.post("/", response_model=ServerResponse, summary="创建服务器")
async def create_server(
    server_in: ServerCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """创建新服务器"""
    # 检查IP是否重复
    result = await db.execute(select(Server).where(Server.ip_address == server_in.ip_address))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="服务器IP已存在")
    
    # 检查名称是否重复
    result = await db.execute(select(Server).where(Server.name == server_in.name))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="服务器名称已存在")
    
    # 如果指定了分组，检查分组是否存在
    if server_in.group_id:
        group_check = await db.execute(select(ServerGroup).where(ServerGroup.id == server_in.group_id))
        if not group_check.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="指定的分组不存在")
    
    server = Server(
        name=server_in.name,
        ip_address=server_in.ip_address,
        ssh_port=server_in.ssh_port,
        ssh_username=server_in.ssh_username,
        ssh_key_path=server_in.ssh_key_path,
        ssh_password=server_in.ssh_password,
        server_type=server_in.server_type,
        os_info=server_in.os_info,
        total_memory=server_in.total_memory,
        total_storage=server_in.total_storage,
        total_cpu_cores=server_in.total_cpu_cores,
        group_id=server_in.group_id,
        status=ServerStatus.offline
    )
    
    db.add(server)
    await db.commit()
    
    # 重新查询以获取完整信息
    result = await db.execute(
        select(Server)
        .options(selectinload(Server.gpu_resources), selectinload(Server.group))
        .where(Server.id == server.id)
    )
    server = result.scalar_one()
    
    return server


@router.put("/{server_id}", response_model=ServerResponse, summary="更新服务器")
async def update_server(
    server_id: int,
    server_in: ServerUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """更新服务器信息"""
    result = await db.execute(select(Server).options(selectinload(Server.group)).where(Server.id == server_id))
    server = result.scalar_one_or_none()
    
    if not server:
        raise HTTPException(status_code=404, detail="服务器不存在")
    
    # 检查名称是否重复
    if server_in.name and server_in.name != server.name:
        name_check = await db.execute(select(Server).where(Server.name == server_in.name))
        if name_check.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="服务器名称已存在")
            
    # 如果指定了分组，检查分组是否存在
    if server_in.group_id:
        group_check = await db.execute(select(ServerGroup).where(ServerGroup.id == server_in.group_id))
        if not group_check.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="指定的分组不存在")
    
    update_data = server_in.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(server, field, value)
    
    await db.commit()
    
    # 重新查询以获取最新状态和关联数据，避免 refresh 导致的 lazy load 问题
    result = await db.execute(
        select(Server)
        .options(selectinload(Server.gpu_resources), selectinload(Server.group))
        .where(Server.id == server_id)
    )
    server = result.scalar_one()
    
    # 手动填充 group_name
    server_dict = server.__dict__.copy()
    if server.group:
        server_dict['group_name'] = server.group.name
    
    return server_dict


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
            # ServerService.test_ssh_connection 已更新了状态和硬件信息
            # 刷新对象以获取最新数据
            await db.refresh(server)
            
            # 获取最新的 GPU 数量
            gpu_result = await db.execute(select(GPUResource).where(GPUResource.server_id == server_id))
            gpu_count = len(gpu_result.scalars().all())
            
            return {
                "status": "success", 
                "message": connection_result["message"],
                "data": {
                    "os_info": server.os_info,
                    "total_cpu_cores": server.total_cpu_cores,
                    "total_memory": server.total_memory,
                    "gpu_count": gpu_count,
                    "status": server.status,
                    "monitor": connection_result["data"].get("monitor", {})
                }
            }
        else:
            # 连接失败，ServerService 已将状态置为 offline
            await db.refresh(server)
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