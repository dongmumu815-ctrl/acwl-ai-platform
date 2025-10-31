#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
环境管理模型
"""

from sqlalchemy import Column, Integer, String, Text, JSON, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from typing import Optional, Dict, Any

from app.core.database import Base


class Environment(Base):
    """
    环境表
    用于存储系统运行环境的名称、配置和描述
    """
    __tablename__ = "acwl_environments"
    __table_args__ = {"comment": "系统环境管理表"}

    id = Column(Integer, primary_key=True, autoincrement=True, comment="环境ID")
    name = Column(String(100), unique=True, nullable=False, index=True, comment="环境名称")
    config = Column(JSON, nullable=True, comment="环境配置(JSON)")
    description = Column(Text, nullable=True, comment="环境描述")

    # 审计字段
    created_by = Column(Integer, ForeignKey("acwl_users.id", ondelete="SET NULL"), nullable=True, comment="创建者ID")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")

    # 关系
    creator = relationship("User", foreign_keys=[created_by])

    def __repr__(self):
        return f"<Environment(id={self.id}, name='{self.name}')>"

    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            "id": self.id,
            "name": self.name,
            "config": self.config or {},
            "description": self.description,
            "created_by": self.created_by,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }