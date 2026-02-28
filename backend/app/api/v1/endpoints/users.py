#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用户管理API端点
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List

from app.core.database import get_db
from app.core.exceptions import NotFoundError, ValidationError, AuthorizationError
from app.models.user import User
from app.schemas.auth import UserResponse, UserUpdate, PasswordChange
from app.schemas.common import PaginatedResponse
from app.api.v1.endpoints.auth import get_current_active_user, get_current_admin_user
from app.core.security import verify_password, get_password_hash

router = APIRouter()


@router.get("/", response_model=PaginatedResponse[UserResponse], summary="获取用户列表")
async def get_users(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    search: str = Query(None, description="搜索关键词"),
    role: str = Query(None, description="角色筛选"),
    status: str = Query(None, description="状态筛选：active/disabled/pending"),
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
) -> PaginatedResponse[UserResponse]:
    """获取用户列表（仅管理员）
    
    - 支持按 `search`(用户名/邮箱)、`role`、`status` 过滤
    - 按 `created_at` 倒序分页
    """
    
    # 构建查询
    query = select(User)
    
    # 搜索条件
    if search:
        query = query.where(
            User.username.contains(search) |
            User.email.contains(search)
        )
    
    # 角色筛选
    if role:
        query = query.where(User.role == role)
    
    # 状态筛选
    if status:
        query = query.where(User.status == status)
    
    # 获取总数
    count_query = select(func.count(User.id))
    if search:
        count_query = count_query.where(
            User.username.contains(search) |
            User.email.contains(search)
        )
    if role:
        count_query = count_query.where(User.role == role)
    if status:
        count_query = count_query.where(User.status == status)
    
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # 分页查询
    offset = (page - 1) * size
    query = query.offset(offset).limit(size).order_by(User.created_at.desc())
    
    result = await db.execute(query)
    users = result.scalars().all()
    
    return PaginatedResponse(
        items=[UserResponse.model_validate(user) for user in users],
        total=total,
        page=page,
        size=size,
        pages=(total + size - 1) // size
    )


@router.get("/me", response_model=UserResponse, summary="获取当前用户信息")
async def get_current_user_profile(
    current_user: User = Depends(get_current_active_user)
) -> UserResponse:
    """获取当前用户信息"""
    return UserResponse.model_validate(current_user)


@router.get("/{user_id}", response_model=UserResponse, summary="获取用户详情")
async def get_user(
    user_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> UserResponse:
    """获取用户详情"""
    
    # 非管理员只能查看自己的信息
    if not current_user.is_admin and current_user.id != user_id:
        raise AuthorizationError("只能查看自己的用户信息")
    
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise NotFoundError("用户不存在")
    
    return UserResponse.model_validate(user)


@router.put("/me", response_model=UserResponse, summary="更新当前用户信息")
async def update_current_user(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> UserResponse:
    """更新当前用户信息"""
    
    # 普通用户不能修改角色
    if user_update.role and not current_user.is_admin:
        raise AuthorizationError("无权修改用户角色")
    
    # 检查邮箱是否已被其他用户使用
    if user_update.email:
        result = await db.execute(
            select(User).where(
                User.email == user_update.email,
                User.id != current_user.id
            )
        )
        if result.scalar_one_or_none():
            raise ValidationError("邮箱已被其他用户使用")
    
    # 更新用户信息
    for field, value in user_update.dict(exclude_unset=True).items():
        setattr(current_user, field, value)
    
    await db.commit()
    await db.refresh(current_user)
    
    return UserResponse.model_validate(current_user)


@router.put("/{user_id}", response_model=UserResponse, summary="更新用户信息")
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
) -> UserResponse:
    """更新用户信息（仅管理员）"""
    
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise NotFoundError("用户不存在")
    
    # 检查邮箱是否已被其他用户使用
    if user_update.email:
        result = await db.execute(
            select(User).where(
                User.email == user_update.email,
                User.id != user_id
            )
        )
        if result.scalar_one_or_none():
            raise ValidationError("邮箱已被其他用户使用")
    
    # 更新用户信息
    for field, value in user_update.dict(exclude_unset=True).items():
        setattr(user, field, value)
    
    await db.commit()
    await db.refresh(user)
    
    return UserResponse.model_validate(user)


@router.post("/me/change-password", summary="修改当前用户密码")
async def change_current_user_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """修改当前用户密码"""
    
    # 验证当前密码
    if not verify_password(password_data.current_password, current_user.password_hash):
        raise ValidationError("当前密码错误")
    
    # 更新密码
    try:
        current_user.password_hash = get_password_hash(password_data.new_password)
    except ValueError as e:
        raise ValidationError(str(e))
    
    await db.commit()
    
    return {"message": "密码修改成功"}


@router.delete("/{user_id}", summary="删除用户")
async def delete_user(
    user_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """删除用户（仅管理员）"""
    
    # 不能删除自己
    if current_user.id == user_id:
        raise ValidationError("不能删除自己的账户")
    
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise NotFoundError("用户不存在")
    
    await db.delete(user)
    await db.commit()
    
    return {"message": "用户删除成功"}