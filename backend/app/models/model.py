#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模型相关数据库模型
"""

from sqlalchemy import Integer, String, Text, Boolean, TIMESTAMP, BigInteger, Enum, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List, Optional, TYPE_CHECKING
import enum

from app.core.database import Base, TimestampMixin

if TYPE_CHECKING:
    from .deployment import Deployment
    from .fine_tuning import FineTuningJob
    # from .evaluation import ModelEvaluation
    # from .agent import Agent


class ModelType(str, enum.Enum):
    """模型类型枚举"""
    LLM = "LLM"
    EMBEDDING = "EMBEDDING"  # 匹配数据库实际枚举值
    MULTIMODAL = "MULTIMODAL"  # 匹配数据库实际枚举值
    OTHER = "OTHER"  # 匹配数据库实际枚举值


class DownloadStatus(str, enum.Enum):
    """下载状态枚举"""
    PENDING = "PENDING"  # 等待下载
    DOWNLOADING = "DOWNLOADING"  # 下载中
    COMPLETED = "COMPLETED"  # 下载完成
    FAILED = "FAILED"  # 下载失败
    UPLOADED = "UPLOADED"  # 直接上传（非下载）


class Model(Base, TimestampMixin):
    """模型信息表"""
    
    __tablename__ = "acwl_models"
    __table_args__ = (
        UniqueConstraint('name', 'version', name='uq_model_name_version'),
        {"comment": "大模型信息表，存储系统中所有模型的基本信息和元数据"}
    )
    
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="模型ID，自增主键"
    )
    
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="模型名称"
    )
    
    version: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="模型版本"
    )
    
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="模型描述"
    )
    
    base_model: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="基础模型名称"
    )
    
    model_type: Mapped[ModelType] = mapped_column(
        Enum(ModelType),
        nullable=False,
        comment="模型类型：LLM、Embedding、多模态或其他"
    )
    
    model_size: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        nullable=True,
        comment="模型大小(字节)"
    )
    
    parameters: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        nullable=True,
        comment="参数量"
    )
    
    framework: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="框架，如PyTorch、TensorFlow等"
    )
    
    quantization: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        comment="量化类型，如FP16、INT8等"
    )
    
    source_url: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="模型下载地址"
    )
    
    local_path: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="本地存储路径"
    )
    
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        comment="是否激活"
    )
    
    download_status: Mapped[DownloadStatus] = mapped_column(
        Enum(DownloadStatus),
        default=DownloadStatus.UPLOADED,
        comment="下载状态：等待下载、下载中、下载完成、下载失败、直接上传"
    )
    
    download_progress: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="下载进度百分比(0-100)"
    )
    
    download_error: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="下载错误信息"
    )
    
    # 关联关系
    deployments: Mapped[List["Deployment"]] = relationship(
        "Deployment",
        back_populates="model",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<Model(id={self.id}, name='{self.name}', version='{self.version}', type='{self.model_type}')>"
    
    @property
    def full_name(self) -> str:
        """完整模型名称"""
        return f"{self.name}:{self.version}"
    
    @property
    def size_mb(self) -> Optional[float]:
        """模型大小(MB)"""
        if self.model_size:
            return round(self.model_size / (1024 * 1024), 2)
        return None
    
    @property
    def parameters_b(self) -> Optional[float]:
        """参数量(B)"""
        if self.parameters:
            return round(self.parameters / 1_000_000_000, 2)
        return None