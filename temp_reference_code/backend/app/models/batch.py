#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批次管理数据库模型

定义数据批次管理相关的数据库模型。
用于管理数据上传的批次信息和状态跟踪。

Author: System
Date: 2024
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy import Column, String, Integer, Boolean, Text, ForeignKey, Index, Enum, Numeric, DateTime, case
from sqlalchemy.orm import relationship, Session, foreign
from sqlalchemy.dialects.mysql import JSON
from sqlalchemy import func
import json
import uuid

from .base import BaseModel


class DataBatch(BaseModel):
    """
    数据批次模型
    
    管理数据上传的批次信息
    """
    
    __tablename__ = "data_batches"
    
    # 关联信息
    customer_id = Column(
        Integer,
        ForeignKey("customers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="客户ID"
    )
    
    api_id = Column(
        Integer,
        ForeignKey("custom_apis.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
        comment="关联的API ID"
    )
    
    # 批次信息
    batch_id = Column(
        String(64),
        nullable=False,
        unique=True,
        index=True,
        comment="批次唯一标识"
    )
    
    batch_name = Column(
        String(100),
        nullable=True,
        comment="批次名称"
    )
    
    description = Column(
        Text,
        nullable=True,
        comment="批次描述"
    )
    
    # 状态信息 (pending:待处理, processing:处理中, completed:已完成, failed:失败, cancelled:已取消)
    status = Column(
        Enum('pending', 'processing', 'completed', 'failed', 'cancelled', name='batch_status'),
        nullable=False,
        default='pending',
        index=True,
        comment="批次状态：pending-待处理，processing-处理中，completed-已完成，failed-失败，cancelled-已取消"
    )
    
    # 数据统计
    expected_count = Column(
        Integer,
        nullable=True,
        comment="预期数据条数"
    )
    
    total_count = Column(
        Integer,
        nullable=False,
        default=0,
        comment="总数据条数"
    )
    
    pending_count = Column(
        Integer,
        nullable=False,
        default=0,
        comment="待处理数据条数"
    )
    
    processing_count = Column(
        Integer,
        nullable=False,
        default=0,
        comment="处理中数据条数"
    )
    
    completed_count = Column(
        Integer,
        nullable=False,
        default=0,
        comment="已完成数据条数"
    )
    
    failed_count = Column(
        Integer,
        nullable=False,
        default=0,
        comment="失败数据条数"
    )
    
    # 处理信息
    started_at = Column(
        "processing_started_at",
        DateTime,
        nullable=True,
        comment="开始处理时间"
    )
    
    completed_at = Column(
        "processing_completed_at",
        DateTime,
        nullable=True,
        comment="完成处理时间"
    )
    
    processing_time = Column(
        "processing_duration",
        Integer,
        nullable=True,
        comment="总处理耗时（秒）"
    )
    
    # 错误信息
    error_message = Column(
        Text,
        nullable=True,
        comment="错误信息"
    )
    
    # 是否需要回调
    needread = Column(
        Boolean,
        nullable=True,
        default=True,
        comment="是否需要回调通知"
    )
    
    # 额外的元数据信息
    meta_data = Column(
        "metadata",
        JSON,
        nullable=True,
        comment="额外的元数据信息"
    )
    
    # 关联关系
    customer = relationship(
        "Customer",
        back_populates="data_batches"
    )
    
    api = relationship(
        "CustomApi",
        back_populates="data_batches"
    )
    
    # 注意：由于DataUpload模型中移除了batch关系，这里也相应注释掉
    # 避免外键约束问题，batch_id只作为标识字段使用
    # data_uploads = relationship(
    #     "DataUpload",
    #     back_populates="batch",
    #     cascade="all, delete-orphan",
    #     primaryjoin="DataBatch.batch_id == foreign(DataUpload.batch_id)"
    # )
    
    # 索引和约束
    __table_args__ = (
        Index('idx_batch_customer_created', 'customer_id', 'created_at'),
        Index('idx_batch_api_created', 'api_id', 'created_at'),
        Index('idx_batch_status_created', 'status', 'created_at'),
    )
    
    @property
    def is_completed(self) -> bool:
        """
        判断批次是否处理完成
        
        Returns:
            bool: 是否完成
        """
        return self.status == 'completed'
    
    @property
    def is_failed(self) -> bool:
        """
        判断批次是否处理失败
        
        Returns:
            bool: 是否失败
        """
        return self.status == 'failed'
    
    @property
    def is_processing(self) -> bool:
        """
        判断批次是否正在处理
        
        Returns:
            bool: 是否正在处理
        """
        return self.status == 'processing'
    
    @property
    def progress_percentage(self) -> float:
        """
        获取处理进度百分比
        
        Returns:
            float: 进度百分比（0-100）
        """
        if self.total_count == 0:
            return 0.0
        
        return (self.completed_count / self.total_count) * 100
    
    @property
    def success_rate(self) -> float:
        """
        获取成功率
        
        Returns:
            float: 成功率（0-1）
        """
        processed_count = self.completed_count + self.failed_count
        if processed_count == 0:
            return 0.0
        
        return self.completed_count / processed_count
    
    def update_counts(self, db: Session) -> None:
        """
        更新批次统计信息
        
        Args:
            db: 数据库会话
        """
        from .log import DataUpload
        
        # 查询批次下的数据统计
        stats = db.query(
            func.count(DataUpload.id).label('total'),
            func.sum(case((DataUpload.status == 'pending', 1), else_=0)).label('pending'),
            func.sum(case((DataUpload.status == 'processing', 1), else_=0)).label('processing'),
            func.sum(case((DataUpload.status == 'completed', 1), else_=0)).label('completed'),
            func.sum(case((DataUpload.status == 'failed', 1), else_=0)).label('failed')
        ).filter(
            DataUpload.batch_id == self.batch_id
        ).first()
        
        if stats:
            self.total_count = stats.total or 0
            self.pending_count = stats.pending or 0
            self.processing_count = stats.processing or 0
            self.completed_count = stats.completed or 0
            self.failed_count = stats.failed or 0
            
            # 更新批次状态 (保持现有状态，不自动更改)
            # 注意：批次状态现在由业务逻辑手动控制，不再根据数据统计自动更新
            # 注意：不在这里提交事务，由调用方决定何时提交
            pass
    
    def set_processing(self, db: Session, status: int = 1) -> None:
        """
        设置批次为处理中状态
        
        Args:
            db: 数据库会话
            status: 处理状态 (1-已检查完成, 2-已入库, 3-已生成审核批次, 4-审核中)
        """
        self.status = status
        if not self.started_at:
            self.started_at = datetime.utcnow()
        db.commit()
    
    def set_completed(self, db: Session, processing_time: float = None) -> None:
        """
        设置批次为完成状态 (状态5-已完成审核)
        
        Args:
            db: 数据库会话
            processing_time: 处理时间
        """
        self.status = 5  # 已完成审核
        self.completed_at = datetime.utcnow()
        
        if processing_time is not None:
            self.processing_time = processing_time
        elif self.started_at:
            self.processing_time = (datetime.utcnow() - self.started_at).total_seconds()
        
        db.commit()
    
    def set_failed(self, db: Session, error_message: str) -> None:
        """
        设置批次为失败状态 (负数状态)
        
        Args:
            db: 数据库会话
            error_message: 错误信息
        """
        self.status = -1  # 失败状态
        self.error_message = error_message
        self.completed_at = datetime.utcnow()
        
        if self.started_at:
            self.processing_time = (datetime.utcnow() - self.started_at).total_seconds()
        
        db.commit()
    
    def cancel(self, db: Session) -> None:
        """
        取消批次处理 (状态-2)
        
        Args:
            db: 数据库会话
        """
        self.status = -2  # 取消状态
        self.completed_at = datetime.utcnow()
        
        if self.started_at:
            self.processing_time = (datetime.utcnow() - self.started_at).total_seconds()
        
        db.commit()
    
    @classmethod
    def create_batch(cls, db: Session, **kwargs) -> 'DataBatch':
        """
        创建新批次
        
        Args:
            db: 数据库会话
            **kwargs: 批次数据
        
        Returns:
            DataBatch: 创建的批次记录
        """
        # 生成批次ID（如果未提供）
        if 'batch_id' not in kwargs:
            kwargs['batch_id'] = str(uuid.uuid4())
        
        # 生成批次名称（如果未提供）
        if 'batch_name' not in kwargs or not kwargs['batch_name']:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            kwargs['batch_name'] = f"batch_{timestamp}"
        
        batch = cls(**kwargs)
        db.add(batch)
        db.commit()
        db.refresh(batch)
        return batch
    
    @classmethod
    def get_by_batch_id(cls, db: Session, batch_id: str) -> Optional['DataBatch']:
        """
        根据批次ID获取记录
        
        Args:
            db: 数据库会话
            batch_id: 批次ID
        
        Returns:
            Optional[DataBatch]: 批次记录或None
        """
        return db.query(cls).filter(cls.batch_id == batch_id).first()
    
    @classmethod
    def get_customer_batches(cls, db: Session, customer_id: int, 
                           status: str = None, limit: int = 100) -> List['DataBatch']:
        """
        获取客户的批次列表
        
        Args:
            db: 数据库会话
            customer_id: 客户ID
            status: 状态过滤
            limit: 限制数量
        
        Returns:
            List[DataBatch]: 批次列表
        """
        query = db.query(cls).filter(cls.customer_id == customer_id)
        
        if status:
            query = query.filter(cls.status == status)
        
        return query.order_by(cls.created_at.desc()).limit(limit).all()
    
    @classmethod
    def get_processing_batches(cls, db: Session, limit: int = 100) -> List['DataBatch']:
        """
        获取正在处理的批次列表
        
        Args:
            db: 数据库会话
            limit: 限制数量
        
        Returns:
            List[DataBatch]: 正在处理的批次列表
        """
        return db.query(cls).filter(
            cls.status.in_([1, 2, 3, 4])  # 处理中的各个阶段
        ).order_by(cls.started_at).limit(limit).all()
    
    @classmethod
    def get_batch_stats(cls, db: Session, customer_id: int = None, 
                       days: int = 30) -> Dict[str, Any]:
        """
        获取批次统计信息
        
        Args:
            db: 数据库会话
            customer_id: 客户ID
            days: 统计天数
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        start_date = datetime.utcnow() - timedelta(days=days)
        
        query = db.query(cls).filter(cls.created_at >= start_date)
        
        if customer_id:
            query = query.filter(cls.customer_id == customer_id)
        
        batches = query.all()
        
        total_batches = len(batches)
        completed_batches = sum(1 for batch in batches if batch.is_completed)
        failed_batches = sum(1 for batch in batches if batch.is_failed)
        processing_batches = sum(1 for batch in batches if batch.is_processing)
        
        total_records = sum(batch.total_count for batch in batches)
        completed_records = sum(batch.completed_count for batch in batches)
        
        return {
            'total_batches': total_batches,
            'completed_batches': completed_batches,
            'failed_batches': failed_batches,
            'processing_batches': processing_batches,
            'success_rate': completed_batches / total_batches if total_batches > 0 else 0,
            'total_records': total_records,
            'completed_records': completed_records,
            'record_success_rate': completed_records / total_records if total_records > 0 else 0,
            'period_days': days
        }
    
    def to_dict(self, **kwargs) -> dict:
        """
        转换为字典
        
        Args:
            **kwargs: 其他参数
        
        Returns:
            dict: 批次记录字典
        """
        result = super().to_dict(**kwargs)
        
        # 添加计算属性
        result['is_completed'] = self.is_completed
        result['is_failed'] = self.is_failed
        result['is_processing'] = self.is_processing
        result['progress_percentage'] = self.progress_percentage
        result['success_rate'] = self.success_rate
        
        return result


if __name__ == "__main__":
    # 测试模型功能
    print("批次管理模型定义完成")
    print(f"DataBatch表名: {DataBatch.__tablename__}")
    
    print("\n批次管理模型测试完成")