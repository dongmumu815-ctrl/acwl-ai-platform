#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库连接和会话管理模块

提供SQLAlchemy数据库引擎、会话管理和基础模型类。
支持连接池、事务管理和异步操作。

Author: System
Date: 2024
"""

from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from contextlib import contextmanager
from typing import Generator
import logging

from app.core.config import settings

# 设置日志
logger = logging.getLogger(__name__)

# 创建数据库引擎
engine = create_engine(
    settings.DATABASE_URL,
    # 连接池配置
    poolclass=QueuePool,
    pool_size=10,  # 连接池大小
    max_overflow=20,  # 最大溢出连接数
    pool_pre_ping=True,  # 连接前检查
    pool_recycle=3600,  # 连接回收时间（秒）
    # 其他配置
    echo=settings.DEBUG,  # 是否打印SQL语句
    echo_pool=False,  # 是否打印连接池信息
    future=True,  # 使用SQLAlchemy 2.0风格
)

# 创建会话工厂
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False  # 提交后不过期对象
)

# 创建基础模型类
Base = declarative_base()

# 元数据配置
metadata = MetaData(
    naming_convention={
        "ix": "ix_%(column_0_label)s",
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s"
    }
)
Base.metadata = metadata


def get_db() -> Generator[Session, None, None]:
    """
    获取数据库会话
    
    FastAPI依赖注入函数，用于获取数据库会话。
    自动处理会话的创建和关闭。
    
    Yields:
        Session: SQLAlchemy数据库会话
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"数据库会话异常: {e}")
        db.rollback()
        raise
    finally:
        db.close()


@contextmanager
def get_db_context() -> Generator[Session, None, None]:
    """
    获取数据库会话上下文管理器
    
    用于在非FastAPI环境中获取数据库会话。
    支持with语句自动管理会话生命周期。
    
    Yields:
        Session: SQLAlchemy数据库会话
    
    Example:
        with get_db_context() as db:
            user = db.query(User).first()
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        logger.error(f"数据库操作异常: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def create_tables():
    """
    创建所有数据库表
    
    根据模型定义创建数据库表结构。
    通常在应用启动时调用。
    """
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("数据库表创建成功")
    except Exception as e:
        logger.error(f"创建数据库表失败: {e}")
        raise


def drop_tables():
    """
    删除所有数据库表
    
    警告：此操作会删除所有数据！
    仅用于开发和测试环境。
    """
    if not settings.DEBUG:
        raise RuntimeError("生产环境禁止删除数据库表")
    
    try:
        Base.metadata.drop_all(bind=engine)
        logger.warning("数据库表已删除")
    except Exception as e:
        logger.error(f"删除数据库表失败: {e}")
        raise


def check_database_connection() -> bool:
    """
    检查数据库连接状态
    
    测试数据库连接是否正常。
    
    Returns:
        bool: 连接状态，True表示正常
    """
    try:
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        logger.info("数据库连接正常")
        return True
    except Exception as e:
        logger.error(f"数据库连接失败: {e}")
        return False


def get_database_info() -> dict:
    """
    获取数据库信息
    
    返回数据库连接和配置信息。
    
    Returns:
        dict: 数据库信息字典
    """
    try:
        with engine.connect() as conn:
            result = conn.execute("SELECT VERSION() as version")
            version = result.fetchone()[0]
        
        return {
            "database_url": settings.DATABASE_URL.replace(settings.DB_PASSWORD, "***"),
            "database_name": settings.DB_NAME,
            "database_version": version,
            "pool_size": engine.pool.size(),
            "checked_in": engine.pool.checkedin(),
            "checked_out": engine.pool.checkedout(),
            "connection_status": "connected"
        }
    except Exception as e:
        logger.error(f"获取数据库信息失败: {e}")
        return {
            "database_url": settings.DATABASE_URL.replace(settings.DB_PASSWORD, "***"),
            "database_name": settings.DB_NAME,
            "connection_status": "disconnected",
            "error": str(e)
        }


class DatabaseManager:
    """
    数据库管理器类
    
    提供数据库操作的高级接口，包括事务管理、批量操作等。
    """
    
    def __init__(self):
        self.engine = engine
        self.SessionLocal = SessionLocal
    
    def execute_raw_sql(self, sql: str, params: dict = None) -> list:
        """
        执行原生SQL语句
        
        Args:
            sql: SQL语句
            params: 参数字典
        
        Returns:
            list: 查询结果列表
        """
        with get_db_context() as db:
            result = db.execute(sql, params or {})
            if result.returns_rows:
                return result.fetchall()
            return []
    
    def bulk_insert(self, model_class, data_list: list) -> int:
        """
        批量插入数据
        
        Args:
            model_class: 模型类
            data_list: 数据列表
        
        Returns:
            int: 插入的记录数
        """
        if not data_list:
            return 0
        
        with get_db_context() as db:
            db.bulk_insert_mappings(model_class, data_list)
            return len(data_list)
    
    def bulk_update(self, model_class, data_list: list) -> int:
        """
        批量更新数据
        
        Args:
            model_class: 模型类
            data_list: 数据列表（必须包含主键）
        
        Returns:
            int: 更新的记录数
        """
        if not data_list:
            return 0
        
        with get_db_context() as db:
            db.bulk_update_mappings(model_class, data_list)
            return len(data_list)
    
    def truncate_table(self, table_name: str):
        """
        清空表数据
        
        Args:
            table_name: 表名
        """
        if not settings.DEBUG:
            raise RuntimeError("生产环境禁止清空表数据")
        
        with get_db_context() as db:
            db.execute(f"TRUNCATE TABLE {table_name}")
            logger.warning(f"表 {table_name} 数据已清空")
    
    def get_table_count(self, table_name: str) -> int:
        """
        获取表记录数
        
        Args:
            table_name: 表名
        
        Returns:
            int: 记录数
        """
        with get_db_context() as db:
            result = db.execute(f"SELECT COUNT(*) FROM {table_name}")
            return result.scalar()


# 全局数据库管理器实例
db_manager = DatabaseManager()


if __name__ == "__main__":
    # 测试数据库连接
    print("测试数据库连接...")
    if check_database_connection():
        print("✅ 数据库连接成功")
        
        # 显示数据库信息
        info = get_database_info()
        print(f"数据库版本: {info.get('database_version', 'Unknown')}")
        print(f"连接池状态: {info.get('pool_size', 0)} total, "
              f"{info.get('checked_out', 0)} checked out, "
              f"{info.get('checked_in', 0)} checked in")
    else:
        print("❌ 数据库连接失败")