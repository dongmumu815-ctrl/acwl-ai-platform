#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
环境管理API端点
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.core.database import get_db
from app.core.exceptions import NotFoundError, ValidationError
from app.models.user import User
from app.schemas.common import IDResponse
from app.schemas.environment import (
    EnvironmentCreate,
    EnvironmentUpdate,
    EnvironmentResponse,
    EnvironmentListResponse,
)
from app.crud.environment import environment_crud
from app.api.v1.endpoints.auth import get_current_active_user, get_current_admin_user

router = APIRouter()


@router.get("/", summary="获取环境列表")
async def get_environments(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> EnvironmentListResponse:
    skip = (page - 1) * size
    items, total = await environment_crud.get_multi(
        db=db,
        skip=skip,
        limit=size,
        search=search
    )

    responses = [EnvironmentResponse(**item.to_dict()) for item in items]
    return EnvironmentListResponse(
        items=responses,
        total=total,
        page=page,
        size=size,
        pages=(total + size - 1) // size
    )


@router.get("/{env_id}", summary="获取环境详情")
async def get_environment(
    env_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> EnvironmentResponse:
    env = await environment_crud.get(db, env_id)
    if not env:
        raise NotFoundError("环境不存在")
    return EnvironmentResponse(**env.to_dict())


@router.post("/", summary="创建环境")
async def create_environment(
    env_in: EnvironmentCreate,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
) -> IDResponse:
    try:
        env = await environment_crud.create(db=db, obj_in=env_in, created_by=current_user.id)
        return IDResponse(id=env.id, message="环境创建成功")
    except Exception as e:
        raise ValidationError(f"创建环境失败: {str(e)}")


@router.put("/{env_id}", summary="更新环境")
async def update_environment(
    env_id: int,
    env_in: EnvironmentUpdate,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
) -> EnvironmentResponse:
    env = await environment_crud.get(db, env_id)
    if not env:
        raise NotFoundError("环境不存在")

    try:
        updated = await environment_crud.update(db=db, db_obj=env, obj_in=env_in)
        return EnvironmentResponse(**updated.to_dict())
    except Exception as e:
        raise ValidationError(f"更新环境失败: {str(e)}")


@router.delete("/{env_id}", summary="删除环境")
async def delete_environment(
    env_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    ok = await environment_crud.delete(db=db, env_id=env_id)
    if not ok:
        raise NotFoundError("环境不存在或已删除")
    return {"success": True, "message": "删除成功"}