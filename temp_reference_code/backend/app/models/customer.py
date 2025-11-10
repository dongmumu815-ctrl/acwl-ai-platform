#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
客户相关数据库模型

定义平台管理和会话管理相关的数据库模型。
包含客户基本信息、认证信息和登录状态管理。

Author: System
Date: 2024
"""

from datetime import datetime, timedelta
from typing import List, Optional
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, ForeignKey, Index
from sqlalchemy.orm import relationship, Session
from sqlalchemy.sql import func
import secrets
import hashlib

from .base import BaseModel
from app.core.config import settings


class Customer(BaseModel):
    """
    客户模型
    
    存储客户的基本信息、认证信息和系统配置
    """
    
    __tablename__ = "customers"
    
    # 基本信息
    name = Column(
        String(100),
        nullable=False,
        comment="客户名称"
    )
    
    email = Column(
        String(100),
        nullable=False,
        unique=True,
        index=True,
        comment="客户邮箱"
    )
    
    phone = Column(
        String(20),
        nullable=True,
        comment="联系电话"
    )
    
    company = Column(
        String(200),
        nullable=True,
        comment="公司名称"
    )
    
    # 认证信息
    app_id = Column(
        String(32),
        nullable=False,
        unique=True,
        index=True,
        comment="应用ID"
    )
    
    app_secret = Column(
        String(64),
        nullable=False,
        comment="应用密钥"
    )
    
    # 外部系统关联
    link_read_id = Column(
        String(50),
        nullable=True,
        index=True,
        comment="链接其他系统的ID"
    )
    
    # 状态管理
    status = Column(
        Boolean,
        nullable=False,
        default=True,
        index=True,
        comment="状态：True-启用，False-禁用"
    )
    
    # 配置信息
    rate_limit = Column(
        Integer,
        nullable=True,
        default=None,
        comment="频率限制（每分钟请求数），None表示使用系统默认值"
    )
    
    max_apis = Column(
        Integer,
        nullable=True,
        default=None,
        comment="最大API数量，None表示使用系统默认值"
    )
    
    # 统计信息
    last_login_at = Column(
        DateTime,
        nullable=True,
        comment="最后登录时间"
    )
    
    last_api_call_at = Column(
        DateTime,
        nullable=True,
        comment="最后API调用时间"
    )
    
    total_api_calls = Column(
        Integer,
        nullable=False,
        default=0,
        comment="总API调用次数"
    )
    
    total_apis = Column(
        Integer,
        nullable=False,
        default=0,
        comment="总API数量"
    )
    
    # 安全信息
    secret_reset_at = Column(
        DateTime,
        nullable=True,
        comment="密钥重置时间"
    )
    
    # 关联关系
    sessions = relationship(
        "CustomerSession",
        back_populates="customer",
        cascade="all, delete-orphan",
        lazy="dynamic"
    )
    
    apis = relationship(
        "CustomApi",
        back_populates="customer",
        cascade="all, delete-orphan",
        lazy="dynamic"
    )
    
    usage_logs = relationship(
        "ApiUsageLog",
        back_populates="customer",
        cascade="all, delete-orphan",
        lazy="dynamic"
    )
    
    data_uploads = relationship(
        "DataUpload",
        back_populates="customer",
        cascade="all, delete-orphan",
        lazy="dynamic"
    )
    
    data_batches = relationship(
        "DataBatch",
        back_populates="customer",
        cascade="all, delete-orphan",
        lazy="dynamic"
    )
    
    # 索引
    __table_args__ = (
        Index('idx_customer_status_created', 'status', 'created_at'),
        Index('idx_customer_company', 'company'),
    )
    
    def __init__(self, **kwargs):
        """
        初始化客户实例
        
        自动生成app_id和app_secret
        """
        if 'app_id' not in kwargs:
            kwargs['app_id'] = self.generate_app_id()
        if 'app_secret' not in kwargs:
            kwargs['app_secret'] = self.generate_app_secret()
        
        super().__init__(**kwargs)
    
    @staticmethod
    def generate_app_id() -> str:
        """
        生成唯一的应用ID
        
        Returns:
            str: 32位的应用ID
        """
        return secrets.token_hex(16)
    
    @staticmethod
    def generate_app_secret() -> str:
        """
        生成应用密钥
        
        Returns:
            str: 64位的应用密钥
        """
        return secrets.token_hex(32)
    
    def verify_app_secret(self, secret: str) -> bool:
        """
        验证应用密钥
        
        Args:
            secret: 待验证的密钥
        
        Returns:
            bool: 验证结果
        """
        return secrets.compare_digest(self.app_secret, secret)
    
    def regenerate_credentials(self) -> tuple:
        """
        重新生成认证凭据
        
        Returns:
            tuple: (新的app_id, 新的app_secret)
        """
        self.app_id = self.generate_app_id()
        self.app_secret = self.generate_app_secret()
        return self.app_id, self.app_secret
    
    def get_effective_rate_limit(self) -> int:
        """
        获取有效的频率限制
        
        Returns:
            int: 频率限制值
        """
        return self.rate_limit or settings.DEFAULT_RATE_LIMIT
    
    def get_effective_max_apis(self) -> int:
        """
        获取有效的最大API数量
        
        Returns:
            int: 最大API数量
        """
        return self.max_apis or settings.MAX_API_PER_CUSTOMER
    
    def is_active(self) -> bool:
        """
        检查客户是否处于活跃状态
        
        Returns:
            bool: 是否活跃
        """
        return self.status
    
    def can_create_api(self, db: Session) -> bool:
        """
        检查是否可以创建新的API
        
        Args:
            db: 数据库会话
        
        Returns:
            bool: 是否可以创建
        """
        if not self.is_active():
            return False
        
        current_api_count = self.apis.count()
        return current_api_count < self.get_effective_max_apis()
    
    def update_last_login(self, db: Session) -> None:
        """
        更新最后登录时间
        
        Args:
            db: 数据库会话
        """
        self.last_login_at = datetime.utcnow()
        db.commit()
    
    def update_api_call_stats(self, db: Session) -> None:
        """
        更新API调用统计
        
        Args:
            db: 数据库会话
        """
        self.last_api_call_at = datetime.utcnow()
        self.total_api_calls += 1
        db.commit()
    
    def get_active_sessions(self, db: Session) -> List['CustomerSession']:
        """
        获取活跃的会话列表
        
        Args:
            db: 数据库会话
        
        Returns:
            List[CustomerSession]: 活跃会话列表
        """
        return self.sessions.filter(
            CustomerSession.is_active == True,
            CustomerSession.expires_at > datetime.utcnow()
        ).all()
    
    def revoke_all_sessions(self, db: Session) -> int:
        """
        撤销所有会话
        
        Args:
            db: 数据库会话
        
        Returns:
            int: 撤销的会话数量
        """
        count = self.sessions.filter(
            CustomerSession.is_active == True
        ).update({CustomerSession.is_active: False})
        db.commit()
        return count
    
    @classmethod
    def get_by_app_id(cls, db: Session, app_id: str) -> Optional['Customer']:
        """
        根据应用ID获取客户
        
        Args:
            db: 数据库会话
            app_id: 应用ID
        
        Returns:
            Optional[Customer]: 客户实例或None
        """
        return db.query(cls).filter(cls.app_id == app_id).first()
    
    @classmethod
    def get_by_email(cls, db: Session, email: str) -> Optional['Customer']:
        """
        根据邮箱获取客户
        
        Args:
            db: 数据库会话
            email: 邮箱地址
        
        Returns:
            Optional[Customer]: 客户实例或None
        """
        return db.query(cls).filter(cls.email == email).first()
    
    @classmethod
    def get_active_customers(cls, db: Session, skip: int = 0, limit: int = 100) -> List['Customer']:
        """
        获取活跃平台列表
        
        Args:
            db: 数据库会话
            skip: 跳过的记录数
            limit: 限制的记录数
        
        Returns:
            List[Customer]: 活跃平台列表
        """
        return db.query(cls).filter(cls.status == True).offset(skip).limit(limit).all()
    
    def to_dict(self, include_sensitive: bool = False, **kwargs) -> dict:
        """
        转换为字典，可选择是否包含敏感信息
        
        Args:
            include_sensitive: 是否包含敏感信息（app_secret）
            **kwargs: 其他参数
        
        Returns:
            dict: 平台信息字典
        """
        exclude = [] if include_sensitive else ['app_secret']
        return super().to_dict(exclude=exclude, **kwargs)


class CustomerSession(BaseModel):
    """
    客户会话模型
    
    管理客户的登录会话状态和令牌
    """
    
    __tablename__ = "customer_sessions"
    
    # 关联客户
    customer_id = Column(
        Integer,
        ForeignKey("customers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="客户ID"
    )
    
    # 会话信息
    session_token = Column(
        String(128),
        nullable=False,
        unique=True,
        index=True,
        comment="会话令牌"
    )
    
    # 登录信息
    login_ip = Column(
        String(45),
        nullable=True,
        comment="登录IP地址"
    )
    
    user_agent = Column(
        Text,
        nullable=True,
        comment="用户代理字符串"
    )
    
    login_time = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        comment="登录时间"
    )
    
    last_activity = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        comment="最后活动时间"
    )
    
    expires_at = Column(
        DateTime,
        nullable=False,
        comment="过期时间"
    )
    
    # 状态管理
    is_active = Column(
        Boolean,
        nullable=False,
        default=True,
        index=True,
        comment="是否活跃"
    )
    
    # 关联关系
    customer = relationship(
        "Customer",
        back_populates="sessions"
    )
    
    # 索引
    __table_args__ = (
        Index('idx_session_customer_active', 'customer_id', 'is_active'),
        Index('idx_session_expires', 'expires_at'),
        Index('idx_session_login_ip', 'login_ip'),
    )
    
    def __init__(self, customer_id: int, login_ip: str = None, 
                 user_agent: str = None, **kwargs):
        """
        初始化会话实例
        
        Args:
            customer_id: 客户ID
            login_ip: 登录IP
            user_agent: 用户代理
            **kwargs: 其他参数
        """
        if 'session_token' not in kwargs:
            kwargs['session_token'] = self.generate_session_token()
        
        if 'expires_at' not in kwargs:
            kwargs['expires_at'] = datetime.utcnow() + timedelta(seconds=settings.SESSION_TIMEOUT)
        
        kwargs.update({
            'customer_id': customer_id,
            'login_ip': login_ip,
            'user_agent': user_agent
        })
        
        super().__init__(**kwargs)
    
    @staticmethod
    def generate_session_token() -> str:
        """
        生成会话令牌
        
        Returns:
            str: 128位的会话令牌
        """
        return secrets.token_hex(64)
    
    def is_valid(self) -> bool:
        """
        检查会话是否有效
        
        Returns:
            bool: 会话是否有效
        """
        return (
            self.is_active and 
            self.expires_at > datetime.utcnow()
        )
    
    def extend_session(self, db: Session, extend_seconds: int = None) -> None:
        """
        延长会话有效期
        
        Args:
            db: 数据库会话
            extend_seconds: 延长的秒数，默认使用配置值
        """
        extend_seconds = extend_seconds or settings.SESSION_TIMEOUT
        self.expires_at = datetime.utcnow() + timedelta(seconds=extend_seconds)
        self.last_activity = datetime.utcnow()
        db.commit()
    
    def revoke(self, db: Session) -> None:
        """
        撤销会话
        
        Args:
            db: 数据库会话
        """
        self.is_active = False
        db.commit()
    
    def update_activity(self, db: Session) -> None:
        """
        更新最后活动时间
        
        Args:
            db: 数据库会话
        """
        self.last_activity = datetime.utcnow()
        db.commit()
    
    @classmethod
    def get_by_token(cls, db: Session, token: str) -> Optional['CustomerSession']:
        """
        根据令牌获取会话
        
        Args:
            db: 数据库会话
            token: 会话令牌
        
        Returns:
            Optional[CustomerSession]: 会话实例或None
        """
        return db.query(cls).filter(cls.session_token == token).first()
    
    @classmethod
    def get_valid_session(cls, db: Session, token: str) -> Optional['CustomerSession']:
        """
        获取有效的会话
        
        Args:
            db: 数据库会话
            token: 会话令牌
        
        Returns:
            Optional[CustomerSession]: 有效的会话实例或None
        """
        session = cls.get_by_token(db, token)
        if session and session.is_valid():
            return session
        return None
    
    @classmethod
    def cleanup_expired_sessions(cls, db: Session) -> int:
        """
        清理过期的会话
        
        Args:
            db: 数据库会话
        
        Returns:
            int: 清理的会话数量
        """
        count = db.query(cls).filter(
            cls.expires_at < datetime.utcnow()
        ).update({cls.is_active: False})
        db.commit()
        return count
    
    @classmethod
    def get_active_sessions_count(cls, db: Session, customer_id: int = None) -> int:
        """
        获取活跃会话数量
        
        Args:
            db: 数据库会话
            customer_id: 客户ID，如果指定则只统计该客户的会话
        
        Returns:
            int: 活跃会话数量
        """
        query = db.query(cls).filter(
            cls.is_active == True,
            cls.expires_at > datetime.utcnow()
        )
        
        if customer_id:
            query = query.filter(cls.customer_id == customer_id)
        
        return query.count()


if __name__ == "__main__":
    # 测试模型功能
    print("客户模型定义完成")
    print(f"Customer表名: {Customer.__tablename__}")
    print(f"CustomerSession表名: {CustomerSession.__tablename__}")
    
    # 测试生成功能
    app_id = Customer.generate_app_id()
    app_secret = Customer.generate_app_secret()
    session_token = CustomerSession.generate_session_token()
    
    print(f"生成的app_id长度: {len(app_id)}")
    print(f"生成的app_secret长度: {len(app_secret)}")
    print(f"生成的session_token长度: {len(session_token)}")