#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
认证相关API端点
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta
from typing import Dict, Any

from app.core.database import get_db
from app.core.config import settings
from app.core.exceptions import AuthenticationError, ValidationError
from app.models.user import User
from app.schemas.auth import Token, UserLogin, UserRegister, UserResponse, LoginResponse
from sqlalchemy.exc import OperationalError
from app.core.exceptions import ACWLException
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    decode_access_token
)

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)) -> User:
    """获取当前用户"""
    import sys
    print("[AUTH_DEBUG] get_current_user called", file=sys.stderr, flush=True)
    try:
        payload = decode_access_token(token)
        user_id_str = payload.get("sub")
        if user_id_str is None:
            print("[AUTH_DEBUG] No sub in payload", file=sys.stderr, flush=True)
            raise AuthenticationError("无效的认证令牌")
        user_id = int(user_id_str)  # 将字符串转换为整数
    except Exception as e:
        print(f"[AUTH_DEBUG] Token decode error: {e}", file=sys.stderr, flush=True)
        raise AuthenticationError("无效的认证令牌")
    
    print(f"[AUTH_DEBUG] Querying user {user_id}", file=sys.stderr, flush=True)
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if user is None:
        print(f"[AUTH_DEBUG] User {user_id} not found", file=sys.stderr, flush=True)
        raise AuthenticationError("用户不存在")
    
    return user


async def get_current_user_ws(token: str, db: AsyncSession) -> User:
    """获取当前用户（WebSocket用）"""
    try:
        payload = decode_access_token(token)
        user_id_str = payload.get("sub")
        if user_id_str is None:
            return None
        user_id = int(user_id_str)
    except Exception:
        return None
    
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """获取当前活跃用户"""
    if not current_user.is_active:
        raise AuthenticationError("用户已被禁用")
    return current_user


async def get_current_admin_user(current_user: User = Depends(get_current_active_user)) -> User:
    """获取当前管理员用户"""
    if not current_user.is_admin:
        raise AuthenticationError("需要管理员权限")
    return current_user


@router.post("/register", response_model=UserResponse, summary="用户注册")
async def register(
    user_data: UserRegister,
    db: AsyncSession = Depends(get_db)
) -> UserResponse:
    """用户注册
    
    - 接受基础信息：`username`、`email`、`password`、`confirm_password`
    - 支持可选字段：`department`、`phone`、`status`、`remark`
    - `role` 字段仅用于兼容，出于安全考虑注册时强制为 `user`
    """
    
    # 检查用户名是否已存在
    result = await db.execute(select(User).where(User.username == user_data.username))
    if result.scalar_one_or_none():
        raise ValidationError("用户名已存在")
    
    # 检查邮箱是否已存在
    result = await db.execute(select(User).where(User.email == user_data.email))
    if result.scalar_one_or_none():
        raise ValidationError("邮箱已存在")
    
    # 创建新用户
    try:
        hashed_password = get_password_hash(user_data.password)
    except ValueError as e:
        raise ValidationError(str(e))
    
    # 角色安全限制：注册阶段一律为普通用户
    # 其他可选字段按需设置
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        password_hash=hashed_password,
        role="user",
        department=user_data.department,
        phone=user_data.phone,
        status=(user_data.status or "active"),
        remark=user_data.remark
    )
    
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    return UserResponse.model_validate(new_user)


@router.post("/login", response_model=Token, summary="用户登录")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
) -> Token:
    """用户登录"""
    
    # 查找用户
    result = await db.execute(select(User).where(User.username == form_data.username))
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(form_data.password, user.password_hash):
        raise AuthenticationError("用户名或密码错误")
    
    if not user.is_active:
        raise AuthenticationError("用户已被禁用")
    
    # 创建访问令牌
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=access_token_expires
    )
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.post("/login/json", response_model=LoginResponse, summary="JSON格式登录")
async def login_json(
    user_data: UserLogin,
    db: AsyncSession = Depends(get_db)
) -> LoginResponse:
    """
    JSON格式用户登录
    
    - 支持用户名或邮箱登录
    - 针对数据库连接过多（1040）进行友好降级提示
    """
    try:
        if user_data.email:
            result = await db.execute(select(User).where(User.email == user_data.email))
        else:
            result = await db.execute(select(User).where(User.username == user_data.username))
        user = result.scalar_one_or_none()

        if not user or not verify_password(user_data.password, user.password_hash):
            raise AuthenticationError("用户名或密码错误")

        if not user.is_active:
            raise AuthenticationError("用户已被禁用")

        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": str(user.id)},
            expires_delta=access_token_expires
        )

        return LoginResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=UserResponse.model_validate(user)
        )
    except OperationalError as e:
        msg = str(e)
        if '1040' in msg or 'Too many connections' in msg:
            raise ACWLException(message="数据库连接过多，请稍后重试", status_code=503, error_code="DB_CONNECTION_LIMIT", detail=msg)
        raise ACWLException(message="数据库错误", status_code=500, error_code="DB_ERROR", detail=msg)


@router.get("/me", response_model=UserResponse, summary="获取当前用户信息")
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
) -> UserResponse:
    """获取当前用户信息"""
    return UserResponse.model_validate(current_user)


@router.post("/refresh", response_model=Token, summary="刷新令牌")
async def refresh_token(
    current_user: User = Depends(get_current_active_user)
) -> Token:
    """刷新访问令牌"""
    
    # 创建新的访问令牌
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(current_user.id)},
        expires_delta=access_token_expires
    )
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.post("/logout", summary="用户登出")
async def logout(
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    用户登出接口
    
    在基于JWT的无状态认证系统中，服务端不需要维护会话状态。
    客户端只需要删除本地存储的token即可实现登出。
    
    Args:
        current_user: 当前认证用户
        
    Returns:
        Dict[str, Any]: 登出成功响应
    """
    return {
        "success": True,
        "message": "登出成功",
        "data": {
            "user_id": current_user.id,
            "username": current_user.username,
            "logout_time": datetime.now().isoformat()
        }
    }