#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批次结果查询接口

实现批次数据处理结果查询功能，包括：
1. 查询批次处理结果
2. 结果状态统计

Author: System
Date: 2024
"""

import json
import os
from datetime import datetime
from typing import Dict, Any, Optional
import hmac
import hashlib
import base64
import json

from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.core.config import settings
from app.models.batch import DataBatch
from app.models.api import CustomApi
from app.services.auth import JWTService
from app.services.external_data import DataLink
from app.core.exceptions import ValidationException
from app.core.business_codes import BusinessException, BusinessCode, BusinessResponse
from app.api.v1.endpoints.data import get_data_key, encrypt_data

router = APIRouter()

# 批次结果响应模型
class BatchResultResponse(BaseModel):
    """
    批次结果响应模型
    """
    status: str = Field(..., description="处理状态：processing/completed/failed")
    data: Optional[str] = Field(None, description="加密后的结果数据")
    iv: Optional[str] = Field(None, description="初始化向量")
    result_sign: Optional[str] = Field(None, description="数据完整性签名")

def get_current_customer(authorization: str = Header(...)) -> Dict[str, Any]:
    """
    获取当前认证的客户信息
    
    Args:
        authorization: Authorization头
        
    Returns:
        Dict[str, Any]: 客户信息
        
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

@router.get("/{api_code}/{batch_id}", summary="查询批次处理结果")
async def get_batch_result(
    api_code: str,
    batch_id: str,
    authorization: str = Header(..., alias="Authorization"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    查询批次的处理结果
    
    Args:
        api_code: API代码，用于区分不同的API接口
        batch_id: 批次ID
        authorization: 认证头
        db: 数据库会话
        
    Returns:
        Dict[str, Any]: 统一业务响应格式，包含批次处理结果
        
    Raises:
        BusinessException: 查询失败时抛出异常
    """
    try:
        # 验证访问令牌
        customer_info = get_current_customer(authorization)
        customer_id = customer_info["customer_id"]
        
        # 首先通过 api_code 查找对应的 API
        api = db.query(CustomApi).filter(
            CustomApi.api_code == api_code,
            CustomApi.customer_id == customer_id
        ).first()
        
        if not api:
            raise BusinessException(
                BusinessCode.API_NOT_FOUND,
                "API不存在或无权限访问"
            )
        
        # 查询批次数据，使用 api_id 和 batch_id 确保不会混淆
        batch = db.query(DataBatch).filter(
            DataBatch.batch_id == batch_id,
            DataBatch.api_id == api.id,
            DataBatch.customer_id == customer_id
        ).first()
        
        #这一部分需要通过data_link = DataLink()
        #此处根据link_read_id，获取结果应该从哪个库的哪个表获取，此处只实现了一般的图书审读取结果
        api.link_read_id



        # 调用get_book_result方法，传递必需的参数
        # 这里使用batch_id作为批次标识，isbn参数传空字符串表示获取该批次的所有结果
        print(batch.status,":::::::::batch.status")
        if batch.status == 'completed':
            data_link = DataLink()
            result = data_link.get_book_result(batch_id, "")
        
        # 检查结果是否成功
            if not result.get('success', False):
                raise BusinessException(
                    BusinessCode.INTERNAL_ERROR,
                    f"获取批次结果失败: {result.get('error', '未知错误')}"
                )
        
            data = result.get('data', [])
        
        # if not batch:
        #     raise HTTPException(
        #         status_code=status.HTTP_404_NOT_FOUND,
        #         detail="批次不存在或不属于指定的API"
        #     )
        
        # 获取批次状态'pending','processing','completed','failed','cancelled'
        if batch.status == 'completed':
            status_value = "completed"
        elif batch.status == 'failed':
            status_value = "failed"
        elif batch.status == 'cancelled':
            status_value = "cancelled"
        else:
            status_value = "processing"
        
        # 准备响应数据
        result_data = None
        result_sign = None
        
        # 如果批次已完成或失败，准备结果数据
        if status_value in ["completed", "failed"]:
            # 构建结果数据
            result_data = {
                "batch_id": batch.batch_id,
                "batch_name": batch.batch_name,
                "status": status_value,
                "result": data,#返回具体的审读结果
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
                raise BusinessException(
                    BusinessCode.DATA_KEY_NOT_FOUND,
                    "数据密钥不存在，请重新认证"
                )
            
            # 加密结果数据
            encrypted_result = encrypt_data(data_key, json.dumps(result_data))
            
            # 生成签名
            signature = hmac.new(
                data_key.encode('utf-8'),
                encrypted_result["data"].encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            result_data = encrypted_result["data"]
            result_iv = encrypted_result["iv"]
            result_sign = signature
        
        # 构建响应数据
        response_data = {
            "status": status_value,
            "data": result_data,
            "iv": result_iv if status_value in ["completed", "failed"] else None,
            "result_sign": result_sign
        }
        
        return BusinessResponse.success(
            data=response_data,
            message="批次结果查询成功"
        )
        
    except BusinessException:
        raise
    except Exception as e:
        raise BusinessException(
            BusinessCode.INTERNAL_ERROR,
            f"查询批次结果失败: {str(e)}"
        )