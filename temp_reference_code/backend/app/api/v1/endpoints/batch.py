#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批次管理接口

实现批次管理功能，包括：
1. 创建批次
2. 查询批次列表
3. 批次状态管理
4. 批次数据统计

Author: System
Date: 2024
"""

import uuid
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from fastapi import APIRouter, Depends, Header, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.models.customer import Customer
from app.models.log import DataUpload
from app.models.batch import DataBatch
from app.services.auth import JWTService
from app.core.exceptions import ValidationException
from app.services.encryption import EncryptionService
from app.core.business_codes import BusinessCode, BusinessResponse, BusinessException
import json
import base64
from datetime import datetime

router = APIRouter()

# 批次数据响应模型
class BatchDataResponse(BaseModel):
    """
    批次数据响应模型
    """
    batch_id: str = Field(..., description="批次ID")
    total: int = Field(..., description="总数据条数")
    page: int = Field(..., description="当前页码")
    size: int = Field(..., description="每页大小")
    items: List[Dict[str, Any]] = Field(..., description="数据列表")

# 批次创建请求模型
class BatchCreateRequest(BaseModel):
    """
    批次创建请求模型
    """
    batch_name: Optional[str] = Field(None, max_length=100, description="批次名称")
    description: Optional[str] = Field(None, max_length=500, description="批次描述")
    expected_count: Optional[int] = Field(None, ge=1, description="预期数据条数")

# 批次完成请求模型
class BatchCompleteRequest(BaseModel):
    """
    批次完成请求模型
    """
    timestamp: int = Field(..., description="时间戳")
    nonce: str = Field(..., description="随机字符串")
    data: str = Field(..., description="加密的业务数据")
    iv: str = Field(..., description="初始化向量")
    signature: Optional[str] = Field(None, description="数据签名")
    needread: Optional[bool] = Field(True, description="是否需要回调")

# 批次完成业务数据模型
class BatchCompleteData(BaseModel):
    """
    批次完成业务数据模型
    """
    remark: Optional[str] = Field(None, description="备注信息")
    callback_url: str = Field(..., description="回调通知地址")
    total: int = Field(..., description="总数据条数")

# 批次响应模型
class BatchResponse(BaseModel):
    """
    批次响应模型
    """
    batch_id: str = Field(..., description="批次ID")
    batch_name: Optional[str] = Field(None, description="批次名称")
    description: Optional[str] = Field(None, description="批次描述")
    status: str = Field(..., description="批次状态")
    total_count: int = Field(0, description="总数据条数")
    pending_count: int = Field(0, description="待处理数据条数")
    processing_count: int = Field(0, description="处理中数据条数")
    completed_count: int = Field(0, description="已完成数据条数")
    failed_count: int = Field(0, description="失败数据条数")
    needread: Optional[bool] = Field(True, description="是否需要审读")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")

# 批次列表响应模型
class BatchListResponse(BaseModel):
    """
    批次列表响应模型
    """
    total: int = Field(..., description="总数量")
    page: int = Field(..., description="当前页码")
    size: int = Field(..., description="每页大小")
    items: List[BatchResponse] = Field(..., description="批次列表")

def get_current_customer(authorization: str = Header(...)) -> Dict[str, Any]:
    """
    获取当前认证的平台信息
    
    Args:
        authorization: Authorization头
        
    Returns:
        Dict[str, Any]: 平台信息
        
    Raises:
        BusinessException: 认证失败时抛出异常
    """
    try:
        # 解析Bearer Token
        if not authorization.startswith("Bearer "):
            raise BusinessException(
                BusinessCode.PARAM_ERROR,
                "无效的Authorization头格式"
            )
        
        token = authorization.split(" ")[1]
        
        # 验证JWT Token
        jwt_service = JWTService()
        payload = jwt_service.decode_token(token)
        
        return {
            "customer_id": payload.get("customer_id"),
            "app_id": payload.get("app_id")
        }
        
    except BusinessException:
        raise
    except Exception as e:
        raise BusinessException(
            BusinessCode.TOKEN_INVALID,
            "Token无效或已过期"
        )

@router.post("/", response_model=Dict[str, Any], summary="创建批次")
async def create_batch(
    batch_request: BatchCreateRequest,
    authorization: str = Header(..., alias="Authorization"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    创建新的数据批次
    
    Args:
        batch_request: 批次创建请求
        authorization: 认证头
        db: 数据库会话
        
    Returns:
        Dict[str, Any]: 创建结果
        
    Raises:
        BusinessException: 创建失败时抛出异常
    """
    try:
        # 验证访问令牌
        customer_info = get_current_customer(authorization)
        customer_id = customer_info["customer_id"]
        
        # 验证客户状态
        customer = db.query(Customer).filter(
            Customer.id == customer_id,
            Customer.status == True
        ).first()
        
        if not customer:
            raise BusinessException(
                BusinessCode.CUSTOMER_DISABLED,
                "客户账户无效或已停用"
            )
        
        # 创建批次记录
        batch = DataBatch.create_batch(
            db=db,
            customer_id=customer_id,
            batch_name=batch_request.batch_name,
            description=batch_request.description,
            expected_count=batch_request.expected_count
        )
        
        return BusinessResponse.success({
            "batch_id": batch.batch_id,
            "batch_name": batch.batch_name,
            "description": batch.description,
            "expected_count": batch.expected_count
        }, "批次创建成功")
        
    except BusinessException:
        raise
    except Exception as e:
        raise BusinessException(
            BusinessCode.INTERNAL_ERROR,
            "批次创建失败"
        )

@router.get("/", response_model=BatchListResponse, summary="查询批次列表")
async def get_batch_list(
    authorization: str = Header(..., alias="Authorization"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页大小"),
    status_filter: Optional[str] = Query(None, description="状态过滤"),
    start_date: Optional[str] = Query(None, description="开始日期 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="结束日期 (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
) -> BatchListResponse:
    """
    查询批次列表
    
    Args:
        authorization: 认证头
        page: 页码
        size: 每页大小
        status_filter: 状态过滤
        start_date: 开始日期
        end_date: 结束日期
        db: 数据库会话
        
    Returns:
        BatchListResponse: 批次列表
        
    Raises:
        BusinessException: 查询失败时抛出异常
    """
    try:
        # 验证访问令牌（仅用于认证，不过滤数据）
        customer_info = get_current_customer(authorization)
        
        # 构建批次查询条件（移除customer_id过滤）
        batch_query_conditions = []
        
        # 日期过滤
        if start_date:
            try:
                start_dt = datetime.strptime(start_date, "%Y-%m-%d")
                batch_query_conditions.append(DataBatch.created_at >= start_dt)
            except ValueError:
                raise BusinessException(
                    BusinessCode.PARAM_ERROR,
                    "开始日期格式错误，请使用 YYYY-MM-DD 格式"
                )
        
        if end_date:
            try:
                end_dt = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
                batch_query_conditions.append(DataBatch.created_at < end_dt)
            except ValueError:
                raise BusinessException(
                    BusinessCode.PARAM_ERROR,
                    "结束日期格式错误，请使用 YYYY-MM-DD 格式"
                )
        
        if status_filter:
            batch_query_conditions.append(DataBatch.status == status_filter)
        
        # 查询批次列表（返回所有用户的批次）
        if batch_query_conditions:
            batch_query = db.query(DataBatch).filter(and_(*batch_query_conditions))
        else:
            batch_query = db.query(DataBatch)
        
        # 分页查询
        total = batch_query.count()
        offset = (page - 1) * size
        batches = batch_query.order_by(DataBatch.created_at.desc()).offset(offset).limit(size).all()
        
        # 更新批次统计信息并构建响应数据
        items = []
        for batch in batches:
            # 更新批次统计信息
            batch.update_counts(db)
            
            items.append(BatchResponse(
                batch_id=batch.batch_id,
                batch_name=batch.batch_name,
                description=batch.description,
                status=batch.status,
                total_count=batch.total_count,
                pending_count=batch.pending_count,
                processing_count=batch.processing_count,
                completed_count=batch.completed_count,
                failed_count=batch.failed_count,
                needread=batch.needread,
                created_at=batch.created_at,
                updated_at=batch.updated_at
            ))
        
        return BatchListResponse(
            total=total,
            page=page,
            size=size,
            items=items
        )
        
    except BusinessException:
        raise
    except Exception as e:
        print("e",e)
        raise BusinessException(
            BusinessCode.INTERNAL_ERROR,
            "查询批次列表失败"
        )

@router.get("/{batch_id}", response_model=BatchResponse, summary="查询批次详情")
async def get_batch_detail(
    batch_id: str,
    authorization: str = Header(..., alias="Authorization"),
    db: Session = Depends(get_db)
) -> BatchResponse:
    """
    查询批次详细信息
    
    Args:
        batch_id: 批次ID
        authorization: 认证头
        db: 数据库会话
        
    Returns:
        BatchResponse: 批次详情
        
    Raises:
        BusinessException: 查询失败时抛出异常
    """
    try:
        # 验证访问令牌
        customer_info = get_current_customer(authorization)
        customer_id = customer_info["customer_id"]
        
        # 查询批次信息
        batch = db.query(DataBatch).filter(
            DataBatch.customer_id == customer_id,
            DataBatch.batch_id == batch_id
        ).first()
        
        if not batch:
            raise BusinessException(
                BusinessCode.BATCH_NOT_FOUND,
                "批次不存在"
            )
        
        # 更新批次统计信息
        batch.update_counts(db)
        
        return BatchResponse(
            batch_id=batch.batch_id,
            batch_name=batch.batch_name,
            description=batch.description,
            status=batch.status,
            total_count=batch.total_count,
            pending_count=batch.pending_count,
            processing_count=batch.processing_count,
            completed_count=batch.completed_count,
            failed_count=batch.failed_count,
            needread=batch.needread,
            created_at=batch.created_at,
            updated_at=batch.updated_at
        )
        
    except BusinessException:
        raise
    except Exception as e:
        raise BusinessException(
            BusinessCode.INTERNAL_ERROR,
            "查询批次详情失败"
        )

@router.get("/{batch_id}/data", response_model=Dict[str, Any], summary="查询批次数据")
async def get_batch_data(
    batch_id: str,
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页大小"),
    authorization: str = Header(..., alias="Authorization"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    根据批次ID查询api_usage_logs表的数据
    
    Args:
        batch_id: 批次ID
        page: 页码，从1开始
        size: 每页大小，最大100
        authorization: 认证头
        db: 数据库会话
        
    Returns:
        Dict[str, Any]: 分页的批次数据
    """
    try:
        # 验证访问令牌
        customer_info = get_current_customer(authorization)
        customer_id = customer_info["customer_id"]
        
        # 使用原生SQL查询批次数据
        import logging
        from sqlalchemy import text
        
        # 设置日志
        logger = logging.getLogger(__name__)
        
        # 打印查询参数
        print(f"[DEBUG] 查询参数: batch_id={batch_id}, customer_id={customer_id}, page={page}, size={size}")
        logger.info(f"查询参数: batch_id={batch_id}, customer_id={customer_id}, page={page}, size={size}")
        
        # 构建原生SQL查询
        count_sql = """
        SELECT COUNT(*) as total
        FROM api_usage_logs 
        WHERE batch_id = :batch_id 
        """
        
        data_sql = """
        SELECT id, batch_id, api_id, http_method, request_url, 
               response_status, processing_time, file_path, created_at
        FROM api_usage_logs 
        WHERE batch_id = :batch_id 
        ORDER BY created_at DESC
        LIMIT :limit OFFSET :offset
        """
        
        
        # 执行计数查询
        count_result = db.execute(text(count_sql), {
            'batch_id': batch_id
        })
        total = count_result.scalar()
        print(f"[DEBUG] 查询总数: {total}")
        logger.info(f"查询总数: {total}")
        
        # 计算分页参数
        offset = (page - 1) * size
        
        # 执行分页查询
        data_result = db.execute(text(data_sql), {
            'batch_id': batch_id,
            'limit': size,
            'offset': offset
        })
        
        logs = data_result.fetchall()
        print(f"[DEBUG] 查询结果数量: {len(logs)}")
        logger.info(f"查询结果数量: {len(logs)}")
        
        # 格式化数据
        items = []
        for log in logs:
            item = {
                "id": log[0],  # id
                "batch_id": log[1],  # batch_id
                "api_id": log[2],  # api_id
                "http_method": log[3],  # http_method
                "request_url": log[4],  # request_url
                "response_status": log[5],  # response_status
                "processing_time": float(log[6]) if log[6] else None,  # processing_time
                "file_path": log[7],  # file_path
                "created_at": log[8].isoformat() if log[8] else None  # created_at
            }
            items.append(item)
            
        print(f"[DEBUG] 格式化后的数据项数: {len(items)}")
        if items:
            print(f"[DEBUG] 第一条数据示例: {items[0]}")
        
        return {
            "success": True,
            "message": "查询成功",
            "data": {
                "total": total,
                "page": page,
                "size": size,
                "items": items
            }
        }
        
    except BusinessException:
        raise
    except Exception as e:
        raise BusinessException(
            BusinessCode.INTERNAL_ERROR,
            f"查询批次数据失败: {str(e)}"
        )

@router.delete("/{batch_id}", summary="删除批次")
async def delete_batch(
    batch_id: str,
    authorization: str = Header(..., alias="Authorization"),
    force: bool = Query(False, description="是否强制删除"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    删除批次及其相关数据
    
    Args:
        batch_id: 批次ID
        authorization: 认证头
        force: 是否强制删除
        db: 数据库会话
        
    Returns:
        Dict[str, Any]: 删除结果
        
    Raises:
        BusinessException: 删除失败时抛出异常
    """
    try:
        # 验证访问令牌
        customer_info = get_current_customer(authorization)
        customer_id = customer_info["customer_id"]
        
        # 查询批次信息
        batch = db.query(DataBatch).filter(
            DataBatch.customer_id == customer_id,
            DataBatch.batch_id == batch_id
        ).first()
        
        if not batch:
            raise BusinessException(
                BusinessCode.BATCH_NOT_FOUND,
                "批次不存在"
            )
        
        # 检查是否有正在处理的数据
        if batch.status == 'processing' and not force:
            raise BusinessException(
                BusinessCode.BATCH_STATUS_INVALID,
                "批次正在处理中，请使用强制删除或等待处理完成"
            )
        
        # 查询批次下的所有上传记录
        uploads = db.query(DataUpload).filter(
            DataUpload.batch_id == batch_id,
            DataUpload.customer_id == customer_id
        ).all()
        
        # 删除上传记录
        deleted_count = len(uploads)
        for upload in uploads:
            db.delete(upload)
        
        # 删除批次记录
        db.delete(batch)
        db.commit()
        
        return BusinessResponse.success({
            "batch_id": batch_id,
            "deleted_count": deleted_count
        }, "批次删除成功")
        
    except BusinessException:
        raise
    except Exception as e:
        db.rollback()
        raise BusinessException(
            BusinessCode.INTERNAL_ERROR,
            "批次删除失败"
        )

@router.post("/{batch_id}/process", summary="处理批次数据")
async def process_batch(
    batch_id: str,
    authorization: str = Header(..., alias="Authorization"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    开始处理批次数据
    
    Args:
        batch_id: 批次ID
        authorization: 认证头
        db: 数据库会话
        
    Returns:
        Dict[str, Any]: 处理结果
        
    Raises:
        BusinessException: 处理失败时抛出异常
    """
    try:
        # 验证访问令牌
        customer_info = get_current_customer(authorization)
        customer_id = customer_info["customer_id"]
        
        # 查询批次信息
        batch = db.query(DataBatch).filter(
            DataBatch.customer_id == customer_id,
            DataBatch.batch_id == batch_id
        ).first()
        
        if not batch:
            raise BusinessException(
                BusinessCode.BATCH_NOT_FOUND,
                "批次不存在"
            )
        
        # 检查批次状态
        if batch.status != 'pending':
            raise BusinessException(
                BusinessCode.BATCH_STATUS_INVALID,
                f"批次状态为 {batch.status}，无法开始处理"
            )
        
        # 查询待处理的上传记录
        pending_uploads = db.query(DataUpload).filter(
            DataUpload.batch_id == batch_id,
            DataUpload.customer_id == customer_id,
            DataUpload.status == 'pending'
        ).all()
        
        if not pending_uploads:
            raise BusinessException(
                BusinessCode.DATA_NOT_FOUND,
                "批次中没有待处理的数据"
            )
        
        # 设置批次为处理中状态
        batch.set_processing()
        
        # 更新上传记录状态为处理中
        for upload in pending_uploads:
            upload.set_processing()
        
        db.commit()
        
        # TODO: 这里可以添加异步任务处理逻辑
        # 例如：使用Celery或其他任务队列来处理数据
        
        return BusinessResponse.success({
            "batch_id": batch_id,
            "processing_count": len(pending_uploads)
        }, "批次处理已开始")
        
    except BusinessException:
        raise
    except Exception as e:
        db.rollback()
        raise BusinessException(
            BusinessCode.INTERNAL_ERROR,
            "批次处理失败"
        )

@router.post("/{api_code}/{batch_id}/complete", summary="批次完成")
async def complete_batch(
    api_code: str,
    batch_id: str,
    request_data: BatchCompleteRequest,
    authorization: str = Header(..., alias="Authorization"),
    x_data_encrypted: str = Header(..., alias="X-Data-Encrypted"),
    x_data_signature: Optional[str] = Header(None, alias="X-Data-Signature"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    标记批次数据上传完成，在data_batches表中创建新记录
    
    当客户端调用此接口时，会在data_batches表中创建一条新的批次记录，
    其他程序检测到data_batches表中有新数据后，会开始处理api_usage_logs表中对应的数据。
    
    Args:
        api_code: API代码（路径参数）
        batch_id: 批次ID
        request_data: 请求数据
        authorization: 认证头
        x_data_encrypted: 数据加密标识
        x_data_signature: 数据签名
        db: 数据库会话
        
    Returns:
        Dict[str, Any]: 完成结果
        
    Raises:
        BusinessException: 处理失败时抛出异常
    """
    try:
        # 验证访问令牌
        customer_info = get_current_customer(authorization)
        customer_id = customer_info["customer_id"]
        
        # 验证API代码是否存在且有效
        from app.models.api import CustomApi
        api_config = db.query(CustomApi).filter(
            CustomApi.api_code == api_code,
            CustomApi.customer_id == customer_id
        ).first()
        
        if not api_config:
            raise BusinessException(
                BusinessCode.API_NOT_FOUND,
                f"API代码 '{api_code}' 不存在或无权限访问"
            )
        
        if not api_config.status:
            raise BusinessException(
                BusinessCode.API_DISABLED,
                f"API '{api_code}' 已停用"
            )
        
        # 检查批次是否已经存在于data_batches表中
        existing_batch = db.query(DataBatch).filter(
            DataBatch.batch_id == batch_id
        ).first()
        
        if existing_batch:
            raise BusinessException(
                BusinessCode.BATCH_ALREADY_COMPLETED,
                f"批次 {batch_id} 已经完成，无法重复提交"
            )
        
        # 获取客户的data_key用于解密
        from .data import get_data_key
        data_key = get_data_key(customer_id)
        if not data_key:
            raise BusinessException(
                BusinessCode.DATA_KEY_NOT_FOUND,
                "客户data_key未配置"
            )
        
        # 解密业务数据（使用与数据上传接口相同的AES-GCM解密方法）
        try:
            # 使用data.py中的decrypt_data函数，它使用AES-GCM模式
            from .data import decrypt_data
            business_data = decrypt_data(
                data_key, 
                request_data.data, 
                request_data.iv
            )
            
            # 验证业务数据
            complete_data = BatchCompleteData(**business_data)
            
        except Exception as e:
            raise BusinessException(
                BusinessCode.DATA_VALIDATION_FAILED,
                f"数据解密或解析失败: 解密失败: {str(e)}"
            )
        
        # 验证签名（如果提供）
        if request_data.signature or x_data_signature:
            from .data import verify_signature
            signature = request_data.signature or x_data_signature
            print("request_data.signature:", request_data.signature)
            print("request_data.data:", request_data.data)
            print("$"*60)
            if not verify_signature(data_key, request_data.data, signature):
                raise BusinessException(
                    BusinessCode.DATA_VALIDATION_FAILED,
                    "数据签名验证失败"
                )
        
        # 构建元数据信息
        metadata = {
            "callback_url": complete_data.callback_url,
            "remark": complete_data.remark,
            "completed_at": datetime.utcnow().isoformat(),
            "timestamp": request_data.timestamp,
            "nonce": request_data.nonce
        }
        
        # 在data_batches表中创建新的批次记录
        # 这是关键步骤：只有在data_batches表中有记录，其他程序才会开始处理api_usage_logs中的数据
        new_batch = DataBatch(
            customer_id=customer_id,
            api_id=api_config.id,  # 设置API ID
            batch_id=batch_id,
            batch_name=f"batch_{batch_id}",
            description=complete_data.remark or f"批次{batch_id}数据上传完成",
            status='pending',  # 待处理状态，等待后续程序处理
            expected_count=complete_data.total,
            total_count=0,  # 初始为0，后续处理时会更新
            pending_count=0,
            processing_count=0,
            completed_count=0,
            failed_count=0,
            needread=request_data.needread,  # 设置是否需要回调
            meta_data=metadata
        )
        
        db.add(new_batch)
        db.commit()
        db.refresh(new_batch)
        
        return BusinessResponse.success({
            "batch_id": batch_id,
            "expected_count": complete_data.total,
            # "callback_url": complete_data.callback_url,
            "status": "待处理",
            "created_at": new_batch.created_at.isoformat()
        }, "批次完成标记成功")
        
    except BusinessException:
        raise
    except Exception as e:
        db.rollback()
        raise BusinessException(
            BusinessCode.INTERNAL_ERROR,
            f"批次完成处理失败: {str(e)}"
        )