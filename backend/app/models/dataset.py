#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据集数据库模型
"""

from sqlalchemy import Column, Integer, String, Text, BigInteger, Boolean, DateTime, Enum, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum

from app.core.database import Base


class DatasetType(PyEnum):
    """数据集类型枚举"""
    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    TABULAR = "tabular"
    MULTIMODAL = "multimodal"


class DatasetStatus(PyEnum):
    """数据集状态枚举"""
    PENDING = "pending"
    PROCESSING = "processing"
    READY = "ready"
    ERROR = "error"


class Dataset(Base):
    """数据集模型"""
    __tablename__ = "acwl_datasets"
    
    id = Column(Integer, primary_key=True, index=True, comment="数据集ID，自增主键")
    name = Column(String(100), nullable=False, comment="数据集名称")
    description = Column(Text, comment="数据集描述")
    dataset_type = Column(
        Enum('text', 'image', 'audio', 'video', 'tabular', 'multimodal', name='datasettype'), 
        nullable=False, 
        comment="数据集类型：文本、图像、音频、视频、多模态"
    )
    format = Column(String(50), comment="格式，如JSON、CSV、JSONL等")
    size = Column(BigInteger, comment="数据集大小(字节)")
    record_count = Column(Integer, comment="记录数量")
    storage_path = Column(Text, comment="存储路径")
    is_public = Column(Boolean, default=False, comment="是否公开")
    status = Column(
        Enum('pending', 'processing', 'ready', 'error', name='datasetstatus'), 
        default='pending', 
        comment="数据集状态"
    )
    tags = Column(Text, comment="标签，JSON格式存储")
    preview_data = Column(Text, comment="预览数据，JSON格式存储")
    
    # 外键关联
    created_by = Column(Integer, ForeignKey("acwl_users.id"), comment="创建者ID")
    
    # 时间戳
    created_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        comment="创建时间"
    )
    updated_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        onupdate=func.now(), 
        comment="更新时间"
    )
    
    # 关系
    creator = relationship("User", back_populates="datasets")
    
    def __repr__(self):
        return f"<Dataset(id={self.id}, name='{self.name}', type='{self.dataset_type}')>"