#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基础服务类

提供所有业务服务的基础功能和通用方法。

Author: System
Date: 2024
"""

from typing import Optional, List, Dict, Any, Type, TypeVar, Generic
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc, func
from datetime import datetime, timedelta
import logging

from app.core.database import get_db_context
from app.core.exceptions import (
    NotFoundException,
    ValidationException,
    DatabaseException,
    BusinessException
)
from app.models.base import BaseModel
from app.schemas.base import PaginationInfo

# 泛型类型变量
ModelType = TypeVar("ModelType", bound=BaseModel)
CreateSchemaType = TypeVar("CreateSchemaType")
UpdateSchemaType = TypeVar("UpdateSchemaType")


class BaseService(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """
    基础服务类
    
    提供通用的CRUD操作和业务逻辑处理功能
    """
    
    def __init__(self, model: Type[ModelType]):
        """
        初始化基础服务
        
        Args:
            model: 数据模型类
        """
        self.model = model
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def get_db(self) -> Session:
        """
        获取数据库会话
        
        Returns:
            数据库会话对象
        """
        return next(get_db_context())
    
    def create(self, db: Session, *, obj_in: CreateSchemaType, **kwargs) -> ModelType:
        """
        创建新记录
        
        Args:
            db: 数据库会话
            obj_in: 创建数据
            **kwargs: 额外参数
            
        Returns:
            创建的模型实例
            
        Raises:
            ValidationException: 数据验证失败
            DatabaseException: 数据库操作失败
        """
        try:
            # 转换为字典
            if hasattr(obj_in, 'dict'):
                obj_data = obj_in.dict(exclude_unset=True)
            else:
                obj_data = obj_in
            
            # 添加额外参数
            obj_data.update(kwargs)
            
            # 创建模型实例
            db_obj = self.model(**obj_data)
            
            # 保存到数据库
            db.add(db_obj)
            db.commit()
            db.refresh(db_obj)
            
            self.logger.info(f"Created {self.model.__name__} with id: {db_obj.id}")
            return db_obj
            
        except Exception as e:
            db.rollback()
            self.logger.error(f"Failed to create {self.model.__name__}: {str(e)}")
            raise DatabaseException(f"创建{self.model.__name__}失败: {str(e)}")
    
    def get(self, db: Session, id: int) -> Optional[ModelType]:
        """
        根据ID获取记录
        
        Args:
            db: 数据库会话
            id: 记录ID
            
        Returns:
            模型实例或None
        """
        return db.query(self.model).filter(self.model.id == id).first()
    
    def get_or_404(self, db: Session, id: int) -> ModelType:
        """
        根据ID获取记录，不存在则抛出异常
        
        Args:
            db: 数据库会话
            id: 记录ID
            
        Returns:
            模型实例
            
        Raises:
            NotFoundException: 记录不存在
        """
        obj = self.get(db, id)
        if not obj:
            raise NotFoundException(f"{self.model.__name__} with id {id} not found")
        return obj
    
    def get_multi(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
        order_desc: bool = False
    ) -> List[ModelType]:
        """
        获取多条记录
        
        Args:
            db: 数据库会话
            skip: 跳过记录数
            limit: 限制记录数
            filters: 过滤条件
            order_by: 排序字段
            order_desc: 是否降序
            
        Returns:
            模型实例列表
        """
        query = db.query(self.model)
        
        # 应用过滤条件
        if filters:
            query = self._apply_filters(query, filters)
        
        # 应用排序
        if order_by:
            if hasattr(self.model, order_by):
                order_field = getattr(self.model, order_by)
                if order_desc:
                    query = query.order_by(desc(order_field))
                else:
                    query = query.order_by(asc(order_field))
        
        return query.offset(skip).limit(limit).all()
    
    def get_paginated(
        self,
        db: Session,
        *,
        page: int = 1,
        page_size: int = 20,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
        order_desc: bool = False
    ) -> tuple[List[ModelType], PaginationInfo]:
        """
        获取分页数据
        
        Args:
            db: 数据库会话
            page: 页码
            page_size: 每页大小
            filters: 过滤条件
            order_by: 排序字段
            order_desc: 是否降序
            
        Returns:
            (记录列表, 分页信息)
        """
        query = db.query(self.model)
        
        # 应用过滤条件
        if filters:
            query = self._apply_filters(query, filters)
        
        # 获取总数
        total = query.count()
        
        # 应用排序
        if order_by:
            if hasattr(self.model, order_by):
                order_field = getattr(self.model, order_by)
                if order_desc:
                    query = query.order_by(desc(order_field))
                else:
                    query = query.order_by(asc(order_field))
        
        # 分页
        skip = (page - 1) * page_size
        items = query.offset(skip).limit(page_size).all()
        
        # 创建分页信息
        pagination = PaginationInfo.create(
            page=page,
            size=page_size,
            total=total
        )
        
        return items, pagination
    
    def update(
        self,
        db: Session,
        *,
        db_obj: ModelType,
        obj_in: UpdateSchemaType,
        **kwargs
    ) -> ModelType:
        """
        更新记录
        
        Args:
            db: 数据库会话
            db_obj: 数据库对象
            obj_in: 更新数据
            **kwargs: 额外参数
            
        Returns:
            更新后的模型实例
            
        Raises:
            DatabaseException: 数据库操作失败
        """
        try:
            # 转换为字典
            if hasattr(obj_in, 'dict'):
                obj_data = obj_in.dict(exclude_unset=True)
            else:
                obj_data = obj_in
            
            # 添加额外参数
            obj_data.update(kwargs)
            
            # 更新字段
            for field, value in obj_data.items():
                if hasattr(db_obj, field):
                    setattr(db_obj, field, value)
            
            # 更新时间戳
            if hasattr(db_obj, 'updated_at'):
                db_obj.updated_at = datetime.utcnow()
            
            db.commit()
            db.refresh(db_obj)
            
            self.logger.info(f"Updated {self.model.__name__} with id: {db_obj.id}")
            return db_obj
            
        except Exception as e:
            db.rollback()
            self.logger.error(f"Failed to update {self.model.__name__}: {str(e)}")
            raise DatabaseException(f"更新{self.model.__name__}失败: {str(e)}")
    
    def delete(self, db: Session, *, id: int) -> bool:
        """
        删除记录
        
        Args:
            db: 数据库会话
            id: 记录ID
            
        Returns:
            是否删除成功
            
        Raises:
            NotFoundException: 记录不存在
            DatabaseException: 数据库操作失败
        """
        try:
            obj = self.get_or_404(db, id)
            
            # 检查是否支持软删除
            if hasattr(obj, 'deleted_at'):
                obj.deleted_at = datetime.utcnow()
                if hasattr(obj, 'updated_at'):
                    obj.updated_at = datetime.utcnow()
            else:
                db.delete(obj)
            
            db.commit()
            
            self.logger.info(f"Deleted {self.model.__name__} with id: {id}")
            return True
            
        except NotFoundException:
            raise
        except Exception as e:
            db.rollback()
            self.logger.error(f"Failed to delete {self.model.__name__}: {str(e)}")
            raise DatabaseException(f"删除{self.model.__name__}失败: {str(e)}")
    
    def count(self, db: Session, *, filters: Optional[Dict[str, Any]] = None) -> int:
        """
        统计记录数量
        
        Args:
            db: 数据库会话
            filters: 过滤条件
            
        Returns:
            记录数量
        """
        query = db.query(self.model)
        
        if filters:
            query = self._apply_filters(query, filters)
        
        return query.count()
    
    def exists(self, db: Session, *, filters: Dict[str, Any]) -> bool:
        """
        检查记录是否存在
        
        Args:
            db: 数据库会话
            filters: 过滤条件
            
        Returns:
            是否存在
        """
        query = db.query(self.model)
        query = self._apply_filters(query, filters)
        return query.first() is not None
    
    def bulk_create(
        self,
        db: Session,
        *,
        objs_in: List[CreateSchemaType],
        batch_size: int = 1000
    ) -> List[ModelType]:
        """
        批量创建记录
        
        Args:
            db: 数据库会话
            objs_in: 创建数据列表
            batch_size: 批次大小
            
        Returns:
            创建的模型实例列表
            
        Raises:
            DatabaseException: 数据库操作失败
        """
        try:
            created_objs = []
            
            for i in range(0, len(objs_in), batch_size):
                batch = objs_in[i:i + batch_size]
                batch_objs = []
                
                for obj_in in batch:
                    if hasattr(obj_in, 'dict'):
                        obj_data = obj_in.dict(exclude_unset=True)
                    else:
                        obj_data = obj_in
                    
                    db_obj = self.model(**obj_data)
                    batch_objs.append(db_obj)
                
                db.add_all(batch_objs)
                db.commit()
                
                # 刷新对象以获取ID
                for obj in batch_objs:
                    db.refresh(obj)
                
                created_objs.extend(batch_objs)
            
            self.logger.info(f"Bulk created {len(created_objs)} {self.model.__name__} records")
            return created_objs
            
        except Exception as e:
            db.rollback()
            self.logger.error(f"Failed to bulk create {self.model.__name__}: {str(e)}")
            raise DatabaseException(f"批量创建{self.model.__name__}失败: {str(e)}")
    
    def bulk_update(
        self,
        db: Session,
        *,
        updates: List[Dict[str, Any]],
        batch_size: int = 1000
    ) -> int:
        """
        批量更新记录
        
        Args:
            db: 数据库会话
            updates: 更新数据列表，每个字典必须包含id字段
            batch_size: 批次大小
            
        Returns:
            更新的记录数量
            
        Raises:
            DatabaseException: 数据库操作失败
        """
        try:
            updated_count = 0
            
            for i in range(0, len(updates), batch_size):
                batch = updates[i:i + batch_size]
                
                for update_data in batch:
                    if 'id' not in update_data:
                        continue
                    
                    obj_id = update_data.pop('id')
                    
                    # 添加更新时间戳
                    if hasattr(self.model, 'updated_at'):
                        update_data['updated_at'] = datetime.utcnow()
                    
                    result = db.query(self.model).filter(
                        self.model.id == obj_id
                    ).update(update_data)
                    
                    updated_count += result
                
                db.commit()
            
            self.logger.info(f"Bulk updated {updated_count} {self.model.__name__} records")
            return updated_count
            
        except Exception as e:
            db.rollback()
            self.logger.error(f"Failed to bulk update {self.model.__name__}: {str(e)}")
            raise DatabaseException(f"批量更新{self.model.__name__}失败: {str(e)}")
    
    def _apply_filters(self, query, filters: Dict[str, Any]):
        """
        应用过滤条件
        
        Args:
            query: SQLAlchemy查询对象
            filters: 过滤条件字典
            
        Returns:
            应用过滤条件后的查询对象
        """
        for field, value in filters.items():
            if not hasattr(self.model, field):
                continue
            
            model_field = getattr(self.model, field)
            
            if value is None:
                query = query.filter(model_field.is_(None))
            elif isinstance(value, list):
                query = query.filter(model_field.in_(value))
            elif isinstance(value, dict):
                # 支持范围查询
                if 'gte' in value:
                    query = query.filter(model_field >= value['gte'])
                if 'lte' in value:
                    query = query.filter(model_field <= value['lte'])
                if 'gt' in value:
                    query = query.filter(model_field > value['gt'])
                if 'lt' in value:
                    query = query.filter(model_field < value['lt'])
                if 'like' in value:
                    query = query.filter(model_field.like(f"%{value['like']}%"))
                if 'ilike' in value:
                    query = query.filter(model_field.ilike(f"%{value['ilike']}%"))
            else:
                query = query.filter(model_field == value)
        
        return query
    
    def get_stats(
        self,
        db: Session,
        *,
        date_field: str = 'created_at',
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        group_by: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取统计信息
        
        Args:
            db: 数据库会话
            date_field: 日期字段名
            start_date: 开始日期
            end_date: 结束日期
            group_by: 分组字段
            
        Returns:
            统计信息字典
        """
        query = db.query(self.model)
        
        # 应用日期过滤
        if hasattr(self.model, date_field):
            date_column = getattr(self.model, date_field)
            
            if start_date:
                query = query.filter(date_column >= start_date)
            if end_date:
                query = query.filter(date_column <= end_date)
        
        # 基础统计
        total_count = query.count()
        
        stats = {
            'total_count': total_count,
            'date_range': {
                'start_date': start_date.isoformat() if start_date else None,
                'end_date': end_date.isoformat() if end_date else None
            }
        }
        
        # 分组统计
        if group_by and hasattr(self.model, group_by):
            group_column = getattr(self.model, group_by)
            group_stats = query.with_entities(
                group_column,
                func.count().label('count')
            ).group_by(group_column).all()
            
            stats['group_stats'] = {
                str(item[0]): item[1] for item in group_stats
            }
        
        return stats
    
    def validate_business_rules(self, db: Session, obj_data: Dict[str, Any]) -> None:
        """
        验证业务规则
        
        子类可以重写此方法来实现特定的业务规则验证
        
        Args:
            db: 数据库会话
            obj_data: 对象数据
            
        Raises:
            BusinessException: 业务规则验证失败
        """
        pass
    
    def before_create(self, db: Session, obj_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        创建前的钩子方法
        
        子类可以重写此方法来实现创建前的处理逻辑
        
        Args:
            db: 数据库会话
            obj_data: 对象数据
            
        Returns:
            处理后的对象数据
        """
        return obj_data
    
    def after_create(self, db: Session, db_obj: ModelType) -> None:
        """
        创建后的钩子方法
        
        子类可以重写此方法来实现创建后的处理逻辑
        
        Args:
            db: 数据库会话
            db_obj: 创建的数据库对象
        """
        pass
    
    def before_update(self, db: Session, db_obj: ModelType, obj_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        更新前的钩子方法
        
        子类可以重写此方法来实现更新前的处理逻辑
        
        Args:
            db: 数据库会话
            db_obj: 数据库对象
            obj_data: 更新数据
            
        Returns:
            处理后的更新数据
        """
        return obj_data
    
    def after_update(self, db: Session, db_obj: ModelType) -> None:
        """
        更新后的钩子方法
        
        子类可以重写此方法来实现更新后的处理逻辑
        
        Args:
            db: 数据库会话
            db_obj: 更新后的数据库对象
        """
        pass
    
    def before_delete(self, db: Session, db_obj: ModelType) -> None:
        """
        删除前的钩子方法
        
        子类可以重写此方法来实现删除前的处理逻辑
        
        Args:
            db: 数据库会话
            db_obj: 要删除的数据库对象
        """
        pass
    
    def after_delete(self, db: Session, obj_id: int) -> None:
        """
        删除后的钩子方法
        
        子类可以重写此方法来实现删除后的处理逻辑
        
        Args:
            db: 数据库会话
            obj_id: 已删除对象的ID
        """
        pass


if __name__ == "__main__":
    print("基础服务类定义完成")