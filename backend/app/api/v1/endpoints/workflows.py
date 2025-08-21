import asyncio
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete
from sqlalchemy.orm import selectinload
from typing import List, Optional
from datetime import datetime

from ....core.database import get_db
from ....models.workflow import (
    Workflow, WorkflowNode, WorkflowConnection, WorkflowInstance, 
    WorkflowNodeInstance, WorkflowSchedule
)
from ....models.unified_node import UnifiedNode, UnifiedNodeInstance
from ....models.task import TaskDefinition
from ....models.project import Project
from ....schemas.workflow import (
    # 工作流相关
    WorkflowCreate, WorkflowUpdate, Workflow as WorkflowSchema,
    WorkflowWithNodes, WorkflowQueryParams, WorkflowListResponse,
    
    # 工作流节点相关
    WorkflowNodeCreate, WorkflowNodeUpdate, WorkflowNode as WorkflowNodeSchema,
    
    # 工作流连接相关
    WorkflowConnectionCreate, WorkflowConnectionUpdate, WorkflowConnection as WorkflowConnectionSchema,
    
    # 工作流实例相关
    WorkflowInstanceCreate, WorkflowInstanceUpdate, WorkflowInstance as WorkflowInstanceSchema,
    WorkflowInstanceWithNodes, WorkflowInstanceQueryParams, WorkflowInstanceListResponse,
    WorkflowExecuteRequest, WorkflowExecutionStatus, WorkflowExecutionStatusListResponse,
    
    # 工作流节点实例相关
    WorkflowNodeInstanceUpdate, WorkflowNodeInstance as WorkflowNodeInstanceSchema,
    WorkflowNodeInstanceQueryParams, WorkflowNodeInstanceListResponse,
    
    # 工作流调度相关
    WorkflowScheduleCreate, WorkflowScheduleUpdate, WorkflowSchedule as WorkflowScheduleSchema,
    
    # 操作相关
    WorkflowCopyRequest, WorkflowImportRequest, WorkflowExportResponse,
    
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
# 工作流管理接口（节点管理已迁移到统一节点接口）
# ============================================

@router.get("/", response_model=WorkflowListResponse)
async def list_workflows(
    params: WorkflowQueryParams = Depends(),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取工作流列表"""
    # 构建基础查询，包含项目信息的关联查询
    query = select(Workflow, Project.name.label('project_name')).outerjoin(
        Project, Workflow.project_id == Project.id
    )
    
    # 应用过滤条件
    if params.name:
        query = query.where(Workflow.name.ilike(f"%{params.name}%"))
    if params.workflow_status:
        query = query.where(Workflow.workflow_status == params.workflow_status)
    if params.workflow_category:
        query = query.where(Workflow.workflow_category == params.workflow_category)
    if params.project_id:
        query = query.where(Workflow.project_id == params.project_id)
    if params.created_by:
        query = query.where(Workflow.created_by == params.created_by)
    if params.is_template is not None:
        query = query.where(Workflow.is_template == params.is_template)
    if params.is_system is not None:
        query = query.where(Workflow.is_system == params.is_system)
    
    # 应用排序
    if params.sort_by:
        if hasattr(Workflow, params.sort_by):
            order_column = getattr(Workflow, params.sort_by)
            if params.sort_order == "desc":
                query = query.order_by(order_column.desc())
            else:
                query = query.order_by(order_column.asc())
    else:
        query = query.order_by(Workflow.created_at.desc())
    
    # 获取总数（使用原始的Workflow查询）
    count_query = select(func.count(Workflow.id))
    if params.name:
        count_query = count_query.where(Workflow.name.ilike(f"%{params.name}%"))
    if params.workflow_status:
        count_query = count_query.where(Workflow.workflow_status == params.workflow_status)
    if params.workflow_category:
        count_query = count_query.where(Workflow.workflow_category == params.workflow_category)
    if params.project_id:
        count_query = count_query.where(Workflow.project_id == params.project_id)
    if params.created_by:
        count_query = count_query.where(Workflow.created_by == params.created_by)
    if params.is_template is not None:
        count_query = count_query.where(Workflow.is_template == params.is_template)
    if params.is_system is not None:
        count_query = count_query.where(Workflow.is_system == params.is_system)
    
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # 应用分页并执行查询
    query = query.offset(params.skip).limit(params.limit)
    result = await db.execute(query)
    rows = result.all()
    
    # 构建工作流列表，设置project_name
    workflows = []
    for row in rows:
        workflow = row[0]  # Workflow对象
        project_name = row[1]  # 项目名称
        
        # 创建工作流字典并添加project_name
        workflow_dict = {
            **workflow.__dict__,
            'project_name': project_name
        }
        # 移除SQLAlchemy的内部属性
        workflow_dict.pop('_sa_instance_state', None)
        workflows.append(workflow_dict)
    
    return WorkflowListResponse(
        items=workflows,
        total=total,
        page=params.page,
        size=params.size,
        pages=(total + params.size - 1) // params.size
    )


@router.post("/", response_model=WorkflowSchema, status_code=status.HTTP_201_CREATED)
async def create_workflow(
    workflow_data: WorkflowCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建工作流"""
    # 检查工作流名称是否已存在
    stmt = select(Workflow).where(Workflow.name == workflow_data.name)
    result = await db.execute(stmt)
    existing_workflow = result.scalar_one_or_none()
    if existing_workflow:
        raise ValidationError(f"工作流名称 '{workflow_data.name}' 已存在")
    
    # 创建工作流
    workflow = Workflow(
        **workflow_data.model_dump(),
        created_by=current_user.id
    )
    db.add(workflow)
    await db.commit()
    await db.refresh(workflow)
    
    return workflow


@router.get("/{workflow_id}", response_model=WorkflowWithNodes)
async def get_workflow(
    workflow_id: int,
    include_nodes: bool = Query(True, description="是否包含节点信息"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取工作流详情"""
    stmt = select(Workflow).where(Workflow.id == workflow_id)
    result = await db.execute(stmt)
    workflow = result.scalar_one_or_none()
    if not workflow:
        raise NotFoundException(f"工作流 {workflow_id} 不存在")
    
    if include_nodes:
        # 获取统一节点和连接信息
        # 从 UnifiedNode 表获取工作流相关的节点
        nodes_stmt = select(UnifiedNode).where(
            UnifiedNode.workflow_id == workflow_id
        )
        nodes_result = await db.execute(nodes_stmt)
        unified_nodes = nodes_result.scalars().all()
        
        # 将 UnifiedNode 转换为节点格式
        nodes = []
        for node in unified_nodes:
            # 将大写枚举值转换为小写以匹配 Pydantic schema
            node_type = node.node_type
            if isinstance(node_type, str):
                node_type = node_type.lower()
            
            # 获取节点配置中的名称和类型
            node_config = node.node_config or {}
            
            # 确保节点类型正确
            if node_config.get('type'):
                node_type = node_config['type'].lower()
            
            # 确保节点配置中包含正确的脚本内容
            if node_type == 'shell-script' and node_config.get('config'):
                # 确保脚本内容存在
                if 'script' not in node_config['config']:
                    node_config['config']['script'] = ''
            
            # 同样处理Python代码和SQL查询
            if node_type == 'python-code' and node_config.get('config'):
                if 'code' not in node_config['config']:
                    node_config['config']['code'] = ''
            
            if node_type == 'sql-query' and node_config.get('config'):
                if 'sql' not in node_config['config']:
                    node_config['config']['sql'] = ''
            
            node_dict = {
                'id': node.id,
                'workflow_id': workflow_id,
                'node_name': node.name,
                'display_name': node.display_name or (node_config.get('name') or ''),
                'node_type': node_type,
                'node_config': node_config,
                'position_x': node.position_x,
                'position_y': node.position_y,
                'description': node.description,
                'executor_group': node.executor_group,
                'timeout_seconds': node.timeout_seconds,
                'max_retry_count': node.max_retry_count,
                'retry_interval_seconds': node.retry_interval_seconds,
                'error_handling': node.error_handling,
                'created_at': node.created_at,
                'updated_at': node.updated_at
            }
            nodes.append(node_dict)
        
        connections_stmt = select(WorkflowConnection).where(WorkflowConnection.workflow_id == workflow_id)
        connections_result = await db.execute(connections_stmt)
        connections = connections_result.scalars().all()
        
        return WorkflowWithNodes(
            **workflow.__dict__,
            nodes=nodes,
            connections=connections
        )
    
    return WorkflowWithNodes(**workflow.__dict__)


@router.put("/{workflow_id}", response_model=WorkflowSchema)
async def update_workflow(
    workflow_id: int,
    workflow_data: WorkflowUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新工作流"""
    stmt = select(Workflow).where(Workflow.id == workflow_id)
    result = await db.execute(stmt)
    workflow = result.scalar_one_or_none()
    if not workflow:
        raise NotFoundException(f"工作流 {workflow_id} 不存在")
    
    # 检查权限（只有创建者或管理员可以修改）
    if workflow.created_by != current_user.id and not current_user.is_admin:
        raise ForbiddenException("没有权限修改此工作流")
    
    # 更新工作流基本信息
    update_data = workflow_data.model_dump(exclude_unset=True, exclude={'nodes', 'connections'})
    for field, value in update_data.items():
        setattr(workflow, field, value)
    
    # 处理节点数据 - 使用 UnifiedNode 表
    if workflow_data.nodes is not None:
        # 删除现有的工作流相关统一节点
        await db.execute(
            delete(UnifiedNode).where(
                UnifiedNode.workflow_id == workflow_id
            )
        )
        
        # 创建新的统一节点
        for node_data in workflow_data.nodes:
            # 从前端数据中提取节点信息
            if node_data.get('shape') == 'workflow-node':
                # 获取节点类型并转换为 UnifiedNodeType 枚举值
                node_type_str = node_data.get('data', {}).get('nodeType', 'custom')
                # 将节点类型映射到 UnifiedNodeType
                node_type_mapping = {
                    'start': 'START',
                    'end': 'END',
                    'python_code': 'PYTHON_CODE',
                    'sql_query': 'SQL_QUERY',
                    'condition': 'CONDITION',
                    'loop': 'LOOP',
                    'parallel': 'PARALLEL',
                    'merge': 'MERGE',
                    'data_transform': 'DATA_TRANSFORM',
                    'api_call': 'API_CALL',
                    'file_operation': 'FILE_OPERATION',
                    'email_send': 'EMAIL_SEND',
                    'delay': 'DELAY',
                    'subprocess': 'SUBPROCESS',
                    'custom': 'CUSTOM'
                }
                node_type = node_type_mapping.get(node_type_str.lower(), 'CUSTOM')
                
                # 创建统一节点
                # 获取节点配置和名称
                node_data_obj = node_data.get('data', {})
                node_config = node_data_obj.get('node_config', {})
                node_name = node_data_obj.get('name', '')
                node_type_from_config = node_config.get('type', '')
                
                # 优先使用node_config中的type，其次使用node_data中的type
                if node_type_from_config:
                    node_type = node_type_from_config.upper().replace('-', '_')
                
                # 确保节点配置中包含正确的脚本内容
                if node_type == 'SHELL_SCRIPT' and 'config' in node_config:
                    # 确保脚本内容被正确保存
                    if 'script' not in node_config['config'] and 'script' in node_data_obj.get('config', {}):
                        if not node_config.get('config'):
                            node_config['config'] = {}
                        node_config['config']['script'] = node_data_obj['config']['script']
                
                # 同样处理Python代码和SQL查询
                if node_type == 'PYTHON_CODE' and 'config' in node_config:
                    if 'code' not in node_config['config'] and 'code' in node_data_obj.get('config', {}):
                        if not node_config.get('config'):
                            node_config['config'] = {}
                        node_config['config']['code'] = node_data_obj['config']['code']
                
                if node_type == 'SQL_QUERY' and 'config' in node_config:
                    if 'sql' not in node_config['config'] and 'sql' in node_data_obj.get('config', {}):
                        if not node_config.get('config'):
                            node_config['config'] = {}
                        node_config['config']['sql'] = node_data_obj['config']['sql']
                
                unified_node = UnifiedNode(
                    name=node_data.get('id', f'node_{len(workflow_data.nodes)}'),
                    display_name=node_name or node_data.get('label', ''),
                    description=f"工作流 {workflow_id} 中的节点",
                    node_type=node_type,
                    node_category='workflow_node',
                    workflow_id=workflow_id,
                    node_config=node_config,
                    position_x=int(node_data.get('position', {}).get('x', 0) or node_data.get('x', 0)),
                    position_y=int(node_data.get('position', {}).get('y', 0) or node_data.get('y', 0)),
                    executor_group=node_data_obj.get('config', {}).get('workerGroup', 'default'),
                    priority='normal',
                    timeout_seconds=3600,
                    max_retry_count=3,
                    retry_interval_seconds=60,
                    project_id=workflow.project_id,
                    created_by=current_user.id,
                    is_active=True,
                    version=1
                )
                db.add(unified_node)
    
    # 处理连接数据 - 基于 UnifiedNode
    if workflow_data.connections is not None:
        # 删除现有连接
        await db.execute(
            delete(WorkflowConnection).where(WorkflowConnection.workflow_id == workflow_id)
        )
        
        # 创建新连接
        for conn_data in workflow_data.connections:
            # 从前端数据中提取连接信息
            if conn_data.get('shape') == 'edge':
                # 需要根据节点名称查找统一节点ID
                source_node_name = conn_data.get('source', {}).get('cell')
                target_node_name = conn_data.get('target', {}).get('cell')
                
                if source_node_name and target_node_name:
                    # 查找源节点和目标节点
                    source_stmt = select(UnifiedNode).where(
                        UnifiedNode.workflow_id == workflow_id,
                        UnifiedNode.name == source_node_name
                    )
                    source_result = await db.execute(source_stmt)
                    source_node = source_result.scalar_one_or_none()
                    
                    target_stmt = select(UnifiedNode).where(
                        UnifiedNode.workflow_id == workflow_id,
                        UnifiedNode.name == target_node_name
                    )
                    target_result = await db.execute(target_stmt)
                    target_node = target_result.scalar_one_or_none()
                    
                    if source_node and target_node:
                        # 确定连接类型
                        conn_type = conn_data.get('data', {}).get('connectionType', 'success')
                        connection_type_mapping = {
                            'success': 'SUCCESS',
                            'failure': 'FAILURE',
                            'conditional': 'CONDITIONAL',
                            'always': 'ALWAYS'
                        }
                        connection_type = connection_type_mapping.get(conn_type.lower(), 'SUCCESS')
                        
                        # 创建工作流连接
                        connection = WorkflowConnection(
                            workflow_id=workflow_id,
                            source_node_id=source_node.id,  # 现在指向 UnifiedNode.id
                            target_node_id=target_node.id,  # 现在指向 UnifiedNode.id
                            connection_type=connection_type,
                            connection_config=conn_data.get('data', {})
                        )
                        db.add(connection)
    
    await db.commit()
    await db.refresh(workflow)
    
    return workflow


@router.delete("/{workflow_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workflow(
    workflow_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除工作流"""
    stmt = select(Workflow).where(Workflow.id == workflow_id)
    result = await db.execute(stmt)
    workflow = result.scalar_one_or_none()
    if not workflow:
        raise NotFoundException(f"工作流 {workflow_id} 不存在")
    
    # 检查权限
    if workflow.created_by != current_user.id and not current_user.is_admin:
        raise ForbiddenException("没有权限删除此工作流")
    
    # 检查是否有运行中的实例
    count_stmt = select(func.count(WorkflowInstance.id)).where(
        WorkflowInstance.workflow_id == workflow_id,
        WorkflowInstance.status.in_(['pending', 'running'])
    )
    count_result = await db.execute(count_stmt)
    running_instances = count_result.scalar()
    if running_instances > 0:
        raise ValidationError(f"工作流有 {running_instances} 个运行中的实例，无法删除")
    
    # 删除相关的统一节点和连接
    await db.execute(delete(UnifiedNode).where(UnifiedNode.workflow_id == workflow_id))
    await db.execute(delete(WorkflowConnection).where(WorkflowConnection.workflow_id == workflow_id))
    
    await db.delete(workflow)
    await db.commit()


# ============================================
# 工作流节点管理接口
# ============================================

@router.get("/{workflow_id}/nodes", response_model=List[WorkflowNodeSchema])
async def list_workflow_nodes(
    workflow_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取工作流节点列表"""
    # 检查工作流是否存在
    workflow_stmt = select(Workflow).where(Workflow.id == workflow_id)
    workflow_result = await db.execute(workflow_stmt)
    workflow = workflow_result.scalar_one_or_none()
    if not workflow:
        raise NotFoundException(f"工作流 {workflow_id} 不存在")
    
    # 从 TaskDefinition 表获取工作流相关的任务定义
    tasks_stmt = select(TaskDefinition).where(
        TaskDefinition.task_category == f'workflow_{workflow_id}'
    )
    tasks_result = await db.execute(tasks_stmt)
    tasks = tasks_result.scalars().all()
    
    # 将 TaskDefinition 转换为 WorkflowNode 格式
    nodes = []
    for task in tasks:
        task_config = task.task_config or {}
        position = task_config.get('position', {'x': 0, 'y': 0})
        
        # 将大写枚举值转换为小写以匹配 Pydantic schema
        node_type = task_config.get('original_node_type', task.task_type)
        if isinstance(node_type, str):
            node_type = node_type.lower()
        
        node_dict = {
            'id': task.id,
            'workflow_id': workflow_id,
            'node_name': task.name,
            'display_name': task.display_name,
            'node_type': node_type,
            'node_config': task_config.get('node_data', {}),
            'position_x': position.get('x', 0),
            'position_y': position.get('y', 0),
            'description': task.description,
            'executor_group': task.executor_group,
            'timeout_seconds': task.timeout_seconds,
            'max_retry_count': task.max_retry_count,
            'created_at': task.created_at,
            'updated_at': task.updated_at
        }
        nodes.append(node_dict)
    
    return nodes


@router.post("/{workflow_id}/nodes", response_model=WorkflowNodeSchema, status_code=status.HTTP_201_CREATED)
async def create_workflow_node(
    workflow_id: int,
    node_data: WorkflowNodeCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建工作流节点"""
    # 检查工作流是否存在
    workflow_stmt = select(Workflow).where(Workflow.id == workflow_id)
    workflow_result = await db.execute(workflow_stmt)
    workflow = workflow_result.scalar_one_or_none()
    if not workflow:
        raise NotFoundError(f"工作流 {workflow_id} 不存在")
    
    # 检查权限
    if workflow.created_by != current_user.id and not current_user.is_admin:
        raise AuthorizationError("没有权限修改此工作流")
    
    # 检查节点名称是否在工作流中唯一
    existing_task_stmt = select(TaskDefinition).where(
        TaskDefinition.task_category == f'workflow_{workflow_id}',
        TaskDefinition.name == node_data.node_name
    )
    existing_task_result = await db.execute(existing_task_stmt)
    existing_task = existing_task_result.scalar_one_or_none()
    if existing_task:
        raise ValidationError(f"节点名称 '{node_data.node_name}' 在工作流中已存在")
    
    # 创建任务定义（节点）
    task_config = {
        'original_node_type': node_data.node_type,
        'node_data': node_data.node_config,
        'position': {
            'x': getattr(node_data, 'position_x', 0),
            'y': getattr(node_data, 'position_y', 0)
        },
        'input_parameters': getattr(node_data, 'input_parameters', None),
        'output_parameters': getattr(node_data, 'output_parameters', None)
    }
    
    task_definition = TaskDefinition(
        name=node_data.node_name,
        display_name=getattr(node_data, 'display_name', None),
        description=getattr(node_data, 'description', None),
        task_type=node_data.node_type,
        task_category=f'workflow_{workflow_id}',
        task_config=task_config,
        executor_group=getattr(node_data, 'executor_group', None),
        timeout_seconds=getattr(node_data, 'timeout_seconds', None),
        max_retry_count=getattr(node_data, 'max_retry_count', None),
        created_by=current_user.id
    )
    
    db.add(task_definition)
    await db.commit()
    await db.refresh(task_definition)
    
    # 转换为 WorkflowNode 格式返回
    position = task_config.get('position', {'x': 0, 'y': 0})
    # 将大写枚举值转换为小写以匹配 Pydantic schema
    node_type = task_config.get('original_node_type', task_definition.task_type)
    if isinstance(node_type, str):
        node_type = node_type.lower()
    
    node_dict = {
        'id': task_definition.id,
        'workflow_id': workflow_id,
        'node_name': task_definition.name,
        'display_name': task_definition.display_name,
        'node_type': node_type,
        'node_config': task_config.get('node_data', {}),
        'position_x': position.get('x', 0),
        'position_y': position.get('y', 0),
        'description': task_definition.description,
        'executor_group': task_definition.executor_group,
        'timeout_seconds': task_definition.timeout_seconds,
        'max_retry_count': task_definition.max_retry_count,
        'created_at': task_definition.created_at,
        'updated_at': task_definition.updated_at
    }
    
    return node_dict


@router.get("/{workflow_id}/nodes/{node_id}", response_model=WorkflowNodeSchema)
async def get_workflow_node(
    workflow_id: int,
    node_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取工作流节点详情"""
    task_stmt = select(TaskDefinition).where(
        TaskDefinition.id == node_id,
        TaskDefinition.task_category == f'workflow_{workflow_id}'
    )
    task_result = await db.execute(task_stmt)
    task = task_result.scalar_one_or_none()
    if not task:
        raise NotFoundError(f"节点 {node_id} 不存在")
    
    # 转换为 WorkflowNode 格式返回
    task_config = task.task_config or {}
    position = task_config.get('position', {'x': 0, 'y': 0})
    # 将大写枚举值转换为小写以匹配 Pydantic schema
    node_type = task_config.get('original_node_type', task.task_type)
    if isinstance(node_type, str):
        node_type = node_type.lower()
    
    node_dict = {
        'id': task.id,
        'workflow_id': workflow_id,
        'node_name': task.name,
        'display_name': task.display_name,
        'node_type': node_type,
        'node_config': task_config.get('node_data', {}),
        'position_x': position.get('x', 0),
        'position_y': position.get('y', 0),
        'description': task.description,
        'executor_group': task.executor_group,
        'timeout_seconds': task.timeout_seconds,
        'max_retry_count': task.max_retry_count,
        'created_at': task.created_at,
        'updated_at': task.updated_at
    }
    
    return node_dict


@router.put("/{workflow_id}/nodes/{node_id}", response_model=WorkflowNodeSchema)
async def update_workflow_node(
    workflow_id: int,
    node_id: int,
    node_data: WorkflowNodeUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新工作流节点"""
    task_stmt = select(TaskDefinition).where(
        TaskDefinition.id == node_id,
        TaskDefinition.task_category == f'workflow_{workflow_id}'
    )
    task_result = await db.execute(task_stmt)
    task = task_result.scalar_one_or_none()
    if not task:
        raise NotFoundError(f"节点 {node_id} 不存在")
    
    # 检查权限
    workflow_stmt = select(Workflow).where(Workflow.id == workflow_id)
    workflow_result = await db.execute(workflow_stmt)
    workflow = workflow_result.scalar_one_or_none()
    if workflow.created_by != current_user.id and not current_user.is_admin:
        raise AuthorizationError("没有权限修改此工作流")
    
    # 更新任务定义
    update_data = node_data.model_dump(exclude_unset=True)
    task_config = task.task_config or {}
    
    # 处理节点特有字段的映射
    if 'node_name' in update_data:
        task.name = update_data['node_name']
    if 'display_name' in update_data:
        task.display_name = update_data['display_name']
    if 'description' in update_data:
        task.description = update_data['description']
    if 'node_type' in update_data:
        task.task_type = update_data['node_type']
        task_config['original_node_type'] = update_data['node_type']
    if 'node_config' in update_data:
        task_config['node_data'] = update_data['node_config']
    if 'position_x' in update_data or 'position_y' in update_data:
        position = task_config.get('position', {'x': 0, 'y': 0})
        if 'position_x' in update_data:
            position['x'] = update_data['position_x']
        if 'position_y' in update_data:
            position['y'] = update_data['position_y']
        task_config['position'] = position
    if 'input_parameters' in update_data:
        task_config['input_parameters'] = update_data['input_parameters']
    if 'output_parameters' in update_data:
        task_config['output_parameters'] = update_data['output_parameters']
    if 'executor_group' in update_data:
        task.executor_group = update_data['executor_group']
    if 'timeout_seconds' in update_data:
        task.timeout_seconds = update_data['timeout_seconds']
    if 'max_retry_count' in update_data:
        task.max_retry_count = update_data['max_retry_count']
    
    task.task_config = task_config
    
    await db.commit()
    await db.refresh(task)
    
    # 转换为 WorkflowNode 格式返回
    position = task_config.get('position', {'x': 0, 'y': 0})
    # 将大写枚举值转换为小写以匹配 Pydantic schema
    node_type = task_config.get('original_node_type', task.task_type)
    if isinstance(node_type, str):
        node_type = node_type.lower()
    
    node_dict = {
        'id': task.id,
        'workflow_id': workflow_id,
        'node_name': task.name,
        'display_name': task.display_name,
        'node_type': node_type,
        'node_config': task_config.get('node_data', {}),
        'position_x': position.get('x', 0),
        'position_y': position.get('y', 0),
        'description': task.description,
        'executor_group': task.executor_group,
        'timeout_seconds': task.timeout_seconds,
        'max_retry_count': task.max_retry_count,
        'created_at': task.created_at,
        'updated_at': task.updated_at
    }
    
    return node_dict


@router.delete("/{workflow_id}/nodes/{node_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workflow_node(
    workflow_id: int,
    node_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除工作流节点"""
    task_stmt = select(TaskDefinition).where(
        TaskDefinition.id == node_id,
        TaskDefinition.task_category == f'workflow_{workflow_id}'
    )
    task_result = await db.execute(task_stmt)
    task = task_result.scalar_one_or_none()
    if not task:
        raise NotFoundError(f"节点 {node_id} 不存在")
    
    # 检查权限
    workflow_stmt = select(Workflow).where(Workflow.id == workflow_id)
    workflow_result = await db.execute(workflow_stmt)
    workflow = workflow_result.scalar_one_or_none()
    if workflow.created_by != current_user.id and not current_user.is_admin:
        raise AuthorizationError("没有权限修改此工作流")
    
    # 检查是否有连接关系（注意：现在连接表中的 node_id 实际指向 TaskDefinition.id）
    connections_stmt = select(func.count(WorkflowConnection.id)).where(
        (WorkflowConnection.source_node_id == node_id) |
        (WorkflowConnection.target_node_id == node_id)
    )
    connections_result = await db.execute(connections_stmt)
    connections = connections_result.scalar()
    if connections > 0:
        raise ValidationError(f"节点有 {connections} 个连接关系，请先删除连接")
    
    await db.delete(task)
    await db.commit()


# ============================================
# 工作流连接管理接口
# ============================================

@router.get("/{workflow_id}/connections", response_model=List[WorkflowConnectionSchema])
async def list_workflow_connections(
    workflow_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取工作流连接列表"""
    connections_stmt = select(WorkflowConnection).where(
        WorkflowConnection.workflow_id == workflow_id
    )
    connections_result = await db.execute(connections_stmt)
    connections = connections_result.scalars().all()
    return connections


@router.post("/{workflow_id}/connections", response_model=WorkflowConnectionSchema, status_code=status.HTTP_201_CREATED)
async def create_workflow_connection(
    workflow_id: int,
    connection_data: WorkflowConnectionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建工作流连接"""
    # 检查工作流是否存在
    workflow_stmt = select(Workflow).where(Workflow.id == workflow_id)
    workflow_result = await db.execute(workflow_stmt)
    workflow = workflow_result.scalar_one_or_none()
    if not workflow:
        raise NotFoundError(f"工作流 {workflow_id} 不存在")
    
    # 检查权限
    if workflow.created_by != current_user.id and not current_user.is_admin:
        raise AuthorizationError("没有权限修改此工作流")
    
    # 检查源任务定义和目标任务定义是否存在
    source_task_stmt = select(TaskDefinition).where(
        TaskDefinition.id == connection_data.source_node_id,
        TaskDefinition.task_category == f'workflow_{workflow_id}'
    )
    source_task_result = await db.execute(source_task_stmt)
    source_task = source_task_result.scalar_one_or_none()
    
    target_task_stmt = select(TaskDefinition).where(
        TaskDefinition.id == connection_data.target_node_id,
        TaskDefinition.task_category == f'workflow_{workflow_id}'
    )
    target_task_result = await db.execute(target_task_stmt)
    target_task = target_task_result.scalar_one_or_none()
    
    if not source_task:
        raise NotFoundError(f"源节点 {connection_data.source_node_id} 不存在")
    if not target_task:
        raise NotFoundError(f"目标节点 {connection_data.target_node_id} 不存在")
    
    # 检查是否已存在相同的连接
    existing_connection_stmt = select(WorkflowConnection).where(
        WorkflowConnection.workflow_id == workflow_id,
        WorkflowConnection.source_node_id == connection_data.source_node_id,
        WorkflowConnection.target_node_id == connection_data.target_node_id,
        WorkflowConnection.connection_type == connection_data.connection_type
    )
    existing_connection_result = await db.execute(existing_connection_stmt)
    existing_connection = existing_connection_result.scalar_one_or_none()
    if existing_connection:
        raise ValidationError("相同的连接已存在")
    
    # 创建连接
    connection = WorkflowConnection(**connection_data.model_dump())
    db.add(connection)
    await db.commit()
    await db.refresh(connection)
    
    return connection


@router.delete("/{workflow_id}/connections/{connection_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workflow_connection(
    workflow_id: int,
    connection_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除工作流连接"""
    connection = db.query(WorkflowConnection).filter(
        WorkflowConnection.id == connection_id,
        WorkflowConnection.workflow_id == workflow_id
    ).first()
    if not connection:
        raise NotFoundError(f"连接 {connection_id} 不存在")
    
    # 检查权限
    workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
    if workflow.created_by != current_user.id and not current_user.is_admin:
        raise AuthorizationError("没有权限修改此工作流")
    
    db.delete(connection)
    db.commit()


# ============================================
# 工作流执行接口
# ============================================

@router.post("/{workflow_id}/execute", response_model=WorkflowInstanceSchema, status_code=status.HTTP_201_CREATED)
async def execute_workflow(
    workflow_id: int,
    execute_request: WorkflowExecuteRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """执行工作流"""
    # 检查工作流是否存在且为活跃状态
    result = await db.execute(
        select(Workflow).filter(
            Workflow.id == workflow_id,
            Workflow.workflow_status == 'active'
        )
    )
    workflow = result.scalar_one_or_none()
    if not workflow:
        raise HTTPException(status_code=404, detail=f"工作流 {workflow_id} 不存在或未激活")
    
    # 生成实例ID
    import uuid
    instance_id = f"wf_{workflow_id}_{int(datetime.now().timestamp())}_{str(uuid.uuid4())[:8]}"
    
    # 创建工作流实例
    workflow_instance = WorkflowInstance(
        instance_id=instance_id,
        workflow_id=workflow_id,
        workflow_version=workflow.workflow_version,
        instance_name=f"{workflow.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        priority=execute_request.priority,
        input_data=execute_request.input_data,
        scheduled_time=execute_request.scheduled_time or datetime.now(),
        triggered_by='manual',
        triggered_by_user=current_user.id
    )
    
    db.add(workflow_instance)
    await db.commit()
    await db.refresh(workflow_instance)
    
    # 触发工作流执行引擎
    from ....services.workflow_engine import workflow_engine
    
    # 异步启动工作流实例
    asyncio.create_task(workflow_engine.start_instance(workflow_instance.id, db))
    
    return workflow_instance


@router.get("/instances", response_model=WorkflowInstanceListResponse)
async def list_workflow_instances(
    params: WorkflowInstanceQueryParams = Depends(),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取工作流实例列表"""
    query = db.query(WorkflowInstance)
    
    # 应用过滤条件
    if params.workflow_id:
        query = query.filter(WorkflowInstance.workflow_id == params.workflow_id)
    if params.status:
        query = query.filter(WorkflowInstance.status == params.status)
    if params.priority:
        query = query.filter(WorkflowInstance.priority == params.priority)
    if params.triggered_by:
        query = query.filter(WorkflowInstance.triggered_by == params.triggered_by)
    if params.triggered_by_user:
        query = query.filter(WorkflowInstance.triggered_by_user == params.triggered_by_user)
    if params.scheduled_start:
        query = query.filter(WorkflowInstance.scheduled_time >= params.scheduled_start)
    if params.scheduled_end:
        query = query.filter(WorkflowInstance.scheduled_time <= params.scheduled_end)
    
    # 应用排序
    if params.sort_by:
        if hasattr(WorkflowInstance, params.sort_by):
            order_column = getattr(WorkflowInstance, params.sort_by)
            if params.sort_order == "desc":
                query = query.order_by(order_column.desc())
            else:
                query = query.order_by(order_column.asc())
    else:
        query = query.order_by(WorkflowInstance.created_at.desc())
    
    # 应用分页
    total = query.count()
    instances = query.offset(params.skip).limit(params.limit).all()
    
    return WorkflowInstanceListResponse(
        items=instances,
        total=total,
        page=params.page,
        size=params.size,
        pages=(total + params.size - 1) // params.size
    )


@router.get("/instances/{instance_id}", response_model=WorkflowInstanceWithNodes)
async def get_workflow_instance(
    instance_id: int,
    include_nodes: bool = Query(True, description="是否包含节点实例信息"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取工作流实例详情"""
    # 使用异步查询获取工作流实例
    result = await db.execute(select(WorkflowInstance).filter(WorkflowInstance.id == instance_id))
    instance = result.scalar_one_or_none()
    if not instance:
        raise NotFoundException(f"工作流实例 {instance_id} 不存在")
    
    if include_nodes:
        # 获取节点实例信息
        node_result = await db.execute(select(WorkflowNodeInstance).filter(
            WorkflowNodeInstance.workflow_instance_id == instance_id
        ))
        node_instances = node_result.scalars().all()
        
        return WorkflowInstanceWithNodes(
            **instance.__dict__,
            node_instances=node_instances
        )
    
    return WorkflowInstanceWithNodes(**instance.__dict__)


@router.post("/instances/{instance_id}/cancel", response_model=WorkflowInstanceSchema)
async def cancel_workflow_instance(
    instance_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """取消工作流实例"""
    instance = db.query(WorkflowInstance).filter(WorkflowInstance.id == instance_id).first()
    if not instance:
        raise NotFoundException(f"工作流实例 {instance_id} 不存在")
    
    # 检查权限
    if instance.triggered_by_user != current_user.id and not current_user.is_admin:
        raise ForbiddenException("没有权限取消此工作流实例")
    
    # 检查状态
    if instance.status not in ['pending', 'running']:
        raise ValidationError(f"工作流实例状态为 {instance.status}，无法取消")
    
    # 更新状态
    instance.status = 'cancelled'
    instance.actual_end_time = datetime.now()
    
    db.commit()
    db.refresh(instance)
    
    # TODO: 这里应该通知执行引擎取消执行
    
    return instance


# ============================================
# 工作流统计接口
# ============================================

@router.get("/execution-status", response_model=WorkflowExecutionStatusListResponse)
async def get_workflow_execution_status(
    workflow_id: Optional[int] = Query(None, description="工作流ID"),
    status: Optional[str] = Query(None, description="实例状态"),
    limit: int = Query(50, ge=1, le=100, description="返回数量限制"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取工作流执行状态"""
    # 构建查询条件
    query = select(
        WorkflowInstance.id.label('workflow_instance_id'),
        WorkflowInstance.instance_id,
        Workflow.name.label('workflow_name'),
        Workflow.name.label('workflow_display_name'),  # 使用 name 字段作为 display_name
        WorkflowInstance.status.label('workflow_status'),
        WorkflowInstance.priority,
        WorkflowInstance.scheduled_time,
        WorkflowInstance.actual_start_time,
        WorkflowInstance.actual_end_time,
        WorkflowInstance.duration_seconds,
        WorkflowInstance.retry_count,
        WorkflowInstance.triggered_by,
        func.coalesce(User.username, 'system').label('triggered_by_username'),
        func.count(WorkflowNodeInstance.id).label('total_nodes'),
        func.sum(func.case((WorkflowNodeInstance.status == 'success', 1), else_=0)).label('completed_nodes'),
        func.sum(func.case((WorkflowNodeInstance.status == 'failed', 1), else_=0)).label('failed_nodes')
    ).select_from(
        WorkflowInstance.__table__.join(
            Workflow.__table__, WorkflowInstance.workflow_id == Workflow.id
        ).outerjoin(
            User.__table__, WorkflowInstance.triggered_by_user == User.id
        ).outerjoin(
            WorkflowNodeInstance.__table__, WorkflowInstance.id == WorkflowNodeInstance.workflow_instance_id
        )
    ).group_by(
        WorkflowInstance.id
    )
    
    # 添加过滤条件
    if workflow_id:
        query = query.where(WorkflowInstance.workflow_id == workflow_id)
    if status:
        query = query.where(WorkflowInstance.status == status)
    
    # 排序和限制
    query = query.order_by(WorkflowInstance.scheduled_time.desc()).limit(limit)
    
    result = await db.execute(query)
    rows = result.fetchall()
    
    # 转换为Schema对象
    execution_statuses = [
        WorkflowExecutionStatus(
            workflow_instance_id=row.workflow_instance_id,
            instance_id=row.instance_id,
            workflow_name=row.workflow_name,
            workflow_display_name=row.workflow_name,
            workflow_status=row.workflow_status,
            priority=row.priority,
            scheduled_time=row.scheduled_time,
            actual_start_time=row.actual_start_time,
            actual_end_time=row.actual_end_time,
            duration_seconds=row.duration_seconds,
            retry_count=row.retry_count,
            triggered_by=row.triggered_by,
            triggered_by_username=row.triggered_by_username,
            total_nodes=row.total_nodes or 0,
            completed_nodes=row.completed_nodes or 0,
            failed_nodes=row.failed_nodes or 0,
            running_nodes=row[16] or 0
        )
        for row in results
    ]
    
    return WorkflowExecutionStatusListResponse(
        items=execution_statuses,
        total=len(execution_statuses),
        page=1,
        size=limit,
        pages=1
    )


@router.get("/node-stats", response_model=NodeExecutionStatsListResponse)
async def get_node_execution_stats(
    workflow_id: Optional[int] = Query(None, description="工作流ID"),
    node_type: Optional[str] = Query(None, description="节点类型"),
    limit: int = Query(50, ge=1, le=100, description="返回数量限制"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取节点执行统计"""
    # 使用视图查询节点统计
    query = db.execute(
        """
        SELECT * FROM v_node_execution_stats
        WHERE 1=1
        {workflow_filter}
        {type_filter}
        ORDER BY total_executions DESC
        LIMIT {limit}
        """.format(
            workflow_filter=f"AND node_id IN (SELECT id FROM acwl_workflow_nodes WHERE workflow_id = {workflow_id})" if workflow_id else "",
            type_filter=f"AND node_type = '{node_type}'" if node_type else "",
            limit=limit
        )
    )
    
    results = query.fetchall()
    
    # 转换为Schema对象
    node_stats = [
        NodeExecutionStats(
            node_id=row[0],
            node_name=row[1],
            node_type=row[2],
            workflow_name=row[3],
            total_executions=row[4] or 0,
            success_count=row[5] or 0,
            failure_count=row[6] or 0,
            avg_duration_seconds=row[7],
            max_duration_seconds=row[8],
            min_duration_seconds=row[9]
        )
        for row in results
    ]
    
    return NodeExecutionStatsListResponse(
        items=node_stats,
        total=len(node_stats),
        page=1,
        size=limit,
        pages=1
    )