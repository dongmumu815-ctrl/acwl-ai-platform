#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据资源类型模型，对应表 acwl_data_resource_types
"""

from sqlalchemy import String, Text, TIMESTAMP, JSON
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from typing import Optional, Dict, Any
from datetime import datetime

from app.core.database import Base
from app.core.id_generator import generate_snowflake_id


class DataResourceType(Base):
    """数据资源类型模型
    对应 MySQL 表: acwl_data_resource_types
    字段:
      - id: 主键，varchar(255)
      - name: 类型名称
      - describe: 字段描述
      - metadata: JSON，字段管理配置（列名为 metadata，Python属性使用 meta）
      - create_time: 创建时间
      - update_time: 更新时间
    """
    __tablename__ = "acwl_data_resource_types"
    __table_args__ = {"comment": "数据资源类型定义表"}

    id: Mapped[str] = mapped_column(
        String(255),
        primary_key=True,
        default=generate_snowflake_id,
        comment="ID"
    )

    name: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="类型名称"
    )

    describe: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="字段描述"
    )

    # 注意：Declarative保留了类属性名 metadata，因此不能使用同名属性
    # 这里将数据库列名设为 metadata，Python属性名为 meta
    meta: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        name="metadata",
        nullable=True,
        comment="字段管理配置(JSON)"
    )

    create_time: Mapped[Optional[datetime]] = mapped_column(
        TIMESTAMP,
        server_default=func.current_timestamp(),
        nullable=True,
        comment="创建时间"
    )

    update_time: Mapped[Optional[datetime]] = mapped_column(
        TIMESTAMP,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
        nullable=True,
        comment="更新时间"
    )