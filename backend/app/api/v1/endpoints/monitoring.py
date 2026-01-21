
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
import psutil
import socket
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, case, select, desc

from app.core.database import get_db
from app.core.config import settings
from app.models.executor import ExecutorNode, ExecutorStatus
from app.models.workflow import WorkflowInstance, InstanceStatus, Workflow
from app.models.task import TaskDefinition, TaskStatus

router = APIRouter()

@router.get("/stats")
async def get_system_stats(
    project_id: Optional[int] = None,
    time_range: str = "24h",
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    获取系统统计信息
    """
    # 计算时间范围
    start_time = get_start_time(time_range)
    
    # 基础查询
    workflow_query = select(WorkflowInstance)
    task_query = select(TaskDefinition) # 简化：这里应该查任务实例，但为了演示用任务定义或Executor的current_load
    
    if project_id:
        # workflow_query = workflow_query.join(Workflow).where(Workflow.project_id == project_id)
        pass # 暂不实现项目过滤，需要关联查询
    
    if start_time:
        workflow_query = workflow_query.where(WorkflowInstance.created_at >= start_time)
    
    # 统计运行中工作流
    running_workflows = await db.scalar(
        select(func.count(WorkflowInstance.id)).where(WorkflowInstance.status == InstanceStatus.RUNNING)
    )
    
    # 统计等待中任务 (这里简化为查询处于PENDING状态的工作流实例，实际应查TaskInstance)
    pending_tasks = await db.scalar(
        select(func.count(WorkflowInstance.id)).where(WorkflowInstance.status == InstanceStatus.PENDING)
    )
    
    # 统计错误数量
    error_count = await db.scalar(
        select(func.count(WorkflowInstance.id)).where(WorkflowInstance.status == InstanceStatus.FAILED)
    )
    
    # 统计总执行数和成功数
    total_executions = await db.scalar(select(func.count(WorkflowInstance.id)))
    success_executions = await db.scalar(
        select(func.count(WorkflowInstance.id)).where(WorkflowInstance.status == InstanceStatus.SUCCESS)
    )
    
    return {
        "running_workflows": running_workflows,
        "pending_tasks": pending_tasks,
        "error_count": error_count,
        "total_executions": total_executions,
        "success_executions": success_executions
    }

@router.get("/resources")
async def get_resource_usage(
    type: str = Query(..., description="资源类型: cpu, memory, disk"),
    time_range: str = "24h",
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    获取资源使用情况
    """
    # 获取所有在线执行器
    result = await db.scalars(
        select(ExecutorNode).where(ExecutorNode.status != ExecutorStatus.OFFLINE)
    )
    executors = result.all()
    
    # 聚合资源使用率 (简单平均)
    usage_list = []
    
    # 这里只是模拟历史数据，实际应该从时序数据库或日志中聚合
    # 为了演示，我们返回当前值，并模拟一些历史点
    
    current_avg = 0
    if executors:
        total = 0
        count = 0
        for exe in executors:
            if exe.resource_usage:
                # resource_usage 格式可能是 {'cpu_percent': 10, ...}
                usage = exe.resource_usage
                key = f"{type}_percent"
                if key in usage:
                    total += usage[key]
                    count += 1
        if count > 0:
            current_avg = round(total / count, 2)
            
    # 构造模拟的时间序列数据
    labels = []
    values = []
    now = datetime.now()
    
    # 生成过去10个点的数据
    for i in range(10, -1, -1):
        t = now - timedelta(minutes=i*5)
        labels.append(t.strftime("%H:%M"))
        # 模拟波动
        import random
        variation = random.uniform(-5, 5)
        val = max(0, min(100, current_avg + variation))
        values.append(round(val, 2))
        
    return {
        "labels": labels,
        "values": values
    }

@router.get("/active-workflows")
async def get_active_workflows(
    project_id: Optional[int] = None,
    page: int = 1,
    size: int = 10,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    获取活跃工作流
    """
    offset = (page - 1) * size
    
    query = select(WorkflowInstance).where(
        WorkflowInstance.status == InstanceStatus.RUNNING
    ).order_by(desc(WorkflowInstance.actual_start_time)).offset(offset).limit(size)
    
    result = await db.scalars(query)
    instances = result.all()
    
    items = []
    for ins in instances:
        # 获取工作流名称
        wf = await db.get(Workflow, ins.workflow_id)
        wf_name = wf.name if wf else "Unknown"
        
        # 计算进度 (模拟)
        progress = 0
        if ins.actual_start_time:
            elapsed = (datetime.utcnow() - ins.actual_start_time).total_seconds()
            progress = min(99, int(elapsed / 60 * 10)) # 假设平均10分钟
            
        items.append({
            "id": ins.id,
            "name": ins.instance_name or wf_name,
            "project_name": "Default Project", # 暂不关联项目表
            "status": ins.status.value,
            "started_at": ins.actual_start_time,
            "duration": ins.duration_seconds,
            "progress": progress
        })
        
    return {"items": items, "total": len(items)}

@router.get("/alerts")
async def get_system_alerts(
    project_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db)
) -> List[Dict[str, Any]]:
    """
    获取系统警告
    """
    # 检查是否有异常节点
    result = await db.scalars(
        select(ExecutorNode).where(ExecutorNode.status == ExecutorStatus.ERROR)
    )
    error_nodes = result.all()
    
    alerts = []
    for node in error_nodes:
        alerts.append({
            "id": f"node-{node.id}",
            "title": "执行器异常",
            "description": f"节点 {node.node_name} 处于错误状态",
            "type": "error",
            "message": f"节点 {node.node_name} ({node.host_ip}) 无法连接或报告错误",
            "created_at": node.updated_at
        })
        
    return alerts

@router.get("/trend")
async def get_execution_trend(
    project_id: Optional[int] = None,
    time_range: str = "24h",
    type: str = "count",
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    获取执行趋势
    """
    # 模拟数据
    labels = ["00:00", "04:00", "08:00", "12:00", "16:00", "20:00"]
    return {
        "labels": labels,
        "success": [10, 15, 25, 30, 20, 15],
        "failed": [1, 0, 2, 1, 0, 1],
        "cancelled": [0, 0, 1, 0, 0, 0]
    }

@router.get("/distribution")
async def get_status_distribution(
    project_id: Optional[int] = None,
    time_range: str = "24h",
    db: AsyncSession = Depends(get_db)
) -> Dict[str, int]:
    """
    获取状态分布
    """
    start_time = get_start_time(time_range)
    
    query = select(WorkflowInstance.status, func.count(WorkflowInstance.id)).group_by(WorkflowInstance.status)
    
    if start_time:
        query = query.where(WorkflowInstance.created_at >= start_time)
        
    result = await db.execute(query)
    results = result.all()
    
    dist = {
        "success": 0,
        "failed": 0,
        "running": 0,
        "pending": 0,
        "cancelled": 0
    }
    
    for status, count in results:
        key = status.value
        if key in dist:
            dist[key] = count
            
    return dist

from app.models.scheduler import SchedulerNode, SchedulerStatus

@router.get("/nodes")
async def get_cluster_nodes(
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    获取集群节点信息（执行器和调度器）
    """
    # 获取执行器节点
    # 过滤掉超过5分钟没有心跳的节点，或者状态为OFFLINE的节点
    heartbeat_threshold = datetime.utcnow() - timedelta(minutes=5)
    
    result = await db.scalars(
        select(ExecutorNode).where(
            ExecutorNode.last_heartbeat >= heartbeat_threshold
        )
    )
    executors = result.all()
    executor_list = []
    for exe in executors:
        resource_usage = exe.resource_usage or {}
        executor_list.append({
            "id": exe.id,
            "node_id": exe.node_id,
            "node_name": exe.node_name,
            "host_ip": exe.host_ip,
            "port": exe.port,
            "status": exe.status.value,
            "group_id": exe.group_id,
            "current_load": exe.current_load,
            "max_concurrent_tasks": exe.max_concurrent_tasks,
            "last_heartbeat": exe.last_heartbeat,
            "resource_usage": resource_usage
        })
        
    # 获取调度器节点
    result = await db.scalars(
        select(SchedulerNode).where(
            SchedulerNode.last_heartbeat >= heartbeat_threshold
        )
    )
    schedulers = result.all()
    scheduler_list = []
    for sch in schedulers:
        # 调度器模型中 metrics 字段存储资源信息
        resource_usage = sch.metrics or {}
        scheduler_list.append({
            "id": sch.id,
            "node_id": sch.node_id,
            "node_name": sch.node_name,
            "host_ip": sch.host_ip,
            "port": sch.port,
            "status": sch.status,
            "is_leader": sch.role == "leader",
            "last_heartbeat": sch.last_heartbeat,
            "resource_usage": resource_usage
        })
    
    # 获取主服务信息
    try:
        host_ip = socket.gethostbyname(socket.gethostname())
    except:
        host_ip = "127.0.0.1"
        
    main_service = {
        "node_id": "main-service",
        "node_name": "Main API Service",
        "host_ip": host_ip,
        "port": settings.PORT,
        "status": "online",
        "version": settings.VERSION,
        "resource_usage": {
            "cpu_percent": psutil.cpu_percent(interval=None),
            "memory_percent": psutil.virtual_memory().percent
        },
        "role": "master"
    }
        
    return {
        "main_service": main_service,
        "executors": executor_list,
        "schedulers": scheduler_list,
        "total_executors": len(executor_list),
        "total_schedulers": len(scheduler_list),
        "online_executors": len([e for e in executor_list if e['status'] == 'online']),
        "online_schedulers": len([s for s in scheduler_list if s['status'] in ['active', 'online']]),
    }

def get_start_time(time_range: str) -> Optional[datetime]:
    now = datetime.utcnow()
    if time_range == "1h":
        return now - timedelta(hours=1)
    elif time_range == "6h":
        return now - timedelta(hours=6)
    elif time_range == "24h":
        return now - timedelta(hours=24)
    elif time_range == "7d":
        return now - timedelta(days=7)
    elif time_range == "30d":
        return now - timedelta(days=30)
    return None
