#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
管理员和系统配置相关数据库模型

定义系统管理员和系统配置的数据库模型。
用于系统管理和配置维护。

Author: System
Date: 2024
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy import Column, String, Integer, Boolean, Text, Index, Enum, DateTime
from sqlalchemy.orm import Session
from sqlalchemy.dialects.mysql import JSON
from passlib.context import CryptContext
import secrets
import json

from .base import BaseModel

# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AdminUser(BaseModel):
    """
    系统管理员模型
    
    管理系统管理员的账户信息和权限
    """
    
    __tablename__ = "admin_users"
    
    # 基本信息
    username = Column(
        String(50),
        nullable=False,
        unique=True,
        index=True,
        comment="用户名"
    )
    
    email = Column(
        String(100),
        nullable=False,
        unique=True,
        index=True,
        comment="邮箱地址"
    )
    
    real_name = Column(
        String(100),
        nullable=True,
        comment="真实姓名"
    )
    
    # 认证信息
    password_hash = Column(
        String(255),
        nullable=False,
        comment="密码哈希"
    )
    
    # 状态管理
    is_active = Column(
        Boolean,
        nullable=False,
        default=True,
        index=True,
        comment="是否激活"
    )
    
    is_superuser = Column(
        Boolean,
        nullable=False,
        default=False,
        comment="是否超级管理员"
    )
    
    # 权限管理
    permissions = Column(
        JSON,
        nullable=True,
        comment="权限列表（JSON数组）"
    )
    
    # 登录信息
    last_login_at = Column(
        DateTime,
        nullable=True,
        comment="最后登录时间"
    )
    
    last_login_ip = Column(
        String(45),
        nullable=True,
        comment="最后登录IP"
    )
    
    login_count = Column(
        Integer,
        nullable=False,
        default=0,
        comment="登录次数"
    )
    
    # 安全信息
    failed_login_count = Column(
        Integer,
        nullable=False,
        default=0,
        comment="失败登录次数"
    )
    
    locked_until = Column(
        DateTime,
        nullable=True,
        comment="锁定到期时间"
    )
    
    # 密码管理
    password_changed_at = Column(
        DateTime,
        nullable=True,
        comment="密码修改时间"
    )
    
    must_change_password = Column(
        Boolean,
        nullable=False,
        default=False,
        comment="是否必须修改密码"
    )
    
    # 索引和约束
    __table_args__ = (
        Index('idx_admin_username', 'username'),
        Index('idx_admin_email', 'email'),
        Index('idx_admin_active', 'is_active'),
        Index('idx_admin_last_login', 'last_login_at'),
    )
    
    def __init__(self, **kwargs):
        """
        初始化管理员用户
        
        自动处理密码哈希
        """
        if 'password' in kwargs:
            password = kwargs.pop('password')
            kwargs['password_hash'] = self.hash_password(password)
            kwargs['password_changed_at'] = datetime.utcnow()
        
        super().__init__(**kwargs)
    
    @staticmethod
    def hash_password(password: str) -> str:
        """
        哈希密码
        
        Args:
            password: 明文密码
        
        Returns:
            str: 密码哈希
        """
        return pwd_context.hash(password)
    
    def verify_password(self, password: str) -> bool:
        """
        验证密码
        
        Args:
            password: 明文密码
        
        Returns:
            bool: 是否匹配
        """
        return pwd_context.verify(password, self.password_hash)
    
    def set_password(self, password: str, db: Session) -> None:
        """
        设置新密码
        
        Args:
            password: 新密码
            db: 数据库会话
        """
        self.password_hash = self.hash_password(password)
        self.password_changed_at = datetime.utcnow()
        self.must_change_password = False
        db.commit()
    
    def is_locked(self) -> bool:
        """
        检查账户是否被锁定
        
        Returns:
            bool: 是否被锁定
        """
        if not self.locked_until:
            return False
        return datetime.utcnow() < self.locked_until
    
    @property
    def role(self) -> str:
        """
        获取管理员角色
        
        Returns:
            str: 角色名称
        """
        if self.is_superuser:
            return "super_admin"
        return "admin"
    
    @property
    def status(self) -> str:
        """
        获取账户状态
        
        Returns:
            str: 状态名称
        """
        if not self.is_active:
            return "inactive"
        elif self.is_locked():
            return "locked"
        else:
            return "active"
    
    def lock_account(self, db: Session, minutes: int = 30) -> None:
        """
        锁定账户
        
        Args:
            db: 数据库会话
            minutes: 锁定时长（分钟）
        """
        self.locked_until = datetime.utcnow() + timedelta(minutes=minutes)
        db.commit()
    
    def unlock_account(self, db: Session) -> None:
        """
        解锁账户
        
        Args:
            db: 数据库会话
        """
        self.locked_until = None
        self.failed_login_count = 0
        db.commit()
    
    def record_login_success(self, db: Session, ip_address: str = None) -> None:
        """
        记录登录成功
        
        Args:
            db: 数据库会话
            ip_address: IP地址
        """
        self.last_login_at = datetime.utcnow()
        self.last_login_ip = ip_address
        self.login_count += 1
        self.failed_login_count = 0
        db.commit()
    
    def record_login_failure(self, db: Session) -> None:
        """
        记录登录失败
        
        Args:
            db: 数据库会话
        """
        self.failed_login_count += 1
        
        # 失败次数过多时锁定账户
        if self.failed_login_count >= 5:
            self.lock_account(db, minutes=30)
        else:
            db.commit()
    
    def has_permission(self, permission: str) -> bool:
        """
        检查是否有指定权限
        
        Args:
            permission: 权限名称
        
        Returns:
            bool: 是否有权限
        """
        if self.is_superuser:
            return True
        
        if not self.permissions:
            return False
        
        return permission in self.permissions
    
    def add_permission(self, permission: str, db: Session) -> None:
        """
        添加权限
        
        Args:
            permission: 权限名称
            db: 数据库会话
        """
        if not self.permissions:
            self.permissions = []
        
        if permission not in self.permissions:
            self.permissions.append(permission)
            db.commit()
    
    def remove_permission(self, permission: str, db: Session) -> None:
        """
        移除权限
        
        Args:
            permission: 权限名称
            db: 数据库会话
        """
        if self.permissions and permission in self.permissions:
            self.permissions.remove(permission)
            db.commit()
    
    @classmethod
    def get_by_username(cls, db: Session, username: str) -> Optional['AdminUser']:
        """
        根据用户名获取管理员
        
        Args:
            db: 数据库会话
            username: 用户名
        
        Returns:
            Optional[AdminUser]: 管理员或None
        """
        return db.query(cls).filter(cls.username == username).first()
    
    @classmethod
    def get_by_email(cls, db: Session, email: str) -> Optional['AdminUser']:
        """
        根据邮箱获取管理员
        
        Args:
            db: 数据库会话
            email: 邮箱地址
        
        Returns:
            Optional[AdminUser]: 管理员或None
        """
        return db.query(cls).filter(cls.email == email).first()
    
    @classmethod
    def get_active_admins(cls, db: Session) -> List['AdminUser']:
        """
        获取活跃的管理员列表
        
        Args:
            db: 数据库会话
        
        Returns:
            List[AdminUser]: 活跃管理员列表
        """
        return db.query(cls).filter(cls.is_active == True).all()
    
    def to_dict(self, include_sensitive: bool = False, **kwargs) -> dict:
        """
        转换为字典
        
        Args:
            include_sensitive: 是否包含敏感信息
            **kwargs: 其他参数
        
        Returns:
            dict: 管理员信息字典
        """
        result = super().to_dict(**kwargs)
        
        # 移除敏感信息
        if not include_sensitive:
            result.pop('password_hash', None)
        
        # 添加计算属性
        result['is_locked'] = self.is_locked()
        
        return result


class SystemConfig(BaseModel):
    """
    系统配置模型
    
    存储系统的各种配置参数
    """
    
    __tablename__ = "system_configs"
    
    # 配置信息
    config_key = Column(
        String(100),
        nullable=False,
        unique=True,
        index=True,
        comment="配置键名"
    )
    
    config_value = Column(
        Text,
        nullable=True,
        comment="配置值"
    )
    
    config_type = Column(
        Enum('string', 'int', 'float', 'boolean', 'json', name='config_type_enum'),
        nullable=False,
        default='string',
        comment="配置类型"
    )
    
    # 分类和描述 - 数据库中暂无此字段
    # category = Column(
    #     String(50),
    #     nullable=True,
    #     index=True,
    #     comment="配置分类"
    # )
    
    description = Column(
        Text,
        nullable=True,
        comment="配置描述"
    )
    
    # 状态管理
    is_active = Column(
        Boolean,
        nullable=False,
        default=True,
        index=True,
        comment="是否启用"
    )
    
    is_system = Column(
        Boolean,
        nullable=False,
        default=False,
        comment="是否系统配置（不可删除）"
    )
    
    # 修改信息
    modified_by = Column(
        String(50),
        nullable=True,
        comment="修改人"
    )
    
    # 索引和约束
    __table_args__ = (
        Index('idx_config_key', 'config_key'),
        # Index('idx_config_category', 'category'),  # 数据库中暂无category字段
        Index('idx_config_active', 'is_active'),
    )
    
    def get_typed_value(self) -> Any:
        """
        获取类型化的配置值
        
        Returns:
            Any: 转换后的配置值
        """
        if self.config_value is None:
            return None
        
        if self.config_type == 'int':
            return int(self.config_value)
        elif self.config_type == 'float':
            return float(self.config_value)
        elif self.config_type == 'boolean':
            return self.config_value.lower() in ('true', '1', 'yes', 'on')
        elif self.config_type == 'json':
            return json.loads(self.config_value)
        else:
            return self.config_value
    
    def set_typed_value(self, value: Any, db: Session) -> None:
        """
        设置类型化的配置值
        
        Args:
            value: 配置值
            db: 数据库会话
        """
        if value is None:
            self.config_value = None
        elif self.config_type == 'json':
            self.config_value = json.dumps(value, ensure_ascii=False)
        else:
            self.config_value = str(value)
        
        db.commit()
    
    @classmethod
    def get_config(cls, db: Session, key: str, default: Any = None) -> Any:
        """
        获取配置值
        
        Args:
            db: 数据库会话
            key: 配置键名
            default: 默认值
        
        Returns:
            Any: 配置值
        """
        config = db.query(cls).filter(
            cls.config_key == key,
            cls.is_active == True
        ).first()
        
        if config:
            return config.get_typed_value()
        
        return default
    
    @classmethod
    def set_config(cls, db: Session, key: str, value: Any, 
                  config_type: str = 'string', category: str = None,
                  description: str = None, modified_by: str = None) -> 'SystemConfig':
        """
        设置配置值
        
        Args:
            db: 数据库会话
            key: 配置键名
            value: 配置值
            config_type: 配置类型
            category: 配置分类
            description: 配置描述
            modified_by: 修改人
        
        Returns:
            SystemConfig: 配置对象
        """
        config = db.query(cls).filter(cls.config_key == key).first()
        
        if config:
            # 更新现有配置
            config.config_type = config_type
            config.modified_by = modified_by
            if category:
                config.category = category
            if description:
                config.description = description
            config.set_typed_value(value, db)
        else:
            # 创建新配置
            config = cls(
                config_key=key,
                config_type=config_type,
                category=category,
                description=description,
                modified_by=modified_by
            )
            db.add(config)
            db.commit()
            config.set_typed_value(value, db)
        
        return config
    
    @classmethod
    def get_configs_by_category(cls, db: Session, category: str) -> List['SystemConfig']:
        """
        根据分类获取配置列表
        
        Args:
            db: 数据库会话
            category: 配置分类
        
        Returns:
            List[SystemConfig]: 配置列表
        """
        return db.query(cls).filter(
            cls.category == category,
            cls.is_active == True
        ).order_by(cls.config_key).all()
    
    @classmethod
    def get_all_configs(cls, db: Session, include_inactive: bool = False) -> Dict[str, Any]:
        """
        获取所有配置
        
        Args:
            db: 数据库会话
            include_inactive: 是否包含非活跃配置
        
        Returns:
            Dict[str, Any]: 配置字典
        """
        query = db.query(cls)
        
        if not include_inactive:
            query = query.filter(cls.is_active == True)
        
        configs = query.all()
        
        return {
            config.config_key: config.get_typed_value()
            for config in configs
        }
    
    @classmethod
    def delete_config(cls, db: Session, key: str) -> bool:
        """
        删除配置
        
        Args:
            db: 数据库会话
            key: 配置键名
        
        Returns:
            bool: 是否删除成功
        """
        config = db.query(cls).filter(cls.config_key == key).first()
        
        if config and not config.is_system:
            db.delete(config)
            db.commit()
            return True
        
        return False
    
    def to_dict(self, **kwargs) -> dict:
        """
        转换为字典
        
        Returns:
            dict: 配置信息字典
        """
        result = super().to_dict(**kwargs)
        result['typed_value'] = self.get_typed_value()
        return result


if __name__ == "__main__":
    # 测试模型功能
    print("管理员模型定义完成")
    print(f"AdminUser表名: {AdminUser.__tablename__}")
    print(f"SystemConfig表名: {SystemConfig.__tablename__}")
    
    # 测试密码哈希
    test_password = "admin123"
    hashed = AdminUser.hash_password(test_password)
    print(f"\n密码哈希测试:")
    print(f"原密码: {test_password}")
    print(f"哈希值: {hashed[:50]}...")
    
    print("\n管理员模型测试完成")