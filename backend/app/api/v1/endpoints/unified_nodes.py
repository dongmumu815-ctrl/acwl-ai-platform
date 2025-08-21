from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete
from sqlalchemy.orm import selectinload
from typing import List, Optional
from datetime import datetime

from ....core.database import get_db
from ....models.unified_node import (
    UnifiedNode, UnifiedNodeInstance, NodeExecution, NodeLog, NodeResult
)
from ....models.project import Project
from ....models.workflow import Workflow
from ....schemas.unified_node import (
    # 统一节点相关
    UnifiedNodeCreate, UnifiedNodeUpdate, UnifiedNodeResponse as UnifiedNodeSchema,
    UnifiedNodeQueryParams, UnifiedNodeListResponse,
    
    # 统一节点实例相关
    UnifiedNodeInstanceCreate, UnifiedNodeInstanceUpdate, UnifiedNodeInstanceResponse as UnifiedNodeInstanceSchema,
    UnifiedNodeInstanceQueryParams, UnifiedNodeInstanceListResponse,
    
    # 节点执行相关
    NodeExecuteRequest, NodeExecutionUpdate, NodeExecutionResponse as NodeExecutionSchema,
    
    # 节点日志相关
    NodeLogCreate, NodeLogResponse as NodeLogSchema, NodeLogQueryParams,
    NodeLogListResponse,
    
    # 节点结果相关
    NodeResultCreate, NodeResultResponse as NodeResultSchema,
    
    # 统计相关
    NodeExecutionStats, NodeExecutionStatsListResponse
)
from .auth import get_current_user
from ....models.user import User
from ....core.exceptions import (
    NotFoundError, ValidationError, AuthorizationError
)

router = APIRouter()


# ============================================
# 统一节点管理接口
# ============================================

@router.get("/", response_model=UnifiedNodeListResponse)
async def list_unified_nodes(
    params: UnifiedNodeQueryParams = Depends(),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取统一节点列表"""
    # 构建基础查询，包含项目和工作流信息的关联查询
    query = select(
        UnifiedNode, 
        Project.name.label('project_name'),
        Workflow.name.label('workflow_name')
    ).outerjoin(
        Project, UnifiedNode.project_id == Project.id
    ).outerjoin(
        Workflow, UnifiedNode.workflow_id == Workflow.id
    )
    
    # 应用过滤条件
    if params.name:
        query = query.where(UnifiedNode.name.ilike(f"%{params.name}%"))
    if params.node_type:
        query = query.where(UnifiedNode.node_type == params.node_type)
    if params.node_status:
        query = query.where(UnifiedNode.node_status == params.node_status)
    if params.node_category:
        query = query.where(UnifiedNode.node_category == params.node_category)
    if params.project_id:
        query = query.where(UnifiedNode.project_id == params.project_id)
    if params.workflow_id:
        query = query.where(UnifiedNode.workflow_id == params.workflow_id)
    if params.created_by:
        query = query.where(UnifiedNode.created_by == params.created_by)
    if params.is_template is not None:
        query = query.where(UnifiedNode.is_template == params.is_template)
    if params.is_system is not None:
        query = query.where(UnifiedNode.is_system == params.is_system)
    
    # 应用排序
    if params.sort_by:
        if hasattr(UnifiedNode, params.sort_by):
            order_column = getattr(UnifiedNode, params.sort_by)
            if params.sort_order == "desc":
                query = query.order_by(order_column.desc())
            else:
                query = query.order_by(order_column.asc())
    else:
        query = query.order_by(UnifiedNode.created_at.desc())
    
    # 获取总数
    count_query = select(func.count(UnifiedNode.id))
    if params.name:
        count_query = count_query.where(UnifiedNode.name.ilike(f"%{params.name}%"))
    if params.node_type:
        count_query = count_query.where(UnifiedNode.node_type == params.node_type)
    if params.node_status:
        count_query = count_query.where(UnifiedNode.node_status == params.node_status)
    if params.node_category:
        count_query = count_query.where(UnifiedNode.node_category == params.node_category)
    if params.project_id:
        count_query = count_query.where(UnifiedNode.project_id == params.project_id)
    if params.workflow_id:
        count_query = count_query.where(UnifiedNode.workflow_id == params.workflow_id)
    if params.created_by:
        count_query = count_query.where(UnifiedNode.created_by == params.created_by)
    if params.is_template is not None:
        count_query = count_query.where(UnifiedNode.is_template == params.is_template)
    if params.is_system is not None:
        count_query = count_query.where(UnifiedNode.is_system == params.is_system)
    
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # 应用分页
    query = query.offset(params.offset).limit(params.limit)
    
    # 执行查询
    result = await db.execute(query)
    rows = result.fetchall()
    
    # 构建响应数据
    items = []
    for row in rows:
        node = row[0]
        project_name = row[1] if len(row) > 1 else None
        workflow_name = row[2] if len(row) > 2 else None
        
        node_dict = {
            **node.__dict__,
            'project_name': project_name,
            'workflow_name': workflow_name
        }
        items.append(node_dict)
    
    return {
        "items": items,
        "total": total,
        "page": params.page,
        "size": params.limit,
        "pages": (total + params.limit - 1) // params.limit
    }


@router.post("/", response_model=UnifiedNodeSchema, status_code=status.HTTP_201_CREATED)
async def create_unified_node(
    node_data: UnifiedNodeCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建统一节点"""
    # 检查节点名称是否已存在（在同一项目或工作流中）
    existing_query = select(UnifiedNode).where(
        UnifiedNode.name == node_data.name
    )
    if node_data.project_id:
        existing_query = existing_query.where(UnifiedNode.project_id == node_data.project_id)
    if node_data.workflow_id:
        existing_query = existing_query.where(UnifiedNode.workflow_id == node_data.workflow_id)
    
    existing_result = await db.execute(existing_query)
    existing_node = existing_result.scalar_one_or_none()
    
    if existing_node:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="节点名称已存在"
        )
    
    # 创建新节点
    new_node = UnifiedNode(
        **node_data.dict(),
        created_by=current_user.id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    db.add(new_node)
    await db.commit()
    await db.refresh(new_node)
    
    return new_node


@router.get("/{node_id}", response_model=UnifiedNodeSchema)
async def get_unified_node(
    node_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取统一节点详情"""
    query = select(UnifiedNode).where(UnifiedNode.id == node_id)
    result = await db.execute(query)
    node = result.scalar_one_or_none()
    
    if not node:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="节点不存在"
        )
    
    return node


@router.put("/{node_id}", response_model=UnifiedNodeSchema)
async def update_unified_node(
    node_id: int,
    node_data: UnifiedNodeUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新统一节点"""
    # 获取现有节点
    query = select(UnifiedNode).where(UnifiedNode.id == node_id)
    result = await db.execute(query)
    node = result.scalar_one_or_none()
    
    if not node:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="节点不存在"
        )
    
    # 检查名称冲突（如果更新了名称）
    if node_data.name and node_data.name != node.name:
        existing_query = select(UnifiedNode).where(
            UnifiedNode.name == node_data.name,
            UnifiedNode.id != node_id
        )
        if node.project_id:
            existing_query = existing_query.where(UnifiedNode.project_id == node.project_id)
        if node.workflow_id:
            existing_query = existing_query.where(UnifiedNode.workflow_id == node.workflow_id)
        
        existing_result = await db.execute(existing_query)
        existing_node = existing_result.scalar_one_or_none()
        
        if existing_node:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="节点名称已存在"
            )
    
    # 更新节点属性
    update_data = node_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(node, field, value)
    
    node.updated_at = datetime.utcnow()
    node.updated_by = current_user.id
    
    await db.commit()
    await db.refresh(node)
    
    return node


@router.delete("/{node_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_unified_node(
    node_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除统一节点"""
    # 检查节点是否存在
    query = select(UnifiedNode).where(UnifiedNode.id == node_id)
    result = await db.execute(query)
    node = result.scalar_one_or_none()
    
    if not node:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="节点不存在"
        )
    
    # 检查是否有正在运行的实例
    running_instances_query = select(func.count(UnifiedNodeInstance.id)).where(
        UnifiedNodeInstance.node_id == node_id,
        UnifiedNodeInstance.instance_status.in_(['pending', 'running', 'paused'])
    )
    running_result = await db.execute(running_instances_query)
    running_count = running_result.scalar()
    
    if running_count > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"无法删除节点，存在 {running_count} 个正在运行的实例"
        )
    
    # 删除节点（级联删除相关的实例、执行记录等）
    await db.delete(node)
    await db.commit()


# ============================================
# 统一节点实例管理接口
# ============================================

@router.post("/{node_id}/execute", response_model=UnifiedNodeInstanceSchema, status_code=status.HTTP_201_CREATED)
async def execute_unified_node(
    node_id: int,
    execute_request: NodeExecuteRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """执行统一节点"""
    # 检查节点是否存在
    node_query = select(UnifiedNode).where(UnifiedNode.id == node_id)
    node_result = await db.execute(node_query)
    node = node_result.scalar_one_or_none()
    
    if not node:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="节点不存在"
        )
    
    # 检查节点状态
    if node.node_status != 'active':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="节点状态不允许执行"
        )
    
    # 创建节点实例
    new_instance = UnifiedNodeInstance(
        node_id=node_id,
        instance_name=execute_request.instance_name or f"{node.name}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
        instance_status='pending',
        priority=execute_request.priority or 'medium',
        input_data=execute_request.input_data,
        config_override=execute_request.config_override,
        workflow_instance_id=execute_request.workflow_instance_id,
        triggered_by=current_user.id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    db.add(new_instance)
    await db.commit()
    await db.refresh(new_instance)
    
    # TODO: 这里应该触发实际的执行逻辑，比如发送到消息队列
    
    return new_instance


@router.get("/instances", response_model=UnifiedNodeInstanceListResponse)
async def list_unified_node_instances(
    params: UnifiedNodeInstanceQueryParams = Depends(),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取统一节点实例列表"""
    # 构建基础查询，包含节点信息的关联查询
    query = select(
        UnifiedNodeInstance,
        UnifiedNode.name.label('node_name'),
        UnifiedNode.node_type.label('node_type')
    ).join(
        UnifiedNode, UnifiedNodeInstance.node_id == UnifiedNode.id
    )
    
    # 应用过滤条件
    if params.instance_name:
        query = query.where(UnifiedNodeInstance.instance_name.ilike(f"%{params.instance_name}%"))
    if params.instance_status:
        query = query.where(UnifiedNodeInstance.instance_status == params.instance_status)
    if params.node_id:
        query = query.where(UnifiedNodeInstance.node_id == params.node_id)
    if params.workflow_instance_id:
        query = query.where(UnifiedNodeInstance.workflow_instance_id == params.workflow_instance_id)
    if params.triggered_by:
        query = query.where(UnifiedNodeInstance.triggered_by == params.triggered_by)
    if params.priority:
        query = query.where(UnifiedNodeInstance.priority == params.priority)
    
    # 应用排序
    if params.sort_by:
        if hasattr(UnifiedNodeInstance, params.sort_by):
            order_column = getattr(UnifiedNodeInstance, params.sort_by)
            if params.sort_order == "desc":
                query = query.order_by(order_column.desc())
            else:
                query = query.order_by(order_column.asc())
    else:
        query = query.order_by(UnifiedNodeInstance.created_at.desc())
    
    # 获取总数
    count_query = select(func.count(UnifiedNodeInstance.id))
    if params.instance_name:
        count_query = count_query.where(UnifiedNodeInstance.instance_name.ilike(f"%{params.instance_name}%"))
    if params.instance_status:
        count_query = count_query.where(UnifiedNodeInstance.instance_status == params.instance_status)
    if params.node_id:
        count_query = count_query.where(UnifiedNodeInstance.node_id == params.node_id)
    if params.workflow_instance_id:
        count_query = count_query.where(UnifiedNodeInstance.workflow_instance_id == params.workflow_instance_id)
    if params.triggered_by:
        count_query = count_query.where(UnifiedNodeInstance.triggered_by == params.triggered_by)
    if params.priority:
        count_query = count_query.where(UnifiedNodeInstance.priority == params.priority)
    
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # 应用分页
    query = query.offset(params.offset).limit(params.limit)
    
    # 执行查询
    result = await db.execute(query)
    rows = result.fetchall()
    
    # 构建响应数据
    items = []
    for row in rows:
        instance = row[0]
        node_name = row[1] if len(row) > 1 else None
        node_type = row[2] if len(row) > 2 else None
        
        instance_dict = {
            **instance.__dict__,
            'node_name': node_name,
            'node_type': node_type
        }
        items.append(instance_dict)
    
    return {
        "items": items,
        "total": total,
        "page": params.page,
        "size": params.limit,
        "pages": (total + params.limit - 1) // params.limit
    }


@router.get("/instances/{instance_id}", response_model=UnifiedNodeInstanceSchema)
async def get_unified_node_instance(
    instance_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取统一节点实例详情"""
    query = select(UnifiedNodeInstance).where(UnifiedNodeInstance.id == instance_id)
    result = await db.execute(query)
    instance = result.scalar_one_or_none()
    
    if not instance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="节点实例不存在"
        )
    
    return instance


@router.post("/instances/{instance_id}/cancel", response_model=UnifiedNodeInstanceSchema)
async def cancel_unified_node_instance(
    instance_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """取消统一节点实例"""
    # 获取实例
    query = select(UnifiedNodeInstance).where(UnifiedNodeInstance.id == instance_id)
    result = await db.execute(query)
    instance = result.scalar_one_or_none()
    
    if not instance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="节点实例不存在"
        )
    
    # 检查实例状态
    if instance.instance_status not in ['pending', 'running', 'paused']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="实例状态不允许取消"
        )
    
    # 更新实例状态
    instance.instance_status = 'cancelled'
    instance.finished_at = datetime.utcnow()
    instance.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(instance)
    
    # TODO: 这里应该通知执行器取消任务
    
    return instance


# ============================================
# 节点日志管理接口
# ============================================

@router.get("/instances/{instance_id}/logs", response_model=NodeLogListResponse)
async def list_node_logs(
    instance_id: int,
    params: NodeLogQueryParams = Depends(),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取节点实例日志列表"""
    # 检查实例是否存在
    instance_query = select(UnifiedNodeInstance).where(UnifiedNodeInstance.id == instance_id)
    instance_result = await db.execute(instance_query)
    instance = instance_result.scalar_one_or_none()
    
    if not instance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="节点实例不存在"
        )
    
    # 构建日志查询
    query = select(NodeLog).where(NodeLog.instance_id == instance_id)
    
    # 应用过滤条件
    if params.log_level:
        query = query.where(NodeLog.log_level == params.log_level)
    if params.start_time:
        query = query.where(NodeLog.created_at >= params.start_time)
    if params.end_time:
        query = query.where(NodeLog.created_at <= params.end_time)
    if params.keyword:
        query = query.where(NodeLog.message.ilike(f"%{params.keyword}%"))
    
    # 应用排序
    if params.sort_order == "desc":
        query = query.order_by(NodeLog.created_at.desc())
    else:
        query = query.order_by(NodeLog.created_at.asc())
    
    # 获取总数
    count_query = select(func.count(NodeLog.id)).where(NodeLog.instance_id == instance_id)
    if params.log_level:
        count_query = count_query.where(NodeLog.log_level == params.log_level)
    if params.start_time:
        count_query = count_query.where(NodeLog.created_at >= params.start_time)
    if params.end_time:
        count_query = count_query.where(NodeLog.created_at <= params.end_time)
    if params.keyword:
        count_query = count_query.where(NodeLog.message.ilike(f"%{params.keyword}%"))
    
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # 应用分页
    query = query.offset(params.offset).limit(params.limit)
    
    # 执行查询
    result = await db.execute(query)
    logs = result.scalars().all()
    
    return {
        "items": logs,
        "total": total,
        "page": params.page,
        "size": params.limit,
        "pages": (total + params.limit - 1) // params.limit
    }


# ============================================
# 节点执行统计接口
# ============================================

@router.get("/execution-stats", response_model=NodeExecutionStatsListResponse)
async def get_node_execution_stats(
    node_id: Optional[int] = Query(None, description="节点ID"),
    node_type: Optional[str] = Query(None, description="节点类型"),
    limit: int = Query(50, ge=1, le=100, description="返回数量限制"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取节点执行统计信息"""
    # 构建统计查询
    query = select(
        UnifiedNode.id,
        UnifiedNode.name,
        UnifiedNode.node_type,
        func.count(UnifiedNodeInstance.id).label('total_executions'),
        func.sum(
            func.case(
                (UnifiedNodeInstance.instance_status == 'completed', 1),
                else_=0
            )
        ).label('successful_executions'),
        func.sum(
            func.case(
                (UnifiedNodeInstance.instance_status == 'failed', 1),
                else_=0
            )
        ).label('failed_executions'),
        func.avg(
            func.case(
                (UnifiedNodeInstance.instance_status == 'completed',
                 func.extract('epoch', UnifiedNodeInstance.finished_at - UnifiedNodeInstance.started_at)),
                else_=None
            )
        ).label('avg_execution_time')
    ).select_from(
        UnifiedNode
    ).outerjoin(
        UnifiedNodeInstance, UnifiedNode.id == UnifiedNodeInstance.node_id
    ).group_by(
        UnifiedNode.id, UnifiedNode.name, UnifiedNode.node_type
    )
    
    # 应用过滤条件
    if node_id:
        query = query.where(UnifiedNode.id == node_id)
    if node_type:
        query = query.where(UnifiedNode.node_type == node_type)
    
    # 应用排序和限制
    query = query.order_by(func.count(UnifiedNodeInstance.id).desc()).limit(limit)
    
    # 执行查询
    result = await db.execute(query)
    stats = result.fetchall()
    
    # 构建响应数据
    items = []
    for stat in stats:
        success_rate = 0.0
        if stat.total_executions > 0:
            success_rate = (stat.successful_executions or 0) / stat.total_executions * 100
        
        items.append({
            "node_id": stat.id,
            "node_name": stat.name,
            "node_type": stat.node_type,
            "total_executions": stat.total_executions or 0,
            "successful_executions": stat.successful_executions or 0,
            "failed_executions": stat.failed_executions or 0,
            "success_rate": round(success_rate, 2),
            "avg_execution_time": round(stat.avg_execution_time or 0, 2)
        })
    
    return {
        "items": items,
        "total": len(items)
    }