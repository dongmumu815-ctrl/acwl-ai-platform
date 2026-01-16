#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库连接和会话管理
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker, Session
from sqlalchemy import Integer, String, Text, Boolean, TIMESTAMP, ForeignKey, func, create_engine
from sqlalchemy.pool import NullPool
from typing import AsyncGenerator
from contextlib import asynccontextmanager
from datetime import datetime
import logging

from .config import settings
from .connection_manager import patch_aiomysql

# 应用aiomysql补丁
# patch_aiomysql()

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    """数据库模型基类"""
    pass


class TimestampMixin:
    """时间戳混入类"""
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        server_default=func.current_timestamp(),
        comment="创建时间"
    )
    updated_at: Mapped[datetime] = mapped_column(
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
    updated_by: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("acwl_users.id", ondelete="SET NULL"),
        nullable=True,
        comment="更新者ID"
    )


# 创建异步数据库引擎
# engine = create_async_engine(
#     settings.database_url.replace("mysql+pymysql", "mysql+aiomysql"),
#     echo=settings.DEBUG,
#     pool_size=20,
#     max_overflow=30,
#     pool_pre_ping=True,
#     pool_recycle=3600,
# )

# 使用 NullPool 禁用连接池，避免 aiomysql 在 Windows 下的并发问题
engine = create_async_engine(
    settings.database_url.replace("mysql+pymysql", "mysql+aiomysql"),
    echo=False, # 禁用 SQL 日志以减少干扰
    poolclass=NullPool,
    # pool_pre_ping=True, # NullPool 不需要 pre_ping
)

# 创建同步数据库引擎（用于兼容现有代码）
sync_engine = create_engine(
    settings.database_url,
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

# 创建同步会话工厂（用于兼容现有代码）
SessionLocal = sessionmaker(
    bind=sync_engine,
    autocommit=False,
    autoflush=False
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """获取数据库会话"""
    import sys
    import asyncio
    # print("[DB_DEBUG] get_db called", file=sys.stderr, flush=True)
    
    # 简单的延时以避免可能的 socket 复用冲突（Windows 特有 hack）
    # await asyncio.sleep(0.01)
    
    session = AsyncSessionLocal()
    try:
        # 强制执行一个简单的查询来预热/验证连接
        # from sqlalchemy import text
        # await session.execute(text("SELECT 1"))
        yield session
    except Exception as e:
        print(f"[DB_DEBUG] get_db error: {e}", file=sys.stderr, flush=True)
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


# 导入所有模型以确保它们被注册到Base中
# 必须放在Base定义之后，以避免循环导入问题
try:
    from app.models.server import Server
    from app.models.server_group import ServerGroup
    # 也可以使用 from app.models import * 如果 __init__.py 配置正确
except ImportError as e:
    # 如果models模块不存在，忽略错误
    logger.warning(f"Import models failed: {e}")
    pass