#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模型管理API端点
"""

from fastapi import APIRouter, Depends, Query, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional
import os
import shutil
from datetime import datetime

from app.core.database import get_db
from app.core.exceptions import NotFoundError, ValidationError
from app.models.user import User
from app.models.model import Model, ModelType
from app.schemas.common import PaginatedResponse, IDResponse
from app.api.v1.endpoints.auth import get_current_active_user, get_current_admin_user

router = APIRouter()


@router.get("/", summary="获取模型列表")
async def get_models(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    search: str = Query(None, description="搜索关键词"),
    model_type: Optional[ModelType] = Query(None, description="模型类型"),
    is_active: Optional[bool] = Query(None, description="是否激活"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取模型列表"""
    
    # 构建查询
    query = select(Model)
    
    # 搜索条件
    if search:
        query = query.where(
            Model.name.contains(search) |
            Model.description.contains(search)
        )
    
    # 类型筛选
    if model_type:
        query = query.where(Model.model_type == model_type)
    
    # 激活状态筛选
    if is_active is not None:
        query = query.where(Model.is_active == is_active)
    
    # 获取总数
    count_query = select(func.count(Model.id))
    if search:
        count_query = count_query.where(
            Model.name.contains(search) |
            Model.description.contains(search)
        )
    if model_type:
        count_query = count_query.where(Model.model_type == model_type)
    if is_active is not None:
        count_query = count_query.where(Model.is_active == is_active)
    
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # 分页查询
    offset = (page - 1) * size
    query = query.offset(offset).limit(size).order_by(Model.created_at.desc())
    
    result = await db.execute(query)
    models = result.scalars().all()
    
    # 序列化模型数据
    model_items = []
    for model in models:
        model_dict = {
            "id": model.id,
            "name": model.name,
            "version": model.version,
            "description": model.description,
            "model_type": model.model_type,
            "model_size": model.model_size,
            "framework": model.framework,
            "local_path": model.local_path,
            "is_active": model.is_active,
            "created_at": model.created_at,
            "updated_at": model.updated_at
        }
        model_items.append(model_dict)
    
    return PaginatedResponse(
        items=model_items,
        total=total,
        page=page,
        size=size,
        pages=(total + size - 1) // size
    )


@router.get("/{model_id}", summary="获取模型详情")
async def get_model(
    model_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取模型详情"""
    
    result = await db.execute(select(Model).where(Model.id == model_id))
    model = result.scalar_one_or_none()
    
    if not model:
        raise NotFoundError("模型不存在")
    
    # 序列化模型数据
    return {
        "id": model.id,
        "name": model.name,
        "version": model.version,
        "description": model.description,
        "model_type": model.model_type,
        "model_size": model.model_size,
        "framework": model.framework,
        "local_path": model.local_path,
        "is_active": model.is_active,
        "created_at": model.created_at,
        "updated_at": model.updated_at
    }


@router.post("/", summary="创建模型")
async def create_model(
    # 这里需要定义模型创建的schema
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> IDResponse:
    """创建模型"""
    # TODO: 实现模型创建逻辑
    return IDResponse(id=1, message="模型创建成功")


@router.put("/{model_id}", summary="更新模型")
async def update_model(
    model_id: int,
    # 这里需要定义模型更新的schema
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """更新模型"""
    # TODO: 实现模型更新逻辑
    return {"message": "模型更新成功"}


@router.delete("/{model_id}", summary="删除模型")
async def delete_model(
    model_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """删除模型（仅管理员）"""
    
    result = await db.execute(select(Model).where(Model.id == model_id))
    model = result.scalar_one_or_none()
    
    if not model:
        raise NotFoundError("模型不存在")
    
    await db.delete(model)
    await db.commit()
    
    return {"message": "模型删除成功"}


@router.post("/upload", summary="上传模型")
async def upload_model(
    file: UploadFile = File(...),
    name: str = Form(...),
    version: str = Form(...),
    model_type: ModelType = Form(...),
    description: str = Form(None),
    framework: str = Form(None),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> IDResponse:
    """上传模型文件"""
    
    # 检查模型名称和版本是否已存在
    existing_model = await db.execute(
        select(Model).where(Model.name == name, Model.version == version)
    )
    if existing_model.scalar_one_or_none():
        raise ValidationError(f"模型 {name}:{version} 已存在")
    
    # 创建上传目录
    upload_dir = f"/models/{name}-{version}"
    os.makedirs(upload_dir, exist_ok=True)
    
    # 保存文件
    file_path = os.path.join(upload_dir, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # 获取文件大小
    file_size = os.path.getsize(file_path)
    
    # 创建模型记录
    new_model = Model(
        name=name,
        version=version,
        description=description,
        model_type=model_type,
        model_size=file_size,
        framework=framework,
        local_path=file_path,
        is_active=True
    )
    
    db.add(new_model)
    await db.commit()
    await db.refresh(new_model)
    
    return IDResponse(id=new_model.id, message="模型上传成功")


@router.get("/{model_id}/download", summary="获取模型下载链接")
async def get_download_url(
    model_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取模型下载链接"""
    
    result = await db.execute(select(Model).where(Model.id == model_id))
    model = result.scalar_one_or_none()
    
    if not model:
        raise NotFoundError("模型不存在")
    
    if not model.local_path or not os.path.exists(model.local_path):
        raise NotFoundError("模型文件不存在")
    
    # 这里应该生成一个临时的下载链接
    # 为了简化，直接返回文件路径
    return {"url": f"/api/v1/models/{model_id}/file"}


@router.post("/{model_id}/clone", summary="克隆模型")
async def clone_model(
    model_id: int,
    request_data: dict,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> IDResponse:
    """克隆模型"""
    
    # 获取新模型名称
    name = request_data.get("name")
    if not name:
        raise ValidationError("模型名称不能为空")
    
    # 获取原模型
    result = await db.execute(select(Model).where(Model.id == model_id))
    original_model = result.scalar_one_or_none()
    
    if not original_model:
        raise NotFoundError("原模型不存在")
    
    # 检查新名称是否已存在
    existing_model = await db.execute(
        select(Model).where(Model.name == name, Model.version == original_model.version)
    )
    if existing_model.scalar_one_or_none():
        raise ValidationError(f"模型 {name}:{original_model.version} 已存在")
    
    # 创建克隆模型
    cloned_model = Model(
        name=name,
        version=original_model.version,
        description=f"克隆自 {original_model.name}",
        base_model=original_model.base_model,
        model_type=original_model.model_type,
        model_size=original_model.model_size,
        parameters=original_model.parameters,
        framework=original_model.framework,
        quantization=original_model.quantization,
        source_url=original_model.source_url,
        local_path=original_model.local_path,  # 共享同一个文件
        is_active=False  # 克隆的模型默认不激活
    )
    
    db.add(cloned_model)
    await db.commit()
    await db.refresh(cloned_model)
    
    return IDResponse(id=cloned_model.id, message="模型克隆成功")


@router.patch("/{model_id}/status", summary="切换模型状态")
async def toggle_model_status(
    model_id: int,
    request_data: dict,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """激活或停用模型"""
    
    # 获取激活状态
    is_active = request_data.get("is_active")
    if is_active is None:
        raise ValidationError("is_active参数不能为空")
    
    result = await db.execute(select(Model).where(Model.id == model_id))
    model = result.scalar_one_or_none()
    
    if not model:
        raise NotFoundError("模型不存在")
    
    model.is_active = is_active
    await db.commit()
    
    status_text = "激活" if is_active else "停用"
    return {"message": f"模型{status_text}成功"}


@router.get("/stats", summary="获取模型统计信息")
async def get_model_stats(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取模型统计信息"""
    
    # 总模型数
    total_result = await db.execute(select(func.count(Model.id)))
    total = total_result.scalar()
    
    # 激活模型数
    active_result = await db.execute(
        select(func.count(Model.id)).where(Model.is_active == True)
    )
    active = active_result.scalar()
    
    # 总存储大小
    size_result = await db.execute(
        select(func.sum(Model.model_size)).where(Model.model_size.isnot(None))
    )
    total_size = size_result.scalar() or 0
    
    return {
        "total": total,
        "active": active,
        "training": 0,  # 训练中的模型需要从其他表获取
        "totalSize": total_size
    }


@router.get("/available-for-agents", summary="获取可用于Agent的模型列表")
async def get_available_models_for_agents(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取可用于Agent配置的模型列表
    只返回激活状态的LLM类型模型，格式化为前端下拉选择所需的格式
    """
    
    # 查询激活的LLM模型
    query = select(Model).where(
        Model.is_active == True,
        Model.model_type == ModelType.LLM
    ).order_by(Model.name, Model.version)
    
    result = await db.execute(query)
    models = result.scalars().all()
    
    # 格式化为前端下拉选择所需的格式
    available_models = []
    for model in models:
        # 生成显示标签和值
        label = f"{model.name}"
        if model.version:
            label += f" ({model.version})"
        
        value = f"{model.name}"
        if model.version:
            value += f":{model.version}"
        
        available_models.append({
            "label": label,
            "value": value,
            "model_id": model.id,
            "description": model.description
        })
    
    return available_models