#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基础模型类

提供所有数据库模型的基础类和通用混入类。
包含通用字段、方法和数据库操作功能。

Author: System
Date: 2024
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Type, TypeVar
from sqlalchemy import Column, BigInteger, DateTime, func
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import Session
from sqlalchemy.inspection import inspect

from app.core.database import Base

# 泛型类型变量
ModelType = TypeVar("ModelType", bound="BaseModel")


class TimestampMixin:
    """
    时间戳混入类
    
    为模型添加创建时间和更新时间字段
    """
    
    created_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        server_default=func.now(),
        comment="创建时间"
    )
    
    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        server_default=func.now(),
        server_onupdate=func.now(),
        comment="更新时间"
    )


class BaseModel(Base, TimestampMixin):
    """
    基础模型类
    
    所有数据库模型的基类，提供通用字段和方法
    """
    
    __abstract__ = True
    
    id = Column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        comment="主键ID"
    )
    
    @declared_attr
    def __tablename__(cls) -> str:
        """
        自动生成表名
        
        将类名转换为下划线分隔的表名
        例如: CustomerSession -> customer_sessions
        """
        import re
        # 将驼峰命名转换为下划线命名
        name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', cls.__name__)
        name = re.sub('([a-z0-9])([A-Z])', r'\1_\2', name).lower()
        # 添加复数形式
        if name.endswith('y'):
            name = name[:-1] + 'ies'
        elif name.endswith(('s', 'sh', 'ch', 'x', 'z')):
            name += 'es'
        else:
            name += 's'
        return name
    
    def to_dict(self, exclude: Optional[List[str]] = None, 
                include_relationships: bool = False) -> Dict[str, Any]:
        """
        将模型实例转换为字典
        
        Args:
            exclude: 要排除的字段列表
            include_relationships: 是否包含关联对象
        
        Returns:
            Dict[str, Any]: 模型数据字典
        """
        exclude = exclude or []
        result = {}
        
        # 获取模型的所有列
        mapper = inspect(self.__class__)
        
        for column in mapper.columns:
            if column.name not in exclude:
                value = getattr(self, column.name)
                # 处理日期时间类型
                if isinstance(value, datetime):
                    result[column.name] = value.isoformat()
                else:
                    result[column.name] = value
        
        # 包含关联对象
        if include_relationships:
            for relationship in mapper.relationships:
                if relationship.key not in exclude:
                    related_obj = getattr(self, relationship.key)
                    if related_obj is not None:
                        if hasattr(related_obj, '__iter__') and not isinstance(related_obj, str):
                            # 一对多关系
                            result[relationship.key] = [
                                obj.to_dict() if hasattr(obj, 'to_dict') else str(obj)
                                for obj in related_obj
                            ]
                        else:
                            # 一对一关系
                            result[relationship.key] = (
                                related_obj.to_dict() if hasattr(related_obj, 'to_dict') 
                                else str(related_obj)
                            )
        
        return result
    
    def update_from_dict(self, data: Dict[str, Any], 
                        exclude: Optional[List[str]] = None) -> None:
        """
        从字典更新模型实例
        
        Args:
            data: 更新数据字典
            exclude: 要排除的字段列表
        """
        exclude = exclude or ['id', 'created_at']
        
        for key, value in data.items():
            if key not in exclude and hasattr(self, key):
                setattr(self, key, value)
    
    @classmethod
    def create(cls: Type[ModelType], db: Session, **kwargs) -> ModelType:
        """
        创建新的模型实例
        
        Args:
            db: 数据库会话
            **kwargs: 模型字段值
        
        Returns:
            ModelType: 创建的模型实例
        """
        instance = cls(**kwargs)
        db.add(instance)
        db.commit()
        db.refresh(instance)
        return instance
    
    @classmethod
    def get_by_id(cls: Type[ModelType], db: Session, id: int) -> Optional[ModelType]:
        """
        根据ID获取模型实例
        
        Args:
            db: 数据库会话
            id: 主键ID
        
        Returns:
            Optional[ModelType]: 模型实例或None
        """
        return db.query(cls).filter(cls.id == id).first()
    
    @classmethod
    def get_all(cls: Type[ModelType], db: Session, 
               skip: int = 0, limit: int = 100) -> List[ModelType]:
        """
        获取所有模型实例
        
        Args:
            db: 数据库会话
            skip: 跳过的记录数
            limit: 限制的记录数
        
        Returns:
            List[ModelType]: 模型实例列表
        """
        return db.query(cls).offset(skip).limit(limit).all()
    
    @classmethod
    def count(cls: Type[ModelType], db: Session) -> int:
        """
        获取模型记录总数
        
        Args:
            db: 数据库会话
        
        Returns:
            int: 记录总数
        """
        return db.query(cls).count()
    
    def save(self, db: Session) -> None:
        """
        保存模型实例
        
        Args:
            db: 数据库会话
        """
        db.add(self)
        db.commit()
        db.refresh(self)
    
    def delete(self, db: Session) -> None:
        """
        删除模型实例
        
        Args:
            db: 数据库会话
        """
        db.delete(self)
        db.commit()
    
    @classmethod
    def bulk_create(cls: Type[ModelType], db: Session, 
                   data_list: List[Dict[str, Any]]) -> List[ModelType]:
        """
        批量创建模型实例
        
        Args:
            db: 数据库会话
            data_list: 数据字典列表
        
        Returns:
            List[ModelType]: 创建的模型实例列表
        """
        instances = [cls(**data) for data in data_list]
        db.add_all(instances)
        db.commit()
        for instance in instances:
            db.refresh(instance)
        return instances
    
    @classmethod
    def bulk_update(cls: Type[ModelType], db: Session, 
                   data_list: List[Dict[str, Any]]) -> int:
        """
        批量更新模型实例
        
        Args:
            db: 数据库会话
            data_list: 包含id和更新字段的数据字典列表
        
        Returns:
            int: 更新的记录数
        """
        if not data_list:
            return 0
        
        updated_count = 0
        for data in data_list:
            if 'id' not in data:
                continue
            
            instance_id = data.pop('id')
            result = db.query(cls).filter(cls.id == instance_id).update(data)
            updated_count += result
        
        db.commit()
        return updated_count
    
    @classmethod
    def exists(cls: Type[ModelType], db: Session, **filters) -> bool:
        """
        检查记录是否存在
        
        Args:
            db: 数据库会话
            **filters: 过滤条件
        
        Returns:
            bool: 记录是否存在
        """
        query = db.query(cls)
        for key, value in filters.items():
            if hasattr(cls, key):
                query = query.filter(getattr(cls, key) == value)
        
        return query.first() is not None
    
    def __repr__(self) -> str:
        """
        模型实例的字符串表示
        
        Returns:
            str: 模型实例的字符串表示
        """
        return f"<{self.__class__.__name__}(id={getattr(self, 'id', None)})>"
    
    def __str__(self) -> str:
        """
        模型实例的用户友好字符串表示
        
        Returns:
            str: 模型实例的字符串表示
        """
        return self.__repr__()


class SoftDeleteMixin:
    """
    软删除混入类
    
    为模型添加软删除功能
    """
    
    deleted_at = Column(
        DateTime,
        nullable=True,
        comment="删除时间"
    )
    
    def soft_delete(self, db: Session) -> None:
        """
        软删除记录
        
        Args:
            db: 数据库会话
        """
        self.deleted_at = datetime.utcnow()
        db.commit()
    
    def restore(self, db: Session) -> None:
        """
        恢复软删除的记录
        
        Args:
            db: 数据库会话
        """
        self.deleted_at = None
        db.commit()
    
    @property
    def is_deleted(self) -> bool:
        """
        检查记录是否被软删除
        
        Returns:
            bool: 是否被删除
        """
        return self.deleted_at is not None
    
    @classmethod
    def get_active(cls: Type[ModelType], db: Session, 
                  skip: int = 0, limit: int = 100) -> List[ModelType]:
        """
        获取未删除的记录
        
        Args:
            db: 数据库会话
            skip: 跳过的记录数
            limit: 限制的记录数
        
        Returns:
            List[ModelType]: 未删除的模型实例列表
        """
        return db.query(cls).filter(cls.deleted_at.is_(None)).offset(skip).limit(limit).all()
    
    @classmethod
    def get_deleted(cls: Type[ModelType], db: Session, 
                   skip: int = 0, limit: int = 100) -> List[ModelType]:
        """
        获取已删除的记录
        
        Args:
            db: 数据库会话
            skip: 跳过的记录数
            limit: 限制的记录数
        
        Returns:
            List[ModelType]: 已删除的模型实例列表
        """
        return db.query(cls).filter(cls.deleted_at.isnot(None)).offset(skip).limit(limit).all()


if __name__ == "__main__":
    # 测试基础模型功能
    print("基础模型类定义完成")
    print(f"BaseModel包含字段: {[col.name for col in BaseModel.__table__.columns]}")
    print(f"TimestampMixin包含字段: created_at, updated_at")
    print(f"SoftDeleteMixin包含字段: deleted_at")