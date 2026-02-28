from fastapi import APIRouter, Depends, HTTPException, Query, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, and_, or_
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import uuid

from ....core.database import get_db
from ....models.executor import ExecutorNode, ExecutorGroup
from ....models.task import TaskInstance
from ....services.executor_cluster import get_executor_cluster_service
from ....schemas.executor import (
    ExecutorNodeCreate, ExecutorNodeUpdate, ExecutorNode as ExecutorNodeSchema,
    ExecutorNodeQueryParams, ExecutorNodeListResponse, ExecutorNodeHeartbeat,
    ExecutorNodeStatusUpdate, ExecutorNodeStatus as ExecutorNodeStatusSchema,
    ClusterHealth, ClusterMetrics
)
from .auth import get_current_user
from ....models.user import User
from ....core.exceptions import (
    NotFoundError, ValidationError, AuthorizationError
)
from ....models.executor import ExecutorStatus as ExecutorNodeStatus
from ....models.task import TaskStatus

router = APIRouter()


# ============================================
# 执行器节点管理接口
# ============================================

@router.get("/nodes", response_model=ExecutorNodeListResponse)
async def list_executor_nodes(
    params: ExecutorNodeQueryParams = Depends(),
    group_id: Optional[int] = Query(None, description="执行器分组ID"),
    status: Optional[ExecutorNodeStatus] = Query(None, description="节点状态"),
    include_offline: bool = Query(True, description="是否包含离线节点"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取执行器节点列表"""
    query = db.query(ExecutorNode)
    
    # 应用过滤条件
    if group_id:
        query = query.filter(ExecutorNode.group_id == group_id)
    
    if params.node_name:
        query = query.filter(ExecutorNode.node_name.ilike(f"%{params.node_name}%"))
    
    if status:
        query = query.filter(ExecutorNode.status == status)
    elif not include_offline:
        query = query.filter(ExecutorNode.status != ExecutorNodeStatus.OFFLINE)
    
    # 应用排序
    if params.sort_by:
        if hasattr(ExecutorNode, params.sort_by):
            order_column = getattr(ExecutorNode, params.sort_by)
            if params.sort_order == "desc":
                query = query.order_by(order_column.desc())
            else:
                query = query.order_by(order_column.asc())
    else:
        query = query.order_by(ExecutorNode.last_heartbeat.desc())
    
    # 分页
    total = query.count()
    items = query.offset(params.skip).limit(params.limit).all()
    
    return ExecutorNodeListResponse(
        total=total,
        page=params.page,
        size=params.size,
        pages=(total + params.size - 1) // params.size,
        items=items
    )


@router.post("/nodes", response_model=ExecutorNodeSchema, status_code=status.HTTP_201_CREATED)
async def register_executor_node(
    node_data: ExecutorNodeCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """注册执行器节点"""
    service = await get_executor_cluster_service(db)
    return await service.register_executor_node(node_data)


@router.get("/nodes/{node_id}", response_model=ExecutorNodeSchema)
async def get_executor_node(
    node_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取执行器节点详情"""
    service = await get_executor_cluster_service(db)
    return await service.get_executor_node(node_id)


@router.put("/nodes/{node_id}", response_model=ExecutorNodeSchema)
async def update_executor_node(
    node_id: str,
    node_data: ExecutorNodeUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新执行器节点信息"""
    service = await get_executor_cluster_service(db)
    return await service.update_executor_node(node_id, node_data)


@router.delete("/nodes/{node_id}", status_code=status.HTTP_204_NO_CONTENT)
async def unregister_executor_node(
    node_id: str,
    force: bool = Query(False, description="是否强制删除（即使有运行中的任务）"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """注销执行器节点"""
    service = await get_executor_cluster_service(db)
    # 注意：service 中没有 force 参数的处理，这里先简单调用
    # 实际应该在 service 中添加 force 参数支持
    # 目前 service.unregister_executor_node 没有检查任务状态，
    # 我们可以先在 API 层检查，或者接受 service 的行为
    
    # 为了保持 API 行为一致，我们这里还是先检查任务
    if not force:
        # 使用 service 获取节点
        node = await service.get_executor_node(node_id)
        
        # 检查是否有运行中的任务 (这里需要手动查询，或者给 service 添加 check 方法)
        running_tasks = await db.scalar(
            select(func.count(TaskInstance.id)).where(
                and_(
                    TaskInstance.assigned_executor_node == node_id,
                    TaskInstance.status.in_([TaskStatus.RUNNING, TaskStatus.QUEUED])
                )
            )
        )
        
        if running_tasks > 0:
            raise ValidationError(f"节点 {node_id} 还有 {running_tasks} 个运行中的任务，请先停止任务或使用强制删除")
            
    await service.unregister_executor_node(node_id)


# ============================================
# 执行器节点心跳和状态管理
# ============================================

@router.post("/nodes/{node_id}/heartbeat")
async def executor_heartbeat(
    node_id: str,
    heartbeat_data: ExecutorNodeHeartbeat,
    db: AsyncSession = Depends(get_db)
):
    """执行器节点心跳接口"""
    service = await get_executor_cluster_service(db)
    await service.update_heartbeat(node_id, heartbeat_data)
    
    return {"status": "success", "message": "心跳更新成功"}


@router.post("/nodes/{node_id}/status")
async def update_executor_status(
    node_id: str,
    status_data: ExecutorNodeStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新执行器节点状态"""
    service = await get_executor_cluster_service(db)
    node = await service.update_node_status(node_id, status_data)
    
    return {
        "status": "success",
        "message": f"节点状态已更新为 {node.status}"
    }


@router.get("/nodes/{node_id}/status")
async def get_executor_status(
    node_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取执行器节点状态详情"""
    node = db.query(ExecutorNode).filter(ExecutorNode.node_id == node_id).first()
    if not node:
        raise NotFoundError(f"执行器节点 {node_id} 不存在")
    
    # 计算节点健康状态
    now = datetime.utcnow()
    last_heartbeat = node.last_heartbeat
    is_healthy = True
    health_message = "节点正常"
    
    if last_heartbeat:
        time_since_heartbeat = (now - last_heartbeat).total_seconds()
        if time_since_heartbeat > 300:  # 5分钟没有心跳
            is_healthy = False
            health_message = f"节点失联 {int(time_since_heartbeat)} 秒"
    else:
        is_healthy = False
        health_message = "从未收到心跳"
    
    # 获取当前运行的任务数量
    running_tasks = db.query(TaskInstance).filter(
        and_(
            TaskInstance.assigned_executor_node == node_id,
            TaskInstance.status == TaskStatus.RUNNING
        )
    ).count()
    
    return {
        "node_id": node.node_id,
        "node_name": node.node_name,
        "status": node.status,
        "is_healthy": is_healthy,
        "health_message": health_message,
        "last_heartbeat": last_heartbeat,
        "current_load": node.current_load,
        "max_concurrent_tasks": node.max_concurrent_tasks,
        "running_tasks": running_tasks,
        "is_available": node.is_available,
        "resource_info": node.resource_info,
        "capabilities": node.capabilities,
        "version": node.version
    }


@router.get("/nodes/{node_id}/tasks")
async def get_executor_tasks(
    node_id: str,
    status: Optional[TaskStatus] = Query(None, description="任务状态过滤"),
    limit: int = Query(50, ge=1, le=100, description="返回数量限制"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取执行器节点上的任务列表"""
    node = db.query(ExecutorNode).filter(ExecutorNode.node_id == node_id).first()
    if not node:
        raise NotFoundError(f"执行器节点 {node_id} 不存在")
    
    query = db.query(TaskInstance).filter(TaskInstance.assigned_executor_node == node_id)
    
    if status:
        query = query.filter(TaskInstance.status == status)
    
    tasks = query.order_by(TaskInstance.scheduled_time.desc()).limit(limit).all()
    
    return {
        "node_id": node_id,
        "total_tasks": len(tasks),
        "tasks": [
            {
                "instance_id": task.instance_id,
                "task_name": task.task_definition.name if task.task_definition else "Unknown",
                "status": task.status,
                "priority": task.priority,
                "scheduled_time": task.scheduled_time,
                "actual_start_time": task.actual_start_time,
                "actual_end_time": task.actual_end_time,
                "duration_seconds": task.duration_seconds
            }
            for task in tasks
        ]
    }


# ============================================
# 执行器节点监控和统计
# ============================================

@router.get("/nodes/health", response_model=ClusterHealth)
async def get_cluster_health(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取执行器集群健康状态"""
    now = datetime.utcnow()
    heartbeat_threshold = now - timedelta(minutes=5)
    
    # 统计各状态的节点数量
    total_nodes = db.query(ExecutorNode).count()
    online_nodes = db.query(ExecutorNode).filter(ExecutorNode.status == ExecutorNodeStatus.ONLINE).count()
    offline_nodes = db.query(ExecutorNode).filter(ExecutorNode.status == ExecutorNodeStatus.OFFLINE).count()
    busy_nodes = db.query(ExecutorNode).filter(ExecutorNode.status == ExecutorNodeStatus.BUSY).count()
    maintenance_nodes = db.query(ExecutorNode).filter(ExecutorNode.status == ExecutorNodeStatus.MAINTENANCE).count()
    error_nodes = db.query(ExecutorNode).filter(ExecutorNode.status == ExecutorNodeStatus.ERROR).count()
    
    # 统计健康节点（最近5分钟有心跳）
    healthy_nodes = db.query(ExecutorNode).filter(
        ExecutorNode.last_heartbeat >= heartbeat_threshold
    ).count()
    
    # 统计总负载
    total_capacity = db.query(func.sum(ExecutorNode.max_concurrent_tasks)).scalar() or 0
    current_load = db.query(func.sum(ExecutorNode.current_load)).scalar() or 0
    
    # 计算空闲节点数（在线但不繁忙的节点）
    idle_nodes = online_nodes - busy_nodes
    
    # 计算集群利用率
    utilization_rate = (current_load / total_capacity * 100) if total_capacity > 0 else 0
    
    # 计算平均负载
    avg_load = (current_load / online_nodes) if online_nodes > 0 else 0
    
    return ClusterHealth(
        total_nodes=total_nodes,
        online_nodes=online_nodes,
        offline_nodes=offline_nodes,
        busy_nodes=busy_nodes,
        idle_nodes=idle_nodes,
        total_capacity=total_capacity,
        used_capacity=current_load,
        utilization_rate=round(utilization_rate, 2),
        avg_load=round(avg_load, 2),
        health_score=round((healthy_nodes / total_nodes * 100) if total_nodes > 0 else 0, 2)
    )


@router.get("/nodes/metrics", response_model=ClusterMetrics)
async def get_cluster_metrics(
    time_range: int = Query(24, description="时间范围（小时）"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取执行器集群性能指标"""
    # 这里可以实现更复杂的性能指标统计
    # 目前返回基本的统计信息
    
    nodes = db.query(ExecutorNode).all()
    
    node_metrics = []
    total_capacity = 0
    total_load = 0
    online_nodes = 0
    
    for node in nodes:
        utilization_rate = round((node.current_load / node.max_concurrent_tasks * 100) if node.max_concurrent_tasks > 0 else 0, 2)
        
        node_metric = {
            "node_id": node.node_id,
            "node_name": node.node_name,
            "status": node.status,
            "current_load": node.current_load,
            "max_concurrent_tasks": node.max_concurrent_tasks,
            "utilization_rate": utilization_rate,
            "resource_info": node.resource_info or {},
            "last_heartbeat": node.last_heartbeat.isoformat() if node.last_heartbeat else None
        }
        node_metrics.append(node_metric)
        
        # 统计汇总数据
        total_capacity += node.max_concurrent_tasks
        total_load += node.current_load
        if node.status == ExecutorNodeStatus.ONLINE:
            online_nodes += 1
    
    # 计算汇总指标
    cluster_utilization = round((total_load / total_capacity * 100) if total_capacity > 0 else 0, 2)
    avg_utilization = round(sum(node["utilization_rate"] for node in node_metrics) / len(node_metrics) if node_metrics else 0, 2)
    
    summary = {
        "total_nodes": len(nodes),
        "online_nodes": online_nodes,
        "total_capacity": total_capacity,
        "total_load": total_load,
        "cluster_utilization": cluster_utilization,
        "avg_utilization": avg_utilization,
        "time_range_hours": time_range
    }
    
    return ClusterMetrics(
        timestamp=datetime.utcnow(),
        nodes=node_metrics,
        summary=summary
    )


# ============================================
# 后台任务：清理离线节点
# ============================================

async def cleanup_offline_nodes(db: AsyncSession):
    """清理长时间离线的节点"""
    offline_threshold = datetime.utcnow() - timedelta(hours=24)  # 24小时没有心跳
    
    offline_nodes = db.query(ExecutorNode).filter(
        or_(
            ExecutorNode.last_heartbeat < offline_threshold,
            ExecutorNode.last_heartbeat.is_(None)
        )
    ).all()
    
    for node in offline_nodes:
        # 检查是否有运行中的任务
        running_tasks = db.query(TaskInstance).filter(
            and_(
                TaskInstance.assigned_executor_node == node.node_id,
                TaskInstance.status.in_([TaskStatus.RUNNING, TaskStatus.QUEUED])
            )
        ).count()
        
        if running_tasks == 0:
            node.status = ExecutorNodeStatus.OFFLINE
    
    db.commit()


@router.post("/maintenance/cleanup-offline")
async def trigger_cleanup_offline_nodes(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """手动触发清理离线节点"""
    background_tasks.add_task(cleanup_offline_nodes, db)
    return {"status": "success", "message": "离线节点清理任务已启动"}