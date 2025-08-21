#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据集服务层
"""

import os
import json
import shutil
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
from pathlib import Path

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc, asc
from fastapi import UploadFile, HTTPException

from app.models.dataset import Dataset, DatasetType, DatasetStatus
from app.schemas.dataset import (
    DatasetCreate, DatasetUpdate, DatasetFilter, 
    DatasetStats, DatasetPreview
)
from app.core.config import settings
from app.core.exceptions import DatasetError
from loguru import logger


class DatasetService:
    """数据集服务类"""
    
    def __init__(self, db: Session):
        self.db = db
        self.upload_dir = Path(settings.UPLOAD_DIR) / "datasets"
        self.upload_dir.mkdir(parents=True, exist_ok=True)
    
    def create_dataset(self, dataset_data: DatasetCreate, user_id: int) -> Dataset:
        """
        创建数据集
        
        Args:
            dataset_data: 数据集创建数据
            user_id: 创建者ID
            
        Returns:
            Dataset: 创建的数据集对象
        """
        try:
            # 检查名称是否重复
            existing = self.db.query(Dataset).filter(
                Dataset.name == dataset_data.name,
                Dataset.created_by == user_id
            ).first()
            
            if existing:
                raise DatasetError(f"数据集名称 '{dataset_data.name}' 已存在")
            
            # 创建数据集对象
            dataset = Dataset(
                name=dataset_data.name,
                description=dataset_data.description,
                dataset_type=DatasetType(dataset_data.dataset_type.value.title()),
                format=dataset_data.format,
                is_public=dataset_data.is_public,
                tags=json.dumps(dataset_data.tags, ensure_ascii=False) if dataset_data.tags else None,
                status=DatasetStatus.PENDING,
                created_by=user_id
            )
            
            self.db.add(dataset)
            self.db.commit()
            self.db.refresh(dataset)
            
            logger.info(f"数据集创建成功: {dataset.name} (ID: {dataset.id})")
            return dataset
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"创建数据集失败: {str(e)}")
            raise DatasetError(f"创建数据集失败: {str(e)}")
    
    def get_dataset(self, dataset_id: int, user_id: Optional[int] = None) -> Optional[Dataset]:
        """
        获取数据集详情
        
        Args:
            dataset_id: 数据集ID
            user_id: 用户ID（用于权限检查）
            
        Returns:
            Dataset: 数据集对象
        """
        query = self.db.query(Dataset).filter(Dataset.id == dataset_id)
        
        # 如果指定了用户ID，只返回该用户的数据集或公开数据集
        if user_id is not None:
            query = query.filter(
                or_(
                    Dataset.created_by == user_id,
                    Dataset.is_public == True
                )
            )
        
        return query.first()
    
    def get_datasets(
        self, 
        filters: DatasetFilter, 
        user_id: Optional[int] = None
    ) -> Tuple[List[Dataset], int]:
        """
        获取数据集列表
        
        Args:
            filters: 筛选条件
            user_id: 用户ID（用于权限检查）
            
        Returns:
            Tuple[List[Dataset], int]: 数据集列表和总数
        """
        query = self.db.query(Dataset)
        
        # 权限过滤
        if user_id is not None:
            query = query.filter(
                or_(
                    Dataset.created_by == user_id,
                    Dataset.is_public == True
                )
            )
        
        # 搜索过滤
        if filters.search:
            search_term = f"%{filters.search}%"
            query = query.filter(
                or_(
                    Dataset.name.like(search_term),
                    Dataset.description.like(search_term)
                )
            )
        
        # 类型过滤
        if filters.dataset_type:
            query = query.filter(
                Dataset.dataset_type == DatasetType(filters.dataset_type.value.title())
            )
        
        # 状态过滤
        if filters.status:
            query = query.filter(
                Dataset.status == DatasetStatus(filters.status.value)
            )
        
        # 公开状态过滤
        if filters.is_public is not None:
            query = query.filter(Dataset.is_public == filters.is_public)
        
        # 创建者过滤
        if filters.created_by:
            query = query.filter(Dataset.created_by == filters.created_by)
        
        # 标签过滤
        if filters.tags:
            for tag in filters.tags:
                query = query.filter(Dataset.tags.like(f"%{tag}%"))
        
        # 获取总数
        total = query.count()
        
        # 排序
        sort_column = getattr(Dataset, filters.sort_by, Dataset.created_at)
        if filters.sort_order == "desc":
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(asc(sort_column))
        
        # 分页
        offset = (filters.page - 1) * filters.size
        datasets = query.offset(offset).limit(filters.size).all()
        
        return datasets, total
    
    def update_dataset(
        self, 
        dataset_id: int, 
        dataset_data: DatasetUpdate, 
        user_id: int
    ) -> Optional[Dataset]:
        """
        更新数据集
        
        Args:
            dataset_id: 数据集ID
            dataset_data: 更新数据
            user_id: 用户ID
            
        Returns:
            Dataset: 更新后的数据集对象
        """
        try:
            dataset = self.db.query(Dataset).filter(
                Dataset.id == dataset_id,
                Dataset.created_by == user_id
            ).first()
            
            if not dataset:
                raise DatasetError("数据集不存在或无权限访问")
            
            # 更新字段
            update_data = dataset_data.dict(exclude_unset=True)
            
            for field, value in update_data.items():
                if field == "dataset_type" and value:
                    setattr(dataset, field, DatasetType(value.value.title()))
                elif field == "status" and value:
                    setattr(dataset, field, DatasetStatus(value.value))
                elif field == "tags" and value is not None:
                    setattr(dataset, field, json.dumps(value, ensure_ascii=False))
                else:
                    setattr(dataset, field, value)
            
            self.db.commit()
            self.db.refresh(dataset)
            
            logger.info(f"数据集更新成功: {dataset.name} (ID: {dataset.id})")
            return dataset
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"更新数据集失败: {str(e)}")
            raise DatasetError(f"更新数据集失败: {str(e)}")
    
    def delete_dataset(self, dataset_id: int, user_id: int) -> bool:
        """
        删除数据集
        
        Args:
            dataset_id: 数据集ID
            user_id: 用户ID
            
        Returns:
            bool: 是否删除成功
        """
        try:
            dataset = self.db.query(Dataset).filter(
                Dataset.id == dataset_id,
                Dataset.created_by == user_id
            ).first()
            
            if not dataset:
                raise DatasetError("数据集不存在或无权限访问")
            
            # 删除存储文件
            if dataset.storage_path and os.path.exists(dataset.storage_path):
                if os.path.isdir(dataset.storage_path):
                    shutil.rmtree(dataset.storage_path)
                else:
                    os.remove(dataset.storage_path)
            
            # 删除数据库记录
            self.db.delete(dataset)
            self.db.commit()
            
            logger.info(f"数据集删除成功: {dataset.name} (ID: {dataset.id})")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"删除数据集失败: {str(e)}")
            raise DatasetError(f"删除数据集失败: {str(e)}")
    
    def get_dataset_stats(self, user_id: Optional[int] = None) -> DatasetStats:
        """
        获取数据集统计信息
        
        Args:
            user_id: 用户ID（用于权限过滤）
            
        Returns:
            DatasetStats: 统计信息
        """
        query = self.db.query(Dataset)
        
        # 权限过滤
        if user_id is not None:
            query = query.filter(
                or_(
                    Dataset.created_by == user_id,
                    Dataset.is_public == True
                )
            )
        
        # 基础统计
        total = query.count()
        total_samples = query.with_entities(
            func.sum(Dataset.record_count)
        ).scalar() or 0
        total_size = query.with_entities(
            func.sum(Dataset.size)
        ).scalar() or 0
        processing = query.filter(
            Dataset.status == DatasetStatus.PROCESSING
        ).count()
        
        # 按类型统计
        type_stats = {}
        for dataset_type in DatasetType:
            count = query.filter(
                Dataset.dataset_type == dataset_type
            ).count()
            type_stats[dataset_type.value.lower()] = count
        
        # 按状态统计
        status_stats = {}
        for status in DatasetStatus:
            count = query.filter(
                Dataset.status == status
            ).count()
            status_stats[status.value] = count
        
        return DatasetStats(
            total=total,
            total_samples=total_samples,
            total_size=total_size,
            processing=processing,
            by_type=type_stats,
            by_status=status_stats
        )
    
    def upload_dataset_files(
        self, 
        dataset_id: int, 
        files: List[UploadFile], 
        user_id: int
    ) -> Dataset:
        """
        上传数据集文件
        
        Args:
            dataset_id: 数据集ID
            files: 上传的文件列表
            user_id: 用户ID
            
        Returns:
            Dataset: 更新后的数据集对象
        """
        try:
            dataset = self.db.query(Dataset).filter(
                Dataset.id == dataset_id,
                Dataset.created_by == user_id
            ).first()
            
            if not dataset:
                raise DatasetError("数据集不存在或无权限访问")
            
            # 创建数据集存储目录
            dataset_dir = self.upload_dir / str(dataset_id)
            dataset_dir.mkdir(parents=True, exist_ok=True)
            
            total_size = 0
            file_paths = []
            
            # 保存文件
            for file in files:
                file_path = dataset_dir / file.filename
                
                with open(file_path, "wb") as buffer:
                    content = file.file.read()
                    buffer.write(content)
                    total_size += len(content)
                
                file_paths.append(str(file_path))
            
            # 更新数据集信息
            dataset.storage_path = str(dataset_dir)
            dataset.size = total_size
            dataset.status = DatasetStatus.PROCESSING
            
            self.db.commit()
            self.db.refresh(dataset)
            
            logger.info(f"数据集文件上传成功: {dataset.name} (ID: {dataset.id})")
            
            # TODO: 异步处理数据集（解析、验证、生成预览等）
            # self._process_dataset_async(dataset)
            
            return dataset
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"上传数据集文件失败: {str(e)}")
            raise DatasetError(f"上传数据集文件失败: {str(e)}")
    
    def get_dataset_preview(
        self, 
        dataset_id: int, 
        user_id: Optional[int] = None,
        limit: int = 10
    ) -> Optional[DatasetPreview]:
        """
        获取数据集预览
        
        Args:
            dataset_id: 数据集ID
            user_id: 用户ID
            limit: 预览样本数量限制
            
        Returns:
            DatasetPreview: 预览数据
        """
        dataset = self.get_dataset(dataset_id, user_id)
        if not dataset or not dataset.preview_data:
            return None
        
        try:
            preview_data = json.loads(dataset.preview_data)
            samples = preview_data.get("samples", [])[:limit]
            
            return DatasetPreview(
                samples=samples,
                total_count=dataset.record_count or 0,
                sample_fields=preview_data.get("fields")
            )
        except Exception as e:
            logger.error(f"获取数据集预览失败: {str(e)}")
            return None