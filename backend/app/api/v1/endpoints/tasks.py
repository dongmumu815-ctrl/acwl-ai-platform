from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, asc, text
from typing import List, Optional
from datetime import datetime
import os
import aiofiles

from ....core.database import get_db
from ....models.task import (
    TaskDefinition, TaskTemplate, TaskDependency,
    TaskSchedule, TaskInstance, TaskExecution, TaskLog, TaskResult,
    TriggerType
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
    TaskLogQueryParams, TaskLogListResponse, TaskLogFileResponse,
    
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

@router.get("/", response_model=TaskDefinitionListResponse)
@router.get("/definitions", response_model=TaskDefinitionListResponse)
async def list_task_definitions(
    params: TaskDefinitionQueryParams = Depends(),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取任务定义列表"""
    query = select(TaskDefinition)
    
    # 应用过滤条件
    if params.task_name:
        query = query.where(TaskDefinition.task_name.ilike(f"%{params.task_name}%"))
    if params.task_type:
        query = query.where(TaskDefinition.task_type == params.task_type)
    if params.task_status:
        query = query.where(TaskDefinition.task_status == params.task_status)
    if params.task_category:
        query = query.where(TaskDefinition.task_category == params.task_category)
    if params.project_id:
        query = query.where(TaskDefinition.project_id == params.project_id)
    if params.workflow_id:
        query = query.where(TaskDefinition.workflow_id == params.workflow_id)
    if params.created_by:
        query = query.where(TaskDefinition.created_by == params.created_by)
    if params.is_template is not None:
        query = query.where(TaskDefinition.is_template == params.is_template)
    if params.is_system is not None:
        query = query.where(TaskDefinition.is_system == params.is_system)
    
    # 计算总数
    count_query = select(func.count(TaskDefinition.id))
    if params.task_name:
        count_query = count_query.where(TaskDefinition.task_name.ilike(f"%{params.task_name}%"))
    if params.task_type:
        count_query = count_query.where(TaskDefinition.task_type == params.task_type)
    if params.task_status:
        count_query = count_query.where(TaskDefinition.task_status == params.task_status)
    if params.task_category:
        count_query = count_query.where(TaskDefinition.task_category == params.task_category)
    if params.project_id:
        count_query = count_query.where(TaskDefinition.project_id == params.project_id)
    if params.workflow_id:
        count_query = count_query.where(TaskDefinition.workflow_id == params.workflow_id)
    if params.created_by:
        count_query = count_query.where(TaskDefinition.created_by == params.created_by)
    if params.is_template is not None:
        count_query = count_query.where(TaskDefinition.is_template == params.is_template)
    if params.is_system is not None:
        count_query = count_query.where(TaskDefinition.is_system == params.is_system)
    
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
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
    query = query.offset(params.skip).limit(params.limit)
    result = await db.execute(query)
    task_definitions = result.scalars().all()
    
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
    result = await db.execute(select(TaskDefinition).where(TaskDefinition.task_name == task_data.task_name))
    existing_task = result.scalar_one_or_none()
    if existing_task:
        raise ValidationError(f"任务名称 '{task_data.task_name}' 已存在")
    
    # 创建任务定义
    task_definition = TaskDefinition(
        **task_data.model_dump(),
        created_by=current_user.id
    )
    db.add(task_definition)
    await db.commit()
    await db.refresh(task_definition)
    
    return task_definition


@router.get("/definitions/{task_id}", response_model=TaskDefinitionSchema)
async def get_task_definition(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取任务定义详情"""
    result = await db.execute(select(TaskDefinition).where(TaskDefinition.id == task_id))
    task_definition = result.scalar_one_or_none()
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
    result = await db.execute(select(TaskDefinition).where(TaskDefinition.id == task_id))
    task_definition = result.scalar_one_or_none()
    if not task_definition:
        raise NotFoundError(f"任务定义 {task_id} 不存在")
    
    # 检查权限（只有创建者或管理员可以修改）
    if task_definition.created_by != current_user.id and not current_user.is_admin:
        raise AuthorizationError("没有权限修改此任务定义")
    
    # 更新任务定义
    update_data = task_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(task_definition, field, value)
    
    await db.commit()
    await db.refresh(task_definition)
    
    return task_definition


@router.delete("/definitions/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task_definition(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除任务定义"""
    result = await db.execute(select(TaskDefinition).where(TaskDefinition.id == task_id))
    task_definition = result.scalar_one_or_none()
    if not task_definition:
        raise NotFoundError(f"任务定义 {task_id} 不存在")
    
    # 检查权限
    if task_definition.created_by != current_user.id and not current_user.is_admin:
        raise AuthorizationError("没有权限删除此任务定义")
    
    # 检查是否有运行中的实例
    result = await db.execute(select(func.count(TaskInstance.id)).where(
        TaskInstance.task_definition_id == task_id,
        TaskInstance.status.in_(['pending', 'running'])
    ))
    running_instances = result.scalar()
    if running_instances > 0:
        raise ValidationError(f"任务有 {running_instances} 个运行中的实例，无法删除")
    
    await db.delete(task_definition)
    await db.commit()


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
    query = select(TaskTemplate)
    count_query = select(func.count(TaskTemplate.id))
    
    # 应用过滤条件
    if params.template_name:
        query = query.where(TaskTemplate.name.ilike(f"%{params.template_name}%"))
        count_query = count_query.where(TaskTemplate.name.ilike(f"%{params.template_name}%"))
    if params.template_category:
        # TaskTemplate 没有 template_category 字段，暂时忽略
        pass
        # query = query.where(TaskTemplate.template_category == params.template_category)
        # count_query = count_query.where(TaskTemplate.template_category == params.template_category)
    if params.task_type:
        query = query.where(TaskTemplate.task_type == params.task_type)
        count_query = count_query.where(TaskTemplate.task_type == params.task_type)
    if params.is_system is not None:
        query = query.where(TaskTemplate.is_system == params.is_system)
        count_query = count_query.where(TaskTemplate.is_system == params.is_system)
    if params.is_active is not None:
        # TaskTemplate 没有 is_active 字段，暂时忽略
        pass
        # query = query.where(TaskTemplate.is_active == params.is_active)
        # count_query = count_query.where(TaskTemplate.is_active == params.is_active)
    
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
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    query = query.offset(params.skip).limit(params.limit)
    result = await db.execute(query)
    templates = result.scalars().all()
    
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
    stmt = select(TaskTemplate).where(TaskTemplate.name == template_data.template_name)
    result = await db.execute(stmt)
    existing_template = result.scalar_one_or_none()
    
    if existing_template:
        raise ValidationError(f"任务模板名称 '{template_data.template_name}' 已存在")
    
    # 创建任务模板
    data = template_data.model_dump()
    if 'template_name' in data:
        data['name'] = data.pop('template_name')
        
    task_template = TaskTemplate(
        **data,
        created_by=current_user.id
    )
    db.add(task_template)
    await db.commit()
    await db.refresh(task_template)
    
    return task_template


@router.get("/templates/{template_id}", response_model=TaskTemplateSchema)
async def get_task_template(
    template_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取任务模板详情"""
    stmt = select(TaskTemplate).where(TaskTemplate.id == template_id)
    result = await db.execute(stmt)
    task_template = result.scalar_one_or_none()
    
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
    stmt = select(TaskTemplate).where(TaskTemplate.id == template_id)
    result = await db.execute(stmt)
    task_template = result.scalar_one_or_none()
    
    if not task_template:
        raise NotFoundException(f"任务模板 {template_id} 不存在")
    
    # 检查权限
    if task_template.created_by != current_user.id and not current_user.is_admin:
        raise ForbiddenException("没有权限修改此任务模板")
    
    # 更新任务模板
    update_data = template_data.model_dump(exclude_unset=True)
    if 'template_name' in update_data:
        update_data['name'] = update_data.pop('template_name')
        
    for field, value in update_data.items():
        setattr(task_template, field, value)
    
    await db.commit()
    await db.refresh(task_template)
    
    return task_template


@router.delete("/templates/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task_template(
    template_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除任务模板"""
    stmt = select(TaskTemplate).where(TaskTemplate.id == template_id)
    result = await db.execute(stmt)
    task_template = result.scalar_one_or_none()
    
    if not task_template:
        raise NotFoundException(f"任务模板 {template_id} 不存在")
    
    # 检查权限
    if task_template.created_by != current_user.id and not current_user.is_admin:
        raise AuthorizationError("没有权限删除此任务模板")
    
    # 检查是否被任务定义引用
    stmt_check = select(func.count(TaskDefinition.id)).where(TaskDefinition.template_id == template_id)
    result_check = await db.execute(stmt_check)
    referenced_tasks = result_check.scalar() or 0
    
    if referenced_tasks > 0:
        raise ValidationError(f"任务模板被 {referenced_tasks} 个任务定义引用，无法删除")
    
    await db.delete(task_template)
    await db.commit()


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
    # 检查任务定义是否存在
    stmt = select(TaskDefinition).where(TaskDefinition.id == task_id)
    result = await db.execute(stmt)
    task_definition = result.scalar_one_or_none()
    
    if not task_definition:
        raise NotFoundException(f"任务定义 {task_id} 不存在")
    
    # 获取依赖列表
    stmt_deps = select(TaskDependency).where(TaskDependency.parent_task_id == task_id)
    result_deps = await db.execute(stmt_deps)
    dependencies = result_deps.scalars().all()
    
    return dependencies


@router.post("/definitions/{task_id}/dependencies", response_model=TaskDependencySchema, status_code=status.HTTP_201_CREATED)
async def create_task_dependency(
    task_id: int,
    dependency_data: TaskDependencyCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建任务依赖"""
    # 检查父任务定义是否存在
    stmt_parent = select(TaskDefinition).where(TaskDefinition.id == task_id)
    result_parent = await db.execute(stmt_parent)
    task_definition = result_parent.scalar_one_or_none()
    
    if not task_definition:
        raise NotFoundException(f"任务定义 {task_id} 不存在")
    
    # 检查子任务定义是否存在
    stmt_child = select(TaskDefinition).where(TaskDefinition.id == dependency_data.child_task_id)
    result_child = await db.execute(stmt_child)
    dependency_task = result_child.scalar_one_or_none()
    
    if not dependency_task:
        raise ValidationError(f"依赖任务 {dependency_data.child_task_id} 不存在")
    
    # 检查依赖是否已存在
    stmt_exist = select(TaskDependency).where(
        TaskDependency.parent_task_id == task_id,
        TaskDependency.child_task_id == dependency_data.child_task_id
    )
    result_exist = await db.execute(stmt_exist)
    existing_dependency = result_exist.scalar_one_or_none()
    
    if existing_dependency:
        raise ValidationError("该依赖关系已存在")
    
    # 检查循环依赖 (简化版，仅检查直接循环)
    if task_id == dependency_data.child_task_id:
        raise ValidationError("不能依赖自身")
    
    # 创建依赖
    dependency = TaskDependency(
        parent_task_id=task_id,
        **dependency_data.model_dump()
    )
    db.add(dependency)
    await db.commit()
    await db.refresh(dependency)
    
    return dependency


@router.delete("/definitions/{task_id}/dependencies/{child_task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task_dependency(
    task_id: int,
    child_task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除任务依赖"""
    stmt = select(TaskDependency).where(
        TaskDependency.parent_task_id == task_id,
        TaskDependency.child_task_id == child_task_id
    )
    result = await db.execute(stmt)
    dependency = result.scalar_one_or_none()
    
    if not dependency:
        raise NotFoundException("依赖关系不存在")
    
    # 检查权限
    # 获取任务定义以检查权限
    stmt_task = select(TaskDefinition).where(TaskDefinition.id == task_id)
    result_task = await db.execute(stmt_task)
    task_definition = result_task.scalar_one_or_none()
    
    if task_definition and task_definition.created_by != current_user.id and not current_user.is_admin:
        raise AuthorizationError("没有权限修改此任务定义")
    
    await db.delete(dependency)
    await db.commit()


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
    query = select(ExecutorGroup)
    count_query = select(func.count(ExecutorGroup.id))
    
    # 应用过滤条件
    if params.group_name:
        query = query.where(ExecutorGroup.group_name.ilike(f"%{params.group_name}%"))
        count_query = count_query.where(ExecutorGroup.group_name.ilike(f"%{params.group_name}%"))
    if params.group_type:
        query = query.where(ExecutorGroup.group_type == params.group_type)
        count_query = count_query.where(ExecutorGroup.group_type == params.group_type)
    if params.is_active is not None:
        query = query.where(ExecutorGroup.is_active == params.is_active)
        count_query = count_query.where(ExecutorGroup.is_active == params.is_active)
    
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
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    query = query.offset(params.skip).limit(params.limit)
    result = await db.execute(query)
    groups = result.scalars().all()
    
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
    stmt = select(ExecutorGroup).where(ExecutorGroup.group_name == group_data.group_name)
    result = await db.execute(stmt)
    existing_group = result.scalar_one_or_none()
    
    if existing_group:
        raise ValidationError(f"执行器分组名称 '{group_data.group_name}' 已存在")
    
    # 提取 executor_ids 并不包含在 model_dump 中
    dump_data = group_data.model_dump(exclude={"executor_ids"})
    
    # 创建执行器分组
    executor_group = ExecutorGroup(
        **dump_data,
        created_by=current_user.id
    )
    
    # 处理执行器节点关联
    if group_data.executor_ids:
        nodes_stmt = select(ExecutorNode).where(ExecutorNode.id.in_(group_data.executor_ids))
        nodes_result = await db.execute(nodes_stmt)
        nodes = nodes_result.scalars().all()
        executor_group.executors = list(nodes)
        
    db.add(executor_group)
    await db.commit()
    await db.refresh(executor_group)
    
    return executor_group


@router.put("/executor-groups/{group_id}", response_model=ExecutorGroupSchema)
async def update_executor_group(
    group_id: int,
    group_data: ExecutorGroupUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新执行器分组"""
    stmt = select(ExecutorGroup).where(ExecutorGroup.id == group_id)
    result = await db.execute(stmt)
    executor_group = result.scalar_one_or_none()
    
    if not executor_group:
        raise NotFoundError(f"执行器分组 {group_id} 不存在")
        
    # 处理基本字段更新
    update_data = group_data.model_dump(exclude_unset=True, exclude={"executor_ids"})
    for field, value in update_data.items():
        setattr(executor_group, field, value)
    
    # 处理执行器节点关联更新
    if group_data.executor_ids is not None:
        # 加载现有关系（如果尚未加载）
        # 注意：如果是 async session，访问 relationship 可能需要 explicit loading 或者 ensure loaded
        # 这里直接赋值新列表，SQLAlchemy 会处理差异
        nodes_stmt = select(ExecutorNode).where(ExecutorNode.id.in_(group_data.executor_ids))
        nodes_result = await db.execute(nodes_stmt)
        nodes = nodes_result.scalars().all()
        executor_group.executors = list(nodes)
        
    await db.commit()
    await db.refresh(executor_group)
    return executor_group


@router.delete("/executor-groups/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_executor_group(
    group_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除执行器分组"""
    stmt = select(ExecutorGroup).where(ExecutorGroup.id == group_id)
    result = await db.execute(stmt)
    executor_group = result.scalar_one_or_none()
    
    if not executor_group:
        raise NotFoundError(f"执行器分组 {group_id} 不存在")
        
    # 检查该分组下是否有执行器节点
    node_stmt = select(ExecutorNode).where(ExecutorNode.group_id == group_id).limit(1)
    node_result = await db.execute(node_stmt)
    if node_result.scalar_one_or_none():
        raise ValidationError(f"无法删除分组 {group_id}，因为该分组下仍有执行器节点")

    await db.delete(executor_group)
    await db.commit()


@router.get("/executor-groups/{group_id}/nodes", response_model=ExecutorNodeListResponse)
async def list_executor_nodes(
    group_id: int,
    params: ExecutorNodeQueryParams = Depends(),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取执行器节点列表"""
    query = select(ExecutorNode).where(ExecutorNode.group_id == group_id)
    count_query = select(func.count(ExecutorNode.id)).where(ExecutorNode.group_id == group_id)
    
    # 应用过滤条件
    if params.node_name:
        query = query.where(ExecutorNode.node_name.ilike(f"%{params.node_name}%"))
        count_query = count_query.where(ExecutorNode.node_name.ilike(f"%{params.node_name}%"))
    if params.node_status:
        query = query.where(ExecutorNode.node_status == params.node_status)
        count_query = count_query.where(ExecutorNode.node_status == params.node_status)
    if params.is_active is not None:
        query = query.where(ExecutorNode.is_active == params.is_active)
        count_query = count_query.where(ExecutorNode.is_active == params.is_active)
    
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
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    query = query.offset(params.skip).limit(params.limit)
    result = await db.execute(query)
    nodes = result.scalars().all()
    
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
    stmt = select(TaskDefinition).where(
        TaskDefinition.id == task_id,
        TaskDefinition.task_status == 'active'
    )
    result = await db.execute(stmt)
    task_definition = result.scalar_one_or_none()
    
    if not task_definition:
        raise NotFoundError(f"任务定义 {task_id} 不存在或未激活")
    
    # 生成实例ID
    import uuid
    instance_id = f"task_{task_id}_{int(datetime.now().timestamp())}_{str(uuid.uuid4())[:8]}"
    
    # 创建任务实例
    task_instance = TaskInstance(
        instance_id=instance_id,
        task_definition_id=task_id,
        task_version=task_definition.version,
        instance_name=f"{task_definition.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        priority=execute_request.priority,
        input_data=execute_request.input_data,
        scheduled_time=execute_request.scheduled_time or datetime.now(),
        triggered_by=TriggerType.MANUAL,
        triggered_by_user=current_user.id
    )
    
    db.add(task_instance)
    await db.commit()
    await db.refresh(task_instance)
    
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
    query = select(TaskInstance)
    count_query = select(func.count(TaskInstance.id))
    
    # 应用过滤条件
    if params.task_definition_id:
        query = query.where(TaskInstance.task_definition_id == params.task_definition_id)
        count_query = count_query.where(TaskInstance.task_definition_id == params.task_definition_id)
    if params.status:
        query = query.where(TaskInstance.status == params.status)
        count_query = count_query.where(TaskInstance.status == params.status)
    if params.priority:
        query = query.where(TaskInstance.priority == params.priority)
        count_query = count_query.where(TaskInstance.priority == params.priority)
    if params.triggered_by:
        query = query.where(TaskInstance.triggered_by == params.triggered_by)
        count_query = count_query.where(TaskInstance.triggered_by == params.triggered_by)
    if params.triggered_by_user:
        query = query.where(TaskInstance.triggered_by_user == params.triggered_by_user)
        count_query = count_query.where(TaskInstance.triggered_by_user == params.triggered_by_user)
    if params.scheduled_start:
        query = query.where(TaskInstance.scheduled_time >= params.scheduled_start)
        count_query = count_query.where(TaskInstance.scheduled_time >= params.scheduled_start)
    if params.scheduled_end:
        query = query.where(TaskInstance.scheduled_time <= params.scheduled_end)
        count_query = count_query.where(TaskInstance.scheduled_time <= params.scheduled_end)
    
    # 计算总数
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    # 应用排序
    if params.sort_by:
        if hasattr(TaskInstance, params.sort_by):
            order_column = getattr(TaskInstance, params.sort_by)
            if params.sort_order == "desc":
                query = query.order_by(desc(order_column))
            else:
                query = query.order_by(asc(order_column))
    else:
        query = query.order_by(desc(TaskInstance.created_at))
    
    # 应用分页
    query = query.offset(params.skip).limit(params.limit)
    result = await db.execute(query)
    instances = result.scalars().all()
    
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
    stmt = select(TaskInstance).where(TaskInstance.id == instance_id)
    result = await db.execute(stmt)
    instance = result.scalar_one_or_none()
    
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
    stmt = select(TaskInstance).where(TaskInstance.id == instance_id)
    result = await db.execute(stmt)
    instance = result.scalar_one_or_none()
    
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
    
    await db.commit()
    await db.refresh(instance)
    
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
    stmt = select(TaskInstance).where(TaskInstance.id == instance_id)
    result = await db.execute(stmt)
    instance = result.scalar_one_or_none()
    
    if not instance:
        raise NotFoundError(f"任务实例 {instance_id} 不存在")
    
    query = select(TaskLog).where(TaskLog.task_instance_id == instance_id)
    count_query = select(func.count(TaskLog.id)).where(TaskLog.task_instance_id == instance_id)
    
    # 应用过滤条件
    if params.log_level:
        query = query.where(TaskLog.log_level == params.log_level)
        count_query = count_query.where(TaskLog.log_level == params.log_level)
    if params.log_source:
        query = query.where(TaskLog.log_source == params.log_source)
        count_query = count_query.where(TaskLog.log_source == params.log_source)
    if params.start_time:
        query = query.where(TaskLog.log_time >= params.start_time)
        count_query = count_query.where(TaskLog.log_time >= params.start_time)
    if params.end_time:
        query = query.where(TaskLog.log_time <= params.end_time)
        count_query = count_query.where(TaskLog.log_time <= params.end_time)
    
    # 应用排序
    if params.sort_by:
        if hasattr(TaskLog, params.sort_by):
            order_column = getattr(TaskLog, params.sort_by)
            if params.sort_order == "desc":
                query = query.order_by(desc(order_column))
            else:
                query = query.order_by(asc(order_column))
    else:
        query = query.order_by(desc(TaskLog.log_time))
    
    # 计算总数
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    # 应用分页
    query = query.offset(params.skip).limit(params.limit)
    result = await db.execute(query)
    logs = result.scalars().all()
    
    return TaskLogListResponse(
        items=logs,
        total=total,
        page=params.page,
        size=params.size,
        pages=(total + params.size - 1) // params.size
    )


@router.get("/instances/{instance_id}/logs/file", response_model=TaskLogFileResponse)
async def get_task_instance_log_file(
    instance_id: int,
    start: int = Query(0, ge=0, description="Start byte offset"),
    length: int = Query(10240, ge=1, le=1048576, description="Number of bytes to read"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """读取任务实例日志文件（支持分段读取）"""
    stmt = select(TaskInstance).where(TaskInstance.id == instance_id)
    result = await db.execute(stmt)
    instance = result.scalar_one_or_none()
    
    if not instance:
        raise NotFoundError(f"任务实例 {instance_id} 不存在")
    
    # 构建日志文件路径
    # 假设日志文件存储在 logs/tasks/{instance_id}.log
    # instance_id 是字符串ID，不是主键ID
    safe_id = "".join([c for c in instance.instance_id if c.isalnum() or c in ('-', '_')])
    log_dir = os.path.join(os.getcwd(), "logs", "tasks")
    log_file = os.path.join(log_dir, f"{safe_id}.log")
    
    if not os.path.exists(log_file):
        return {
            "content": "",
            "size": 0,
            "offset": start,
            "length": 0,
            "has_more": False
        }
        
    file_size = os.path.getsize(log_file)
    
    # 如果start超过文件大小，返回空
    if start >= file_size:
        return {
            "content": "",
            "size": file_size,
            "offset": start,
            "length": 0,
            "has_more": False
        }
    
    # 异步读取文件
    try:
        async with aiofiles.open(log_file, mode='r', encoding='utf-8', errors='replace') as f:
            await f.seek(start)
            content = await f.read(length)
    except Exception as e:
        # 如果aiofiles失败，尝试同步读取（作为回退）
        # 或者直接抛出错误
        # 这里简单起见，如果出错返回空
        return {
            "content": f"Error reading log file: {str(e)}",
            "size": file_size,
            "offset": start,
            "length": 0,
            "has_more": False
        }
    
    return {
        "content": content,
        "size": file_size,
        "offset": start,
        "length": len(content),
        "has_more": (start + len(content)) < file_size
    }


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
    query_str = "SELECT * FROM v_task_execution_stats WHERE 1=1"
    params_dict = {"limit": limit}
    
    if task_definition_id:
        query_str += " AND task_definition_id = :task_definition_id"
        params_dict["task_definition_id"] = task_definition_id
        
    if task_type:
        query_str += " AND task_type = :task_type"
        params_dict["task_type"] = task_type
        
    query_str += " ORDER BY total_executions DESC LIMIT :limit"
    
    result = await db.execute(text(query_str), params_dict)
    results = result.fetchall()
    
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