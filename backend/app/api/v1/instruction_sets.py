from typing import List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.crud.instruction_set import instruction_set, instruction_node, instruction_execution
from app.schemas.instruction_set import (
    InstructionSet, InstructionSetCreate, InstructionSetUpdate,
    InstructionNode, InstructionNodeCreate, InstructionNodeUpdate,
    InstructionExecution, InstructionExecutionCreate,
    InstructionExecuteRequest, InstructionExecuteResponse,
    InstructionTreeNode, InstructionSetListResponse
)
from app.schemas.common import ResponseModel
from app.services.instruction_executor import InstructionExecutor

router = APIRouter()


# 指令集相关接口
@router.get("/", response_model=InstructionSetListResponse)
async def get_instruction_sets(
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(100, ge=1, le=1000, description="返回的记录数"),
    status: Optional[str] = Query(None, description="状态筛选"),
    created_by: Optional[int] = Query(None, description="创建者筛选"),
    db: AsyncSession = Depends(get_db)
):
    """获取指令集列表"""
    # 获取数据和总数
    data = await instruction_set.get_multi(
        db, skip=skip, limit=limit, status=status, created_by=created_by
    )
    total = await instruction_set.get_count(
        db, status=status, created_by=created_by
    )
    
    # 将 SQLAlchemy 模型列表转换为 Pydantic 模型列表
    instruction_sets_data = [InstructionSet.model_validate(item) for item in data]
    
    # 计算分页信息
    page = (skip // limit) + 1
    total_pages = (total + limit - 1) // limit
    has_next = skip + limit < total
    has_prev = skip > 0
    
    return InstructionSetListResponse(
        data=instruction_sets_data,
        total=total,
        page=page,
        page_size=limit,
        total_pages=total_pages,
        has_next=has_next,
        has_prev=has_prev
    )


@router.post("/", response_model=ResponseModel)
async def create_instruction_set(
    instruction_set_in: InstructionSetCreate,
    db: AsyncSession = Depends(get_db)
):
    """创建指令集"""
    # 创建指令集
    new_instruction_set = await instruction_set.create(db, obj_in=instruction_set_in)
    
    # 自动创建默认根节点
    from app.schemas.instruction_set import InstructionNodeCreate
    from app.models.instruction_set import NodeType, ConditionType, ActionType
    
    default_root_node = InstructionNodeCreate(
        instruction_set_id=new_instruction_set.id,
        parent_id=None,
        title="根节点",
        description="默认创建的根节点，您可以修改此节点或添加子节点",
        node_type=NodeType.CONDITION,
        condition_text="请输入条件描述",
        condition_type=ConditionType.AI_CLASSIFICATION,
        action_type=ActionType.CONTINUE,
        sort_order=0,
        is_active=True
    )
    
    # 创建默认根节点
    await instruction_node.create(db, obj_in=default_root_node)
    
    # 将 SQLAlchemy 模型转换为 Pydantic 模型
    instruction_set_data = InstructionSet.model_validate(new_instruction_set)
    
    return ResponseModel(
        success=True,
        message="指令集创建成功",
        data=instruction_set_data
    )


@router.get("/{instruction_set_id}", response_model=ResponseModel)
async def get_instruction_set(
    instruction_set_id: int,
    db: AsyncSession = Depends(get_db)
):
    """获取指令集详情"""
    db_instruction_set = await instruction_set.get(db, id=instruction_set_id)
    if not db_instruction_set:
        raise HTTPException(status_code=404, detail="指令集不存在")
    # 将 SQLAlchemy 模型转换为 Pydantic 模型
    instruction_set_data = InstructionSet.model_validate(db_instruction_set)
    return ResponseModel(
        success=True,
        message="获取指令集详情成功",
        data=instruction_set_data
    )


@router.put("/{instruction_set_id}", response_model=ResponseModel)
async def update_instruction_set(
    instruction_set_id: int,
    instruction_set_in: InstructionSetUpdate,
    db: AsyncSession = Depends(get_db)
):
    """更新指令集"""
    db_instruction_set = await instruction_set.get(db, id=instruction_set_id)
    if not db_instruction_set:
        raise HTTPException(status_code=404, detail="指令集不存在")
    
    updated_instruction_set = await instruction_set.update(
        db, db_obj=db_instruction_set, obj_in=instruction_set_in
    )
    # 将 SQLAlchemy 模型转换为 Pydantic 模型
    instruction_set_data = InstructionSet.model_validate(updated_instruction_set)
    return ResponseModel(
        success=True,
        message="指令集更新成功",
        data=instruction_set_data
    )


@router.delete("/{instruction_set_id}", response_model=ResponseModel)
async def delete_instruction_set(
    instruction_set_id: int,
    db: AsyncSession = Depends(get_db)
):
    """删除指令集"""
    db_instruction_set = await instruction_set.get(db, id=instruction_set_id)
    if not db_instruction_set:
        raise HTTPException(status_code=404, detail="指令集不存在")
    await instruction_set.remove(db, id=instruction_set_id)
    return ResponseModel(
        success=True,
        message="指令集删除成功",
        data=None
    )


# 指令节点相关接口
@router.get("/{instruction_set_id}/nodes", response_model=ResponseModel)
async def get_instruction_nodes(
    instruction_set_id: int,
    parent_id: Optional[int] = Query(None, description="父节点ID"),
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(100, ge=1, le=1000, description="返回的记录数"),
    db: AsyncSession = Depends(get_db)
):
    """获取指令节点列表"""
    # 验证指令集是否存在
    db_instruction_set = await instruction_set.get(db, id=instruction_set_id)
    if not db_instruction_set:
        raise HTTPException(status_code=404, detail="指令集不存在")
    
    nodes = await instruction_node.get_multi(
        db, instruction_set_id=instruction_set_id, parent_id=parent_id, skip=skip, limit=limit
    )
    # 将 SQLAlchemy 模型列表转换为 Pydantic 模型列表，手动映射字段以避免metadata冲突
    nodes_data = []
    for node in nodes:
        node_dict = {
            "id": node.id,
            "instruction_set_id": node.instruction_set_id,
            "parent_id": node.parent_id,
            "node_type": node.node_type,
            "title": node.title,
            "description": node.description,
            "keywords": node.keywords,
            "condition_text": node.condition_text,
            "condition_type": node.condition_type,
            "action_type": node.action_type,
            "result_value": node.result_value,
            "risk_level": getattr(node, 'risk_level', 'medium'),
            "result_confidence": node.result_confidence,
            "metadata": node.meta_data,  # 映射 meta_data 到 metadata
            "sort_order": node.sort_order,
            "is_active": node.is_active,
            "created_at": node.created_at,
            "updated_at": node.updated_at
        }
        nodes_data.append(InstructionNode.model_validate(node_dict))
    return ResponseModel(
        success=True,
        message="获取指令节点列表成功",
        data=nodes_data
    )


@router.get("/{instruction_set_id}/tree", response_model=ResponseModel)
async def get_instruction_tree(
    instruction_set_id: int,
    db: AsyncSession = Depends(get_db)
):
    """获取指令集的完整树结构"""
    # 验证指令集是否存在
    db_instruction_set = await instruction_set.get(db, id=instruction_set_id)
    if not db_instruction_set:
        raise HTTPException(status_code=404, detail="指令集不存在")
    
    tree_nodes = await instruction_node.get_tree(db, instruction_set_id=instruction_set_id)
    
    def generate_node_numbers(nodes, parent_number=""):
        """为节点生成编号"""
        for i, node in enumerate(nodes, 1):
            if parent_number:
                node.node_number = f"{parent_number}.{i}"
            else:
                node.node_number = str(i)
            
            if hasattr(node, 'children') and node.children:
                generate_node_numbers(node.children, node.node_number)
    
    def convert_to_tree_node(node) -> InstructionTreeNode:
        """转换为树节点格式"""
        children = []
        if hasattr(node, 'children'):
            children = [convert_to_tree_node(child) for child in node.children]
        
        return InstructionTreeNode(
            id=node.id,
            title=node.title,
            node_type=node.node_type,
            parent_id=node.parent_id,
            keywords=node.keywords,
            condition_text=node.condition_text,
            risk_level=getattr(node, 'risk_level', 'medium'),
            sort_order=node.sort_order,
            is_active=node.is_active,
            node_number=getattr(node, 'node_number', ''),
            children=children
        )
    
    # 为节点生成编号
    generate_node_numbers(tree_nodes)
    
    tree_data = [convert_to_tree_node(node) for node in tree_nodes]
    return ResponseModel(
        success=True,
        message="获取指令树结构成功",
        data=tree_data
    )


@router.post("/{instruction_set_id}/nodes", response_model=ResponseModel)
async def create_instruction_node(
    instruction_set_id: int,
    node_in: InstructionNodeCreate,
    db: AsyncSession = Depends(get_db)
):
    """创建指令节点"""
    # 验证指令集是否存在
    db_instruction_set = await instruction_set.get(db, id=instruction_set_id)
    if not db_instruction_set:
        raise HTTPException(status_code=404, detail="指令集不存在")
    
    # 设置指令集ID
    node_in.instruction_set_id = instruction_set_id
    new_node = await instruction_node.create(db, obj_in=node_in)
    # 将 SQLAlchemy 模型转换为 Pydantic 模型，手动映射字段以避免metadata冲突
    node_dict = {
        "id": new_node.id,
        "instruction_set_id": new_node.instruction_set_id,
        "parent_id": new_node.parent_id,
        "node_type": new_node.node_type,
        "title": new_node.title,
        "description": new_node.description,
        "keywords": new_node.keywords,
        "condition_text": new_node.condition_text,
        "condition_type": new_node.condition_type,
        "action_type": new_node.action_type,
        "result_value": new_node.result_value,
        "result_confidence": new_node.result_confidence,
        "metadata": new_node.meta_data,  # 映射 meta_data 到 metadata
        "sort_order": new_node.sort_order,
        "is_active": new_node.is_active,
        "created_at": new_node.created_at,
        "updated_at": new_node.updated_at
    }
    node_data = InstructionNode.model_validate(node_dict)
    return ResponseModel(
        success=True,
        message="指令节点创建成功",
        data=node_data
    )


@router.get("/nodes/{node_id}", response_model=ResponseModel)
async def get_instruction_node(
    node_id: int,
    db: AsyncSession = Depends(get_db)
):
    """获取指令节点详情"""
    db_node = await instruction_node.get(db, id=node_id)
    if not db_node:
        raise HTTPException(status_code=404, detail="指令节点不存在")
    # 将 SQLAlchemy 模型转换为 Pydantic 模型
    # 手动构建字典以避免 metadata 字段冲突
    node_dict = {
        'id': db_node.id,
        'instruction_set_id': db_node.instruction_set_id,
        'parent_id': db_node.parent_id,
        'node_type': db_node.node_type,
        'title': db_node.title,
        'description': db_node.description,
        'keywords': db_node.keywords,
        'condition_text': db_node.condition_text,
        'condition_type': db_node.condition_type,
        'action_type': db_node.action_type,
        'result_value': db_node.result_value,
        'result_confidence': db_node.result_confidence,
        'risk_level': getattr(db_node, 'risk_level', 'medium'),
        'sort_order': db_node.sort_order,
        'is_active': db_node.is_active,
        'metadata': db_node.meta_data,  # 映射字段名
        'created_at': db_node.created_at,
        'updated_at': db_node.updated_at,
        'children': []
    }
    node_data = InstructionNode.model_validate(node_dict)
    return ResponseModel(
        success=True,
        message="获取指令节点详情成功",
        data=node_data
    )


@router.put("/nodes/{node_id}", response_model=ResponseModel)
async def update_instruction_node(
    node_id: int,
    node_in: InstructionNodeUpdate,
    db: AsyncSession = Depends(get_db)
):
    """更新指令节点"""
    db_node = await instruction_node.get(db, id=node_id)
    if not db_node:
        raise HTTPException(status_code=404, detail="指令节点不存在")
    updated_node = await instruction_node.update(db, db_obj=db_node, obj_in=node_in)
    # 将 SQLAlchemy 模型转换为 Pydantic 模型，手动映射字段以避免metadata冲突
    node_dict = {
        "id": updated_node.id,
        "instruction_set_id": updated_node.instruction_set_id,
        "parent_id": updated_node.parent_id,
        "node_type": updated_node.node_type,
        "title": updated_node.title,
        "description": updated_node.description,
        "keywords": updated_node.keywords,
        "condition_text": updated_node.condition_text,
        "condition_type": updated_node.condition_type,
        "action_type": updated_node.action_type,
        "result_value": updated_node.result_value,
        "result_confidence": updated_node.result_confidence,
        "risk_level": getattr(updated_node, 'risk_level', 'medium'),
        "metadata": updated_node.meta_data,  # 映射 meta_data 到 metadata
        "sort_order": updated_node.sort_order,
        "is_active": updated_node.is_active,
        "created_at": updated_node.created_at,
        "updated_at": updated_node.updated_at
    }
    node_data = InstructionNode.model_validate(node_dict)
    return ResponseModel(
        success=True,
        message="指令节点更新成功",
        data=node_data
    )


@router.delete("/nodes/{node_id}", response_model=ResponseModel)
async def delete_instruction_node(
    node_id: int,
    db: AsyncSession = Depends(get_db)
):
    """删除指令节点"""
    db_node = await instruction_node.get(db, id=node_id)
    if not db_node:
        raise HTTPException(status_code=404, detail="指令节点不存在")
    await instruction_node.remove(db, id=node_id)
    return ResponseModel(
        success=True,
        message="指令节点删除成功",
        data=None
    )


@router.put("/nodes/{node_id}/move", response_model=ResponseModel)
async def move_instruction_node(
    node_id: int,
    new_parent_id: Optional[int] = None,
    new_sort_order: int = 0,
    db: AsyncSession = Depends(get_db)
):
    """移动指令节点"""
    db_node = await instruction_node.get(db, id=node_id)
    if not db_node:
        raise HTTPException(status_code=404, detail="指令节点不存在")
    
    updated_node = await instruction_node.move_node(
        db, node_id=node_id, new_parent_id=new_parent_id, new_sort_order=new_sort_order
    )
    # 将 SQLAlchemy 模型转换为 Pydantic 模型
    node_data = InstructionNode.model_validate(updated_node)
    return ResponseModel(
        success=True,
        message="指令节点移动成功",
        data=node_data
    )


# 指令执行相关接口
@router.post("/execute", response_model=ResponseModel)
async def execute_instruction_set(
    execute_request: InstructionExecuteRequest,
    db: AsyncSession = Depends(get_db)
):
    """执行指令集"""
    # 验证指令集是否存在
    db_instruction_set = await instruction_set.get(db, id=execute_request.instruction_set_id)
    if not db_instruction_set:
        raise HTTPException(status_code=404, detail="指令集不存在")
    
    # 检查指令集状态
    if db_instruction_set.status != "ACTIVE":
        raise HTTPException(status_code=400, detail="指令集未激活，无法执行")
    
    try:
        # 创建执行器并执行
        executor = InstructionExecutor(db)
        result = await executor.execute(
            instruction_set_id=execute_request.instruction_set_id,
            input_text=execute_request.input_text
        )
        
        # 保存执行记录
        if execute_request.save_execution:
            execution_record = InstructionExecutionCreate(
                instruction_set_id=execute_request.instruction_set_id,
                input_text=execute_request.input_text,
                execution_path=result["execution_path"],
                final_result=result["final_result"],
                confidence_score=result["confidence_score"],
                execution_time_ms=result["execution_time_ms"],
                status="SUCCESS"
            )
            db_execution = await instruction_execution.create(db, obj_in=execution_record)
            result["execution_id"] = db_execution.id
        
        execute_response = InstructionExecuteResponse(**result)
        return ResponseModel(
            success=True,
            message="指令集执行成功",
            data=execute_response
        )
        
    except Exception as e:
        # 保存错误记录
        if execute_request.save_execution:
            error_record = InstructionExecutionCreate(
                instruction_set_id=execute_request.instruction_set_id,
                input_text=execute_request.input_text,
                status="FAILED",
                error_message=str(e)
            )
            await instruction_execution.create(db, obj_in=error_record)
        
        raise HTTPException(status_code=500, detail=f"执行失败: {str(e)}")


@router.get("/{instruction_set_id}/executions", response_model=ResponseModel)
async def get_instruction_executions(
    instruction_set_id: int,
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(100, ge=1, le=1000, description="返回的记录数"),
    db: AsyncSession = Depends(get_db)
):
    """获取指令集执行记录"""
    # 验证指令集是否存在
    db_instruction_set = await instruction_set.get(db, id=instruction_set_id)
    if not db_instruction_set:
        raise HTTPException(status_code=404, detail="指令集不存在")
    
    executions = await instruction_execution.get_multi(
        db, instruction_set_id=instruction_set_id, skip=skip, limit=limit
    )
    # 将 SQLAlchemy 模型列表转换为 Pydantic 模型列表
    executions_data = [InstructionExecution.model_validate(execution) for execution in executions]
    return ResponseModel(
        success=True,
        message="获取执行记录成功",
        data=executions_data
    )


@router.get("/{instruction_set_id}/statistics", response_model=ResponseModel)
async def get_instruction_set_statistics(
    instruction_set_id: int,
    db: AsyncSession = Depends(get_db)
):
    """获取指令集统计信息"""
    # 验证指令集是否存在
    db_instruction_set = await instruction_set.get(db, id=instruction_set_id)
    if not db_instruction_set:
        raise HTTPException(status_code=404, detail="指令集不存在")
    
    statistics = await instruction_execution.get_statistics(db, instruction_set_id=instruction_set_id)
    return ResponseModel(
        success=True,
        message="获取统计信息成功",
        data=statistics
    )