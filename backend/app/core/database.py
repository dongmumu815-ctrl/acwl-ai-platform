#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库连接和会话管理
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Text, Boolean, TIMESTAMP, ForeignKey, func
from typing import AsyncGenerator
from contextlib import asynccontextmanager
import logging

from .config import settings
from .connection_manager import patch_aiomysql

# 应用aiomysql补丁
patch_aiomysql()

logger = logging.getLogger(__name__)

# 导入所有模型以确保它们被注册到Base中
try:
    from app.models import *  # noqa
except ImportError:
    # 如果models模块不存在，忽略错误
    pass


class Base(DeclarativeBase):
    """数据库模型基类"""
    pass


class TimestampMixin:
    """时间戳混入类"""
    created_at: Mapped[TIMESTAMP] = mapped_column(
        TIMESTAMP,
        server_default=func.current_timestamp(),
        comment="创建时间"
    )
    updated_at: Mapped[TIMESTAMP] = mapped_column(
        TIMESTAMP,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
        comment="更新时间"
    )


class UserMixin:
    """用户关联混入类"""
    created_by: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("acwl_users.id", ondelete="SET NULL"),
        nullable=True,
        comment="创建者ID"
    )


# 创建异步数据库引擎
engine = create_async_engine(
    settings.database_url.replace("mysql+pymysql", "mysql+aiomysql"),
    echo=settings.DEBUG,
    pool_size=20,
    max_overflow=30,
    pool_pre_ping=True,
    pool_recycle=3600,
)

# 创建异步会话工厂
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """获取数据库会话"""
    session = AsyncSessionLocal()
    try:
        yield session
    except Exception:
        await session.rollback()
        raise
    finally:
        # 确保会话被正确关闭
        await session.close()


@asynccontextmanager
async def get_db_context():
    """获取数据库会话上下文管理器"""
    session = AsyncSessionLocal()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        # 确保会话被正确关闭
        await session.close()


async def init_db():
    """初始化数据库"""
    async with engine.begin() as conn:
        # 创建所有表
        await conn.run_sync(Base.metadata.create_all)


async def close_db():
    """关闭数据库连接"""
    await engine.dispose()