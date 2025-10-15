#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志相关数据库模型

定义API使用日志和数据上传记录的数据库模型。
用于记录系统的使用情况和数据处理状态。

Author: System
Date: 2024
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy import Column, String, Integer, Boolean, Text, ForeignKey, Index, Enum, Numeric, DateTime, BigInteger
from sqlalchemy.orm import relationship, Session
from sqlalchemy.dialects.mysql import JSON, LONGTEXT
from sqlalchemy import func
import json

from .base import BaseModel


class ApiUsageLog(BaseModel):
    """
    API使用日志模型
    
    记录每次API调用的详细信息，用于统计分析和问题排查
    """
    
    __tablename__ = "api_usage_logs"
    
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
        nullable=False,
        index=True,
        comment="API ID"
    )
    
    # 请求信息
    request_id = Column(
        String(64),
        nullable=False,
        unique=True,
        index=True,
        comment="请求唯一标识"
    )
    
    http_method = Column(
        String(10),
        nullable=False,
        comment="HTTP方法"
    )
    
    request_url = Column(
        String(500),
        nullable=False,
        comment="请求URL"
    )
    
    request_headers = Column(
        JSON,
        nullable=True,
        comment="请求头信息（JSON格式）"
    )
    
    request_params = Column(
        JSON,
        nullable=True,
        comment="请求参数（JSON格式）"
    )
    
    # 客户端信息
    client_ip = Column(
        String(45),
        nullable=True,
        index=True,
        comment="客户端IP地址"
    )
    
    user_agent = Column(
        String(500),
        nullable=True,
        comment="用户代理字符串"
    )
    
    # 响应信息
    response_status = Column(
        Integer,
        nullable=False,
        index=True,
        comment="HTTP响应状态码"
    )
    
    response_headers = Column(
        JSON,
        nullable=True,
        comment="响应头信息（JSON格式）"
    )
    
    # 性能信息
    processing_time = Column(
        Numeric(10, 6),
        nullable=True,
        comment="处理时间（秒）"
    )
    
    # 错误信息
    error_message = Column(
        Text,
        nullable=True,
        comment="错误信息"
    )
    
    error_traceback = Column(
        LONGTEXT,
        nullable=True,
        comment="错误堆栈信息"
    )
    
    # 业务信息
    data_size = Column(
        Integer,
        nullable=True,
        comment="数据大小（字节）"
    )
    
    record_count = Column(
        Integer,
        nullable=True,
        comment="处理记录数"
    )
    
    batch_id = Column(
        String(64),
        nullable=True,
        index=True,
        comment="批次标识（用于批量上传）"
    )
    
    # 文件存储路径
    file_path = Column(
        String(500),
        nullable=True,
        comment="文件存储路径"
    )
    
    # 加密相关字段
    timestamp = Column(
        BigInteger,
        nullable=True,
        comment="请求时间戳（用于防重放攻击）"
    )
    
    nonce = Column(
        String(32),
        nullable=True,
        comment="随机字符串（用于增强请求唯一性）"
    )
    
    encrypted_data = Column(
        LONGTEXT,
        nullable=True,
        comment="加密后的业务数据（Base64编码）"
    )
    
    iv = Column(
        String(64),
        nullable=True,
        comment="初始化向量（IV），用于AES解密"
    )
    
    signature = Column(
        String(128),
        nullable=True,
        comment="数据签名值（HMAC-SHA256）"
    )
    
    needread = Column(
        Boolean,
        nullable=True,
        default=False,
        comment="是否需要读取确认"
    )
    
    is_encrypted = Column(
        Boolean,
        nullable=True,
        default=False,
        comment="是否为加密请求"
    )
    
    # 关联关系
    customer = relationship(
        "Customer",
        back_populates="usage_logs"
    )
    
    api = relationship(
        "CustomApi",
        back_populates="usage_logs"
    )
    
    # 索引和约束
    __table_args__ = (
        Index('idx_log_customer_created', 'customer_id', 'created_at'),
        Index('idx_log_api_created', 'api_id', 'created_at'),
        Index('idx_log_status_created', 'response_status', 'created_at'),
        Index('idx_log_ip_created', 'client_ip', 'created_at'),
        Index('idx_log_processing_time', 'processing_time'),
        Index('idx_log_batch', 'batch_id'),
        Index('idx_log_batch_created', 'batch_id', 'created_at'),
        Index('idx_log_encrypted', 'is_encrypted'),
        Index('idx_log_timestamp', 'timestamp'),
        Index('idx_log_nonce', 'nonce'),
    )
    
    @property
    def is_success(self) -> bool:
        """
        判断请求是否成功
        
        Returns:
            bool: 是否成功（状态码200-299）
        """
        return 200 <= self.response_status < 300
    
    @property
    def is_error(self) -> bool:
        """
        判断请求是否出错
        
        Returns:
            bool: 是否出错（状态码400+）
        """
        return self.response_status >= 400
    
    @classmethod
    def create_log(cls, db: Session, **kwargs) -> 'ApiUsageLog':
        """
        创建使用日志记录
        
        Args:
            db: 数据库会话
            **kwargs: 日志数据
        
        Returns:
            ApiUsageLog: 创建的日志记录
        """
        log = cls(**kwargs)
        db.add(log)
        db.commit()
        db.refresh(log)
        return log
    
    @classmethod
    def get_usage_stats(cls, db: Session, customer_id: int = None, 
                       api_id: int = None, days: int = 30) -> Dict[str, Any]:
        """
        获取使用统计信息
        
        Args:
            db: 数据库会话
            customer_id: 客户ID
            api_id: API ID
            days: 统计天数
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        start_date = datetime.utcnow() - timedelta(days=days)
        
        query = db.query(cls).filter(cls.created_at >= start_date)
        
        if customer_id:
            query = query.filter(cls.customer_id == customer_id)
        
        if api_id:
            query = query.filter(cls.api_id == api_id)
        
        logs = query.all()
        
        total_calls = len(logs)
        success_calls = sum(1 for log in logs if log.is_success)
        error_calls = sum(1 for log in logs if log.is_error)
        
        avg_processing_time = 0
        if logs:
            processing_times = [log.processing_time for log in logs if log.processing_time]
            if processing_times:
                avg_processing_time = sum(processing_times) / len(processing_times)
        
        return {
            'total_calls': total_calls,
            'success_calls': success_calls,
            'error_calls': error_calls,
            'success_rate': success_calls / total_calls if total_calls > 0 else 0,
            'avg_processing_time': float(avg_processing_time),
            'period_days': days
        }
    
    @classmethod
    def get_error_logs(cls, db: Session, customer_id: int = None, 
                      api_id: int = None, limit: int = 100) -> List['ApiUsageLog']:
        """
        获取错误日志
        
        Args:
            db: 数据库会话
            customer_id: 客户ID
            api_id: API ID
            limit: 限制数量
        
        Returns:
            List[ApiUsageLog]: 错误日志列表
        """
        query = db.query(cls).filter(cls.response_status >= 400)
        
        if customer_id:
            query = query.filter(cls.customer_id == customer_id)
        
        if api_id:
            query = query.filter(cls.api_id == api_id)
        
        return query.order_by(cls.created_at.desc()).limit(limit).all()
    
    def to_dict(self, include_sensitive: bool = False, **kwargs) -> dict:
        """
        转换为字典
        
        Args:
            include_sensitive: 是否包含敏感信息
            **kwargs: 其他参数
        
        Returns:
            dict: 日志信息字典
        """
        result = super().to_dict(**kwargs)
        
        # 添加计算属性
        result['is_success'] = self.is_success
        result['is_error'] = self.is_error
        
        # 处理敏感信息
        if not include_sensitive:
            # 移除敏感的请求和响应数据
            result.pop('request_headers', None)
            result.pop('request_body', None)
            result.pop('response_headers', None)
            result.pop('error_traceback', None)
        
        return result


class DataUpload(BaseModel):
    """
    数据上传记录模型
    
    记录通过API上传的数据信息和处理状态
    """
    
    __tablename__ = "data_uploads"
    
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
        nullable=False,
        index=True,
        comment="API ID"
    )
    
    usage_log_id = Column(
        Integer,
        ForeignKey("api_usage_logs.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="关联的使用日志ID"
    )
    
    # 上传信息
    upload_id = Column(
        String(64),
        nullable=False,
        unique=True,
        index=True,
        comment="上传唯一标识"
    )
    
    batch_id = Column(
        String(64),
        nullable=True,
        index=True,
        comment="批次标识（用于批量上传）"
    )
    
    # 文件存储路径
    file_path = Column(
        String(500),
        nullable=True,
        comment="文件存储路径"
    )
    
    # 数据信息
    original_filename = Column(
        String(255),
        nullable=True,
        comment="原始文件名"
    )
    
    file_path = Column(
        String(500),
        nullable=True,
        comment="文件存储路径"
    )
    
    file_size = Column(
        Integer,
        nullable=True,
        comment="文件大小（字节）"
    )
    
    file_type = Column(
        String(50),
        nullable=True,
        comment="文件类型"
    )
    
    # 数据内容
    data_content = Column(
        LONGTEXT,
        nullable=True,
        comment="数据内容（JSON格式）"
    )
    
    # 处理状态
    status = Column(
        Enum('pending', 'processing', 'completed', 'failed', name='upload_status_enum'),
        nullable=False,
        default='pending',
        index=True,
        comment="处理状态"
    )
    
    # 处理信息
    processed_at = Column(
        DateTime,
        nullable=True,
        comment="处理完成时间"
    )
    
    processing_time = Column(
        Numeric(10, 6),
        nullable=True,
        comment="处理耗时（秒）"
    )
    
    record_count = Column(
        Integer,
        nullable=True,
        comment="记录数量"
    )
    
    # 验证结果
    validation_errors = Column(
        JSON,
        nullable=True,
        comment="验证错误信息（JSON数组）"
    )
    
    # 错误信息
    error_message = Column(
        Text,
        nullable=True,
        comment="错误信息"
    )
    
    # 元数据
    meta_data = Column(
        JSON,
        nullable=True,
        comment="额外的元数据信息"
    )
    
    # 关联关系
    customer = relationship(
        "Customer",
        back_populates="data_uploads"
    )
    
    api = relationship(
        "CustomApi",
        back_populates="data_uploads"
    )
    
    # 注意：batch_id字段不设置外键约束，只作为标识字段使用
    # 这样可以避免在批次不存在时的外键约束错误
    # batch = relationship(
    #     "DataBatch",
    #     back_populates="data_uploads",
    #     primaryjoin="DataUpload.batch_id == DataBatch.batch_id",
    #     foreign_keys="DataUpload.batch_id"
    # )
    
    # 索引和约束
    __table_args__ = (
        Index('idx_upload_customer_created', 'customer_id', 'created_at'),
        Index('idx_upload_api_created', 'api_id', 'created_at'),
        Index('idx_upload_status_created', 'status', 'created_at'),
        Index('idx_upload_batch', 'batch_id'),
    )
    
    @property
    def is_completed(self) -> bool:
        """
        判断是否处理完成
        
        Returns:
            bool: 是否完成
        """
        return self.status == 'completed'
    
    @property
    def is_failed(self) -> bool:
        """
        判断是否处理失败
        
        Returns:
            bool: 是否失败
        """
        return self.status == 'failed'
    
    @property
    def has_validation_errors(self) -> bool:
        """
        判断是否有验证错误
        
        Returns:
            bool: 是否有验证错误
        """
        return bool(self.validation_errors)
    
    def set_processing(self, db: Session) -> None:
        """
        设置为处理中状态
        
        Args:
            db: 数据库会话
        """
        self.status = 'processing'
        db.commit()
    
    def set_completed(self, db: Session, record_count: int = None, 
                     processing_time: float = None) -> None:
        """
        设置为完成状态
        
        Args:
            db: 数据库会话
            record_count: 处理记录数
            processing_time: 处理时间
        """
        self.status = 'completed'
        self.processed_at = datetime.utcnow()
        
        if record_count is not None:
            self.record_count = record_count
        
        if processing_time is not None:
            self.processing_time = processing_time
        
        db.commit()
    
    def set_failed(self, db: Session, error_message: str, 
                  validation_errors: List[str] = None) -> None:
        """
        设置为失败状态
        
        Args:
            db: 数据库会话
            error_message: 错误信息
            validation_errors: 验证错误列表
        """
        self.status = 'failed'
        self.processed_at = datetime.utcnow()
        self.error_message = error_message
        
        if validation_errors:
            self.validation_errors = validation_errors
        
        db.commit()
    
    @classmethod
    def create_upload_record(cls, db: Session, **kwargs) -> 'DataUpload':
        """
        创建上传记录
        
        Args:
            db: 数据库会话
            **kwargs: 上传数据
        
        Returns:
            DataUpload: 创建的上传记录
        """
        upload = cls(**kwargs)
        db.add(upload)
        db.commit()
        db.refresh(upload)
        return upload
    
    @classmethod
    def get_by_upload_id(cls, db: Session, upload_id: str) -> Optional['DataUpload']:
        """
        根据上传ID获取记录
        
        Args:
            db: 数据库会话
            upload_id: 上传ID
        
        Returns:
            Optional[DataUpload]: 上传记录或None
        """
        return db.query(cls).filter(cls.upload_id == upload_id).first()
    
    @classmethod
    def get_batch_uploads(cls, db: Session, batch_id: str) -> List['DataUpload']:
        """
        获取批次上传记录
        
        Args:
            db: 数据库会话
            batch_id: 批次ID
        
        Returns:
            List[DataUpload]: 批次上传记录列表
        """
        return db.query(cls).filter(cls.batch_id == batch_id).all()
    
    @classmethod
    def get_pending_uploads(cls, db: Session, limit: int = 100) -> List['DataUpload']:
        """
        获取待处理的上传记录
        
        Args:
            db: 数据库会话
            limit: 限制数量
        
        Returns:
            List[DataUpload]: 待处理上传记录列表
        """
        return db.query(cls).filter(
            cls.status == 'pending'
        ).order_by(cls.created_at).limit(limit).all()
    
    @classmethod
    def get_upload_stats(cls, db: Session, customer_id: int = None, 
                        api_id: int = None, days: int = 30) -> Dict[str, Any]:
        """
        获取上传统计信息
        
        Args:
            db: 数据库会话
            customer_id: 客户ID
            api_id: API ID
            days: 统计天数
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        start_date = datetime.utcnow() - timedelta(days=days)
        
        query = db.query(cls).filter(cls.created_at >= start_date)
        
        if customer_id:
            query = query.filter(cls.customer_id == customer_id)
        
        if api_id:
            query = query.filter(cls.api_id == api_id)
        
        uploads = query.all()
        
        total_uploads = len(uploads)
        completed_uploads = sum(1 for upload in uploads if upload.is_completed)
        failed_uploads = sum(1 for upload in uploads if upload.is_failed)
        
        total_records = sum(upload.record_count or 0 for upload in uploads)
        total_size = sum(upload.file_size or 0 for upload in uploads)
        
        return {
            'total_uploads': total_uploads,
            'completed_uploads': completed_uploads,
            'failed_uploads': failed_uploads,
            'success_rate': completed_uploads / total_uploads if total_uploads > 0 else 0,
            'total_records': total_records,
            'total_size': total_size,
            'period_days': days
        }
    
    def to_dict(self, include_content: bool = False, **kwargs) -> dict:
        """
        转换为字典
        
        Args:
            include_content: 是否包含数据内容
            **kwargs: 其他参数
        
        Returns:
            dict: 上传记录字典
        """
        result = super().to_dict(**kwargs)
        
        # 添加计算属性
        result['is_completed'] = self.is_completed
        result['is_failed'] = self.is_failed
        result['has_validation_errors'] = self.has_validation_errors
        
        # 处理数据内容
        if not include_content:
            result.pop('data_content', None)
        
        return result


if __name__ == "__main__":
    # 测试模型功能
    print("日志模型定义完成")
    print(f"ApiUsageLog表名: {ApiUsageLog.__tablename__}")
    print(f"DataUpload表名: {DataUpload.__tablename__}")
    
    print("\n日志模型测试完成")