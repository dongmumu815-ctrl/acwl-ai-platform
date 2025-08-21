#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据集管理API端点
"""

import json
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.v1.endpoints.auth import get_current_user
from app.models.user import User
from app.schemas.dataset import (
    DatasetCreate, DatasetUpdate, DatasetResponse, DatasetListResponse,
    DatasetFilter, DatasetStats, DatasetPreview, DatasetUpload
)
from app.services.dataset import DatasetService
from app.core.exceptions import DatasetError
from loguru import logger

# 创建路由器
router = APIRouter()


@router.post("/", response_model=DatasetResponse, summary="创建数据集")
async def create_dataset(
    dataset_data: DatasetCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    创建新的数据集
    
    Args:
        dataset_data: 数据集创建数据
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        DatasetResponse: 创建的数据集信息
    """
    try:
        service = DatasetService(db)
        dataset = service.create_dataset(dataset_data, current_user.id)
        return DatasetResponse.from_orm(dataset)
    except DatasetError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"创建数据集API错误: {str(e)}")
        raise HTTPException(status_code=500, detail="内部服务器错误")


@router.get("/", response_model=DatasetListResponse, summary="获取数据集列表")
async def get_datasets(
    search: Optional[str] = Query(None, description="搜索关键词"),
    dataset_type: Optional[str] = Query(None, description="数据集类型"),
    status: Optional[str] = Query(None, description="数据集状态"),
    is_public: Optional[bool] = Query(None, description="是否公开"),
    tags: Optional[List[str]] = Query(None, description="标签筛选"),
    sort_by: str = Query("created_at", description="排序字段"),
    sort_order: str = Query("desc", description="排序方向"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页大小"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取数据集列表
    
    Args:
        search: 搜索关键词
        dataset_type: 数据集类型筛选
        status: 状态筛选
        is_public: 公开状态筛选
        tags: 标签筛选
        sort_by: 排序字段
        sort_order: 排序方向
        page: 页码
        size: 每页大小
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        DatasetListResponse: 数据集列表响应
    """
    try:
        # 构建筛选条件
        filters = DatasetFilter(
            search=search,
            dataset_type=dataset_type,
            status=status,
            is_public=is_public,
            tags=tags,
            sort_by=sort_by,
            sort_order=sort_order,
            page=page,
            size=size
        )
        
        service = DatasetService(db)
        datasets, total = service.get_datasets(filters, current_user.id)
        
        # 计算总页数
        pages = (total + size - 1) // size
        
        return DatasetListResponse(
            items=[DatasetResponse.from_orm(dataset) for dataset in datasets],
            total=total,
            page=page,
            size=size,
            pages=pages
        )
    except Exception as e:
        logger.error(f"获取数据集列表API错误: {str(e)}")
        raise HTTPException(status_code=500, detail="内部服务器错误")


@router.get("/stats", response_model=DatasetStats, summary="获取数据集统计信息")
async def get_dataset_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取数据集统计信息
    
    Args:
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        DatasetStats: 统计信息
    """
    try:
        service = DatasetService(db)
        return service.get_dataset_stats(current_user.id)
    except Exception as e:
        logger.error(f"获取数据集统计API错误: {str(e)}")
        raise HTTPException(status_code=500, detail="内部服务器错误")


@router.get("/{dataset_id}", response_model=DatasetResponse, summary="获取数据集详情")
async def get_dataset(
    dataset_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取数据集详情
    
    Args:
        dataset_id: 数据集ID
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        DatasetResponse: 数据集详情
    """
    try:
        service = DatasetService(db)
        dataset = service.get_dataset(dataset_id, current_user.id)
        
        if not dataset:
            raise HTTPException(status_code=404, detail="数据集不存在")
        
        return DatasetResponse.from_orm(dataset)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取数据集详情API错误: {str(e)}")
        raise HTTPException(status_code=500, detail="内部服务器错误")


@router.put("/{dataset_id}", response_model=DatasetResponse, summary="更新数据集")
async def update_dataset(
    dataset_id: int,
    dataset_data: DatasetUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    更新数据集信息
    
    Args:
        dataset_id: 数据集ID
        dataset_data: 更新数据
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        DatasetResponse: 更新后的数据集信息
    """
    try:
        service = DatasetService(db)
        dataset = service.update_dataset(dataset_id, dataset_data, current_user.id)
        
        if not dataset:
            raise HTTPException(status_code=404, detail="数据集不存在或无权限访问")
        
        return DatasetResponse.from_orm(dataset)
    except DatasetError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新数据集API错误: {str(e)}")
        raise HTTPException(status_code=500, detail="内部服务器错误")


@router.delete("/{dataset_id}", summary="删除数据集")
async def delete_dataset(
    dataset_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    删除数据集
    
    Args:
        dataset_id: 数据集ID
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        dict: 删除结果
    """
    try:
        service = DatasetService(db)
        success = service.delete_dataset(dataset_id, current_user.id)
        
        if not success:
            raise HTTPException(status_code=404, detail="数据集不存在或无权限访问")
        
        return {"message": "数据集删除成功"}
    except DatasetError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除数据集API错误: {str(e)}")
        raise HTTPException(status_code=500, detail="内部服务器错误")


@router.post("/{dataset_id}/upload", response_model=DatasetResponse, summary="上传数据集文件")
async def upload_dataset_files(
    dataset_id: int,
    files: List[UploadFile] = File(..., description="数据集文件"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    上传数据集文件
    
    Args:
        dataset_id: 数据集ID
        files: 上传的文件列表
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        DatasetResponse: 更新后的数据集信息
    """
    try:
        # 验证文件
        if not files:
            raise HTTPException(status_code=400, detail="请选择要上传的文件")
        
        # 检查文件大小和类型
        max_file_size = 1024 * 1024 * 1024  # 1GB
        allowed_extensions = {
            '.csv', '.json', '.jsonl', '.txt', '.zip', '.tar.gz',
            '.jpg', '.jpeg', '.png', '.gif', '.bmp',
            '.mp3', '.wav', '.flac', '.aac',
            '.mp4', '.avi', '.mov', '.mkv'
        }
        
        for file in files:
            if file.size > max_file_size:
                raise HTTPException(
                    status_code=400, 
                    detail=f"文件 {file.filename} 超过最大大小限制 (1GB)"
                )
            
            file_ext = '.' + file.filename.split('.')[-1].lower()
            if file_ext not in allowed_extensions:
                raise HTTPException(
                    status_code=400,
                    detail=f"不支持的文件类型: {file_ext}"
                )
        
        service = DatasetService(db)
        dataset = service.upload_dataset_files(dataset_id, files, current_user.id)
        
        return DatasetResponse.from_orm(dataset)
    except DatasetError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"上传数据集文件API错误: {str(e)}")
        raise HTTPException(status_code=500, detail="内部服务器错误")


@router.get("/{dataset_id}/preview", response_model=DatasetPreview, summary="获取数据集预览")
async def get_dataset_preview(
    dataset_id: int,
    limit: int = Query(10, ge=1, le=50, description="预览样本数量"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取数据集预览
    
    Args:
        dataset_id: 数据集ID
        limit: 预览样本数量限制
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        DatasetPreview: 预览数据
    """
    try:
        service = DatasetService(db)
        preview = service.get_dataset_preview(dataset_id, current_user.id, limit)
        
        if not preview:
            raise HTTPException(status_code=404, detail="数据集不存在或暂无预览数据")
        
        return preview
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取数据集预览API错误: {str(e)}")
        raise HTTPException(status_code=500, detail="内部服务器错误")


@router.post("/{dataset_id}/clone", response_model=DatasetResponse, summary="克隆数据集")
async def clone_dataset(
    dataset_id: int,
    name: str = Form(..., description="新数据集名称"),
    description: Optional[str] = Form(None, description="新数据集描述"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    克隆数据集
    
    Args:
        dataset_id: 源数据集ID
        name: 新数据集名称
        description: 新数据集描述
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        DatasetResponse: 克隆的数据集信息
    """
    try:
        service = DatasetService(db)
        
        # 获取源数据集
        source_dataset = service.get_dataset(dataset_id, current_user.id)
        if not source_dataset:
            raise HTTPException(status_code=404, detail="源数据集不存在")
        
        # 创建克隆数据集
        clone_data = DatasetCreate(
            name=name,
            description=description or f"克隆自: {source_dataset.name}",
            dataset_type=source_dataset.dataset_type.value.lower(),
            format=source_dataset.format,
            is_public=False,  # 克隆的数据集默认为私有
            tags=json.loads(source_dataset.tags) if source_dataset.tags else []
        )
        
        cloned_dataset = service.create_dataset(clone_data, current_user.id)
        
        # TODO: 复制数据文件（异步处理）
        
        return DatasetResponse.from_orm(cloned_dataset)
    except DatasetError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"克隆数据集API错误: {str(e)}")
        raise HTTPException(status_code=500, detail="内部服务器错误")


@router.post("/{dataset_id}/analyze", summary="分析数据集")
async def analyze_dataset(
    dataset_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    分析数据集
    
    Args:
        dataset_id: 数据集ID
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        dict: 分析结果
    """
    try:
        service = DatasetService(db)
        dataset = service.get_dataset(dataset_id, current_user.id)
        
        if not dataset:
            raise HTTPException(status_code=404, detail="数据集不存在")
        
        # TODO: 实现数据集分析逻辑
        # 包括数据质量检查、统计分析、可视化等
        
        return {
            "message": "数据集分析已启动",
            "dataset_id": dataset_id,
            "status": "analyzing"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"分析数据集API错误: {str(e)}")
        raise HTTPException(status_code=500, detail="内部服务器错误")