#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
结果查询接口

实现数据处理结果查询功能，包括：
1. 查询单条数据处理结果
2. 查询批次处理结果
3. 结果状态统计
4. 结果数据导出

Author: System
Date: 2024
"""

import json
import os
import base64
import hmac
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union, Tuple
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status, Header, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from pydantic import BaseModel, Field
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes

from app.core.database import get_db
from app.core.config import settings
from app.models.customer import Customer
from app.models.log import DataUpload
from app.services.auth import JWTService
from app.core.exceptions import ValidationException
from app.core.business_codes import BusinessException, BusinessCode, BusinessResponse

router = APIRouter()

# 结果查询响应模型
class ResultResponse(BaseModel):
    """
    结果查询响应模型
    """
    upload_id: str = Field(..., description="上传记录ID")
    batch_id: str = Field(..., description="批次ID")
    filename: str = Field(..., description="文件名")
    file_size: int = Field(..., description="文件大小")
    status: str = Field(..., description="处理状态")
    progress: Optional[float] = Field(None, description="处理进度")
    result_data: Optional[Dict[str, Any]] = Field(None, description="处理结果数据")
    error_message: Optional[str] = Field(None, description="错误信息")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")
    completed_at: Optional[datetime] = Field(None, description="完成时间")

# 结果列表响应模型
class ResultListResponse(BaseModel):
    """
    结果列表响应模型
    """
    total: int = Field(..., description="总数量")
    page: int = Field(..., description="当前页码")
    size: int = Field(..., description="每页大小")
    items: List[ResultResponse] = Field(..., description="结果列表")

# 批次结果加密响应模型
class BatchResultResponse(BaseModel):
    """
    批次结果加密响应模型
    
    用于返回加密的批次结果数据
    """
    status: str = Field(..., description="批次状态")
    data: Optional[str] = Field(None, description="加密的结果数据（Base64编码）")
    iv: Optional[str] = Field(None, description="初始化向量（Base64编码）")
    result_sign: Optional[str] = Field(None, description="结果数据签名")

# 结果统计响应模型
class ResultStatsResponse(BaseModel):
    """
    结果统计响应模型
    """
    total_count: int = Field(..., description="总数量")
    pending_count: int = Field(..., description="待处理数量")
    processing_count: int = Field(..., description="处理中数量")
    completed_count: int = Field(..., description="已完成数量")
    failed_count: int = Field(..., description="失败数量")
    success_rate: float = Field(..., description="成功率")
    avg_processing_time: Optional[float] = Field(None, description="平均处理时间（秒）")

def get_current_customer(authorization: str = Header(...)) -> Dict[str, Any]:
    """
    获取当前认证的平台信息
    
    Args:
        authorization: Authorization头
        
    Returns:
        Dict[str, Any]: 平台信息
        
    Raises:
        HTTPException: 认证失败时抛出异常
    """
    try:
        # 解析Bearer Token
        if not authorization.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的Authorization头格式"
            )
        
        token = authorization.split(" ")[1]
        
        # 验证JWT Token
        jwt_service = JWTService()
        payload = jwt_service.decode_token(token)
        
        return {
            "customer_id": payload.get("customer_id"),
            "app_id": payload.get("app_id")
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token无效或已过期"
        )

# Redis客户端（用于获取data_key）
try:
    import redis
    redis_client = redis.Redis.from_url(settings.REDIS_URL)
except ImportError:
    redis_client = None

# 内存存储（Redis不可用时的备选方案）
data_key_store = {}

def get_data_key(customer_id: int) -> Optional[str]:
    """
    获取客户的数据加密密钥
    
    Args:
        customer_id: 客户ID
        
    Returns:
        Optional[str]: 数据密钥，如果不存在返回None
    """
    if redis_client:
        try:
            data_key = redis_client.get(f"data_key:{customer_id}")
            if data_key:
                return data_key.decode('utf-8')
        except Exception:
            pass
    
    return data_key_store.get(customer_id)

def encrypt_data(data_key: str, plaintext: str) -> Dict[str, str]:
    """
    使用AES-256-GCM加密数据
    
    Args:
        data_key: 数据密钥（Base64编码）
        plaintext: 明文数据
        
    Returns:
        Dict[str, str]: 包含加密数据和IV的字典
        
    Raises:
        Exception: 加密失败时抛出异常
    """
    try:
        # 解码data_key（假设是Base64编码）
        key = base64.b64decode(data_key)
        
        # 生成随机IV
        iv = get_random_bytes(12)  # GCM模式推荐12字节IV
        
        # 创建AES-GCM加密器
        cipher = AES.new(key, AES.MODE_GCM, nonce=iv)
        
        # 加密数据
        ciphertext, tag = cipher.encrypt_and_digest(plaintext.encode('utf-8'))
        
        # 将密文和认证标签合并
        encrypted_data = ciphertext + tag
        
        return {
            "data": base64.b64encode(encrypted_data).decode('utf-8'),
            "iv": base64.b64encode(iv).decode('utf-8')
        }
        
    except Exception as e:
        raise Exception(f"数据加密失败: {str(e)}")

def load_result_data(file_path: str) -> Optional[Dict[str, Any]]:
    """
    从文件加载结果数据
    
    Args:
        file_path: 文件路径
        
    Returns:
        Optional[Dict[str, Any]]: 结果数据，如果文件不存在返回None
    """
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception:
        pass
    return None

@router.get("/{upload_id}", response_model=ResultResponse, summary="查询单条数据处理结果")
async def get_result(
    upload_id: str,
    authorization: str = Header(..., alias="Authorization"),
    include_data: bool = Query(True, description="是否包含结果数据"),
    db: Session = Depends(get_db)
) -> ResultResponse:
    """
    查询单条数据的处理结果
    
    Args:
        upload_id: 上传记录ID
        authorization: 认证头
        include_data: 是否包含结果数据
        db: 数据库会话
        
    Returns:
        ResultResponse: 处理结果
        
    Raises:
        HTTPException: 查询失败时抛出异常
    """
    try:
        # 验证访问令牌
        customer_info = get_current_customer(authorization)
        customer_id = customer_info["customer_id"]
        
        # 查询上传记录
        upload = db.query(DataUpload).filter(
            DataUpload.upload_id == upload_id,
            DataUpload.customer_id == customer_id
        ).first()
        
        if not upload:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="上传记录不存在"
            )
        
        # 构建响应数据
        result = ResultResponse(
            upload_id=upload.upload_id,
            batch_id=upload.batch_id,
            filename=upload.filename,
            file_size=upload.file_size,
            status=upload.status,
            progress=upload.progress,
            error_message=upload.error_message,
            created_at=upload.created_at,
            updated_at=upload.updated_at,
            completed_at=upload.completed_at
        )
        
        # 如果需要包含结果数据且状态为已完成，加载结果数据
        if include_data and upload.status == "completed":
            result_file_path = os.path.join(
                settings.UPLOAD_DIR,
                "results",
                upload.batch_id,
                f"{upload.upload_id}.json"
            )
            result.result_data = load_result_data(result_file_path)
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"查询处理结果失败: {str(e)}"
        )


@router.get("/batch/{batch_id}/encrypted", response_model=BatchResultResponse, summary="查询加密的批次处理结果")
async def get_batch_result_encrypted(
    batch_id: str,
    authorization: str = Header(..., alias="Authorization"),
    db: Session = Depends(get_db)
) -> BatchResultResponse:
    """
    查询批次的处理结果，并以加密形式返回
    
    Args:
        batch_id: 批次ID
        authorization: 认证头
        db: 数据库会话
        
    Returns:
        BatchResultResponse: 加密的批次结果
        
    Raises:
        HTTPException: 查询失败时抛出异常
    """
    try:
        # 验证访问令牌
        customer_info = get_current_customer(authorization)
        customer_id = customer_info["customer_id"]
        
        # 查询批次数据
        from app.models.batch import DataBatch
        batch = db.query(DataBatch).filter(
            DataBatch.batch_id == batch_id,
            DataBatch.customer_id == customer_id
        ).first()
        
        if not batch:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="批次不存在"
            )
        
        # 获取批次状态
        status_value = batch.status
        
        # 如果批次已完成或失败，准备结果数据
        if status_value in ["completed", "failed"]:
            # 构建结果数据
            result_data = {
                "batch_id": batch.batch_id,
                "batch_name": batch.batch_name,
                "status": status_value,
                "total_count": batch.total_count,
                "completed_count": batch.completed_count,
                "failed_count": batch.failed_count,
                "success_rate": batch.success_rate,
                "processing_time": batch.processing_time,
                "started_at": batch.started_at.isoformat() if batch.started_at else None,
                "completed_at": batch.completed_at.isoformat() if batch.completed_at else None,
                "error_message": batch.error_message
            }
            
            # 获取数据密钥
            data_key = get_data_key(customer_id)
            if not data_key:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="数据密钥不存在，请重新认证"
                )
            
            # 加密结果数据
            encrypted_result = encrypt_data(data_key, json.dumps(result_data))
            
            # 生成签名
            signature = hmac.new(
                data_key.encode('utf-8'),
                encrypted_result["data"].encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            return BatchResultResponse(
                status=status_value,
                data=encrypted_result["data"],
                iv=encrypted_result["iv"],
                result_sign=signature
            )
        else:
            # 批次未完成，只返回状态
            return BatchResultResponse(
                status=status_value
            )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="查询批次结果失败"
        )
        
        # 查询上传记录
        upload = db.query(DataUpload).filter(
            DataUpload.upload_id == upload_id,
            DataUpload.customer_id == customer_id
        ).first()
        
        if not upload:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="数据记录不存在"
            )
        
        # 加载结果数据
        result_data = None
        if include_data and upload.file_path:
            result_data = load_result_data(upload.file_path)
        
        # 计算处理进度
        progress = None
        if upload.status == 'processing':
            # 这里可以根据实际情况计算进度
            # 暂时使用简单的时间估算
            elapsed_time = (datetime.now() - upload.created_at).total_seconds()
            progress = min(elapsed_time / 300.0, 0.95)  # 假设5分钟完成，最多95%
        elif upload.status == 'completed':
            progress = 1.0
        elif upload.status == 'failed':
            progress = 0.0
        
        return ResultResponse(
            upload_id=upload.upload_id or str(upload.id),
            batch_id=upload.batch_id or "unknown",
            filename=upload.filename,
            file_size=upload.file_size,
            status=upload.status,
            progress=progress,
            result_data=result_data,
            error_message=upload.error_message,
            created_at=upload.created_at,
            updated_at=upload.updated_at,
            completed_at=upload.completed_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="查询结果失败"
        )

@router.get("/batch/{batch_id}", response_model=ResultListResponse, summary="查询批次处理结果")
async def get_batch_results(
    batch_id: str,
    authorization: str = Header(..., alias="Authorization"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页大小"),
    status_filter: Optional[str] = Query(None, description="状态过滤"),
    include_data: bool = Query(False, description="是否包含结果数据"),
    db: Session = Depends(get_db)
) -> ResultListResponse:
    """
    查询批次的处理结果列表
    
    Args:
        batch_id: 批次ID
        authorization: 认证头
        page: 页码
        size: 每页大小
        status_filter: 状态过滤
        include_data: 是否包含结果数据
        db: 数据库会话
        
    Returns:
        ResultListResponse: 结果列表
        
    Raises:
        HTTPException: 查询失败时抛出异常
    """
    try:
        # 验证访问令牌
        customer_info = get_current_customer(authorization)
        customer_id = customer_info["customer_id"]
        
        # 构建查询条件
        query_conditions = [
            DataUpload.batch_id == batch_id,
            DataUpload.customer_id == customer_id
        ]
        
        if status_filter:
            query_conditions.append(DataUpload.status == status_filter)
        
        # 查询总数
        total = db.query(DataUpload).filter(
            and_(*query_conditions)
        ).count()
        
        # 分页查询
        offset = (page - 1) * size
        uploads = db.query(DataUpload).filter(
            and_(*query_conditions)
        ).order_by(
            DataUpload.created_at.desc()
        ).offset(offset).limit(size).all()
        
        # 构建响应数据
        items = []
        for upload in uploads:
            # 加载结果数据
            result_data = None
            if include_data and upload.file_path:
                result_data = load_result_data(upload.file_path)
            
            # 计算处理进度
            progress = None
            if upload.status == 'processing':
                elapsed_time = (datetime.now() - upload.created_at).total_seconds()
                progress = min(elapsed_time / 300.0, 0.95)
            elif upload.status == 'completed':
                progress = 1.0
            elif upload.status == 'failed':
                progress = 0.0
            
            items.append(ResultResponse(
                upload_id=upload.upload_id or str(upload.id),
                batch_id=upload.batch_id or "unknown",
                filename=upload.filename,
                file_size=upload.file_size,
                status=upload.status,
                progress=progress,
                result_data=result_data,
                error_message=upload.error_message,
                created_at=upload.created_at,
                updated_at=upload.updated_at,
                completed_at=upload.completed_at
            ))
        
        return ResultListResponse(
            total=total,
            page=page,
            size=size,
            items=items
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="查询批次结果失败"
        )

@router.get("/batch/{batch_id}/stats", response_model=ResultStatsResponse, summary="查询批次统计信息")
async def get_batch_stats(
    batch_id: str,
    authorization: str = Header(..., alias="Authorization"),
    db: Session = Depends(get_db)
) -> ResultStatsResponse:
    """
    查询批次的统计信息
    
    Args:
        batch_id: 批次ID
        authorization: 认证头
        db: 数据库会话
        
    Returns:
        ResultStatsResponse: 统计信息
        
    Raises:
        HTTPException: 查询失败时抛出异常
    """
    try:
        # 验证访问令牌
        customer_info = get_current_customer(authorization)
        customer_id = customer_info["customer_id"]
        
        # 查询批次数据
        uploads = db.query(DataUpload).filter(
            DataUpload.batch_id == batch_id,
            DataUpload.customer_id == customer_id
        ).all()
        
        if not uploads:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="批次不存在"
            )
        
        # 统计信息
        total_count = len(uploads)
        pending_count = sum(1 for u in uploads if u.status == 'pending')
        processing_count = sum(1 for u in uploads if u.status == 'processing')
        completed_count = sum(1 for u in uploads if u.status == 'completed')
        failed_count = sum(1 for u in uploads if u.status == 'failed')
        
        # 计算成功率
        success_rate = completed_count / total_count if total_count > 0 else 0.0
        
        # 计算平均处理时间
        avg_processing_time = None
        completed_uploads = [u for u in uploads if u.status == 'completed' and u.completed_at]
        if completed_uploads:
            total_time = sum(
                (u.completed_at - u.created_at).total_seconds()
                for u in completed_uploads
            )
            avg_processing_time = total_time / len(completed_uploads)
        
        return ResultStatsResponse(
            total_count=total_count,
            pending_count=pending_count,
            processing_count=processing_count,
            completed_count=completed_count,
            failed_count=failed_count,
            success_rate=success_rate,
            avg_processing_time=avg_processing_time
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="查询统计信息失败"
        )

@router.get("/batch/{batch_id}/export", summary="导出批次结果")
async def export_batch_results(
    batch_id: str,
    authorization: str = Header(..., alias="Authorization"),
    format: str = Query("json", description="导出格式 (json/csv)"),
    status_filter: Optional[str] = Query(None, description="状态过滤"),
    db: Session = Depends(get_db)
):
    """
    导出批次的处理结果
    
    Args:
        batch_id: 批次ID
        authorization: 认证头
        format: 导出格式
        status_filter: 状态过滤
        db: 数据库会话
        
    Returns:
        FileResponse: 导出文件
        
    Raises:
        HTTPException: 导出失败时抛出异常
    """
    try:
        # 验证访问令牌
        customer_info = get_current_customer(authorization)
        customer_id = customer_info["customer_id"]
        
        # 构建查询条件
        query_conditions = [
            DataUpload.batch_id == batch_id,
            DataUpload.customer_id == customer_id
        ]
        
        if status_filter:
            query_conditions.append(DataUpload.status == status_filter)
        
        # 查询数据
        uploads = db.query(DataUpload).filter(
            and_(*query_conditions)
        ).order_by(
            DataUpload.created_at.asc()
        ).all()
        
        if not uploads:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="批次不存在或无数据"
            )
        
        # 创建导出目录
        export_dir = Path(settings.UPLOAD_PATH) / "exports"
        export_dir.mkdir(parents=True, exist_ok=True)
        
        # 生成文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"batch_{batch_id[:8]}_{timestamp}.{format}"
        file_path = export_dir / filename
        
        if format.lower() == "json":
            # JSON格式导出
            export_data = []
            for upload in uploads:
                result_data = load_result_data(upload.file_path) if upload.file_path else None
                
                export_data.append({
                    "upload_id": upload.upload_id or str(upload.id),
                    "batch_id": upload.batch_id,
                    "filename": upload.filename,
                    "file_size": upload.file_size,
                    "status": upload.status,
                    "result_data": result_data,
                    "error_message": upload.error_message,
                    "created_at": upload.created_at.isoformat(),
                    "updated_at": upload.updated_at.isoformat() if upload.updated_at else None,
                    "completed_at": upload.completed_at.isoformat() if upload.completed_at else None
                })
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            
            return FileResponse(
                path=str(file_path),
                filename=filename,
                media_type="application/json"
            )
            
        elif format.lower() == "csv":
            # CSV格式导出
            import csv
            
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                # 写入表头
                writer.writerow([
                    "上传ID", "批次ID", "文件名", "文件大小", "状态",
                    "错误信息", "创建时间", "更新时间", "完成时间"
                ])
                
                # 写入数据
                for upload in uploads:
                    writer.writerow([
                        upload.upload_id or str(upload.id),
                        upload.batch_id,
                        upload.filename,
                        upload.file_size,
                        upload.status,
                        upload.error_message or "",
                        upload.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                        upload.updated_at.strftime("%Y-%m-%d %H:%M:%S") if upload.updated_at else "",
                        upload.completed_at.strftime("%Y-%m-%d %H:%M:%S") if upload.completed_at else ""
                    ])
            
            return FileResponse(
                path=str(file_path),
                filename=filename,
                media_type="text/csv"
            )
        
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="不支持的导出格式"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="导出结果失败"
        )

@router.get("/", response_model=ResultListResponse, summary="查询所有结果")
async def get_all_results(
    authorization: str = Header(..., alias="Authorization"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页大小"),
    status_filter: Optional[str] = Query(None, description="状态过滤"),
    batch_id_filter: Optional[str] = Query(None, description="批次ID过滤"),
    start_date: Optional[str] = Query(None, description="开始日期 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="结束日期 (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
) -> ResultListResponse:
    """
    查询所有处理结果
    
    Args:
        authorization: 认证头
        page: 页码
        size: 每页大小
        status_filter: 状态过滤
        batch_id_filter: 批次ID过滤
        start_date: 开始日期
        end_date: 结束日期
        db: 数据库会话
        
    Returns:
        ResultListResponse: 结果列表
        
    Raises:
        HTTPException: 查询失败时抛出异常
    """
    try:
        # 验证访问令牌
        customer_info = get_current_customer(authorization)
        customer_id = customer_info["customer_id"]
        
        # 构建查询条件
        query_conditions = [DataUpload.customer_id == customer_id]
        
        if status_filter:
            query_conditions.append(DataUpload.status == status_filter)
        
        if batch_id_filter:
            query_conditions.append(DataUpload.batch_id == batch_id_filter)
        
        # 日期过滤
        if start_date:
            try:
                start_dt = datetime.strptime(start_date, "%Y-%m-%d")
                query_conditions.append(DataUpload.created_at >= start_dt)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="开始日期格式错误，请使用 YYYY-MM-DD 格式"
                )
        
        if end_date:
            try:
                end_dt = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
                query_conditions.append(DataUpload.created_at < end_dt)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="结束日期格式错误，请使用 YYYY-MM-DD 格式"
                )
        
        # 查询总数
        total = db.query(DataUpload).filter(
            and_(*query_conditions)
        ).count()
        
        # 分页查询
        offset = (page - 1) * size
        uploads = db.query(DataUpload).filter(
            and_(*query_conditions)
        ).order_by(
            DataUpload.created_at.desc()
        ).offset(offset).limit(size).all()
        
        # 构建响应数据
        items = []
        for upload in uploads:
            # 计算处理进度
            progress = None
            if upload.status == 'processing':
                elapsed_time = (datetime.now() - upload.created_at).total_seconds()
                progress = min(elapsed_time / 300.0, 0.95)
            elif upload.status == 'completed':
                progress = 1.0
            elif upload.status == 'failed':
                progress = 0.0
            
            items.append(ResultResponse(
                upload_id=upload.upload_id or str(upload.id),
                batch_id=upload.batch_id or "unknown",
                filename=upload.filename,
                file_size=upload.file_size,
                status=upload.status,
                progress=progress,
                result_data=None,  # 列表查询不包含详细数据
                error_message=upload.error_message,
                created_at=upload.created_at,
                updated_at=upload.updated_at,
                completed_at=upload.completed_at
            ))
        
        return ResultListResponse(
            total=total,
            page=page,
            size=size,
            items=items
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="查询结果列表失败"
        )