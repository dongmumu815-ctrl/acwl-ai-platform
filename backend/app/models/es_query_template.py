#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ES查询模板相关模型
"""

from sqlalchemy import Integer, String, Boolean, Text, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List, Dict, Any, Optional, TYPE_CHECKING

from app.core.database import Base, TimestampMixin

if TYPE_CHECKING:
    from .user import User
    from .datasource import Datasource


class ESQueryTemplate(Base, TimestampMixin):
    """ES查询模板模型"""
    
    __tablename__ = "es_query_templates"
    __table_args__ = {"comment": "ES查询模板表，存储用户保存的ES查询模板和实例"}
    
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="模板ID，自增主键"
    )
    
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="模板名称"
    )
    
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="模板描述"
    )
    
    datasource_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("acwl_datasources.id", ondelete="CASCADE"),
        nullable=False,
        comment="关联的数据源ID"
    )
    
    data_resource_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("acwl_data_resources.id", ondelete="SET NULL"),
        nullable=True,
        comment="关联的数据资源ID"
    )
    
    indices: Mapped[List[str]] = mapped_column(
        JSON,
        nullable=False,
        comment="ES索引列表"
    )
    
    query: Mapped[Dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        comment="ES查询DSL或可视化查询配置"
    )
    
    tags: Mapped[List[str]] = mapped_column(
        JSON,
        nullable=True,
        default=list,
        comment="标签列表"
    )
    
    is_template: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="是否为模板（True）还是实例（False）"
    )
    
    created_by: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("acwl_users.id", ondelete="CASCADE"),
        nullable=False,
        comment="创建者用户ID"
    )
    
    # 条件锁定相关字段
    condition_lock_types: Mapped[Optional[Dict[str, str]]] = mapped_column(
        JSON,
        nullable=True,
        comment="条件锁定类型配置，key为conditionId，value为锁定类型(full/range/operator)"
    )
    
    condition_ranges: Mapped[Optional[Dict[str, Dict[str, Any]]]] = mapped_column(
        JSON,
        nullable=True,
        comment="条件值范围限制配置，key为conditionId，value为范围对象{min, max}"
    )
    
    allowed_operators: Mapped[Optional[Dict[str, List[str]]]] = mapped_column(
        JSON,
        nullable=True,
        comment="允许的操作符配置，key为conditionId，value为操作符列表"
    )
    
    # 关系映射
    creator: Mapped["User"] = relationship(
        "User",
        foreign_keys=[created_by],
        back_populates="es_query_templates"
    )
    
    datasource: Mapped["Datasource"] = relationship(
        "Datasource",
        foreign_keys=[datasource_id],
        back_populates="es_query_templates"
    )
    
    def __repr__(self) -> str:
        return f"<ESQueryTemplate(id={self.id}, name='{self.name}', is_template={self.is_template})>"
    
    @property
    def template_type(self) -> str:
        """获取模板类型描述"""
        return "模板" if self.is_template else "实例"