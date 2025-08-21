from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import datetime

from ....core.database import get_db
from ....models.task import (
    TaskDefinition, TaskTemplate, TaskDependency,
    TaskSchedule, TaskInstance, TaskExecution, TaskLog, TaskResult
)
from ....models.unified_node import UnifiedNode, UnifiedNodeInstance
from ....models.executor import ExecutorGroup, ExecutorNode
from ....schemas.task import (
    # 任务定义相关
    TaskDefinitionCreate, TaskDefinitionUpdate, TaskDefinition as TaskDefinitionSchema,
    TaskDefinitionQueryParams, TaskDefinitionListResponse,
    
    # 任务模板相关
    TaskTemplateCreate, TaskTemplateUpdate, TaskTemplate as TaskTemplateSchema,
    TaskTemplateQueryParams, TaskTemplateListResponse,
    
    # 任务依赖相关
    TaskDependencyCreate, TaskDependencyUpdate, TaskDependency as TaskDependencySchema,
    

    
    # 任务调度相关
    TaskScheduleCreate, TaskScheduleUpdate, TaskSchedule as TaskScheduleSchema,
    TaskScheduleQueryParams, TaskScheduleListResponse,
    
    # 任务实例相关
    TaskInstanceCreate, TaskInstanceUpdate, TaskInstance as TaskInstanceSchema,
    TaskInstanceQueryParams, TaskInstanceListResponse,
    TaskExecuteRequest, TaskExecutionStatus, TaskExecutionStatusListResponse,
    
    # 任务执行相关
    TaskExecutionUpdate, TaskExecution as TaskExecutionSchema,
    TaskExecutionQueryParams, TaskExecutionListResponse,
    
    # 任务日志相关
    TaskLogCreate, TaskLog as TaskLogSchema,
    TaskLogQueryParams, TaskLogListResponse,
    
    # 任务结果相关
    TaskResultCreate, TaskResult as TaskResultSchema,
    
    # 统计相关
    TaskExecutionStats, TaskExecutionStatsListResponse
)
from ....schemas.executor import (
    ExecutorGroupCreate, ExecutorGroupUpdate, ExecutorGroup as ExecutorGroupSchema,
    ExecutorNodeCreate, ExecutorNodeUpdate, ExecutorNode as ExecutorNodeSchema,
    ExecutorGroupQueryParams, ExecutorGroupListResponse,
    ExecutorNodeQueryParams, ExecutorNodeListResponse
)
from .auth import get_current_user
from ....models.user import User
from ....core.exceptions import (
    NotFoundError, ValidationError, AuthorizationError
)

router = APIRouter()


# ============================================
# 任务定义管理接口（兼容性接口，推荐使用统一节点接口）
# ============================================

@router.get("/definitions", response_model=TaskDefinitionListResponse)
async def list_task_definitions(
    params: TaskDefinitionQueryParams = Depends(),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取任务定义列表"""
    query = db.query(TaskDefinition)
    
    # 应用过滤条件
    if params.task_name:
        query = query.filter(TaskDefinition.task_name.ilike(f"%{params.task_name}%"))
    if params.task_type:
        query = query.filter(TaskDefinition.task_type == params.task_type)
    if params.task_status:
        query = query.filter(TaskDefinition.task_status == params.task_status)
    if params.task_category:
        query = query.filter(TaskDefinition.task_category == params.task_category)
    if params.project_id:
        query = query.filter(TaskDefinition.project_id == params.project_id)
    if params.workflow_id:
        query = query.filter(TaskDefinition.workflow_id == params.workflow_id)
    if params.created_by:
        query = query.filter(TaskDefinition.created_by == params.created_by)
    if params.is_template is not None:
        query = query.filter(TaskDefinition.is_template == params.is_template)
    if params.is_system is not None:
        query = query.filter(TaskDefinition.is_system == params.is_system)
    
    # 应用排序
    if params.sort_by:
        if hasattr(TaskDefinition, params.sort_by):
            order_column = getattr(TaskDefinition, params.sort_by)
            if params.sort_order == "desc":
                query = query.order_by(order_column.desc())
            else:
                query = query.order_by(order_column.asc())
    else:
        query = query.order_by(TaskDefinition.created_at.desc())
    
    # 应用分页
    total = query.count()
    task_definitions = query.offset(params.skip).limit(params.limit).all()
    
    return TaskDefinitionListResponse(
        items=task_definitions,
        total=total,
        page=params.page,
        size=params.size,
        pages=(total + params.size - 1) // params.size
    )


@router.post("/definitions", response_model=TaskDefinitionSchema, status_code=status.HTTP_201_CREATED)
async def create_task_definition(
    task_data: TaskDefinitionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建任务定义"""
    # 检查任务名称是否已存在
    existing_task = db.query(TaskDefinition).filter(
        TaskDefinition.task_name == task_data.task_name
    ).first()
    if existing_task:
        raise ValidationError(f"任务名称 '{task_data.task_name}' 已存在")
    
    # 创建任务定义
    task_definition = TaskDefinition(
        **task_data.model_dump(),
        created_by=current_user.id
    )
    db.add(task_definition)
    db.commit()
    db.refresh(task_definition)
    
    return task_definition


@router.get("/definitions/{task_id}", response_model=TaskDefinitionSchema)
async def get_task_definition(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取任务定义详情"""
    task_definition = db.query(TaskDefinition).filter(TaskDefinition.id == task_id).first()
    if not task_definition:
        raise NotFoundError(f"任务定义 {task_id} 不存在")
    
    return task_definition


@router.put("/definitions/{task_id}", response_model=TaskDefinitionSchema)
async def update_task_definition(
    task_id: int,
    task_data: TaskDefinitionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新任务定义"""
    task_definition = db.query(TaskDefinition).filter(TaskDefinition.id == task_id).first()
    if not task_definition:
        raise NotFoundError(f"任务定义 {task_id} 不存在")
    
    # 检查权限（只有创建者或管理员可以修改）
    if task_definition.created_by != current_user.id and not current_user.is_admin:
        raise AuthorizationError("没有权限修改此任务定义")
    
    # 更新任务定义
    update_data = task_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(task_definition, field, value)
    
    db.commit()
    db.refresh(task_definition)
    
    return task_definition


@router.delete("/definitions/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task_definition(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除任务定义"""
    task_definition = db.query(TaskDefinition).filter(TaskDefinition.id == task_id).first()
    if not task_definition:
        raise NotFoundError(f"任务定义 {task_id} 不存在")
    
    # 检查权限
    if task_definition.created_by != current_user.id and not current_user.is_admin:
        raise AuthorizationError("没有权限删除此任务定义")
    
    # 检查是否有运行中的实例
    running_instances = db.query(TaskInstance).filter(
        TaskInstance.task_definition_id == task_id,
        TaskInstance.status.in_(['pending', 'running'])
    ).count()
    if running_instances > 0:
        raise ValidationError(f"任务有 {running_instances} 个运行中的实例，无法删除")
    
    db.delete(task_definition)
    db.commit()


# ============================================
# 任务模板管理接口
# ============================================

@router.get("/templates", response_model=TaskTemplateListResponse)
async def list_task_templates(
    params: TaskTemplateQueryParams = Depends(),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取任务模板列表"""
    query = db.query(TaskTemplate)
    
    # 应用过滤条件
    if params.template_name:
        query = query.filter(TaskTemplate.template_name.ilike(f"%{params.template_name}%"))
    if params.template_category:
        query = query.filter(TaskTemplate.template_category == params.template_category)
    if params.task_type:
        query = query.filter(TaskTemplate.task_type == params.task_type)
    if params.is_system is not None:
        query = query.filter(TaskTemplate.is_system == params.is_system)
    if params.is_active is not None:
        query = query.filter(TaskTemplate.is_active == params.is_active)
    
    # 应用排序
    if params.sort_by:
        if hasattr(TaskTemplate, params.sort_by):
            order_column = getattr(TaskTemplate, params.sort_by)
            if params.sort_order == "desc":
                query = query.order_by(order_column.desc())
            else:
                query = query.order_by(order_column.asc())
    else:
        query = query.order_by(TaskTemplate.created_at.desc())
    
    # 应用分页
    total = query.count()
    templates = query.offset(params.skip).limit(params.limit).all()
    
    return TaskTemplateListResponse(
        items=templates,
        total=total,
        page=params.page,
        size=params.size,
        pages=(total + params.size - 1) // params.size
    )


@router.post("/templates", response_model=TaskTemplateSchema, status_code=status.HTTP_201_CREATED)
async def create_task_template(
    template_data: TaskTemplateCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建任务模板"""
    # 检查模板名称是否已存在
    existing_template = db.query(TaskTemplate).filter(
        TaskTemplate.template_name == template_data.template_name
    ).first()
    if existing_template:
        raise ValidationError(f"任务模板名称 '{template_data.template_name}' 已存在")
    
    # 创建任务模板
    task_template = TaskTemplate(
        **template_data.model_dump(),
        created_by=current_user.id
    )
    db.add(task_template)
    db.commit()
    db.refresh(task_template)
    
    return task_template


@router.get("/templates/{template_id}", response_model=TaskTemplateSchema)
async def get_task_template(
    template_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取任务模板详情"""
    task_template = db.query(TaskTemplate).filter(TaskTemplate.id == template_id).first()
    if not task_template:
        raise NotFoundError(f"任务模板 {template_id} 不存在")
    
    return task_template


@router.put("/templates/{template_id}", response_model=TaskTemplateSchema)
async def update_task_template(
    template_id: int,
    template_data: TaskTemplateUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新任务模板"""
    task_template = db.query(TaskTemplate).filter(TaskTemplate.id == template_id).first()
    if not task_template:
        raise NotFoundException(f"任务模板 {template_id} 不存在")
    
    # 检查权限
    if task_template.created_by != current_user.id and not current_user.is_admin:
        raise ForbiddenException("没有权限修改此任务模板")
    
    # 更新任务模板
    update_data = template_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(task_template, field, value)
    
    db.commit()
    db.refresh(task_template)
    
    return task_template


@router.delete("/templates/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task_template(
    template_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除任务模板"""
    task_template = db.query(TaskTemplate).filter(TaskTemplate.id == template_id).first()
    if not task_template:
        raise NotFoundException(f"任务模板 {template_id} 不存在")
    
    # 检查权限
    if task_template.created_by != current_user.id and not current_user.is_admin:
        raise AuthorizationError("没有权限删除此任务模板")
    
    # 检查是否被任务定义引用
    referenced_tasks = db.query(TaskDefinition).filter(
        TaskDefinition.template_id == template_id
    ).count()
    if referenced_tasks > 0:
        raise ValidationError(f"任务模板被 {referenced_tasks} 个任务定义引用，无法删除")
    
    db.delete(task_template)
    db.commit()


# ============================================
# 任务依赖管理接口
# ============================================

@router.get("/definitions/{task_id}/dependencies", response_model=List[TaskDependencySchema])
async def list_task_dependencies(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取任务依赖列表"""
    # 检查任务是否存在
    task_definition = db.query(TaskDefinition).filter(TaskDefinition.id == task_id).first()
    if not task_definition:
        raise NotFoundError(f"任务定义 {task_id} 不存在")
    
    dependencies = db.query(TaskDependency).filter(
        TaskDependency.task_id == task_id
    ).all()
    return dependencies


@router.post("/definitions/{task_id}/dependencies", response_model=TaskDependencySchema, status_code=status.HTTP_201_CREATED)
async def create_task_dependency(
    task_id: int,
    dependency_data: TaskDependencyCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建任务依赖"""
    # 检查任务是否存在
    task_definition = db.query(TaskDefinition).filter(TaskDefinition.id == task_id).first()
    if not task_definition:
        raise NotFoundException(f"任务定义 {task_id} 不存在")
    
    # 检查权限
    if task_definition.created_by != current_user.id and not current_user.is_admin:
        raise AuthorizationError("没有权限修改此任务定义")
    
    # 检查依赖任务是否存在
    dependency_task = db.query(TaskDefinition).filter(
        TaskDefinition.id == dependency_data.dependency_task_id
    ).first()
    if not dependency_task:
        raise NotFoundError(f"依赖任务 {dependency_data.dependency_task_id} 不存在")
    
    # 检查是否已存在相同的依赖
    existing_dependency = db.query(TaskDependency).filter(
        TaskDependency.task_id == task_id,
        TaskDependency.dependency_task_id == dependency_data.dependency_task_id
    ).first()
    if existing_dependency:
        raise ValidationError("相同的依赖关系已存在")
    
    # 检查是否会形成循环依赖
    # TODO: 实现循环依赖检测逻辑
    
    # 创建依赖
    dependency = TaskDependency(
        task_id=task_id,
        **dependency_data.model_dump()
    )
    db.add(dependency)
    db.commit()
    db.refresh(dependency)
    
    return dependency


@router.delete("/definitions/{task_id}/dependencies/{dependency_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task_dependency(
    task_id: int,
    dependency_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除任务依赖"""
    dependency = db.query(TaskDependency).filter(
        TaskDependency.id == dependency_id,
        TaskDependency.task_id == task_id
    ).first()
    if not dependency:
        raise NotFoundException(f"任务依赖 {dependency_id} 不存在")
    
    # 检查权限
    task_definition = db.query(TaskDefinition).filter(TaskDefinition.id == task_id).first()
    if task_definition.created_by != current_user.id and not current_user.is_admin:
        raise ForbiddenException("没有权限修改此任务定义")
    
    db.delete(dependency)
    db.commit()


# ============================================
# 执行器管理接口
# ============================================

@router.get("/executor-groups", response_model=ExecutorGroupListResponse)
async def list_executor_groups(
    params: ExecutorGroupQueryParams = Depends(),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取执行器分组列表"""
    query = db.query(ExecutorGroup)
    
    # 应用过滤条件
    if params.group_name:
        query = query.filter(ExecutorGroup.group_name.ilike(f"%{params.group_name}%"))
    if params.group_type:
        query = query.filter(ExecutorGroup.group_type == params.group_type)
    if params.is_active is not None:
        query = query.filter(ExecutorGroup.is_active == params.is_active)
    
    # 应用排序
    if params.sort_by:
        if hasattr(ExecutorGroup, params.sort_by):
            order_column = getattr(ExecutorGroup, params.sort_by)
            if params.sort_order == "desc":
                query = query.order_by(order_column.desc())
            else:
                query = query.order_by(order_column.asc())
    else:
        query = query.order_by(ExecutorGroup.created_at.desc())
    
    # 应用分页
    total = query.count()
    groups = query.offset(params.skip).limit(params.limit).all()
    
    return ExecutorGroupListResponse(
        items=groups,
        total=total,
        page=params.page,
        size=params.size,
        pages=(total + params.size - 1) // params.size
    )


@router.post("/executor-groups", response_model=ExecutorGroupSchema, status_code=status.HTTP_201_CREATED)
async def create_executor_group(
    group_data: ExecutorGroupCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建执行器分组"""
    # 检查分组名称是否已存在
    existing_group = db.query(ExecutorGroup).filter(
        ExecutorGroup.group_name == group_data.group_name
    ).first()
    if existing_group:
        raise ValidationError(f"执行器分组名称 '{group_data.group_name}' 已存在")
    
    # 创建执行器分组
    executor_group = ExecutorGroup(
        **group_data.model_dump(),
        created_by=current_user.id
    )
    db.add(executor_group)
    db.commit()
    db.refresh(executor_group)
    
    return executor_group


@router.get("/executor-groups/{group_id}/nodes", response_model=ExecutorNodeListResponse)
async def list_executor_nodes(
    group_id: int,
    params: ExecutorNodeQueryParams = Depends(),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取执行器节点列表"""
    query = db.query(ExecutorNode).filter(ExecutorNode.group_id == group_id)
    
    # 应用过滤条件
    if params.node_name:
        query = query.filter(ExecutorNode.node_name.ilike(f"%{params.node_name}%"))
    if params.node_status:
        query = query.filter(ExecutorNode.node_status == params.node_status)
    if params.is_active is not None:
        query = query.filter(ExecutorNode.is_active == params.is_active)
    
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
    
    # 应用分页
    total = query.count()
    nodes = query.offset(params.skip).limit(params.limit).all()
    
    return ExecutorNodeListResponse(
        items=nodes,
        total=total,
        page=params.page,
        size=params.size,
        pages=(total + params.size - 1) // params.size
    )


# ============================================
# 任务执行接口
# ============================================

@router.post("/definitions/{task_id}/execute", response_model=TaskInstanceSchema, status_code=status.HTTP_201_CREATED)
async def execute_task(
    task_id: int,
    execute_request: TaskExecuteRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """执行任务"""
    # 检查任务定义是否存在且为活跃状态
    task_definition = db.query(TaskDefinition).filter(
        TaskDefinition.id == task_id,
        TaskDefinition.task_status == 'active'
    ).first()
    if not task_definition:
        raise NotFoundError(f"任务定义 {task_id} 不存在或未激活")
    
    # 生成实例ID
    import uuid
    instance_id = f"task_{task_id}_{int(datetime.now().timestamp())}_{str(uuid.uuid4())[:8]}"
    
    # 创建任务实例
    task_instance = TaskInstance(
        instance_id=instance_id,
        task_definition_id=task_id,
        task_version=task_definition.task_version,
        instance_name=f"{task_definition.task_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        priority=execute_request.priority,
        input_data=execute_request.input_data,
        scheduled_time=execute_request.scheduled_time or datetime.now(),
        triggered_by='manual',
        triggered_by_user=current_user.id
    )
    
    db.add(task_instance)
    db.commit()
    db.refresh(task_instance)
    
    # TODO: 这里应该触发任务执行引擎
    # 可以发送消息到队列或调用执行服务
    
    return task_instance


@router.get("/instances", response_model=TaskInstanceListResponse)
async def list_task_instances(
    params: TaskInstanceQueryParams = Depends(),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取任务实例列表"""
    query = db.query(TaskInstance)
    
    # 应用过滤条件
    if params.task_definition_id:
        query = query.filter(TaskInstance.task_definition_id == params.task_definition_id)
    if params.status:
        query = query.filter(TaskInstance.status == params.status)
    if params.priority:
        query = query.filter(TaskInstance.priority == params.priority)
    if params.triggered_by:
        query = query.filter(TaskInstance.triggered_by == params.triggered_by)
    if params.triggered_by_user:
        query = query.filter(TaskInstance.triggered_by_user == params.triggered_by_user)
    if params.scheduled_start:
        query = query.filter(TaskInstance.scheduled_time >= params.scheduled_start)
    if params.scheduled_end:
        query = query.filter(TaskInstance.scheduled_time <= params.scheduled_end)
    
    # 应用排序
    if params.sort_by:
        if hasattr(TaskInstance, params.sort_by):
            order_column = getattr(TaskInstance, params.sort_by)
            if params.sort_order == "desc":
                query = query.order_by(order_column.desc())
            else:
                query = query.order_by(order_column.asc())
    else:
        query = query.order_by(TaskInstance.created_at.desc())
    
    # 应用分页
    total = query.count()
    instances = query.offset(params.skip).limit(params.limit).all()
    
    return TaskInstanceListResponse(
        items=instances,
        total=total,
        page=params.page,
        size=params.size,
        pages=(total + params.size - 1) // params.size
    )


@router.get("/instances/{instance_id}", response_model=TaskInstanceSchema)
async def get_task_instance(
    instance_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取任务实例详情"""
    instance = db.query(TaskInstance).filter(TaskInstance.id == instance_id).first()
    if not instance:
        raise NotFoundError(f"任务实例 {instance_id} 不存在")
    
    return instance


@router.post("/instances/{instance_id}/cancel", response_model=TaskInstanceSchema)
async def cancel_task_instance(
    instance_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """取消任务实例"""
    instance = db.query(TaskInstance).filter(TaskInstance.id == instance_id).first()
    if not instance:
        raise NotFoundError(f"任务实例 {instance_id} 不存在")
    
    # 检查权限
    if instance.triggered_by_user != current_user.id and not current_user.is_admin:
        raise AuthorizationError("没有权限取消此任务实例")
    
    # 检查状态
    if instance.status not in ['pending', 'running']:
        raise ValidationError(f"任务实例状态为 {instance.status}，无法取消")
    
    # 更新状态
    instance.status = 'cancelled'
    instance.actual_end_time = datetime.now()
    
    db.commit()
    db.refresh(instance)
    
    # TODO: 这里应该通知执行引擎取消执行
    
    return instance


# ============================================
# 任务日志接口
# ============================================

@router.get("/instances/{instance_id}/logs", response_model=TaskLogListResponse)
async def list_task_logs(
    instance_id: int,
    params: TaskLogQueryParams = Depends(),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取任务日志列表"""
    # 检查任务实例是否存在
    instance = db.query(TaskInstance).filter(TaskInstance.id == instance_id).first()
    if not instance:
        raise NotFoundError(f"任务实例 {instance_id} 不存在")
    
    query = db.query(TaskLog).filter(TaskLog.task_instance_id == instance_id)
    
    # 应用过滤条件
    if params.log_level:
        query = query.filter(TaskLog.log_level == params.log_level)
    if params.log_source:
        query = query.filter(TaskLog.log_source == params.log_source)
    if params.start_time:
        query = query.filter(TaskLog.log_time >= params.start_time)
    if params.end_time:
        query = query.filter(TaskLog.log_time <= params.end_time)
    
    # 应用排序
    if params.sort_by:
        if hasattr(TaskLog, params.sort_by):
            order_column = getattr(TaskLog, params.sort_by)
            if params.sort_order == "desc":
                query = query.order_by(order_column.desc())
            else:
                query = query.order_by(order_column.asc())
    else:
        query = query.order_by(TaskLog.log_time.desc())
    
    # 应用分页
    total = query.count()
    logs = query.offset(params.skip).limit(params.limit).all()
    
    return TaskLogListResponse(
        items=logs,
        total=total,
        page=params.page,
        size=params.size,
        pages=(total + params.size - 1) // params.size
    )


# ============================================
# 任务统计接口
# ============================================

@router.get("/execution-stats", response_model=TaskExecutionStatsListResponse)
async def get_task_execution_stats(
    task_definition_id: Optional[int] = Query(None, description="任务定义ID"),
    task_type: Optional[str] = Query(None, description="任务类型"),
    limit: int = Query(50, ge=1, le=100, description="返回数量限制"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取任务执行统计"""
    # 使用视图查询执行统计
    query = db.execute(
        """
        SELECT * FROM v_task_execution_stats
        WHERE 1=1
        {task_filter}
        {type_filter}
        ORDER BY total_executions DESC
        LIMIT {limit}
        """.format(
            task_filter=f"AND task_definition_id = {task_definition_id}" if task_definition_id else "",
            type_filter=f"AND task_type = '{task_type}'" if task_type else "",
            limit=limit
        )
    )
    
    results = query.fetchall()
    
    # 转换为Schema对象
    execution_stats = [
        TaskExecutionStats(
            task_definition_id=row[0],
            task_name=row[1],
            task_type=row[2],
            total_executions=row[3] or 0,
            success_count=row[4] or 0,
            failure_count=row[5] or 0,
            avg_duration_seconds=row[6],
            max_duration_seconds=row[7],
            min_duration_seconds=row[8]
        )
        for row in results
    ]
    
    return TaskExecutionStatsListResponse(
        items=execution_stats,
        total=len(execution_stats),
        page=1,
        size=limit,
        pages=1
    )