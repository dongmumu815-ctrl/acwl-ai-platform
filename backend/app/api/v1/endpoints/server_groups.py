#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
服务器分组管理 API
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete
from typing import List

from app.core.database import get_db
from app.api.v1.endpoints.auth import get_current_user
from app.models.user import User
from app.models.server_group import ServerGroup
from app.models.server import Server
from app.schemas.server_group import ServerGroupCreate, ServerGroupUpdate, ServerGroupResponse, ServerGroupListResponse

router = APIRouter()

@router.post("/", response_model=ServerGroupResponse, summary="创建服务器分组")
async def create_server_group(
    group_in: ServerGroupCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """创建新的服务器分组"""
    # 检查名称是否重复
    result = await db.execute(select(ServerGroup).where(ServerGroup.name == group_in.name))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="分组名称已存在")
    
    new_group = ServerGroup(
        name=group_in.name,
        description=group_in.description,
        created_by=current_user.id,
        updated_by=current_user.id
    )
    
    db.add(new_group)
    await db.commit()
    await db.refresh(new_group)
    
    return new_group

@router.get("/", response_model=ServerGroupListResponse, summary="获取服务器分组列表")
async def get_server_groups(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取服务器分组列表"""
    # 查询分组及其服务器数量
    stmt = (
        select(
            ServerGroup,
            func.count(Server.id).label("server_count")
        )
        .outerjoin(Server, Server.group_id == ServerGroup.id)
        .group_by(ServerGroup.id)
        .offset(skip)
        .limit(limit)
    )
    
    result = await db.execute(stmt)
    items = []
    for group, count in result:
        # 手动添加 server_count 属性以匹配 Pydantic 模型
        setattr(group, "server_count", count)
        items.append(group)
    
    # 获取总数
    total_result = await db.execute(select(func.count(ServerGroup.id)))
    total = total_result.scalar_one()
    
    return {"total": total, "items": items}

@router.put("/{group_id}", response_model=ServerGroupResponse, summary="更新服务器分组")
async def update_server_group(
    group_id: int,
    group_in: ServerGroupUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """更新服务器分组"""
    result = await db.execute(select(ServerGroup).where(ServerGroup.id == group_id))
    group = result.scalar_one_or_none()
    
    if not group:
        raise HTTPException(status_code=404, detail="分组不存在")
    
    # 如果修改名称，检查重复
    if group_in.name and group_in.name != group.name:
        name_check = await db.execute(select(ServerGroup).where(ServerGroup.name == group_in.name))
        if name_check.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="分组名称已存在")
    
    update_data = group_in.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(group, field, value)
    
    group.updated_by = current_user.id
    await db.commit()
    await db.refresh(group)
    
    # 重新获取 server_count
    count_result = await db.execute(
        select(func.count(Server.id)).where(Server.group_id == group_id)
    )
    setattr(group, "server_count", count_result.scalar_one())
    
    return group

@router.delete("/{group_id}", summary="删除服务器分组")
async def delete_server_group(
    group_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """删除服务器分组"""
    result = await db.execute(select(ServerGroup).where(ServerGroup.id == group_id))
    group = result.scalar_one_or_none()
    
    if not group:
        raise HTTPException(status_code=404, detail="分组不存在")
    
    # 检查是否有服务器关联
    server_check = await db.execute(select(Server).where(Server.group_id == group_id))
    if server_check.first():
        raise HTTPException(status_code=400, detail="该分组下仍有服务器，无法删除")
    
    await db.delete(group)
    await db.commit()
    
    return {"message": "分组已删除"}
