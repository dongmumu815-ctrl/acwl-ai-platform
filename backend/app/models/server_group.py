#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
服务器分组模型
"""

from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, TimestampMixin, UserMixin

class ServerGroup(Base, TimestampMixin, UserMixin):
    """服务器分组表"""
    
    __tablename__ = "acwl_server_groups"
    __table_args__ = {"comment": "服务器分组表"}
    
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="分组ID"
    )
    
    name: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        unique=True,
        comment="分组名称"
    )
    
    description: Mapped[str] = mapped_column(
        String(255),
        nullable=True,
        comment="分组描述"
    )
    
    # 关联
    servers: Mapped[list["Server"]] = relationship("Server", back_populates="group")
